import discord
import re
import asyncio
import json
import time
import runtime
from discord import MediaGalleryItem, ComponentType
from discord.ui import View, Button, MediaGallery, Thumbnail, Select
from Commands import definitions
from Commands.user_commands_on_message import (rubies_emote, gold_emote, ascension_emote,common_emote_1, uncommon_emote_1, uncommon_emote_2,
                                               rare_emote, super_rare_1, super_rare_2, ultra_rare_1, ultra_rare_2)
from db_methods import cards, general, players
from misc import time_calculations
from datetime import timezone, datetime
from math import floor, ceil

picture_caeser = "https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif"


async def discord_components_v2(message, trigger):
    clan_shop = False
    card_info = False
    pack_opened = False
    global_market = False
    card_select = False
    for component in message.components:
        if hasattr(component, "children"):
            for child in component.children:
                if hasattr(child, "children"):
                    for subchild in child.children:
                        if trigger == "on_message":
                            if hasattr(subchild, "content") and "Clan Shop" in subchild.content:
                                clan_shop = True
                                break
                            if hasattr(subchild, "content") and "Copies In Existence (SR/UR)" in subchild.content and "Location/Floor" in subchild.content:
                                card_info = True
                                break
                            if hasattr(subchild, "content") and "Global Market that matches" in subchild.content:
                                global_market = True
                                break
                            if hasattr(subchild, "content") and "Battle Card Selection" in subchild.content:
                                card_select = True
                                break
                            if hasattr(subchild, "content") and "All the cards in your inventory are shown below!" in subchild.content:
                                try:
                                    await message.add_reaction("<:Caeser_purple:1495870697577250888>")
                                except Exception:
                                    pass
                        if trigger == "on_edit":
                            if hasattr(subchild, "content") and "Pack Opened!" in subchild.content:
                                pack_opened = True
                                break
                if clan_shop:
                    break
                if card_info:
                    break
                if global_market:
                    break
                if card_select:
                    break
                if pack_opened:
                    break
        if clan_shop:
            break
        if card_info:
            break
        if global_market:
            break
        if card_select:
            break
        if pack_opened:
            break
    if clan_shop:
        await v2_improved_clan_shop(message)
    if card_info:
        await v2_improved_card_info(message)
    if global_market:
        await v2_global_market_update(message)
    if card_select:
        await v2_card_select(message)
    if pack_opened:
        await v2_pack_opening(message)


