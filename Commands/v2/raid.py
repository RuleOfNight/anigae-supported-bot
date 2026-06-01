"""
V2 Raid handler — xử lý raid lobby từ Components V2 Container.

Bot gốc đã chuyển từ embed sang Container, file này bridge
text từ Container → logic cũ (in_raid_lobby / raid_lobby_waiting_room).
"""

import re
import time as _time

import discord

import runtime
from Commands import user_commands_on_message
from Commands.v2.utils import get_all_component_text


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _find_image_recursive(obj) -> str | None:
    """Tìm URL ảnh (thumbnail / media) trong component tree."""
    if hasattr(obj, "accessory") and obj.accessory:
        acc = obj.accessory
        if hasattr(acc, "media") and acc.media:
            if hasattr(acc.media, "url") and acc.media.url:
                return acc.media.url
    if hasattr(obj, "items"):
        for item in (obj.items or []):
            if hasattr(item, "media") and item.media:
                if hasattr(item.media, "url") and item.media.url:
                    return item.media.url
    for child in getattr(obj, "children", []) or []:
        url = _find_image_recursive(child)
        if url:
            return url
    return None


def _extract_thumbnail(message) -> str | None:
    """Trả về URL thumbnail đầu tiên tìm được trong components."""
    for comp in message.components:
        url = _find_image_recursive(comp)
        if url:
            return url
    return None


def _parse_container_text(full_text: str) -> tuple[str, str, str]:
    """
    Tách text Container thành (title, description, footer).

    - Title:  dòng ``## heading`` đầu tiên (bỏ ``##`` và emoji shortcode)
    - Footer: dòng ``-#`` subtext (thường ở cuối)
    - Description: phần còn lại
    """
    lines = full_text.split("\n")
    title = ""
    footer = ""
    desc_lines: list[str] = []

    for line in lines:
        if line.startswith("## ") and not title:
            raw_title = line[3:].strip()
            title = re.sub(r":\w+:", "", raw_title).strip()
        elif line.startswith("-# "):
            footer = line[3:].strip().strip("*").strip()
        else:
            desc_lines.append(line)

    description = "\n".join(desc_lines).strip()
    return title, description, footer


# ─── Main handler ─────────────────────────────────────────────────────────────

async def v2_raid_handler(message):
    """Xử lý raid lobby / waiting room từ Components V2 Container."""
    full_text = get_all_component_text(message)
    title, description, footer = _parse_container_text(full_text)

    # Normalize emoji: :HP_HEART: → ❤️  (để regex HP cũ vẫn hoạt động)
    description = description.replace(":HP_HEART:", "❤️")

    is_active  = "Type .rd battle when you have Energy!" in full_text
    is_waiting = "Current Raid Participants" in full_text and not is_active

    if is_active:
        runtime.active_raid_guilds[message.guild.id] = _time.time()
        t, d, f = await user_commands_on_message.in_raid_lobby(
            title, description, footer,
        )
    elif is_waiting:
        t, d, f = await user_commands_on_message.raid_lobby_waiting_room(
            title, description, footer,
        )
    else:
        return

    # Build replacement embed
    thumb_url = _extract_thumbnail(message)
    embed = discord.Embed(title=t, description=d, color=0x71368A)
    if f:
        embed.set_footer(text=f)
    if thumb_url:
        embed.set_thumbnail(url=thumb_url)

    view = user_commands_on_message.DeleteButtonView()
    await message.channel.send(embed=embed, view=view)
    try:
        await message.delete()
    except (discord.errors.NotFound, discord.errors.Forbidden):
        pass
