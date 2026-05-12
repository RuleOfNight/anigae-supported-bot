from Commands.v2.utils import find_text_in_components
from Commands.v2.clan_shop import v2_improved_clan_shop
from Commands.v2.card_info import v2_improved_card_info
from Commands.v2.pack_opening import v2_pack_opening
from Commands.v2.market import v2_global_market_update
from Commands.v2.card_select import v2_card_select


async def discord_components_v2(message, trigger: str):
    """Router chính — phát hiện loại message và gọi handler tương ứng."""
    if trigger == "on_message":
        if find_text_in_components(message, "Clan Shop"):
            await v2_improved_clan_shop(message)
        if (find_text_in_components(message, "Copies In Existence (SR/UR)")
                and find_text_in_components(message, "Location/Floor")):
            await v2_improved_card_info(message)
        if find_text_in_components(message, "Global Market that matches"):
            await v2_global_market_update(message)
        if find_text_in_components(message, "Battle Card Selection"):
            await v2_card_select(message)
        if find_text_in_components(message, "All the cards in your inventory are shown below!"):
            try:
                await message.add_reaction("🛒")
            except Exception:
                pass

    elif trigger == "on_edit":
        if find_text_in_components(message, "Pack Opened!"):
            await v2_pack_opening(message)
