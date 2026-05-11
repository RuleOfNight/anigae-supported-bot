import discord
import re
import asyncio
import json
import time
import runtime
from discord.ext import commands
from discord.ui import Button, Select, View
import Commands.user_commands_prefix_definition
from db_methods import cards, players, general
from Commands import definitions, help_def, user_commands_on_message, user_commands_prefix_definition, admin_commands
from Commands.user_commands_on_message import gold_emote
from misc import time_calculations


class ViewDeleteButtonPrefix(View):
    def __init__(self, author_id):
        super().__init__(timeout=180)
        self.delete_button = Button(label="", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.delete_button.callback = self.delete_callback
        self.add_item(self.delete_button)
        self.author_id = author_id

    async def delete_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return
        await interaction.message.delete()


class UserCommandsPrefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def compare(self, ctx, *, text: str = None):
        if text is None:
            await ctx.send("Please provide at least one filter.")
            return
        name_list = []
        series_list = []
        element_list = []
        talent_list = []
        state_codes = []
        match = re.search(r"-(?:name|n)\s*([\w\d\s,\(\)\.]+)\s*-?", text, re.IGNORECASE)
        if match:
            card_name = [n.strip().title() for n in match.group(1).split(",")]
            name_list.append(card_name)
        match = re.search(r"-(?:series|serie)\s*([\w\d\s,\(\)\.]+)\s*-?", text, re.IGNORECASE)
        if match:
            series_name = [s.strip().title() for s in match.group(1).split(",")]
            series_list.append(series_name)
        match = re.search(r"-(?:element|ele|e)\s*([\w\s,]+)\s*-?", text, re.IGNORECASE)
        if match:
            element = [e.strip().title() for e in match.group(1).split(",")]
            element_list.append(element)
        match = re.search(r"-(?:talent|skill|t)\s*([\w\s,]+)\s*-?", text, re.IGNORECASE)
        if match:
            talent = [t.strip().title() for t in match.group(1).split(",")]
            talent_list.append(talent)
        match = re.search(r"-(?:state|stat)\s*([\w\d,\s]+)\s*-?", text, re.IGNORECASE)
        if match:
            state_codes = [s.strip().upper() for s in match.group(1).split(",")]
        if len(name_list) + len(series_list) + len(element_list) + len(talent_list) == 0:
            await ctx.send("Please provide at least one filter.")
            return
        card_data_db = await cards.get_compare_data_from_cards(name_list, series_list, element_list, talent_list)
        if len(card_data_db) > 18:
            await ctx.send(f"Please provide only up to 18 results. Currently found: {len(card_data_db)}.")
            return
        compare_cards = []
        for idx, card in enumerate(card_data_db):
            state = {
                "card_rarity": "Base",
                "card_level": 1,
                "card_evo": 1,
                "card_asc": 0,
                "card_fam": 0,
                "card_clan": {"clan_hp": 0, "clan_atk": 0, "clan_def": 0, "clan_spd": 0}}
            if idx < len(state_codes):
                code = state_codes[idx].upper()
                m = re.search(r"R(UR|SR|UC|C|R)", code)
                if m:
                    rarity_code = m.group(1)
                    if rarity_code == "UR":
                        state["card_rarity"] = "Ultra Rare"
                    elif rarity_code == "SR":
                        state["card_rarity"] = "Super Rare"
                    elif rarity_code == "UC":
                        state["card_rarity"] = "Uncommon"
                    elif rarity_code == "C":
                        state["card_rarity"] = "Common"
                    elif rarity_code == "R":
                        state["card_rarity"] = "Rare"
                m = re.search(r"L(\d+)", code)
                if m:
                    state["card_level"] = min(int(m.group(1)), 60)
                m = re.search(r"E(\d+)", code)
                if m:
                    state["card_evo"] = min(int(m.group(1)), 3)
                m = re.search(r"A(\d+)", code)
                if m:
                    state["card_asc"] = min(int(m.group(1)), 5)
                m = re.search(r"F(\d+)", code)
                if m:
                    state["card_fam"] = min(int(m.group(1)), 3) * 2
                m = re.search(r"H(\d+)", code)
                if m:
                    state["card_fam"] = min(int(m.group(1)), 1) * 12
                m = re.search(r"CL(\d+)", code)
                if m:
                    val = min(int(m.group(1)), 15)
                    if val != 0:
                        val += 5
                    state["card_clan"] = {"clan_hp": val, "clan_atk": val, "clan_def": val, "clan_spd": val}
            compare_cards.append({"card_data": card, "card_state": state})
        compare_embed = await user_commands_prefix_definition.compare_embed_builder(ctx, compare_cards)
        view = user_commands_prefix_definition.CompareView(ctx, compare_embed, compare_cards)
        await ctx.send(embed=compare_embed, view=view)

    @commands.command(aliases=["sfl"])      # added as slash command
    async def setfloor(self, ctx, *args):
        if args:
            location_floor = " ".join(args)
            location_floor_pattern = r"(\d+)\s*,\s*(\d+)"
            location_floor_match = re.search(location_floor_pattern, location_floor)
            if location_floor_match:
                location = location_floor_match.group(1)
                floor = location_floor_match.group(2)
                await players.update_location_floor_players_by_player_id(ctx.author.id, ctx.author.name, location, floor)
                await ctx.send(f"Your location has been set to {location} and the floor set to {floor}.")
            else:
                await ctx.send("The format is not matching. If you need further instructions please use the help command")
            return
        channel = ctx.channel
        await ctx.send("```To set your max Location and Floor, send a message with the corresponding numbers seperated by a comma. as example:```\n"
                       "``71,20 [for Location 71, Floor 20]``")

        def check(message):
            return message.author == ctx.author and message.channel == channel
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            location_floor_pattern = r"(\d+),\s*(\d+)"
            location_floor_match = re.search(location_floor_pattern, msg.content)
            if location_floor_match:
                location = location_floor_match.group(1)
                floor = location_floor_match.group(2)
                await players.update_location_floor_players_by_player_id(msg.author.id, msg.author.name, location, floor)
                await ctx.send(f"Your location has been set to {location} and the floor set to {floor}.")
            else:
                await ctx.send("The format is not matching. If you need further instructions please use the help command")
        except asyncio.TimeoutError:
            await ctx.send(f"Command timeout. Please try again.")

    @commands.command(aliases=["soullist", "floorlist"])    # added as slash command
    async def shardlist(self, ctx):
        player_max_location, player_max_floor = await players.get_player_info_for_floors_from_players_by_discord_id(ctx.author.id, ctx.author.name)
        sorted_cards = await cards.get_all_card_location_floor_element_for_shards_display(player_max_location, player_max_floor)
        shards_embed = discord.Embed(title="Caeser's shard overview!", description="If you want to set your location and floor use [5setfloor].", color=0x71368A)
        for card_data in sorted_cards:
            element = card_data.get('card_element', '')
            card_name = card_data.get('card_name', '')
            location = card_data.get('location', '')
            floor = card_data.get('floor', '')
            value = card_data.get('value', '')
            element_emote = await definitions.element_converter_from_database(element)
            shards_embed.add_field(name=f"{element} {element_emote}", value=f"{card_name} **|** __Location__: {location} **|** __Floor__: {floor}", inline=False)
        shards_embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")
        author_avatar = ctx.author.avatar.url if ctx.author.avatar else None
        shards_embed.set_author(name=ctx.author.name, icon_url=author_avatar)
        view = ViewDeleteButtonPrefix(author_id=ctx.author.id)
        await ctx.channel.send(embed=shards_embed, view=view)

    @commands.command(aliases=["rh"])   # added as slash command
    async def raidhistory(self, ctx, *, args: str = None):
        VALID_DIFFICULTIES = {"easy": "easy", "e": "easy", "medium": "medium", "m": "medium", "hard": "hard", "h": "hard", "impossible": "impossible", "i": "impossible"}
        VALID_RARITIES = {"uncommon": "uncommon", "uc": "uncommon", "rare": "rare", "r": "rare", "super rare": "super rare", "sr": "super rare", "ultra rare": "ultra rare", "ur": "ultra rare"}
        user_id = ctx.author.id
        raid_history = await players.get_raid_history_from_db(user_id)
        if not raid_history:
            await ctx.send("Please use the .rd party command to update your history.")
            return
        filter_difficulty = None
        filter_boss_name = None
        filter_rarity = None
        filter_level = None
        level_operator = None
        if args:
            difficulty_match = re.search(r"-d (\w+)\s*", args, re.IGNORECASE)
            boss_match = re.search(r"-n ([\w\s]+)\s*", args, re.IGNORECASE)
            rarity_match = re.search(r"-r ([\w\s]+)\s*", args, re.IGNORECASE)
            level_match = re.search(r"-l([<>]?)\s*(\d+)\s*", args, re.IGNORECASE)
            if difficulty_match:
                difficulty_value = difficulty_match.group(1).lower()
                filter_difficulty = VALID_DIFFICULTIES.get(difficulty_value)
                if not filter_difficulty:
                    await ctx.send("No valid difficulty filter found. Please check the help command.")
                    return
            if boss_match:
                filter_boss_name = boss_match.group(1).lower()
            if rarity_match:
                rarity_value = rarity_match.group(1).lower()
                filter_rarity = VALID_RARITIES.get(rarity_value)
                if not filter_rarity:
                    await ctx.send("No valid rarity filter found. Please check the help command.")
                    return
            if level_match:
                level_operator = level_match.group(1)
                filter_level = int(level_match.group(2))
        if filter_difficulty:
            raid_history = [raid for raid in raid_history if
                            raid.get("raid_boss_difficulty", "").lower() == filter_difficulty]
        if filter_boss_name:
            raid_history = [raid for raid in raid_history if filter_boss_name in raid.get("raid_boss_name", "").lower()]
        if filter_rarity:
            raid_history = [raid for raid in raid_history if raid.get("raid_boss_rarity", "").lower() == filter_rarity]
        if filter_level is not None:
            if level_operator == "<":
                raid_history = [raid for raid in raid_history if raid.get("raid_boss_level", 0) < filter_level]
            elif level_operator == ">":
                raid_history = [raid for raid in raid_history if raid.get("raid_boss_level", 0) > filter_level]
            else:
                raid_history = [raid for raid in raid_history if raid.get("raid_boss_level", 0) == filter_level]
        if not raid_history:
            return
        raid_history.reverse()
        raid_history_embed = discord.Embed(title="Caeser's Raid History Tracking", description=f"Raid History of player: {ctx.author.name}", color=0x71368A)
        raid_history_embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")
        raid_history_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        for raid in raid_history:
            raid_timer = f"<t:{raid.get('raid_timer')}:R>" if raid.get("raid_timer") else "N/A"
            raid_boss_stats = f"__{raid['raid_boss_rarity']}__ | {raid['raid_boss_name']} | Level: {raid['raid_boss_level']} [{raid['raid_boss_difficulty']}]"
            raid_stats = (f"#{raid['player_number']} | Level: {raid['player_level']} | "
                          f"Power Level: {raid['player_power_level']}\nTotal Damage: {raid['player_max_dmg']}\n"
                          f"Damage Status: {raid['player_dmg_status']}\nTotal Attacks: {raid['player_total_atk']}\n"
                          f"Last Attack: {raid['player_last_atk']}m ago\nLogged: {raid_timer}")
            raid_history_embed.add_field(name=raid_boss_stats, value=raid_stats, inline=False)
        pages = []
        total_raids = len(raid_history)
        for i in range(0, total_raids, 5):
            current_raids = raid_history[i:i + 5]
            embed = discord.Embed(title="Caeser's Raid History Tracking", description=f"Raid History of player: {ctx.author.name}", color=0x71368A)
            embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            for raid in current_raids:
                raid_timer = f"<t:{raid.get('raid_timer')}:R>" if raid.get("raid_timer") else "N/A"
                raid_boss_stats = f"__{raid['raid_boss_rarity']}__ | {raid['raid_boss_name']} | Level: {raid['raid_boss_level']} [{raid['raid_boss_difficulty']}]"
                raid_stats = (f"#{raid['player_number']} | Level: {raid['player_level']} | "
                              f"Power Level: {raid['player_power_level']}\nTotal Damage: {raid['player_max_dmg']}\n"
                              f"Damage Status: {raid['player_dmg_status']}\nTotal Attacks: {raid['player_total_atk']}\n"
                              f"Last Attack: {raid['player_last_atk']}m ago\nLogged: {raid_timer}")
                embed.add_field(name=raid_boss_stats, value=raid_stats, inline=False)
            page_number = len(pages) + 1
            embed.set_footer(text=f"Page {page_number} | {len(current_raids)} / {total_raids} Raids")
            pages.append(embed)
        if len(pages) == 1:
            await ctx.send(embed=pages[0])
        else:
            paginator = user_commands_prefix_definition.PaginatorRaidHistory(ctx, pages, author_id=ctx.author.id)
            await paginator.send_initial_message()

    @commands.command(aliases=["mdex"])     # added as slash command
    async def marketdex(self, ctx, *, text: str = None):
        if text is None:
            await ctx.send("Please provide at least one filter.")
            return
        full_list = []
        name_list = []
        series_list = []
        element_list = []
        talent_list = []
        rarity_list = []
        price_status_list = None
        price_value_list = None
        match = re.search(r"-(?:page|p)\s*(\d+)", text)
        wanted_page = int(match.group(1)) - 1 if match else 0
        if "-all" in text:
            full_list.append("all")
        match = re.search(r"-(?:name|n)\s*([\w\d\s,\(\)\.]+)\s*-?", text, re.IGNORECASE)
        if match:
            card_name = [n.strip().title() for n in match.group(1).split(",")]
            name_list.append(card_name)
        match = re.search(r"-(?:series|s)\s*([\w\d\s,\(\)\.]+)\s*-?", text, re.IGNORECASE)
        if match:
            series_name = [s.strip().title() for s in match.group(1).split(",")]
            series_list.append(series_name)
        match = re.search(r"-(?:element|ele|e)\s*([\w\s,]+)\s*-?", text, re.IGNORECASE)
        if match:
            element = [e.strip().title() for e in match.group(1).split(",")]
            element_list.append(element)
        match = re.search(r"-(?:talent|skill|t)\s*([\w\s,]+)\s*-?", text, re.IGNORECASE)
        if match:
            talent = [t.strip().title() for t in match.group(1).split(",")]
            talent_list.append(talent)
        match = re.search(r"-(?:rarity|r)\s*(super rare|ultra rare|sr|ur)\s*-?", text, re.IGNORECASE)
        if match:
            rarity = match.group(1).strip().lower()
            if ("sr" or "super rare") in rarity:
                rarity_list.append("sr")
            elif ("ur" or "ultra rare") in rarity:
                rarity_list.append("ur")
        match = re.search(r"-price\s*(<|=|>)?\s*(\d+)\s*-?", text)
        if match:
            price_status = match.group(1)
            price_value = int(match.group(2))
            price_status_list = price_status
            price_value_list = price_value
        results = await cards.get_market_dex_data_from_cards(full_list, name_list, series_list, element_list, talent_list, rarity_list)
        if results:
            filtered_results = []
            for card in results:
                card_name = card["card_name"]
                card_price_sr = card["market_price_sr"]
                sr_time = card["market_price_sr_timestamp"]
                card_price_ur = card["market_price_ur"]
                ur_time = card["market_price_ur_timestamp"]
                card_element = card["card_element"]
                card_talent = card["card_talent"]
                card_element = await definitions.element_converter_from_database(card_element)
                card_talent = await definitions.skill_converter_from_database(card_talent)
                market_price_sr_timer = f"<t:{sr_time}:R>" if sr_time and sr_time != "N/A" else "N/A"
                market_price_ur_timer = f"<t:{ur_time}:R>" if ur_time and ur_time != "N/A" else "N/A"
                if "sr" in rarity_list:
                    if price_status_list == "=" and card_price_sr != "N/A" and price_value_list == int(card_price_sr):
                        filtered_results.append((card_name, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent))
                    elif price_status_list == "<" and card_price_sr != "N/A" and price_value_list > int(card_price_sr):
                        filtered_results.append((card_name, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent))
                    elif price_status_list == ">" and card_price_sr != "N/A" and price_value_list < int(card_price_sr):
                        filtered_results.append((card_name, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent))
                    elif price_status_list is None:
                        filtered_results.append((card_name, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent))
                elif "ur" in rarity_list:
                    if price_status_list == "=" and card_price_ur != "N/A" and price_value_list == int(card_price_ur):
                        filtered_results.append((card_name, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent))
                    elif price_status_list == "<" and card_price_ur != "N/A" and price_value_list > int(card_price_ur):
                        filtered_results.append((card_name, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent))
                    elif price_status_list == ">" and card_price_ur != "N/A" and price_value_list < int(card_price_ur):
                        filtered_results.append((card_name, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent))
                    elif price_status_list is None:
                        filtered_results.append((card_name, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent))
                else:
                    if price_status_list == "=" and card_price_sr != "N/A" and price_value_list == int(card_price_sr):
                        filtered_results.append((card_name, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent))
                    elif price_status_list == "<" and card_price_sr != "N/A" and price_value_list > int(card_price_sr):
                        filtered_results.append((card_name, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent))
                    elif price_status_list == ">" and card_price_sr != "N/A" and price_value_list < int(card_price_sr):
                        filtered_results.append((card_name, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent))
                    elif price_status_list is None:
                        filtered_results.append((card_name, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent))
            if filtered_results:
                passcode = "All"
                if rarity_list:
                    passcode = "super rare" if "sr" in rarity_list else "ultra rare"
                view = user_commands_prefix_definition.PaginatorMarketDex(ctx.author, filtered_results, passcode, wanted_page=wanted_page, items_per_page=10)
                await ctx.send(embed=view.get_page_embed(), view=view)
            else:
                await ctx.send("No matching cards found after filtering.")
        else:
            await ctx.send("No matching cards found.")

    @commands.command(aliases=["dw"])
    async def dailywatch(self, ctx):
        await user_commands_prefix_definition.send_daily_watch_embed(ctx)

    @commands.command(aliases=["sl"])
    async def setlocation(self, ctx):
        locations_data = await runtime.retrieve_data("locations")
        locations_list = list(locations_data.items())
        page_size = 25
        max_pages = (len(locations_list) - 1) // page_size + 1
        selected_ids = await players.get_player_selected_locations_by_player_id_in_players(ctx.author.id)
        view = user_commands_prefix_definition.LocationPaginationView(locations_list, page_size, 0, max_pages, selected_ids)
        await ctx.send("Selecting any option will enable/disable the ping. The pings are exclusive on the official Discord server.", view=view)
