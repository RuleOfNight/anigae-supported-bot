import re
import discord
import runtime
from Commands import definitions
from Commands.v2.utils import get_all_component_text
from Commands.user_commands_on_message import (
    ultra_rare_1, ultra_rare_2, super_rare_1, super_rare_2,
    rare_emote, uncommon_emote_1, uncommon_emote_2, common_emote_1,
    ascension_emote,
)
from db_methods import cards as cards_db
from db_methods import players as players_db

_RARITY_EMOTE_MAP = {
    "Ultra Rare": f"{ultra_rare_1}{ultra_rare_2}",
    "Super Rare": f"{super_rare_1}{super_rare_2}",
    "Rare": rare_emote,
    "Uncommon": f"{uncommon_emote_1}{uncommon_emote_2}",
    "Common": common_emote_1,
}


# ---------------------------------------------------------------------------
# Text parsers
# ---------------------------------------------------------------------------

def _extract_card_id(text: str) -> str | None:
    m = re.search(r"Card ID:\s*(\d+)", text)
    return m.group(1) if m else None


def _extract_card_name(text: str) -> str | None:
    m = re.search(r"Card Name:\*{0,2}\s*(.+)", text)
    if not m:
        return None
    return re.sub(r"^\*+", "", m.group(1)).strip()


def _strip_custom_emotes(text: str) -> str:
    """Xóa custom emote <:name:id> và animated <a:name:id> của AniGame."""
    return re.sub(r"<a?:[^:>]+:\d+>", "", text)


def _replace_rarity_emote(text: str) -> str:
    for rarity_name, emote in _RARITY_EMOTE_MAP.items():
        text = re.sub(rf"(\*\*Rarity:\*\*\s*){re.escape(rarity_name)}", rf"\g<1>{emote}", text)
    return text


def _replace_copies_with_ascend(text: str, ascend: int) -> str:
    stars = ascension_emote * ascend if ascend > 0 else "—"
    return re.sub(r"\*\*Copies In Existence[^\n]*\n?", f"**Ascend:** {stars}\n", text)


def _split_text_sections(full_text: str) -> tuple[str, str, str]:
    """Tách thành 3 phần: card_info / talent / footer (quote + Card ID + Pity)."""
    talent_match = re.search(r"(\*{2,4}Talent\*{2,4}.*)", full_text, re.DOTALL)
    if talent_match:
        card_info = full_text[:talent_match.start()].rstrip()
        talent_and_footer = full_text[talent_match.start():]
        # Footer là dòng chứa Card ID (quote | Card ID: xxx | Pity: x)
        footer_match = re.search(r"\n(.*Card ID:.*)", talent_and_footer)
        if footer_match:
            talent = talent_and_footer[:footer_match.start()].rstrip()
            footer = footer_match.group(1).strip()
        else:
            talent = talent_and_footer
            footer = ""
    else:
        card_info = full_text
        talent = ""
        footer = ""
    return card_info, talent, footer


async def _swap_talent_emote(talent_text: str) -> str:
    """Thay emote AniGame trong talent bằng emote của bot mình."""
    # Tên talent nằm giữa ** sau emote: "**<:NAME:id> **Talent Name** [PSV]:"
    m = re.search(r"<:[^>]+>\s*\*\*([^\*\[]+?)\*\*", talent_text)
    if m:
        talent_name = m.group(1).strip()
        our_emote = await definitions.skill_converter_from_database(talent_name)
        # Thay emote AniGame đầu tiên bằng emote của bot
        talent_text = re.sub(r"<:[^>]+>", our_emote, talent_text, count=1)
    return talent_text


# ---------------------------------------------------------------------------
# Container builder
# ---------------------------------------------------------------------------

class _InfoInstanceView(discord.ui.LayoutView):
    async def on_timeout(self):
        try:
            if hasattr(self, "message"):
                for child in self.children:
                    if hasattr(child, "children"):
                        for sub in child.children:
                            if isinstance(sub, discord.ui.ActionRow):
                                for item in sub.children:
                                    item.disabled = True
                await self.message.edit(view=self)
        except Exception:
            pass
        self.stop()


def _build_container(card_info_text: str, talent_text: str, picture_url: str, footer_text: str, avatar_url: str | None = None) -> discord.ui.Container:
    container = discord.ui.Container(accent_colour=0x71368A)
    if avatar_url:
        section = discord.ui.Section(
            discord.ui.TextDisplay(card_info_text),
            accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=avatar_url))
        )
        container.add_item(section)
    else:
        container.add_item(discord.ui.TextDisplay(card_info_text))
    if talent_text:
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(talent_text))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.MediaGallery(
        discord.MediaGalleryItem(media=picture_url, spoiler=False)
    ))
    if footer_text:
        container.add_item(discord.ui.TextDisplay(footer_text))

    del_button = discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="info_instance_delete")

    async def _del_callback(interaction: discord.Interaction):
        await interaction.message.delete()

    del_button.callback = _del_callback
    container.add_item(discord.ui.ActionRow(del_button))
    return container


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

async def v2_card_info_instance(message: discord.Message):
    """Khi .info message được detect, thay ảnh bằng custom picture nếu player đã bật info_replace."""
    full_text = get_all_component_text(message)

    card_id = _extract_card_id(full_text)
    card_name = _extract_card_name(full_text)
    if not card_id or not card_name:
        return

    # Xác định player từ message.reference
    player = None
    player_settings = None
    if message.reference:
        cached = discord.utils.get(runtime.bot.cached_messages, id=message.reference.message_id)
        if cached:
            player = cached.author
        else:
            try:
                original = await message.channel.fetch_message(message.reference.message_id)
                player = original.author
            except Exception:
                pass
    if player:
        player_settings = await players_db.get_settings_from_player_by_discord_id(player.id)

    # Chỉ chạy nếu player đã bật info_replace
    if not player_settings or player_settings.get("info_replace") != "yes":
        return

    custom_picture, ascend = await cards_db.get_custom_card_instance_picture(card_id, card_name)
    if not custom_picture:
        return

    # Tách text sections
    card_info_raw, talent_raw, footer_raw = _split_text_sections(full_text)

    # Clean AniGame emotes, thay rarity + copies
    card_info_clean = _strip_custom_emotes(card_info_raw)
    card_info_clean = _replace_rarity_emote(card_info_clean)
    card_info_clean = _replace_copies_with_ascend(card_info_clean, ascend)

    # Swap talent emote
    talent_clean = await _swap_talent_emote(talent_raw)

    avatar_url = player.display_avatar.url if player else None
    container = _build_container(card_info_clean, talent_clean, custom_picture, footer_raw, avatar_url)

    view = _InfoInstanceView(timeout=120)
    view.add_item(container)
    msg = await message.channel.send(view=view)
    view.message = msg

    try:
        await message.delete()
    except (discord.errors.NotFound, discord.errors.Forbidden):
        pass
