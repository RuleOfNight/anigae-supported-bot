import re
from collections import deque

from db_methods import guilds, weekly_donations
from Commands.v2.utils import get_all_component_text
from misc.time_calculations import get_last_monday_berlin_time_from_current_time_in_unix

BREACH_DAMAGE_WAIVER_THRESHOLD = 400_000

_processed_breach_pages: deque[tuple[int, int]] = deque(maxlen=500)


def _find_image_recursive(obj) -> str | None:
    images = _collect_images_recursive(obj)
    return images[0] if images else None


def _collect_images_recursive(obj) -> list[str]:
    urls = []
    if hasattr(obj, "accessory") and obj.accessory:
        accessory = obj.accessory
        media = getattr(accessory, "media", None)
        if media and getattr(media, "url", None):
            urls.append(media.url)
    for item in getattr(obj, "items", []) or []:
        media = getattr(item, "media", None)
        if media and getattr(media, "url", None):
            urls.append(media.url)
        urls.extend(_collect_images_recursive(item))
    for child in getattr(obj, "children", []) or []:
        urls.extend(_collect_images_recursive(child))
    return urls


def _extract_component_images(message) -> list[str]:
    urls = []
    for component in message.components:
        urls.extend(_collect_images_recursive(component))
    return urls


def _extract_first_component_image(message) -> str | None:
    images = _extract_component_images(message)
    return images[0] if images else None


def _extract_last_component_image(message) -> str | None:
    images = _extract_component_images(message)
    return images[-1] if images else None


def _parse_breach_boss_name(text: str) -> str | None:
    patterns = [
        r"World\s+Ender\s*:\s*(?P<name>.+?)(?:\s+Level\b|\n|$)",
        r"Boss(?:\s*Name)?\s*[:\-]\s*(?P<name>[^\n|]+)",
        r"Breach\s+Boss\s*[:\-]\s*(?P<name>[^\n|]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            boss_name = re.sub(r"[`*_~]", "", match.group("name")).strip()
            return boss_name[:120] or None
    return None


def _parse_breach_phase(text: str) -> str | None:
    match = re.search(r"Phase\s*:\s*([^\n]+)", text, re.IGNORECASE)
    if not match:
        return None

    raw_phase = re.sub(r"[`*_~]", "", match.group(1)).strip()
    normalized = raw_phase.casefold()
    phase_aliases = {
        "docile": "Docile",
        "chaos": "Chaos",
        "herald of damnation": "Herald - Damnation",
        "herald - damnation": "Herald - Damnation",
        "herald of salvation": "Herald - Salvation",
        "herald - salvation": "Herald - Salvation",
        "gambit": "Gambit",
        "enraged": "Enraged",
        "collapse": "Collapse",
    }
    for alias, phase in phase_aliases.items():
        if alias in normalized:
            return phase

    phase = re.sub(r"\s+", " ", raw_phase)
    return phase[:80] or None


async def maybe_track_breach_boss_info(message, full_text: str | None = None):
    if not message.guild:
        return

    full_text = full_text if full_text is not None else get_all_component_text(message)
    if "Breach" not in full_text or "Breach Clan Standings" in full_text:
        return

    image_url = _extract_last_component_image(message)
    boss_name = _parse_breach_boss_name(full_text)
    phase = _parse_breach_phase(full_text)
    if not image_url and not boss_name and not phase:
        return

    week_start = await get_last_monday_berlin_time_from_current_time_in_unix()
    await guilds.set_breach_boss_info(
        message.guild.id,
        boss_name=boss_name,
        image_url=image_url,
        phase=phase,
        week_start=week_start,
    )


def _clean_player_name(raw_name: str) -> str:
    name = raw_name.strip()
    name = re.sub(r"[`*_~]", "", name)
    return name.strip()


def parse_breach_standings(text: str) -> tuple[list[dict], int | None, int | None, str | None]:
    """Parse AniGame Breach Clan Standings text from a Components V2 message."""
    page = total_pages = None
    page_match = re.search(r"Page\s+(\d+)\s*/\s*(\d+)", text, re.IGNORECASE)
    if page_match:
        page = int(page_match.group(1))
        total_pages = int(page_match.group(2))

    clan_name = None
    clan_match = re.search(r"Clan:\s*([^\n]+)", text, re.IGNORECASE)
    if clan_match:
        clan_name = clan_match.group(1).strip()

    entries = []
    entry_pattern = re.compile(
        r"#\s*[^|\n]*\|\s*(?P<name>[^\n]+?)\s*\n\s*Damage:\s*(?P<damage>[\d,]+)",
        re.IGNORECASE,
    )
    for match in entry_pattern.finditer(text):
        player_name = _clean_player_name(match.group("name"))
        damage = int(match.group("damage").replace(",", ""))
        if player_name:
            entries.append({"player_name": player_name, "damage": damage})

    return entries, page, total_pages, clan_name


async def v2_breach_standings_handler(message):
    """Grant next-week weekly donation waivers from Breach Clan Standings pages."""
    full_text = get_all_component_text(message)
    entries, page, total_pages, clan_name = parse_breach_standings(full_text)

    if message.guild:
        clan_image_url = _extract_first_component_image(message)
        if clan_image_url:
            await guilds.set_breach_playbook_image_url(message.guild.id, clan_image_url)

    if not entries:
        return

    page_key = (message.id, page or 0)
    if page_key in _processed_breach_pages:
        return
    _processed_breach_pages.append(page_key)

    qualified = [entry for entry in entries if entry["damage"] >= BREACH_DAMAGE_WAIVER_THRESHOLD]
    if not qualified:
        try:
            await message.add_reaction("\u2611\ufe0f")
        except Exception:
            pass
        return

    waiver_channel_id = None
    if message.guild:
        waiver_channel_id = await guilds.get_weekly_donation_channel(message.guild.id)
    if waiver_channel_id is None:
        waiver_channel_id = message.channel.id

    recorded = []
    already_seen = []
    for entry in qualified:
        player_name = entry["player_name"]
        damage = entry["damage"]
        discord_id = await weekly_donations.get_discord_id_by_player_name(player_name)
        waiver_key = f"breach:{message.id}:{page or 0}:{player_name.lower()}"
        applied = await weekly_donations.grant_next_week_waiver(
            player_name=player_name,
            discord_id=discord_id,
            channel_id=waiver_channel_id,
            waiver_key=waiver_key,
            damage=damage,
            source="breach_clan_standings",
        )
        if applied:
            recorded.append(entry)
        else:
            already_seen.append(entry)

    try:
        await message.add_reaction("\u2705")
    except Exception:
        pass

    page_text = f"Page {page}/{total_pages}" if page and total_pages else "Current page"
    clan_text = f" for **{clan_name}**" if clan_name else ""
    lines = [
        f"Breach waiver recorded{clan_text} - {page_text}",
        f"Threshold: **{BREACH_DAMAGE_WAIVER_THRESHOLD:,} dmg** -> weekly donation waived next week.",
    ]

    if recorded:
        preview = "\n".join(
            f"- `{entry['player_name']}` - **{entry['damage']:,}** dmg"
            for entry in recorded[:10]
        )
        lines.append(f"\n**Recorded ({len(recorded)}):**\n{preview}")
        if len(recorded) > 10:
            lines.append(f"...and **{len(recorded) - 10}** more.")

    if already_seen:
        lines.append(f"\nAlready recorded on this page: **{len(already_seen)}**")

    await message.reply("\n".join(lines), mention_author=False)
