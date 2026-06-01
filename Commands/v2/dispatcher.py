from Commands.v2.utils import find_text_in_components, get_all_component_text
from Commands.v2.clan_shop import v2_improved_clan_shop
from Commands.v2.card_info import v2_improved_card_info
from Commands.v2.card_info_instance import v2_card_info_instance
from Commands.v2.pack_opening import v2_pack_opening
from Commands.v2.market import v2_global_market_update
from Commands.v2.card_select import v2_card_select
from Commands.v2.inventory import v2_inventory_mset
from Commands.v2.raid import v2_raid_handler


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
            await v2_inventory_mset(message)
        # .info — dùng get_all_component_text vì text có thể nằm ở nhiều level
        _full_text = get_all_component_text(message)
        if "Skin Equipped:" in _full_text and "Card ID:" in _full_text:
            await v2_card_info_instance(message)

        # ── V2 Raid handler ──
        if ("Raid Challenge" in _full_text
                or "Type .rd battle" in _full_text
                or "Players in Raid Party" in _full_text):
            await v2_raid_handler(message)

    elif trigger == "on_edit":
        if find_text_in_components(message, "Pack Opened!"):
            await v2_pack_opening(message)
        if find_text_in_components(message, "All the cards in your inventory are shown below!"):
            await v2_inventory_mset(message)
