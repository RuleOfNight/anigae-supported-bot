import re
from db_methods import cards


# Ngưỡng giá và hệ số chênh lệch tối đa chấp nhận được khi cập nhật SR price
_SR_PRICE_FACTORS = [
    (10,    50000),
    (50,    10000),
    (100,   5000),
    (500,   1000),
    (1000,  50),
    (5000,  10),
    (10000, 5),
    (20000, 4),
    (30000, 3),
]


def _get_sr_price_factor(current_price: int) -> int:
    """Trả về hệ số tối đa dựa trên giá hiện tại của SR card."""
    for threshold, factor in _SR_PRICE_FACTORS:
        if current_price <= threshold:
            return factor
    return 2


async def v2_global_market_update(message):
    """Parse global market message và cập nhật giá thấp nhất SR/UR vào database."""
    global_market_sr: dict[str, int] = {}
    global_market_ur: dict[str, int] = {}

    for component in message.components:
        if not hasattr(component, "children"):
            continue
        for child in component.children:
            if not hasattr(child, "children"):
                continue
            for subchild in child.children:
                if not (hasattr(subchild, "content") and "| ID:" in subchild.content):
                    continue
                content = (subchild.content
                           .replace("<:Null:1329746549382582285>", "")
                           .replace("⛰️", "")
                           .replace("☀️", ""))
                entries = re.findall(
                    fr"\*\*(\d+) Gold <a:gold:1219941344450052187> \| (.*?) \[Evo 1] [🍃🔥💧⚡🌙✨]? <:(?:.*?)>\s*⌛?\*\*\n(?:​)?\s*<a?:(\w+):",
                    content.replace(",", ""))
                for gold_str, card_name, rarity in entries:
                    gold = int(gold_str)
                    if rarity == "super":
                        if card_name not in global_market_sr or gold < global_market_sr[card_name]:
                            global_market_sr[card_name] = gold
                    elif rarity == "ultra":
                        if card_name not in global_market_ur or gold < global_market_ur[card_name]:
                            global_market_ur[card_name] = gold

    # Cập nhật giá SR — lọc bỏ giá bất thường dựa theo hệ số
    for card_name, price in global_market_sr.items():
        current = await cards.get_card_market_price_sr_by_cards_name(card_name)
        if current != "N/A":
            factor = _get_sr_price_factor(int(current))
            if price > factor * int(current):
                continue
        await cards.update_market_price_sr_by_cards_name(card_name, str(price))

    # Cập nhật giá UR — không lọc
    for card_name, price in global_market_ur.items():
        await cards.update_market_price_ur_by_cards_name(card_name, str(price))
