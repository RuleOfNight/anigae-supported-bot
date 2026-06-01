from Commands.v2.utils import find_text_in_components, get_all_component_text
from Commands.v2.clan_shop import v2_improved_clan_shop
from Commands.v2.card_info import v2_improved_card_info
from Commands.v2.card_info_instance import v2_card_info_instance
from Commands.v2.pack_opening import v2_pack_opening
from Commands.v2.market import v2_global_market_update
from Commands.v2.card_select import v2_card_select
from Commands.v2.inventory import v2_inventory_mset


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

        # ── DEBUG: Raid detection in Components V2 ──
        if ("Raid Challenge" in _full_text
                or "Type .rd battle" in _full_text
                or "Players in Raid Party" in _full_text):
            # Gửi full text lên Discord để debug cấu trúc
            debug_msg = f"**[RAID V2 DEBUG]** Detected raid keywords in Container!\n"
            # Cắt thành chunks nhỏ để Discord không reject
            text_chunks = [_full_text[i:i+1800] for i in range(0, len(_full_text), 1800)]
            for idx, chunk in enumerate(text_chunks):
                await message.channel.send(f"{debug_msg if idx == 0 else ''}```\n{chunk}\n```")
        # ── END DEBUG ──

    elif trigger == "on_edit":
        if find_text_in_components(message, "Pack Opened!"):
            await v2_pack_opening(message)
        if find_text_in_components(message, "All the cards in your inventory are shown below!"):
            await v2_inventory_mset(message)
