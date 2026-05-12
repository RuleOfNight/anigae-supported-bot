import re
import discord
from Commands.v2.utils import get_all_component_text
from db_methods import cards as cards_db


# ---------------------------------------------------------------------------
# Parser helpers — làm việc trên full text string từ components
# ---------------------------------------------------------------------------

def _extract_card_id(text: str) -> str | None:
    m = re.search(r"Card ID:\s*(\d+)", text)
    return m.group(1) if m else None


def _extract_card_name(text: str) -> str | None:
    m = re.search(r"Card Name:\s*(.+)", text)
    return m.group(1).strip() if m else None


# ---------------------------------------------------------------------------
# Delete button view
# ---------------------------------------------------------------------------

class _DeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🗑️", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

async def v2_card_info_instance(message: discord.Message):
    """Khi .info message được detect, thay ảnh mặc định bằng custom picture nếu đã set."""
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

    # Gửi embed mới với custom picture, xóa tin nhắn gốc
    embed = discord.Embed(title=card_name, color=0x71368A)
    embed.set_image(url=custom_picture)
    embed.set_footer(text=f"Card ID: {card_id} | Custom picture")

    view = _DeleteView()
    await message.channel.send(embed=embed, view=view)

    try:
        await message.delete()
    except (discord.errors.NotFound, discord.errors.Forbidden):
        pass
