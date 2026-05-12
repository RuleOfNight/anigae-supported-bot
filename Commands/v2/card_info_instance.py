import re
import discord
from Commands.v2.utils import get_all_component_text
from db_methods import cards as cards_db


# ---------------------------------------------------------------------------
# Parser helpers
# ---------------------------------------------------------------------------

def _extract_card_id(text: str) -> str | None:
    m = re.search(r"Card ID:\s*(\d+)", text)
    return m.group(1) if m else None


def _extract_card_name(text: str) -> str | None:
    m = re.search(r"Card Name:\*{0,2}\s*(.+)", text)
    if not m:
        return None
    return re.sub(r"^\*+", "", m.group(1)).strip()


def _split_text_sections(full_text: str) -> tuple[str, str]:
    """Tách full_text thành (card_info, talent_footer).
    Talent section bắt đầu ở dòng chứa 'Talent'.
    """
    # ****Talent**** hoặc **Talent** hoặc Talent đứng một mình trên dòng
    m = re.search(r"(\*{2,4}Talent\*{2,4}.*)", full_text, re.DOTALL)
    if m:
        talent_start = m.start()
        card_info = full_text[:talent_start].rstrip()
        talent_footer = full_text[talent_start:]
    else:
        card_info = full_text
        talent_footer = ""
    return card_info, talent_footer


# ---------------------------------------------------------------------------
# Container builder
# ---------------------------------------------------------------------------

class _InfoInstanceView(discord.ui.LayoutView):
    async def on_timeout(self):
        try:
            if hasattr(self, "message"):
                # Disable delete button on timeout
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

    # Phần 1: thông tin card
    container.add_item(discord.ui.TextDisplay(card_info_text))
    container.add_item(discord.ui.Separator())

    # Phần 2: ảnh custom
    container.add_item(discord.ui.MediaGallery(
        discord.MediaGalleryItem(media=picture_url, spoiler=False)
    ))

    # Phần 3: talent + footer (nếu có)
    if talent_footer_text:
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(talent_footer_text))

    # Delete button
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
    """Khi .info message được detect, thay ảnh bằng custom picture nếu đã set."""
    full_text = get_all_component_text(message)
    print(f"[CINFO_INSTANCE] full_text={full_text!r}")

    card_id = _extract_card_id(full_text)
    card_name = _extract_card_name(full_text)
    print(f"[CINFO_INSTANCE] card_id={card_id!r} card_name={card_name!r}")

    if not card_id or not card_name:
        return

    custom_picture = await cards_db.get_custom_card_instance_picture(card_id, card_name)
    print(f"[CINFO_INSTANCE] custom_picture={custom_picture!r}")
    if not custom_picture:
        return

    card_info_text, talent_footer_text = _split_text_sections(full_text)
    container = _build_container(card_info_text, talent_footer_text, custom_picture)

    view = _InfoInstanceView(timeout=120)
    view.add_item(container)
    msg = await message.channel.send(view=view)
    view.message = msg

    try:
        await message.delete()
    except (discord.errors.NotFound, discord.errors.Forbidden):
        pass
