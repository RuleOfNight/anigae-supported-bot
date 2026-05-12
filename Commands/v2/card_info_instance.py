import re
import discord
from db_methods import cards as cards_db


# ---------------------------------------------------------------------------
# Parser helpers
# ---------------------------------------------------------------------------

def _extract_card_id(footer_text: str) -> str | None:
    m = re.search(r"Card ID:\s*(\d+)", footer_text)
    return m.group(1) if m else None


def _extract_card_name(embed: discord.Embed) -> str | None:
    # Ưu tiên tìm trong description (format: "Card Name: Shizuku Murasaki")
    if embed.description:
        m = re.search(r"Card Name:\s*(.+)", embed.description)
        if m:
            return m.group(1).strip()

    # Fallback: tìm trong fields
    for field in embed.fields:
        if "card name" in field.name.lower():
            return field.value.strip()

    # Fallback cuối: parse từ title "#6096 | Shizuku Murasaki🌟"
    if embed.title:
        m = re.search(r"\|\s*(.+)", embed.title)
        if m:
            name = m.group(1).strip()
            # Strip trailing emoji/star decorations
            name = re.sub(r"[\U0001F000-\U0010FFFF⭐🌟✨]+$", "", name).strip()
            return name or None

    return None


def _rebuild_embed(original: discord.Embed, picture_url: str) -> discord.Embed:
    """Copy toàn bộ embed gốc, thay image bằng custom picture."""
    new_embed = discord.Embed(
        title=original.title,
        description=original.description,
        color=original.color,
        url=original.url or None,
    )
    if original.author and original.author.name:
        new_embed.set_author(
            name=original.author.name,
            url=original.author.url,
            icon_url=original.author.icon_url,
        )
    if original.thumbnail and original.thumbnail.url:
        new_embed.set_thumbnail(url=original.thumbnail.url)
    for field in original.fields:
        new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
    new_embed.set_image(url=picture_url)
    if original.footer and original.footer.text:
        new_embed.set_footer(
            text=original.footer.text,
            icon_url=original.footer.icon_url,
        )
    return new_embed


# ---------------------------------------------------------------------------
# Delete button view
# ---------------------------------------------------------------------------

class _DeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.message: discord.Message | None = None

    @discord.ui.button(label="🗑️", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

async def v2_card_info_instance(message: discord.Message):
    """Khi .info embed được detect, thay ảnh mặc định bằng custom picture nếu đã set."""
    if not message.embeds:
        return

    embed = message.embeds[0]
    footer_text = embed.footer.text if embed.footer else ""

    print(f"[CINFO_INSTANCE] footer={footer_text!r}")
    print(f"[CINFO_INSTANCE] title={embed.title!r}")
    print(f"[CINFO_INSTANCE] description={embed.description!r}")

    card_id = _extract_card_id(footer_text)
    print(f"[CINFO_INSTANCE] card_id={card_id!r}")
    if not card_id:
        return

    card_name = _extract_card_name(embed)
    print(f"[CINFO_INSTANCE] card_name={card_name!r}")
    if not card_name:
        return

    custom_picture = await cards_db.get_custom_card_instance_picture(card_id, card_name)
    print(f"[CINFO_INSTANCE] custom_picture={custom_picture!r}")
    if not custom_picture:
        return

    new_embed = _rebuild_embed(embed, custom_picture)
    view = _DeleteView()
    msg = await message.channel.send(embed=new_embed, view=view)
    view.message = msg

    try:
        await message.delete()
    except (discord.errors.NotFound, discord.errors.Forbidden):
        pass
