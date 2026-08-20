import re
from collections import deque

import discord

from Commands.v2.utils import get_all_component_text

BOUNTY_HUNT_REACTION = "⚔️"
TARGET_BOT_ID = 571027211407196161

_processed_bounty_messages: deque[int] = deque(maxlen=500)

BOUNTY_SLOT_CONFIGS = (
    {"rarity": "Rare", "evo": 3, "ascension": 3, "lvl": 320},
    {"rarity": "Super Rare", "evo": 3, "ascension": 4, "lvl": 375},
    {"rarity": "Ultra Rare", "evo": 3, "ascension": 5, "lvl": 430},
)


def _clean_bounty_line(line: str) -> str:
    line = re.sub(r"[`*_~]", "", line)
    line = re.sub(r"<a?:[^>]+>", "", line)
    return re.sub(r"\s+", " ", line).strip()


def _normalize_bounty_text(text: str) -> str:
    text = re.sub(r"[`*_~]", "", text)
    text = re.sub(r"<a?:[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _extract_card_name(line: str) -> str | None:
    line = _clean_bounty_line(line)
    match = re.search(
        r"\b(?:R|SR|UR|Rare|Super Rare|Ultra Rare)\b\s+(.+?)\s+Level\s+\d+\s+\[Evo\s+\d+\]",
        line,
        re.IGNORECASE,
    )
    if not match:
        return None
    return match.group(1).strip(" -")


def parse_bounty_slots(text: str) -> list[dict]:
    cleaned_text = re.sub(r"\r", "", text)
    slot_pattern = re.compile(
        r"(?ms)^#(?P<slot>\d+)\s+.*?(?=^#\d+\s+|Fresh Bounties Arrive\b|\Z)"
    )
    slots: list[dict] = []

    for match in slot_pattern.finditer(cleaned_text):
        slot_number = int(match.group("slot"))
        block = match.group(0)
        names = []
        for raw_line in block.splitlines():
            name = _extract_card_name(raw_line)
            if name:
                names.append(name)
            if len(names) == 2:
                break
        if len(names) >= 2:
            slots.append(
                {
                    "slot": slot_number,
                    "boss_names": names[:2],
                }
            )

    return sorted(slots, key=lambda item: item["slot"])


def _is_bounty_hunt_message(full_text: str) -> bool:
    normalized = _normalize_bounty_text(full_text)
    return "bounty hunt #" in normalized and "fresh bounties arrive" in normalized


async def maybe_add_bounty_hunt_reaction(message, full_text: str | None = None):
    if message.author.id != TARGET_BOT_ID:
        return

    full_text = full_text if full_text is not None else get_all_component_text(message)
    if not _is_bounty_hunt_message(full_text):
        return
    if not parse_bounty_slots(full_text):
        return
    if message.id in _processed_bounty_messages:
        return

    _processed_bounty_messages.append(message.id)
    try:
        await message.add_reaction(BOUNTY_HUNT_REACTION)
    except Exception:
        pass


async def on_raw_reaction_add(payload, bot):
    if payload.user_id == bot.user.id:
        return
    if payload.emoji.name != BOUNTY_HUNT_REACTION:
        return

    message = discord.utils.get(bot.cached_messages, id=payload.message_id)
    if not message:
        channel = bot.get_channel(payload.channel_id)
        if not channel:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

    if message.author.id != TARGET_BOT_ID or not message.components:
        return

    full_text = get_all_component_text(message)
    if not _is_bounty_hunt_message(full_text):
        return

    slots = parse_bounty_slots(full_text)
    if len(slots) < 3:
        return

    view = BountyHuntView(message=message, user_id=payload.user_id, slots=slots[:3])
    await message.channel.send(view=view)


class BountyHuntView(discord.ui.LayoutView):
    def __init__(self, message, user_id: int, slots: list[dict], timeout: int = 120):
        super().__init__(timeout=timeout)
        self.message = message
        self.user_id = user_id
        self.slots = slots
        self.container = self._build_container()
        self.add_item(self.container)

    def _build_container(self) -> discord.ui.Container:
        container = discord.ui.Container(accent_colour=0x71368A)
        container.add_item(discord.ui.TextDisplay("## :crossed_swords: Bounty Hunt Helper"))
        container.add_item(discord.ui.TextDisplay("-# Chon boss de lay lenh /dg battle"))
        container.add_item(discord.ui.Separator())

        for slot_data in self.slots:
            primary_name = slot_data["boss_names"][0]
            button = discord.ui.Button(
                label=f"#{slot_data['slot']} {primary_name[:60]}",
                style=discord.ButtonStyle.primary,
            )
            button.callback = self._make_slot_callback(slot_data)
            container.add_item(discord.ui.ActionRow(button))

        return container

    def _make_slot_callback(self, slot_data: dict):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.defer(ephemeral=True)
                return

            config = BOUNTY_SLOT_CONFIGS[slot_data["slot"] - 1]
            boss_1, boss_2 = slot_data["boss_names"][:2]
            command = (
                f"/dg battle rarity:{config['rarity']} evo:{config['evo']} "
                f"ascension:{config['ascension']} lvl:{config['lvl']} "
                f"cards:{boss_1}, {boss_2} ruleset_code:00001w"
            )
            await interaction.response.send_message(command)

        return callback
