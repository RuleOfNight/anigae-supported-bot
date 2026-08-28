import re


BREACH_CHANNEL_ID = 1514597283201679380
ELEMENT_ROLE_IDS = {
    "ground": 1542794514987622481,
    "water": 1542794567890247690,
    "grass": 1542794577402925128,
    "electric": 1542794651134861413,
    "fire": 1542794713306890270,
    "dark": 1542794749683961906,
    "light": 1542794822199279688,
}


def get_breach_chaos_role_id(channel_id: int, title: str, text: str) -> int | None:
    """Return role for an official Elemental Chaos notification."""
    is_chaos = title.strip().casefold() == "elemental chaos" or "elemental chaos" in text.casefold()
    if channel_id != BREACH_CHANNEL_ID or not is_chaos:
        return None
    match = re.search(r"world-ender's type is now\s+(?:\*\*)?(ground|water|grass|electric|fire|dark|light)\b", text, re.IGNORECASE)
    return ELEMENT_ROLE_IDS.get(match.group(1).casefold()) if match else None
