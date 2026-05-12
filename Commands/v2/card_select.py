import re
import discord
from Commands.user_commands_on_message import (
    common_emote_1, uncommon_emote_1, uncommon_emote_2,
    rare_emote, super_rare_1, super_rare_2, ultra_rare_1, ultra_rare_2)
from db_methods import players


# Mapping rarity token → emote display
_RARITY_EMOTE = {
    "common": lambda: common_emote_1,
    "not":    lambda: f"{uncommon_emote_1}{uncommon_emote_2}",
    "rare":   lambda: rare_emote,
    "super":  lambda: f"{super_rare_1}{super_rare_2}",
    "ultra":  lambda: f"{ultra_rare_1}{ultra_rare_2}",
}


async def v2_card_select(message):
    """Theo dõi card selection của người chơi và reply thông báo vào message gốc."""
    card_rarity = card_name = card_lvl = card_evo = card_emote = "Error"

    for component in message.components:
        if not hasattr(component, "children"):
            continue
        for child in component.children:
            if not (hasattr(child, "content") and "Active Battle Card" in child.content):
                continue
            m = re.search(
                r"<a?:([a-zA-Z0-9_]+):\d+>(?:<a?:.+>)?\*\*(.*)\*\* __Level (\d+)__ \*\*\[Evo (\d+)]",
                child.content)
            if not m:
                continue
            rarity_token = m.group(1)
            card_rarity  = rarity_token
            emote_fn     = _RARITY_EMOTE.get(rarity_token)
            card_emote   = emote_fn() if emote_fn else "Error"
            card_name    = m.group(2)
            card_lvl     = m.group(3)
            card_evo     = m.group(4)

    if not (message.reference and message.reference.resolved):
        return

    original_message = message.reference.resolved
    if not isinstance(original_message, discord.Message):
        return

    user_id   = original_message.author.id
    user_name = original_message.author.name
    select_card_status = await players.get_selected_card_info_from_player_by_discord_id(user_id)
    if select_card_status == "yes":
        await original_message.reply(
            f"The user **{user_name}** selected the card {card_emote} ``{card_name}`` Level {card_lvl} [EVO {card_evo}]")
        await message.delete()
