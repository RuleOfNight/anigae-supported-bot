import re
import discord
import runtime
from Commands import definitions
from Commands.v2.utils import get_all_component_text
from db_methods import cards as cards_db
from db_methods import players as players_db


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
    """Xóa custom emote <:name:id> của AniGame mà bot mình không dùng được."""
    return re.sub(r"<:[^:>]+:\d+>", "", text)


def _split_text_sections(full_text: str) -> tuple[str, str]:
    """Tách card_info (trước Talent) và talent_footer (từ Talent trở đi)."""
    m = re.search(r"(\*{2,4}Talent\*{2,4}.*)", full_text, re.DOTALL)
    if m:
        card_info = full_text[:m.start()].rstrip()
        talent_footer = full_text[m.start():]
    else:
        card_info = full_text
        talent_footer = ""
    return card_info, talent_footer


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


def _build_container(card_info_text: str, talent_footer_text: str, picture_url: str) -> discord.ui.Container:
    container = discord.ui.Container(accent_colour=0x71368A)
    container.add_item(discord.ui.TextDisplay(card_info_text))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.MediaGallery(
        discord.MediaGalleryItem(media=picture_url, spoiler=False)
    ))
    if talent_footer_text:
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(talent_footer_text))

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

    custom_picture = await cards_db.get_custom_card_instance_picture(card_id, card_name)
    if not custom_picture:
        return

    # Tách text sections
    card_info_raw, talent_footer_raw = _split_text_sections(full_text)

    # Clean emote card info (strip AniGame emotes khỏi rarity etc.)
    card_info_clean = _strip_custom_emotes(card_info_raw)

    # Swap talent emote
    talent_footer_clean = await _swap_talent_emote(talent_footer_raw)

    container = _build_container(card_info_clean, talent_footer_clean, custom_picture)

    view = _InfoInstanceView(timeout=120)
    view.add_item(container)
    msg = await message.channel.send(view=view)
    view.message = msg

    try:
        await message.delete()
    except (discord.errors.NotFound, discord.errors.Forbidden):
        pass
