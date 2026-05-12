import re
import discord
from Commands import definitions
from Commands.user_commands_on_message import gold_emote
from db_methods import cards


async def v2_pack_opening(message):
    """Parse pack opening message và gửi thêm giá thị trường của SR/UR vừa mở."""
    card_text = ""
    for component in message.components:
        if not hasattr(component, "children"):
            continue
        for child in component.children:
            if not hasattr(child, "children"):
                continue
            for subchild in child.children:
                if not hasattr(subchild, "content"):
                    continue
                opened_cards = re.findall(r"(Common|Uncommon|Rare|Super Rare|Ultra Rare)\s\*\*(.*)\*\*", subchild.content)
                for rarity, name in opened_cards:
                    if rarity not in ("Super Rare", "Ultra Rare"):
                        continue
                    card_data = await cards.get_card_data_by_name(name)
                    price_sr = card_data[0].get("card_price_sr", 0)
                    price_ur = card_data[0].get("card_price_ur", 0)
                    if price_sr != "N/A":
                        price_sr = "{:,}".format(int(price_sr))
                    if price_ur != "N/A":
                        price_ur = "{:,}".format(int(price_ur))
                    card_price   = price_sr if rarity == "Super Rare" else price_ur
                    card_element = await definitions.element_converter_from_database(card_data[0]['card_element'])
                    card_talent  = await definitions.skill_converter_from_database(card_data[0]['card_talent'])
                    card_text   += f"{card_data[0]['card_name']} {card_element} {card_talent}\n{card_price} {gold_emote}\n\n"

    if not card_text:
        return

    class PackOpeningContainer(discord.ui.Container):
        text_rare = discord.ui.TextDisplay(card_text)

    class PackOpeningView(discord.ui.LayoutView):
        container = PackOpeningContainer(id=1, accent_colour=0x71368A)

    await message.channel.send(view=PackOpeningView())