async def v2_improved_clan_shop(message):
    await time_calculations.update_counter()
    clan_shop_series_data = await cards.get_card_data_by_series_name()
    base_saturday, base_monday = await time_calculations.get_next_saturday_and_monday_unix()
    cl_shop_start = await time_calculations.get_clan_shop_start_time()
    week_seconds = 7 * 24 * 60 * 60
    total_cards = len(clan_shop_series_data)
    card_data = []
    for index, card in enumerate(clan_shop_series_data):
        offset = index * week_seconds
        c1_saturday = base_saturday + offset
        c1_monday = base_monday + offset
        c2_offset = (index + total_cards) * week_seconds
        c2_saturday = base_saturday + c2_offset
        c2_monday = base_monday + c2_offset
        card_element = await definitions.element_converter_from_database(card['card_element'])
        card_talent = await definitions.skill_converter_from_database(card['card_talent'])
        card_data.append({"card_name": card["card_name"],
                          "card_element": card_element,
                          "card_talent": card_talent,
                          "cycle_1_saturday": c1_saturday,
                          "cycle_1_monday": c1_monday,
                          "cycle_2_saturday": c2_saturday,
                          "cycle_2_monday": c2_monday})
    super_rare = False
    ultra_rare = False
    for component in message.components:
        if hasattr(component, "children"):
            for child in component.children:
                if hasattr(child, "children"):
                    for subchild in child.children:
                        if hasattr(subchild, "content"):
                            if "Clan Shop" in subchild.content:
                                placeholder_header = subchild.content
                                placeholder_header = placeholder_header.replace("Clan Shop", "Improved Clan Shop")
                            elif "__Common__" in subchild.content:
                                placeholder_common = subchild.content
                                placeholder_common = placeholder_common.replace("**500** Rubies", f"**500** {rubies_emote} | **2,500** {gold_emote}")
                            elif "__Uncommon__" in subchild.content:
                                placeholder_uncommon = subchild.content
                                placeholder_uncommon = placeholder_uncommon.replace("**1,000** Rubies", f"**1,000** {rubies_emote} | **5,000** {gold_emote}")
                            elif "__Rare__" in subchild.content:
                                placeholder_rare = subchild.content
                                placeholder_rare = placeholder_rare.replace("**2,000** Rubies", f"**2,000** {rubies_emote} | **10,000** {gold_emote}")
                            elif "__Super Rare__" in subchild.content:
                                placeholder_superrare = subchild.content
                                placeholder_superrare = placeholder_superrare.replace("**20,000** Rubies", f"**20,000** {rubies_emote} | **100,000** {gold_emote}")
                                super_rare = True
                                placeholder_ultrarare = ""
                            elif "__Ultra Rare__" in subchild.content:
                                placeholder_ultrarare = subchild.content
                                placeholder_ultrarare = placeholder_ultrarare.replace("**200,000** Rubies", f"**200,000** {rubies_emote} | **1,000,000** {gold_emote}")
                                ultra_rare = True
                                placeholder_superrare = ""
                if hasattr(child, "items"):
                    for item in child.items:
                        if hasattr(item, "media") and hasattr(item.media, "url"):
                            clan_shop_picture = item.media.url
    for card in card_data:
        if card["card_name"] in placeholder_common:
            placeholder_common = placeholder_common.replace(f"{card['card_name']}", f"{card['card_name']} {card['card_element']} {card['card_talent']}")
        if card["card_name"] in placeholder_uncommon:
            placeholder_uncommon = placeholder_uncommon.replace(f"{card['card_name']}", f"{card['card_name']} {card['card_element']} {card['card_talent']}")
        if card["card_name"] in placeholder_rare:
            placeholder_rare = placeholder_rare.replace(f"{card['card_name']}", f"{card['card_name']} {card['card_element']} {card['card_talent']}")
        if card["card_name"] in placeholder_superrare:
            placeholder_superrare = placeholder_superrare.replace(f"{card['card_name']}", f"{card['card_name']} {card['card_element']} {card['card_talent']}")
        if card["card_name"] in placeholder_ultrarare:
            placeholder_ultrarare = placeholder_ultrarare.replace(f"{card['card_name']}", f"{card['card_name']} {card['card_element']} {card['card_talent']}")
    now = datetime.now(timezone.utc).timestamp()
    next_cl_shop_char = await time_calculations.get_next_cl_shop_character()
    cycle1_start = cl_shop_start
    cycle1_end = base_monday + ((total_cards - 2) * week_seconds)
    cycle2_start = cycle1_end
    cycle2_end = cl_shop_start + (2 * total_cards * week_seconds)
    next_card_text = ""
    for card in card_data:
        if card["card_name"] == next_cl_shop_char:
            if cycle1_start <= now < cycle1_end:
                next_card_text = (f"**Next UR in Rotation:**\n"
                                  f"**{card['card_name']}** {card['card_element']} {card['card_talent']}\n"
                                  f"Start **[**<t:{int(card['cycle_1_saturday'])}:R>**]** - End **[**<t:{int(card['cycle_1_monday'])}:R>**]**")
            elif cycle2_start <= now < cycle2_end:
                next_card_text = (f"**Next UR in Rotation:**\n"
                                  f"**{card['card_name']}** {card['card_element']} {card['card_talent']}\n"
                                  f"Start **[**<t:{int(card['cycle_2_saturday'])}:R>**]** - End **[**<t:{int(card['cycle_2_monday'])}:R>**]**")
            else:
                next_card_text = "Clan Shop finished the 2nd cycle and therefor waiting for the next shop to release."
        else:
            continue

    class ClanShopContainer(discord.ui.Container):
        thumbnail = discord.ui.Section(discord.ui.TextDisplay(f"{placeholder_header}"), accessory=discord.ui.Thumbnail(media=f"{picture_caeser}"))
        text_common = discord.ui.TextDisplay(f"{placeholder_common}")
        sep1 = discord.ui.Separator()
        text_uncommon = discord.ui.TextDisplay(f"{placeholder_uncommon}")
        sep2 = discord.ui.Separator()
        text_rare = discord.ui.TextDisplay(f"{placeholder_rare}")
        sep3 = discord.ui.Separator()
        if super_rare:
            text_sr_rare = discord.ui.TextDisplay(f"{placeholder_superrare}")
        elif ultra_rare:
            text_ur_rare = discord.ui.TextDisplay(f"{placeholder_ultrarare}")
        sep4 = discord.ui.Separator()
        gallery = MediaGallery(MediaGalleryItem(media=clan_shop_picture,description="cl shop picture",spoiler=False))
        text_next_ur = discord.ui.TextDisplay(next_card_text)
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="Main", style=discord.ButtonStyle.primary, custom_id="Main"),
                                           discord.ui.Button(label="Cycle 1", style=discord.ButtonStyle.secondary, custom_id="Cycle 1"),
                                           discord.ui.Button(label="Cycle 2", style=discord.ButtonStyle.secondary, custom_id="Cycle 2"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="Delete"))

    class ClanShopContainerButton1(discord.ui.Container):
        header = discord.ui.TextDisplay("## Clan Shop Cards Cycle 1")
        text_field = "\n\n".join(f"{card['card_name']} {card['card_element']} {card['card_talent']}\n"
                               f"Start: <t:{int(card['cycle_1_saturday'])}:f> [ <t:{int(card['cycle_1_saturday'])}:R> ]\nEnd: <t:{int(card['cycle_1_monday'])}:f> [ <t:{int(card['cycle_1_monday'])}:R> ]" for card in card_data)
        text = discord.ui.TextDisplay(f"{text_field}")
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="Main", style=discord.ButtonStyle.primary, custom_id="Main"),
                                            discord.ui.Button(label="Cycle 1", style=discord.ButtonStyle.secondary, custom_id="Cycle 1"),
                                            discord.ui.Button(label="Cycle 2", style=discord.ButtonStyle.secondary, custom_id="Cycle 2"),
                                            discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="Delete"))

    class ClanShopContainerButton2(discord.ui.Container):
        header = discord.ui.TextDisplay("## Clan Shop Cards Cycle 2")
        text_field = "\n\n".join(f"{card['card_name']} {card['card_element']} {card['card_talent']}\n"
                                 f"Start: <t:{int(card['cycle_2_saturday'])}:f> [ <t:{int(card['cycle_2_saturday'])}:R> ]\nEnd: <t:{int(card['cycle_2_monday'])}:f> [ <t:{int(card['cycle_2_monday'])}:R> ]" for card in card_data)
        text = discord.ui.TextDisplay(f"{text_field}")
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="Main", style=discord.ButtonStyle.primary, custom_id="Main"),
                                            discord.ui.Button(label="Cycle 1", style=discord.ButtonStyle.secondary, custom_id="Cycle 1"),
                                            discord.ui.Button(label="Cycle 2", style=discord.ButtonStyle.secondary, custom_id="Cycle 2"),
                                            discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="Delete"))

    class ClanShopView(discord.ui.LayoutView):
        container = ClanShopContainer(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            cid = interaction.data.get("custom_id")
            if cid == "Main":
                await interaction.response.edit_message(view=ClanShopView())
            elif cid == "Cycle 1":
                await interaction.response.edit_message(view=ClanShopViewCycle1())
            elif cid == "Cycle 2":
                await interaction.response.edit_message(view=ClanShopViewCycle2())
            elif cid == "Delete":
                await interaction.message.delete()
            return True

    class ClanShopViewCycle1(discord.ui.LayoutView):
        container = ClanShopContainerButton1(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            cid = interaction.data.get("custom_id")
            if cid == "Main":
                await interaction.response.edit_message(view=ClanShopView())
            elif cid == "Cycle 1":
                await interaction.response.edit_message(view=self)
            elif cid == "Cycle 2":
                await interaction.response.edit_message(view=ClanShopViewCycle2())
            elif cid == "Delete":
                await interaction.message.delete()
            return True

    class ClanShopViewCycle2(discord.ui.LayoutView):
        container = ClanShopContainerButton2(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            cid = interaction.data.get("custom_id")
            if cid == "Main":
                await interaction.response.edit_message(view=ClanShopView())
            elif cid == "Cycle 1":
                await interaction.response.edit_message(view=ClanShopViewCycle1())
            elif cid == "Cycle 2":
                await interaction.response.edit_message(view=self)
            elif cid == "Delete":
                await interaction.message.delete()
            return True

    view = ClanShopView()
    await message.channel.send(view=view)


class CardInfoContainer1(discord.ui.Container):
    thumbnail = discord.ui.Section(discord.ui.TextDisplay("card data"), accessory=discord.ui.Thumbnail(media=f"{picture_caeser}"))
    sep = discord.ui.Separator()
    card_stats = discord.ui.TextDisplay("card stats")
    card_talent = discord.ui.TextDisplay("card talent")
    sep2 = discord.ui.Separator()
    card_picture = MediaGallery(MediaGalleryItem(media=picture_caeser,spoiler=False))
    sep3 = discord.ui.Separator()
    rarity_row = discord.ui.ActionRow(discord.ui.Select(placeholder="Select the rarity / ascension level.", min_values=1, max_values=1,
                                                        options=[discord.SelectOption(label="UR A5", value="UR A5"),
                                                                 discord.SelectOption(label="UR A4", value="UR A4"),
                                                                 discord.SelectOption(label="UR A3", value="UR A3"),
                                                                 discord.SelectOption(label="UR A2", value="UR A2"),
                                                                 discord.SelectOption(label="UR A1", value="UR A1"),
                                                                 discord.SelectOption(label="UR E3", value="UR E3"),
                                                                 discord.SelectOption(label="UR E2", value="UR E2"),
                                                                 discord.SelectOption(label="UR E1", value="UR E1"),
                                                                 discord.SelectOption(label="SR A4", value="SR A4"),
                                                                 discord.SelectOption(label="SR A3", value="SR A3"),
                                                                 discord.SelectOption(label="SR A2", value="SR A2"),
                                                                 discord.SelectOption(label="SR A1", value="SR A1"),
                                                                 discord.SelectOption(label="SR E3", value="SR E3"),
                                                                 discord.SelectOption(label="SR E2", value="SR E2"),
                                                                 discord.SelectOption(label="SR E1", value="SR E1"),
                                                                 discord.SelectOption(label="Base", value="Base")], custom_id="rarity_row"))
    clan_row = discord.ui.ActionRow(discord.ui.Select(placeholder="Select clan level & stat to adjust.", min_values=1, max_values=1,
                                                      options=[discord.SelectOption(label="All Stats", value="all stats"),
                                                               discord.SelectOption(label="Adjust HP", value="clan hp"),
                                                               discord.SelectOption(label="Adjust ATK", value="clan atk"),
                                                               discord.SelectOption(label="Adjust DEF", value="clan def"),
                                                               discord.SelectOption(label="Adjust SPD", value="clan spd"),
                                                               discord.SelectOption(label="0 - No Clan", value="0"),
                                                               discord.SelectOption(label="1", value="1"),
                                                               discord.SelectOption(label="2", value="2"),
                                                               discord.SelectOption(label="3", value="3"),
                                                               discord.SelectOption(label="4", value="4"),
                                                               discord.SelectOption(label="5", value="5"),
                                                               discord.SelectOption(label="6", value="6"),
                                                               discord.SelectOption(label="7", value="7"),
                                                               discord.SelectOption(label="8", value="8"),
                                                               discord.SelectOption(label="9", value="9"),
                                                               discord.SelectOption(label="10", value="10"),
                                                               discord.SelectOption(label="11", value="11"),
                                                               discord.SelectOption(label="12", value="12"),
                                                               discord.SelectOption(label="13", value="13"),
                                                               discord.SelectOption(label="14", value="14"),
                                                               discord.SelectOption(label="15", value="15")], custom_id="clan_row"))
    fam_row = discord.ui.ActionRow(discord.ui.Select(placeholder="Select fam / holo level.", min_values=1, max_values=1,
                                                     options=[discord.SelectOption(label="Fam 0", value="fam 0"),
                                                              discord.SelectOption(label="Fam 1", value="fam 1"),
                                                              discord.SelectOption(label="Fam 2", value="fam 2"),
                                                              discord.SelectOption(label="Fam 3", value="fam 3"),
                                                              discord.SelectOption(label="Holo", value="holo")], custom_id="holo_row"))
    del_row = discord.ui.ActionRow(discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="Delete"))

class CardInfoContainer2(discord.ui.Container):
    thumbnail = discord.ui.Section(discord.ui.TextDisplay("card data"), accessory=discord.ui.Thumbnail(media=f"{picture_caeser}"))
    sep = discord.ui.Separator()
    card_stats = discord.ui.TextDisplay("card stats")
    card_talent = discord.ui.TextDisplay("card talent")
    sep2 = discord.ui.Separator()
    rarity_row = discord.ui.ActionRow(discord.ui.Select(placeholder="Select the rarity / ascension level.", min_values=1, max_values=1,
                                                        options=[discord.SelectOption(label="UR A5", value="UR A5"),
                                                                 discord.SelectOption(label="UR A4", value="UR A4"),
                                                                 discord.SelectOption(label="UR A3", value="UR A3"),
                                                                 discord.SelectOption(label="UR A2", value="UR A2"),
                                                                 discord.SelectOption(label="UR A1", value="UR A1"),
                                                                 discord.SelectOption(label="UR E3", value="UR E3"),
                                                                 discord.SelectOption(label="UR E2", value="UR E2"),
                                                                 discord.SelectOption(label="UR E1", value="UR E1"),
                                                                 discord.SelectOption(label="SR A4", value="SR A4"),
                                                                 discord.SelectOption(label="SR A3", value="SR A3"),
                                                                 discord.SelectOption(label="SR A2", value="SR A2"),
                                                                 discord.SelectOption(label="SR A1", value="SR A1"),
                                                                 discord.SelectOption(label="SR E3", value="SR E3"),
                                                                 discord.SelectOption(label="SR E2", value="SR E2"),
                                                                 discord.SelectOption(label="SR E1", value="SR E1"),
                                                                 discord.SelectOption(label="Base", value="Base")], custom_id="rarity_row"))
    clan_row = discord.ui.ActionRow(discord.ui.Select(placeholder="Select clan level & stat to adjust.", min_values=1, max_values=1,
                                                        options=[discord.SelectOption(label="All Stats", value="all stats"),
                                                                 discord.SelectOption(label="Adjust HP", value="clan hp"),
                                                                 discord.SelectOption(label="Adjust ATK", value="clan atk"),
                                                                 discord.SelectOption(label="Adjust DEF", value="clan def"),
                                                                 discord.SelectOption(label="Adjust SPD", value="clan spd"),
                                                                 discord.SelectOption(label="0 - No Clan", value="0"),
                                                                 discord.SelectOption(label="1", value="1"),
                                                                 discord.SelectOption(label="2", value="2"),
                                                                 discord.SelectOption(label="3", value="3"),
                                                                 discord.SelectOption(label="4", value="4"),
                                                                 discord.SelectOption(label="5", value="5"),
                                                                 discord.SelectOption(label="6", value="6"),
                                                                 discord.SelectOption(label="7", value="7"),
                                                                 discord.SelectOption(label="8", value="8"),
                                                                 discord.SelectOption(label="9", value="9"),
                                                                 discord.SelectOption(label="10", value="10"),
                                                                 discord.SelectOption(label="11", value="11"),
                                                                 discord.SelectOption(label="12", value="12"),
                                                                 discord.SelectOption(label="13", value="13"),
                                                                 discord.SelectOption(label="14", value="14"),
                                                                 discord.SelectOption(label="15", value="15")], custom_id="clan_row"))
    fam_row = discord.ui.ActionRow(discord.ui.Select(placeholder="Select fam / holo level.", min_values=1, max_values=1,
                                                      options=[discord.SelectOption(label="Fam 0", value="fam 0"),
                                                               discord.SelectOption(label="Fam 1", value="fam 1"),
                                                               discord.SelectOption(label="Fam 2", value="fam 2"),
                                                               discord.SelectOption(label="Fam 3", value="fam 3"),
                                                               discord.SelectOption(label="Holo", value="holo")], custom_id="holo_row"))
    del_row = discord.ui.ActionRow(discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="Delete"))

class CardInfoView(discord.ui.LayoutView):
    async def on_timeout(self):
        for child in self.children:
            for subchild in child.children:
                if isinstance(subchild, discord.ui.ActionRow):
                    for item in subchild.children:
                        item.disabled = True
        try:
            if hasattr(self, "message"):
                await self.message.edit(view=self)
        except Exception:
            pass
        self.stop()

async def v2_improved_card_info(message):
    for component in message.components:
        if hasattr(component, "children"):
            for child in component.children:
                if hasattr(child, "children"):
                    for subchild in child.children:
                        if hasattr(subchild, "content"):
                            card_data = re.search(
                                r"## \*\*(.*)\*\*\n\n"
                                r"\*\*Card ID:\*\*\s*(\d+)\n"
                                r"\*\*Card Series:\*\*\s*(.*)\n"
                                r"\*\*Location/Floor:\*\*\s*(None|(\d+)\s*\|\s*(\d+),\s*(\d+),\s*(\d+))\n"
                                r"\*\*Copies In Existence \(SR/UR\):\*\*\s*(\d+)\s*\|\s*(\d+)\n"
                                r"\*\*Type:\*\*\s*(.*?)\n"
                                r"\*\*HP:\*\*\s*(\d+)\n"
                                r"\*\*ATK:\*\*\s*(\d+)\n"
                                r"\*\*DEF:\*\*\s*(\d+)\n"
                                r"\*\*SPEED:\*\*\s*(\d+)", subchild.content)
                            card_name = card_data.group(1)
                            card_id = card_data.group(2)
                            card_series = card_data.group(3)
                            if card_data.group(4) == "None":
                                next_daily = "not available"
                                card_loc = "None"
                                event_cards = await runtime.retrieve_data("event cards")
                                if card_name in event_cards.get("clan_shop", []):
                                    card_floor = "Clan Shop"
                                elif card_name in event_cards.get("monthly_vote", []):
                                    card_floor = "Monthly Vote"
                                elif card_name in event_cards.get("event", []):
                                    card_floor = "Event"
                                else:
                                    card_floor = "None"
                            else:
                                card_loc = card_data.group(5)
                                floor_1 = card_data.group(6)
                                floor_2 = card_data.group(7)
                                floor_3 = card_data.group(8)
                                card_floor = ", ".join((floor_1, floor_2, floor_3))
                                locations = await runtime.retrieve_data("locations")
                                total_locations = len(locations)
                                current_counter = await general.get_daily_watch_counter()
                                loc_index = next((int(i) for i, name in locations.items() if name.lower() == card_series.lower()), None)
                                print(f"[CINFO DEBUG] card_series={card_series!r} loc_index={loc_index} current_counter={current_counter}")
                                if loc_index is None or current_counter is None:
                                    next_daily = "not available"
                                else:
                                    relative_offset = (loc_index - current_counter - 1) % total_locations
                                    daily_watch_tick = 43200
                                    base_tick = await general.get_global_daily_watch_timer()
                                    print(f"[CINFO DEBUG] base_tick={base_tick} relative_offset={relative_offset}")
                                    if base_tick is None:
                                        next_daily = "not available"
                                    else:
                                        now = int(time.time())
                                        while base_tick <= now:
                                            base_tick += daily_watch_tick
                                        next_daily = base_tick + (relative_offset * daily_watch_tick)
                                        next_daily = f"<t:{next_daily}:d> <t:{next_daily}:R>"
                            card_amount_sr = card_data.group(9)
                            card_amount_ur = card_data.group(10)
                            card_element = re.search(r"(\w+)", card_data.group(11))
                            card_element = card_element.group(1)
                            card_hp = card_data.group(12)
                            card_atk = card_data.group(13)
                            card_def = card_data.group(14)
                            card_speed = card_data.group(15)
                if hasattr(child, "items"):
                    for item in child.items:
                        if hasattr(item, "media") and hasattr(item.media, "url"):
                            card_info_picture = item.media.url
                if hasattr(child, "content"):
                    if "**Talent**" in child.content:
                        card_talent_name = re.search(r">\s\*\*(.*)\*\*\s?(?:\[PSV])?:", child.content)
                        card_talent_emote = await definitions.skill_converter_from_database(card_talent_name.group(1))
                        card_talent_description = re.search(r"\*\*\s?(?:\[PSV])?:\s?(.*)\*\*", child.content)
                        card_talent_text_sr = re.sub(r"__(\d+)__", lambda m: f"__{floor(int(m.group(1)) * 1.8)}__", card_talent_description.group(1))
                        card_talent_text_ur = re.sub(r"__(\d+)__", lambda m: f"__{floor(int(m.group(1)) * 2)}__", card_talent_description.group(1))
    ele_emote = await definitions.element_converter_from_database(card_element)
    card_data = await cards.get_cinfo_card_data_by_name(card_name)
    if not card_data:
        if message.channel.id == 1334918305819136171:
            if card_loc == "None":
                card_floor_db = "None"
            else:
                card_floor_db = [floor_1, floor_2, floor_3]
            await cards.create_card_in_collection(card_id, card_name, card_element, card_loc, card_floor_db, card_hp, card_atk, card_def, card_speed, card_talent_name.group(1), card_talent_description.group(1), card_series,
                                                  "N/A", "N/A", card_info_picture)
            card_data = await cards.get_cinfo_card_data_by_name(card_name)
        else:
            return
    if card_data[0]["card_price_sr"] == "N/A":
        market_price_sr = "N/A"
    else:
        market_price_sr = "{:,}".format(int(card_data[0]["card_price_sr"]))
    if card_data[0]["card_price_ur"] == "N/A":
        market_price_ur = "N/A"
    else:
        market_price_ur = "{:,}".format(int(card_data[0]["card_price_ur"]))
    if message.author.id == 571027211407196161 and message.reference:
        ref = message.reference
        cached = discord.utils.get(runtime.bot.cached_messages, id=ref.message_id)
        if cached:
            player = cached.author
        else:
            original = await message.channel.fetch_message(ref.message_id)
            player = original.author
        player_settings = await players.get_settings_from_player_by_discord_id(player.id)
    card_rarity = "Base"
    card_rarity_name = "Base"
    evolution_sr = 1
    evolution_ur = 1
    sr_asc_lvl = 0
    ur_asc_lvl = 0
    familiarity_bonus = 0
    familiarity_bonus_name = "F0"
    clan_stat_to_change = "all"
    clan_stat_hp = 0
    clan_stat_atk = 0
    clan_stat_def = 0
    clan_stat_spd = 0
    if player_settings["cinfo_picture"] == "original":
        container = CardInfoContainer1(id=1, accent_colour=0x71368A)
        container.card_picture.items[0].media = card_info_picture
    else:
        container = CardInfoContainer2(id=1, accent_colour=0x71368A)
        container.thumbnail.accessory.media = card_info_picture
    thumbnail_text = (f"## **{card_name}**\n\n"
                     f"**Card ID:** {card_id}\n"
                     f"**Card Series:** {card_series}\n"
                     f"**Location/Floor:** {card_loc} | {card_floor}\n"
                     f"**Next Daily:** {next_daily}\n"
                     f"**Copies In Existence (SR/UR):** {card_amount_sr} / {card_amount_ur}\n"
                     f"**Element:** {card_element} {ele_emote}\n"
                     f"**Market Price SR:** {market_price_sr} <t:{card_data[0]['market_price_sr_timer']}:R>\n"
                     f"**Market Price UR:** {market_price_ur} <t:{card_data[0]['market_price_ur_timer']}:R>\n")
    container.thumbnail.children[0].content = thumbnail_text
    _sr_hp  = ceil(int(card_hp)    * 3.5)
    _sr_atk = ceil(int(card_atk)   * 3.5)
    _sr_def = ceil(int(card_def)   * 3.5)
    _sr_spd = ceil(int(card_speed) * 3.5)
    _ur_hp  = ceil(int(card_hp)    * 4.2)
    _ur_atk = ceil(int(card_atk)   * 4.2)
    _ur_def = ceil(int(card_def)   * 4.2)
    _ur_spd = ceil(int(card_speed) * 4.2)
    _base_total = int(card_hp) + int(card_atk) + int(card_def) + int(card_speed)
    _sr_total   = _sr_hp + _sr_atk + _sr_def + _sr_spd
    _ur_total   = _ur_hp + _ur_atk + _ur_def + _ur_spd
    _W = 16
    _stats_table = (
        f"{'Base Stats':<{_W}}{'SR A4':<{_W}}UR A5\n"
        f"{'HP: '+str(card_hp):<{_W}}{'HP: '+str(_sr_hp):<{_W}}HP: {_ur_hp}\n"
        f"{'ATK: '+str(card_atk):<{_W}}{'ATK: '+str(_sr_atk):<{_W}}ATK: {_ur_atk}\n"
        f"{'DEF: '+str(card_def):<{_W}}{'DEF: '+str(_sr_def):<{_W}}DEF: {_ur_def}\n"
        f"{'SPEED: '+str(card_speed):<{_W}}{'SPEED: '+str(_sr_spd):<{_W}}SPEED: {_ur_spd}\n"
        f"{'TOTAL: '+str(_base_total):<{_W}}{'TOTAL: '+f'{_sr_total:,}':<{_W}}TOTAL: {_ur_total:,}"
    )
    container.card_stats.content = f"```\n{_stats_table}\n```"
    container.card_talent.content = (
        f"**__SR Talent__**\n"
        f"{card_talent_emote} **{card_talent_name.group(1)}:** {card_talent_text_sr}\n\n"
        f"**__UR Talent__**\n"
        f"{card_talent_emote} **{card_talent_name.group(1)}:** {card_talent_text_ur}"
    )
    rarity_select = container.rarity_row.children[0]
    clan_select = container.clan_row.children[0]
    fam_select = container.fam_row.children[0]
    del_button = container.del_row.children[0]
    async def rarity_callback(interaction: discord.Interaction):
        if interaction.user.id != player.id:
            await interaction.response.defer()
            return
        select_value = rarity_select.values[0]
        nonlocal card_rarity, card_rarity_name, evolution_sr,evolution_ur,sr_asc_lvl,ur_asc_lvl,familiarity_bonus, familiarity_bonus_name, clan_stat_hp, clan_stat_atk, clan_stat_def, clan_stat_spd
        if select_value == "UR A5":
            evolution_ur = 3
            ur_asc_lvl = 5
            card_rarity = "Ultra Rare"
            card_rarity_name = select_value
        elif select_value == "UR A4":
            evolution_ur = 3
            ur_asc_lvl = 4
            card_rarity = "Ultra Rare"
            card_rarity_name = select_value
        elif select_value == "UR A3":
            evolution_ur = 3
            ur_asc_lvl = 3
            card_rarity = "Ultra Rare"
            card_rarity_name = select_value
        elif select_value == "UR A2":
            evolution_ur = 3
            ur_asc_lvl = 2
            card_rarity = "Ultra Rare"
            card_rarity_name = select_value
        elif select_value == "UR A1":
            evolution_ur = 3
            ur_asc_lvl = 1
            card_rarity = "Ultra Rare"
            card_rarity_name = select_value
        elif select_value == "UR E3":
            evolution_ur = 3
            ur_asc_lvl = 0
            card_rarity = "Ultra Rare"
            card_rarity_name = select_value
        elif select_value == "UR E2":
            evolution_ur = 2
            ur_asc_lvl = 0
            card_rarity = "Ultra Rare"
            card_rarity_name = select_value
        elif select_value == "UR E1":
            evolution_ur = 1
            ur_asc_lvl = 0
            card_rarity = "Ultra Rare"
            card_rarity_name = select_value
        elif select_value == "SR A4":
            evolution_sr = 3
            sr_asc_lvl = 4
            card_rarity = "Super Rare"
            card_rarity_name = select_value
        elif select_value == "SR A3":
            evolution_sr = 3
            sr_asc_lvl = 3
            card_rarity = "Super Rare"
            card_rarity_name = select_value
        elif select_value == "SR A2":
            evolution_sr = 3
            sr_asc_lvl = 2
            card_rarity = "Super Rare"
            card_rarity_name = select_value
        elif select_value == "SR A1":
            evolution_sr = 3
            sr_asc_lvl = 1
            card_rarity = "Super Rare"
            card_rarity_name = select_value
        elif select_value == "SR E3":
            evolution_sr = 3
            sr_asc_lvl = 0
            card_rarity = "Super Rare"
            card_rarity_name = select_value
        elif select_value == "SR E2":
            evolution_sr = 2
            sr_asc_lvl = 0
            card_rarity = "Super Rare"
            card_rarity_name = select_value
        elif select_value == "SR E1":
            evolution_sr = 1
            sr_asc_lvl = 0
            card_rarity = "Super Rare"
            card_rarity_name = select_value
        else:
            card_rarity = "Base"
            card_rarity_name = "Base"
        if card_rarity == "Ultra Rare":
            evolution = evolution_ur
            ascension = ur_asc_lvl
        elif card_rarity == "Super Rare":
            evolution = evolution_sr
            ascension = sr_asc_lvl
        else:
            evolution = 1
            ascension = 0
        calc_hp, calc_atk, calc_def, calc_spd = await definitions.calc_card_stats(card_hp, card_atk, card_def, card_speed, card_rarity, evolution, ascension, familiarity_bonus, clan_stat_hp, clan_stat_atk, clan_stat_def, clan_stat_spd)
        if player_settings["cinfo_stat_display"] == "compact":
            container.card_stats.content = f"**__{card_rarity_name} {familiarity_bonus_name}__**\n**HP:** {calc_hp} (+{clan_stat_hp}%) **|** **ATK:** {calc_atk} (+{clan_stat_atk}%) **|** **DEF:** {calc_def} (+{clan_stat_def}%) **|** **SPD:** {calc_spd} (+{clan_stat_spd}%)"
        else:
            container.card_stats.content = f"**__{card_rarity_name} {familiarity_bonus_name}__**\n**HP:** {calc_hp} (+{clan_stat_hp}%)\n**ATK:** {calc_atk} (+{clan_stat_atk}%)\n**DEF:** {calc_def} (+{clan_stat_def}%)\n**SPD:** {calc_spd} (+{clan_stat_spd}%)"
        if card_rarity == "Super Rare":
            container.card_talent.content = f"**__Talent__**\n{card_talent_emote} **{card_talent_name.group(1)}:** {card_talent_text_sr}"
        elif card_rarity == "Ultra Rare":
            container.card_talent.content = f"**__Talent__**\n{card_talent_emote} **{card_talent_name.group(1)}:** {card_talent_text_ur}"
        else:
            container.card_talent.content = f"**Talent**\n{card_talent_emote} **{card_talent_name.group(1)}:** {card_talent_description.group(1)}"
        await interaction.response.edit_message(view=view)
        return
    async def clan_callback(interaction: discord.Interaction):
        if interaction.user.id != player.id:
            await interaction.response.defer()
            return
        select_value = clan_select.values[0]
        nonlocal card_rarity, card_rarity_name, evolution_sr,evolution_ur,sr_asc_lvl,ur_asc_lvl,familiarity_bonus, familiarity_bonus_name, clan_stat_to_change, clan_stat_hp, clan_stat_atk, clan_stat_def, clan_stat_spd
        if select_value == "all stats":
            clan_stat_to_change = "all"
            await interaction.response.send_message("All following clan stat changes will affect: ``all``. If you want to change that, please select a different value.", ephemeral=True)
            return
        elif select_value == "clan hp":
            clan_stat_to_change = "hp"
            await interaction.response.send_message("All following clan stat change will affect: ``hp``. If you want to change that, please select a different value.", ephemeral=True)
            return
        elif select_value == "clan atk":
            clan_stat_to_change = "atk"
            await interaction.response.send_message("All following clan stat change will affect: ``atk``. If you want to change that, please select a different value.", ephemeral=True)
            return
        elif select_value == "clan def":
            clan_stat_to_change = "def"
            await interaction.response.send_message("All following clan stat change will affect: ``def``. If you want to change that, please select a different value.", ephemeral=True)
            return
        elif select_value == "clan spd":
            clan_stat_to_change = "spd"
            await interaction.response.send_message("All following clan stat change will affect: ``spd``. If you want to change that, please select a different value.", ephemeral=True)
            return
        elif select_value == "1":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 6
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 6
            elif clan_stat_to_change == "def":
                clan_stat_def = 6
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 6
            else:
                clan_stat_hp = 6
                clan_stat_atk = 6
                clan_stat_def = 6
                clan_stat_spd = 6
        elif select_value == "2":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 7
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 7
            elif clan_stat_to_change == "def":
                clan_stat_def = 7
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 7
            else:
                clan_stat_hp = 7
                clan_stat_atk = 7
                clan_stat_def = 7
                clan_stat_spd = 7
        elif select_value == "3":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 8
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 8
            elif clan_stat_to_change == "def":
                clan_stat_def = 8
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 8
            else:
                clan_stat_hp = 8
                clan_stat_atk = 8
                clan_stat_def = 8
                clan_stat_spd = 8
        elif select_value == "4":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 9
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 9
            elif clan_stat_to_change == "def":
                clan_stat_def = 9
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 9
            else:
                clan_stat_hp = 9
                clan_stat_atk = 9
                clan_stat_def = 9
                clan_stat_spd = 9
        elif select_value == "5":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 10
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 10
            elif clan_stat_to_change == "def":
                clan_stat_def = 10
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 10
            else:
                clan_stat_hp = 10
                clan_stat_atk = 10
                clan_stat_def = 10
                clan_stat_spd = 10
        elif select_value == "6":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 11
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 11
            elif clan_stat_to_change == "def":
                clan_stat_def = 11
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 11
            else:
                clan_stat_hp = 11
                clan_stat_atk = 11
                clan_stat_def = 11
                clan_stat_spd = 11
        elif select_value == "7":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 12
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 12
            elif clan_stat_to_change == "def":
                clan_stat_def = 12
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 12
            else:
                clan_stat_hp = 12
                clan_stat_atk = 12
                clan_stat_def = 12
                clan_stat_spd = 12
        elif select_value == "8":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 13
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 13
            elif clan_stat_to_change == "def":
                clan_stat_def = 13
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 13
            else:
                clan_stat_hp = 13
                clan_stat_atk = 13
                clan_stat_def = 13
                clan_stat_spd = 13
        elif select_value == "9":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 14
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 14
            elif clan_stat_to_change == "def":
                clan_stat_def = 14
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 14
            else:
                clan_stat_hp = 14
                clan_stat_atk = 14
                clan_stat_def = 14
                clan_stat_spd = 14
        elif select_value == "10":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 15
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 15
            elif clan_stat_to_change == "def":
                clan_stat_def = 15
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 15
            else:
                clan_stat_hp = 15
                clan_stat_atk = 15
                clan_stat_def = 15
                clan_stat_spd = 15
        elif select_value == "11":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 16
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 16
            elif clan_stat_to_change == "def":
                clan_stat_def = 16
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 16
            else:
                clan_stat_hp = 16
                clan_stat_atk = 16
                clan_stat_def = 16
                clan_stat_spd = 16
        elif select_value == "12":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 17
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 17
            elif clan_stat_to_change == "def":
                clan_stat_def = 17
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 17
            else:
                clan_stat_hp = 17
                clan_stat_atk = 17
                clan_stat_def = 17
                clan_stat_spd = 17
        elif select_value == "13":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 18
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 18
            elif clan_stat_to_change == "def":
                clan_stat_def = 18
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 18
            else:
                clan_stat_hp = 18
                clan_stat_atk = 18
                clan_stat_def = 18
                clan_stat_spd = 18
        elif select_value == "14":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 19
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 19
            elif clan_stat_to_change == "def":
                clan_stat_def = 19
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 19
            else:
                clan_stat_hp = 19
                clan_stat_atk = 19
                clan_stat_def = 19
                clan_stat_spd = 19
        elif select_value == "15":
            if clan_stat_to_change == "hp":
                clan_stat_hp = 20
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 20
            elif clan_stat_to_change == "def":
                clan_stat_def = 20
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 20
            else:
                clan_stat_hp = 20
                clan_stat_atk = 20
                clan_stat_def = 20
                clan_stat_spd = 20
        else:
            if clan_stat_to_change == "hp":
                clan_stat_hp = 0
            elif clan_stat_to_change == "atk":
                clan_stat_atk = 0
            elif clan_stat_to_change == "def":
                clan_stat_def = 0
            elif clan_stat_to_change == "spd":
                clan_stat_spd = 0
            else:
                clan_stat_hp = 0
                clan_stat_atk = 0
                clan_stat_def = 0
                clan_stat_spd = 0
        if card_rarity == "Ultra Rare":
            evolution = evolution_ur
            ascension = ur_asc_lvl
        elif card_rarity == "Super Rare":
            evolution = evolution_sr
            ascension = sr_asc_lvl
        else:
            evolution = 1
            ascension = 0
        calc_hp, calc_atk, calc_def, calc_spd = await definitions.calc_card_stats(card_hp, card_atk, card_def, card_speed, card_rarity, evolution, ascension, familiarity_bonus, clan_stat_hp, clan_stat_atk, clan_stat_def, clan_stat_spd)
        if player_settings["cinfo_stat_display"] == "compact":
            container.card_stats.content = f"**__{card_rarity_name} {familiarity_bonus_name}__**\n**HP:** {calc_hp} (+{clan_stat_hp}%) **|** **ATK:** {calc_atk} (+{clan_stat_atk}%) **|** **DEF:** {calc_def} (+{clan_stat_def}%) **|** **SPD:** {calc_spd} (+{clan_stat_spd}%)"
        else:
            container.card_stats.content = f"**__{card_rarity_name} {familiarity_bonus_name}__**\n**HP:** {calc_hp} (+{clan_stat_hp}%)\n**ATK:** {calc_atk} (+{clan_stat_atk}%)\n**DEF:** {calc_def} (+{clan_stat_def}%)\n**SPD:** {calc_spd} (+{clan_stat_spd}%)"
        await interaction.response.edit_message(view=view)
        return
    async def fam_callback(interaction: discord.Interaction):
        if interaction.user.id != player.id:
            await interaction.response.defer()
            return
        select_value = fam_select.values[0]
        nonlocal card_rarity, card_rarity_name, evolution_sr,evolution_ur,sr_asc_lvl,ur_asc_lvl,familiarity_bonus, familiarity_bonus_name, clan_stat_to_change, clan_stat_hp, clan_stat_atk, clan_stat_def, clan_stat_spd
        if select_value == "fam 1":
            familiarity_bonus = 2
            familiarity_bonus_name = "F1"
        elif select_value == "fam 2":
            familiarity_bonus = 4
            familiarity_bonus_name = "F2"
        elif select_value == "fam 3":
            familiarity_bonus = 6
            familiarity_bonus_name = "F3"
        elif select_value == "holo":
            familiarity_bonus = 12
            familiarity_bonus_name = "H1"
        else:
            familiarity_bonus = 0
            familiarity_bonus_name = "F0"
        if card_rarity == "Ultra Rare":
            evolution = evolution_ur
            ascension = ur_asc_lvl
        elif card_rarity == "Super Rare":
            evolution = evolution_sr
            ascension = sr_asc_lvl
        else:
            evolution = 1
            ascension = 0
        calc_hp, calc_atk, calc_def, calc_spd = await definitions.calc_card_stats(card_hp, card_atk, card_def, card_speed, card_rarity, evolution, ascension, familiarity_bonus, clan_stat_hp, clan_stat_atk, clan_stat_def, clan_stat_spd)
        if player_settings["cinfo_stat_display"] == "compact":
            container.card_stats.content = f"**__{card_rarity_name} {familiarity_bonus_name}__**\n**HP:** {calc_hp} (+{clan_stat_hp}%) **|** **ATK:** {calc_atk} (+{clan_stat_atk}%) **|** **DEF:** {calc_def} (+{clan_stat_def}%) **|** **SPD:** {calc_spd} (+{clan_stat_spd}%)"
        else:
            container.card_stats.content = f"**__{card_rarity_name} {familiarity_bonus_name}__**\n**HP:** {calc_hp} (+{clan_stat_hp}%)\n**ATK:** {calc_atk} (+{clan_stat_atk}%)\n**DEF:** {calc_def} (+{clan_stat_def}%)\n**SPD:** {calc_spd} (+{clan_stat_spd}%)"
        await interaction.response.edit_message(view=view)
        return
    async def del_button_callback(interaction: discord.Interaction):
        if interaction.user.id != player.id:
            await interaction.response.defer()
            return
        await interaction.message.delete()
        return
    rarity_select.callback = rarity_callback
    clan_select.callback = clan_callback
    fam_select.callback = fam_callback
    del_button.callback = del_button_callback
    view = CardInfoView(timeout=120)
    view.container = container
    view.add_item(container)
    msg = await message.channel.send(view=view)
    view.message = msg
    if player_settings["cinfo_delete"] == "yes":
        try:
            await message.delete()
        except (discord.errors.NotFound, discord.errors.Forbidden):
            pass


async def v2_pack_opening(message):
    card_text = ""
    for component in message.components:
        if hasattr(component, "children"):
            for child in component.children:
                if hasattr(child, "children"):
                    for subchild in child.children:
                        if hasattr(subchild, "content"):
                            opened_pack_cards = re.findall(r"(Common|Uncommon|Rare|Super Rare|Ultra Rare)\s\*\*(.*)\*\*", subchild.content)
                            for rarity, name in opened_pack_cards:
                                if rarity in ("Super Rare", "Ultra Rare"):
                                    card_data = await cards.get_card_data_by_name(name)
                                    card_price_sr = card_data[0].get("card_price_sr", 0)
                                    if card_price_sr != "N/A":
                                        card_price_sr = "{:,}".format(int(card_price_sr))
                                    card_price_ur = card_data[0].get("card_price_ur", 0)
                                    if card_price_ur != "N/A":
                                        card_price_ur = "{:,}".format(int(card_price_ur))
                                    card_price = card_price_sr if rarity == "Super Rare" else card_price_ur
                                    card_element = await definitions.element_converter_from_database(card_data[0]['card_element'])
                                    card_talent = await definitions.skill_converter_from_database(card_data[0]['card_talent'])
                                    card_text += (f"{card_data[0]['card_name']} {card_element} {card_talent}\n"
                                                  f"{card_price} {gold_emote}\n\n")

    class PackOpeningContainer(discord.ui.Container):
        text_rare = discord.ui.TextDisplay(f"{card_text}")

    class PackOpeningView(discord.ui.LayoutView):
        container = PackOpeningContainer(id=1, accent_colour=0x71368A)

    view = PackOpeningView()
    if card_text:
        await message.channel.send(view=view)

# -----------------------
# REWORKED V2
# -----------------------


async def v2_global_market_update(message):
    global_market_data = []
    global_market_sr = {}
    global_market_ur = {}
    for component in message.components:
        if hasattr(component, "children"):
            for child in component.children:
                if hasattr(child, "children"):
                    for subchild in child.children:
                        if hasattr(subchild, "content") and "| ID:" in subchild.content:
                            if "Null:" in subchild.content:
                                subchild.content = subchild.content.replace("<:Null:1329746549382582285>", "")
                            if "⛰️" in subchild.content:
                                subchild.content = subchild.content.replace("⛰️", "")
                            if "☀️" in subchild.content:
                                subchild.content = subchild.content.replace("☀️", "")
                            global_market = re.findall(fr"\*\*(\d+) Gold <a:gold:1219941344450052187> \| (.*?) \[Evo 1] [🍃🔥💧⚡🌙✨]? <:(?:.*?)>\s*⌛?\*\*\n(?:\u200b)?\s*<a?:(\w+):", subchild.content.replace(",",""))
                            global_market_data.extend(global_market)
    for gold, card_name, rarity in global_market_data:
        gold = int(gold)
        if rarity == "super":
            if card_name not in global_market_sr or gold < global_market_sr[card_name]:
                global_market_sr[card_name] = gold
        elif rarity == "ultra":
            if card_name not in global_market_ur or gold < global_market_ur[card_name]:
                global_market_ur[card_name] = gold
    for card_name, price in global_market_sr.items():
        card_price_sr = await cards.get_card_market_price_sr_by_cards_name(card_name)
        if card_price_sr != "N/A":
            price_factor = 2
            if int(card_price_sr) <= 10:
                price_factor = 50000
            elif int(card_price_sr) <= 50:
                price_factor = 10000
            elif int(card_price_sr) <= 100:
                price_factor = 5000
            elif int(card_price_sr) <= 500:
                price_factor = 1000
            elif int(card_price_sr) <= 1000:
                price_factor = 50
            elif int(card_price_sr) <= 5000:
                price_factor = 10
            elif int(card_price_sr) <= 10000:
                price_factor = 5
            elif int(card_price_sr) <= 20000:
                price_factor = 4
            elif int(card_price_sr) <= 30000:
                price_factor = 3
            if price > price_factor * int(card_price_sr):
                continue
        await cards.update_market_price_sr_by_cards_name(card_name, str(price))
    for card_name, price in global_market_ur.items():
        await cards.update_market_price_ur_by_cards_name(card_name, str(price))


async def v2_card_select(message):
    card_rarity = "Error"
    card_name = "Error"
    card_lvl = "Error"
    card_evo = "Error"
    card_emote = "Error"
    for component in message.components:
        if hasattr(component, "children"):
            for child in component.children:
                if hasattr(child, "content") and "Active Battle Card" in child.content:
                    card_data = re.search(r"<a?:([a-zA-Z0-9_]+):\d+>(?:<a?:.+>)?\*\*(.*)\*\* __Level (\d+)__ \*\*\[Evo (\d+)]", child.content)
                    if card_data:
                        card_rarity = card_data.group(1)
                        if card_rarity == "common":
                            card_emote = common_emote_1
                        elif card_rarity == "not":
                            card_emote = f"{uncommon_emote_1}{uncommon_emote_2}"
                        elif card_rarity == "rare":
                            card_emote = rare_emote
                        elif card_rarity == "super":
                            card_emote = f"{super_rare_1}{super_rare_2}"
                        elif card_rarity == "ultra":
                            card_emote = f"{ultra_rare_1}{ultra_rare_2}"
                        card_name = card_data.group(2)
                        card_lvl = card_data.group(3)
                        card_evo = card_data.group(4)
    if message.reference and message.reference.resolved:
        original_message = message.reference.resolved
        if isinstance(original_message, discord.Message):
            user_id = original_message.author.id
            user_name = original_message.author.name
            select_card_status = await players.get_selected_card_info_from_player_by_discord_id(user_id)
            if select_card_status == "yes":
                await original_message.reply(f"The user **{user_name}** selected the card {card_emote} ``{card_name}`` Level {card_lvl} [EVO {card_evo}]")
                await message.delete()
    else:
        return

async def on_raw_reaction_add(payload, bot):
    if payload.user_id == bot.user.id:
        return
    if payload.emoji.id == 1495870697577250888:
        message = discord.utils.get(bot.cached_messages, id=payload.message_id)
        if not message:
            channel = bot.get_channel(payload.channel_id)
            if not channel:
                return
            message = await channel.fetch_message(payload.message_id)
        if message.reference and message.reference.message_id:
            original_message = message.reference.resolved or await message.channel.fetch_message(message.reference.message_id)
            if original_message.author.id != payload.user_id:
                return
            view = InventoryHelperView(message=message, user_id=original_message.author.id)
            await message.channel.send(view=view)


class InventoryHelperView(discord.ui.LayoutView):
    def __init__(self, message, user_id, timeout=120):
        super().__init__(timeout=timeout)
        self.message = message
        self.captured_options = []
        for component in message.components:
            for child in component.children:
                if hasattr(child, "children"):
                    for sub in child.children:
                        if sub.type == ComponentType.select:
                            self.captured_options = [discord.SelectOption(label=o.label, value=o.value, description=o.description, emoji=o.emoji, default=o.default) for o in sub.options]
                            break
            if self.captured_options:
                break
        self.selected_for_selling = []
        self.max_value = min(4, len(self.captured_options))
        self.user_id = user_id
        self.container = self.build_container()
        self.add_item(self.container)

    def build_container(self):
        container = discord.ui.Container(accent_colour=0x71368A)
        container.add_item(discord.ui.TextDisplay(f"## :notepad_spiral: Choose your action"))
        container.add_item(discord.ui.Separator())
        options = self.captured_options if self.captured_options else [discord.SelectOption(label="No Items found", value="none")]

        # 1. Global ID Selection
        select_menu_global_id = discord.ui.Select(placeholder="Global ID selection.", min_values=1, options=options)

        async def select_global_id_callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.defer(ephemeral=True)
                return
            selection = interaction.data["values"][0]
            option = next(o for o in self.captured_options if o.value == selection)
            desc = option.description
            global_card_id = desc.split("ID: ")[1]
            await interaction.response.send_message(global_card_id)
        select_menu_global_id.callback = select_global_id_callback
        container.add_item(discord.ui.ActionRow(select_menu_global_id))
        container.add_item(discord.ui.Separator())

        # 2. Selling Selection
        select_menu_selling = discord.ui.Select(placeholder="Selling selection.", min_values=1, max_values=len(options), options=options)

        async def select_selling_callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.defer(ephemeral=True)
                return
            selected = interaction.data["values"]
            for v in selected:
                option = next(o for o in self.captured_options if o.value == v)
                desc = option.description
                card_id = desc.split("ID: ")[1]
                if card_id not in self.selected_for_selling:
                    self.selected_for_selling.append(card_id)
            channel = interaction.channel
            bot = interaction.client
            await interaction.response.defer()
            asyncio.create_task(process_selling(bot, channel, self.selected_for_selling))
        select_menu_selling.callback = select_selling_callback
        container.add_item(discord.ui.ActionRow(select_menu_selling))
        container.add_item(discord.ui.Separator())

        # 3. Building Selection
        select_menu_building = discord.ui.Select(placeholder="Building selection.", min_values=1, max_values=self.max_value, options=options)

        async def select_building_callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.defer(ephemeral=True)
                return
            selected = interaction.data["values"]
            if len(selected) == 1 or len(selected) == 3:
                await interaction.response.send_message(f"Please select either 2 or 4 and not {len(selected)}", ephemeral=True)
                return
            inventory_ids = []
            for v in selected:
                option = next(o for o in self.captured_options if o.value == v)
                inv_id = extract_inventory_id(option)
                inventory_ids.append(inv_id)
            inventory_ids = sorted(inventory_ids, key=int)
            actions = build_evo_commands(inventory_ids)
            await interaction.response.send_message("\n".join(actions))
        select_menu_building.callback = select_building_callback
        container.add_item(discord.ui.ActionRow(select_menu_building))
        return container


async def process_selling(bot, channel, selected_ids):
    for card_id in selected_ids:
        await channel.send(f".mk sell {card_id}")

        def check(msg):
            if msg.author.id != 571027211407196161:
                return False
            if msg.channel.id != channel.id:
                return False
            if not msg.components:
                return False
            content = extract_text_from_components(msg.components)
            return "Market Listing Complete" in content and str(card_id) in content
        try:
            await bot.wait_for("message", check=check, timeout=30)
            await asyncio.sleep(5)
        except asyncio.TimeoutError:
            await channel.send(f"❌ Timeout on ID {card_id}")
            break

def extract_text_from_components(components):
    texts = []
    for comp in components:
        if hasattr(comp, "content") and isinstance(comp.content, str):
            texts.append(comp.content)
        if hasattr(comp, "children"):
            texts.append(extract_text_from_components(comp.children))
    return "\n".join(texts)

def extract_inventory_id(option: discord.SelectOption) -> str:
    match = re.match(r"#(\d+)", option.label)
    return match.group(1) if match else None

def build_evo_commands(card_ids: list[str]) -> list[str]:
    ids = sorted(card_ids, key=int)
    actions = []
    if len(ids) == 4:
        a, b, c, d = ids
        actions += [f".soulenh {a}", f".soulenh {b}", f".soulenh {c}", f".soulenh {d}",]
        actions += [f".evo {a} {d}", f".evo {b} {c}",]
        actions += [ f".soulenh {a}", f".soulenh {b}",]
        actions += [f".evo {a} {b}",]
        actions += [f".soulenh {a}"]
    elif len(ids) == 2:
        a, b = ids
        actions += [f".soulenh {a}", f".soulenh {b}",  f".evo {a} {b}", f".soulenh {a}",]
    return actions


async def player_stamina_v2(message):
    stamina_data = re.search(r"\*\*(.*)\*\*, you currently have __(\d+)/(\d+)__ stamina", message.content)
    player_name = stamina_data.group(1)
    player_current_stamina = stamina_data.group(2)
    player_max_stamina = stamina_data.group(3)
    player_days_left, player_id = await players.get_premium_days_left_by_discord_name(player_name)
    if player_days_left == "player not found":
        return
    stamina_view = PlayerStaminaView(message, player_name, player_id, int(player_current_stamina), int(player_max_stamina), player_days_left)
    try:
        await message.reply(view=stamina_view)
    except discord.HTTPException:
        await message.channel.send(view=stamina_view)


class PlayerStaminaView(discord.ui.LayoutView):
    def __init__(self, message, player_name, player_id, player_current_stamina, player_max_stamina, premium_days_left, timeout=120):
        super().__init__(timeout=timeout)
        self.message = message
        self.player_name = player_name
        self.player_id = player_id
        self.player_current_stamina = player_current_stamina
        self.player_max_stamina = player_max_stamina
        self.premium_days_left = premium_days_left
        self.stamina_regen_amount = 2
        self.stamina_regen_amount_vip = 3
        self.stamina_regen_time = 240
        self.battle_xp = 2
        self.fam_xp = 2
        self.now = int(time.time())
        self.container = self.build_container()
        self.add_item(self.container)

    def build_container(self):
        container = discord.ui.Container(accent_colour=0x71368A)
        container.add_item(discord.ui.TextDisplay(f"Player** {self.player_name}** currently has **{self.player_current_stamina:,}/{self.player_max_stamina}** stamina."))
        if self.player_current_stamina >= self.player_max_stamina:
            timer_till_full = self.now
        else:
            missing_stamina = self.player_max_stamina - self.player_current_stamina
            if self.premium_days_left > 0:
                time_in_s = missing_stamina * (self.stamina_regen_time // self.stamina_regen_amount_vip)
            else:
                time_in_s = missing_stamina * (self.stamina_regen_time // self.stamina_regen_amount)
            timer_till_full = self.now + time_in_s
        container.add_item(discord.ui.TextDisplay(f"Full in: <t:{timer_till_full}:S> [<t:{timer_till_full}:R>]"))
        battle_amount = self.player_current_stamina // 5
        container.add_item(discord.ui.TextDisplay(f"[**Battles:** {battle_amount}] [**EXP / FAM:** {battle_amount * 2}]"))
        vip_timer = self.now + (self.premium_days_left * 86400)
        status = "<a:check:1380797984979030016>" if self.premium_days_left > 0 else "<a:cross:1380797973373521962>"
        container.add_item(discord.ui.TextDisplay(f"-# [VIP active: {status}] [VIP Days left: {self.premium_days_left} <t:{vip_timer}:d>]"))
        button_delete = discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger)
        button_delete.callback = self.delete_button
        container.add_item(discord.ui.ActionRow(button_delete))
        return container

    async def delete_button(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.player_id:
            return
        await interaction.message.delete()


async def raid_pass_v2(message):
    raid_pass_data = re.search(r"\*\*(.*)\*\* currently has __(\d+)/10__ Raid Pass\(es\) <:raidpass:861860078742929428>\. \[Refills \*\*<t:(\d+):R>", message.content)
    player_name = raid_pass_data.group(1)
    player_current_raid_pass = raid_pass_data.group(2)
    unix_timer = raid_pass_data.group(3)
    player_days_left, player_id = await players.get_premium_days_left_by_discord_name(player_name)
    if player_days_left == "player not found":
        return
    raid_pass_view = PlayerRaidPassesView(message, player_name, player_id, int(player_current_raid_pass), int(unix_timer), player_days_left)
    try:
        await message.reply(view=raid_pass_view)
    except discord.HTTPException:
        await message.channel.send(view=raid_pass_view)


class PlayerRaidPassesView(discord.ui.LayoutView):
    def __init__(self, message, player_name, player_id, player_current_raid_pass, unix_timer, premium_days_left, timeout=120):
        super().__init__(timeout=timeout)
        self.message = message
        self.player_name = player_name
        self.player_id = player_id
        self.player_current_raid_pass = player_current_raid_pass
        self.unix_timer = unix_timer
        self.raid_pass_regen_timer = 18000
        self.premium_days_left = premium_days_left
        self.now = int(time.time())
        self.container = self.build_container()
        self.add_item(self.container)

    def build_container(self):
        container = discord.ui.Container(accent_colour=0x71368A)
        container.add_item(discord.ui.TextDisplay(f"Player** {self.player_name}** currently has **{self.player_current_raid_pass}/10** Raid Pass(es) <:raid_pass:1497633575892156536>."))
        if self.player_current_raid_pass < 10:
            needed_passes = 10 - (self.player_current_raid_pass + 1)
            raid_pass_refill = self.unix_timer + (needed_passes * self.raid_pass_regen_timer)
        else:
            raid_pass_refill = self.now
        container.add_item(discord.ui.TextDisplay(f"[**Refill in:** <t:{self.unix_timer}:R>] [**Full in:** <t:{raid_pass_refill}:R>]"))
        vip_timer = self.now + (self.premium_days_left * 86400)
        status = "<a:check:1380797984979030016>" if self.premium_days_left > 0 else "<a:cross:1380797973373521962>"
        container.add_item(discord.ui.TextDisplay(f"-# [VIP active: {status}] [VIP Days left: {self.premium_days_left} <t:{vip_timer}:d>]"))
        button_delete = discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger)
        button_delete.callback = self.delete_button
        container.add_item(discord.ui.ActionRow(button_delete))
        return container

    async def delete_button(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.player_id:
            return
        await interaction.message.delete()


async def player_lvl_v2(message):
    message_clean = message.content.replace(",", "")
    player_data = re.search(r"\*\*(.*)\*\*: Level (\d+)\s+", message.content)
    player_name = player_data.group(1)
    player_lvl = player_data.group(2)
    player_exp_data = re.search(r"\[(\d+) / (\d+) EXP", message_clean)
    player_current_exp = player_exp_data.group(1)
    player_max_exp = player_exp_data.group(2)
    player_days_left, player_id = await players.get_premium_days_left_by_discord_name(player_name)
    if player_days_left == "player not found":
        return
    player_view = PlayerLevelView(message, player_name, player_id, int(player_lvl), int(player_current_exp), int(player_max_exp), player_days_left)
    try:
        await message.reply(view=player_view)
    except discord.HTTPException:
        await message.channel.send(view=player_view)

class PlayerLevelView(discord.ui.LayoutView):
    def __init__(self, message, player_name, player_id, player_lvl, player_current_exp, player_max_exp, premium_days_left, timeout=120):
        super().__init__(timeout=timeout)
        self.message = message
        self.player_name = player_name
        self.player_id = player_id
        self.player_lvl = player_lvl
        self.player_current_exp = player_current_exp
        self.player_max_exp = player_max_exp
        self.premium_days_left = premium_days_left
        self.now = int(time.time())
        self.container = self.build_container()
        self.add_item(self.container)

    def build_container(self):
        container = discord.ui.Container(accent_colour=0x71368A)
        container.add_item(discord.ui.TextDisplay(f"Player **{self.player_name}** is currently Level **{self.player_lvl}** [{self.player_current_exp:,}/{self.player_max_exp:,}]"))
        if self.player_current_exp < self.player_max_exp:
            needed_exp = self.player_max_exp - self.player_current_exp
            battles = needed_exp // 2 + 1
        else:
            battles = 0
        container.add_item(discord.ui.TextDisplay(f"[**Battles for level up:** {battles:,}] [**Needed Stamina:** {battles * 5:,}]"))
        container.add_item(discord.ui.TextDisplay(f"**Raid Level Spawn Range:** {self.player_lvl * 18:,}/{self.player_lvl * 26:,}"))
        vip_timer = self.now + (self.premium_days_left * 86400)
        status = "<a:check:1380797984979030016>" if self.premium_days_left > 0 else "<a:cross:1380797973373521962>"
        container.add_item(discord.ui.TextDisplay(f"-# [VIP active: {status}] [VIP Days left: {self.premium_days_left} <t:{vip_timer}:d>]"))
        button_delete = discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger)
        button_delete.callback = self.delete_button
        container.add_item(discord.ui.ActionRow(button_delete))
        return container

    async def delete_button(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.player_id:
            return
        await interaction.message.delete()