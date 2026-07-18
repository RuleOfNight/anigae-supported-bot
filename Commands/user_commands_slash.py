import asyncio
import json
import discord
import re
import os
import runtime
from discord import app_commands
from discord.ext import commands
from db_methods import breach_comps, cards, guilds, players, channel_donations
from Commands.user_commands_on_message import MONTHLY_DONATION_CHANNEL_ID
from Commands import breach_comp_views, definitions, user_commands_prefix_definition, user_commands_slash_definition_v2, help_def_v2, user_commands_slash_definiton_embed
from misc import time_calculations
from Commands.user_commands_prefix import ViewDeleteButtonPrefix
from Commands.user_commands_on_message import gold_emote, rare_emote, super_rare_1, super_rare_2, ultra_rare_1, ultra_rare_2


# noinspection PyUnresolvedReferences
class UserCommandsSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    guild = app_commands.Group(name="guild", description="Guild commands")
    donation = app_commands.Group(name="donation", description="Donation commands", parent=guild)
    guild_member = app_commands.Group(name="member", description="Guild member commands", parent=guild)
    archive = app_commands.Group(name="archive", description="Archive related commands", parent=guild)
    threshold = app_commands.Group(name="threshold", description="2nd donation threshold related commands", parent=guild)

    @app_commands.command(name="help", description="Shows the help command.")
    async def help(self, interaction: discord.Interaction):
        view = await help_def_v2.help_v2(interaction, True)
        await interaction.response.send_message(view=view)

    @app_commands.command(name="compare", description="compare cards depending on the filter (name, serie, element, talent).")
    @app_commands.describe(name="card names separated by comma", series="series names separated by comma", element="element names separated by comma", talent="talent names separated by comma", stat="stat codes (a.e. RURL60E3A1) per card, separated by comma to match the name order")
    async def compare(self, interaction: discord.Interaction, name: str = None, series: str = None, element: str = None, talent: str = None, stat: str = None):
        name_list = [[n.strip().title() for n in name.split(",")]] if name else []
        series_list = [[s.strip().title() for s in series.split(",")]] if series else []
        element_list = [[e.strip().title() for e in element.split(",")]] if element else []
        talent_list = [[t.strip().title() for t in talent.split(",")]] if talent else []
        state_codes = [s.strip().upper() for s in stat.split(",")] if stat else []
        if len(name_list) + len(series_list) + len(element_list) + len(talent_list) == 0:
            await interaction.response.send_message("Please provide at least one filter.", ephemeral=True)
            return
        card_data_db = await cards.get_compare_data_from_cards(name_list, series_list, element_list, talent_list)
        if len(card_data_db) > 18:
            await interaction.response.send_message(f"Please provide only up to 18 results. Currently found: {len(card_data_db)}.", ephemeral=True)
            return
        compare_cards = []
        for idx, card in enumerate(card_data_db):
            state_dict = {"card_rarity": "Base", "card_level": 1, "card_evo": 1, "card_asc": 0, "card_fam": 0,
                          "card_clan": {"clan_hp": 0, "clan_atk": 0, "clan_def": 0, "clan_spd": 0}}
            if idx < len(state_codes):
                code = state_codes[idx]
                m = re.search(r"R(UR|SR|UC|C|R)", code)
                if m:
                    rarity_code = m.group(1)
                    if rarity_code == "UR":
                        state_dict["card_rarity"] = "Ultra Rare"
                    elif rarity_code == "SR":
                        state_dict["card_rarity"] = "Super Rare"
                    elif rarity_code == "UC":
                        state_dict["card_rarity"] = "Uncommon"
                    elif rarity_code == "C":
                        state_dict["card_rarity"] = "Common"
                    elif rarity_code == "R":
                        state_dict["card_rarity"] = "Rare"
                m = re.search(r"L(\d+)", code)
                if m:
                    state_dict["card_level"] = min(int(m.group(1)), 60)
                m = re.search(r"E(\d+)", code)
                if m:
                    state_dict["card_evo"] = min(int(m.group(1)), 3)
                m = re.search(r"A(\d+)", code)
                if m:
                    state_dict["card_asc"] = min(int(m.group(1)), 5)
                m = re.search(r"F(\d+)", code)
                if m:
                    state_dict["card_fam"] = min(int(m.group(1)), 3) * 2
                m = re.search(r"H(\d+)", code)
                if m:
                    state_dict["card_fam"] = min(int(m.group(1)), 1) * 12
                m = re.search(r"CL(\d+)", code)
                if m:
                    val = min(int(m.group(1)), 15)
                    if val != 0:
                        val += 5
                    state_dict["card_clan"] = {"clan_hp": val, "clan_atk": val, "clan_def": val, "clan_spd": val}
            compare_cards.append({"card_data": card, "card_state": state_dict})
        compare_embed = await user_commands_prefix_definition.compare_embed_builder(interaction, compare_cards)
        view = user_commands_prefix_definition.CompareView(interaction, compare_embed, compare_cards)
        await interaction.response.send_message(embed=compare_embed, view=view)

    @app_commands.command(name="set_floor", description="Set your location and floor.")
    @app_commands.describe(location="The location number (e.g., 71)", floor="The floor number (e.g., 20)")
    async def setfloor(self, interaction: discord.Interaction, location: int, floor: int):
        await players.update_location_floor_players_by_player_id(interaction.user.id, interaction.user.name, location, floor)
        await interaction.response.send_message(f"Your location has been set to {location} and the floor set to {floor}.")

    @app_commands.command(name="shard_list", description="Shows the best location to farm shards.")
    async def shardlist(self, interaction: discord.Interaction):
        await self.send_shardlist(interaction)

    @app_commands.command(name="soul_list", description="Shows the best location to farm shards.")
    async def soullist(self, interaction: discord.Interaction):
        await self.send_shardlist(interaction)

    @app_commands.command(name="floor_list", description="Shows the best location to farm shards.")
    async def floorlist(self, interaction: discord.Interaction):
        await self.send_shardlist(interaction)

    async def send_shardlist(self, interaction: discord.Interaction):
        await interaction.response.defer()
        player_max_location, player_max_floor = await players.get_player_info_for_floors_from_players_by_discord_id(interaction.user.id, interaction.user.name)
        sorted_cards = await cards.get_all_card_location_floor_element_for_shards_display(player_max_location, player_max_floor)
        shards_embed = discord.Embed(title="Caeser's shard overview!", description="If you want to set your location and floor use [5setfloor].", color=0x71368A)
        for card_data in sorted_cards:
            element = card_data.get('card_element', '')
            card_name = card_data.get('card_name', '')
            location = card_data.get('location', '')
            floor = card_data.get('floor', '')
            element_emote = await definitions.element_converter_from_database(element)
            shards_embed.add_field(name=f"{element} {element_emote}", value=f"{card_name} **|** __Location__: {location} **|** __Floor__: {floor}", inline=False)
        shards_embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")
        author_avatar = interaction.user.avatar.url if interaction.user.avatar else None
        shards_embed.set_author(name=interaction.user.name, icon_url=author_avatar)
        view = ViewDeleteButtonPrefix(author_id=interaction.user.id)
        await interaction.followup.send(embed=shards_embed, view=view)


    @app_commands.command(name="raid_history", description="Shows your raid history with optional filters.")
    @app_commands.describe(
        difficulty="Filter by difficulty [easy / e] [medium / m] [hard / h] [impossible / i]",
        boss_name="Filter by boss name",
        rarity="Filter by rarity [uncommon / uc] [rare / r] [super rare / sr] [ultra rare / ur]",
        level_operator="Operator for level filter: '=', '<', or '>'",
        level="Level number to filter")
    async def raidhistory(self, interaction: discord.Interaction, difficulty: str = None, boss_name: str = None, rarity: str = None, level_operator: str = None, level: int = None):
        VALID_DIFFICULTIES = {"easy": "easy", "e": "easy", "medium": "medium", "m": "medium", "hard": "hard",
                              "h": "hard", "impossible": "impossible", "i": "impossible"}
        VALID_RARITIES = {"uncommon": "uncommon", "uc": "uncommon", "rare": "rare", "r": "rare",
                          "super rare": "super rare", "sr": "super rare", "ultra rare": "ultra rare",
                          "ur": "ultra rare"}
        user_id = interaction.user.id
        raid_history = await players.get_raid_history_from_db(user_id)
        if not raid_history:
            await interaction.response.send_message("Please use the /rd party command to update your history.")
            return
        filter_difficulty = VALID_DIFFICULTIES.get(difficulty.lower()) if difficulty else None
        filter_rarity = VALID_RARITIES.get(rarity.lower()) if rarity else None
        if difficulty and not filter_difficulty:
            await interaction.response.send_message("No valid difficulty filter found. Please check your input.", ephemeral=True)
            return
        if rarity and not filter_rarity:
            await interaction.response.send_message("No valid rarity filter found. Please check your input.", ephemeral=True)
            return
        if filter_difficulty:
            raid_history = [raid for raid in raid_history if raid.get("raid_boss_difficulty", "").lower() == filter_difficulty]
        if boss_name:
            raid_history = [raid for raid in raid_history if boss_name.lower() in raid.get("raid_boss_name", "").lower()]
        if filter_rarity:
            raid_history = [raid for raid in raid_history if raid.get("raid_boss_rarity", "").lower() == filter_rarity]
        if level is not None:
            if level_operator == "<":
                raid_history = [raid for raid in raid_history if raid.get("raid_boss_level", 0) < level]
            elif level_operator == ">":
                raid_history = [raid for raid in raid_history if raid.get("raid_boss_level", 0) > level]
            else:
                raid_history = [raid for raid in raid_history if raid.get("raid_boss_level", 0) == level]
        if not raid_history:
            await interaction.response.send_message("No raids found with the given filters.", ephemeral=True)
            return
        raid_history.reverse()
        pages = []
        total_raids = len(raid_history)
        for i in range(0, total_raids, 5):
            current_raids = raid_history[i:i + 5]
            embed = discord.Embed(title="Caeser's Raid History Tracking", description=f"Raid History of player: {interaction.user.name}", color=0x71368A)
            embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
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
            await interaction.response.send_message(embed=pages[0])
        else:
            paginator = user_commands_prefix_definition.PaginatorRaidHistory(interaction, pages, author_id=interaction.user.id)
            await paginator.send_initial_message()

    @app_commands.command(name="market_dex", description="Custom market dex for anigame.")
    @app_commands.describe(name="Filter by card names (comma separated)", series="Filter by series names (comma separated)",
                           element="Filter by elements (comma separated)", talent="Filter by talents/skills (comma separated)",
                           rarity="Filter by card rarity (sr or ur)", price_operator="Price operator: <, =, >",
                           price_value="Price value to compare against", page="Page number")
    async def marketdex(self, interaction: discord.Interaction, name: str = None, series: str = None,
                        element: str = None, talent: str = None, rarity: str = None, price_operator: str = None,
                        price_value: int = None, page: int = 1):
        await interaction.response.defer()
        full_list = []
        name_list = []
        series_list = []
        element_list = []
        talent_list = []
        rarity_list = []
        price_status_list = None
        price_value_list = None
        wanted_page = max(page - 1, 0)
        # If no filters provided, assume "-all"
        if not any([name, series, element, talent, rarity, price_operator, price_value]):
            full_list.append("all")
        else:
            if name:
                card_name = [n.strip().title() for n in name.split(",")]
                name_list.append(card_name)
            if series:
                series_name = [s.strip().title() for s in series.split(",")]
                series_list.append(series_name)
            if element:
                element_name = [e.strip().title() for e in element.split(",")]
                element_list.append(element_name)
            if talent:
                talent_name = [t.strip().title() for t in talent.split(",")]
                talent_list.append(talent_name)
            if rarity:
                rarity = rarity.lower()
                if "sr" in rarity or "super rare" in rarity:
                    rarity_list.append("sr")
                elif "ur" in rarity or "ultra rare" in rarity:
                    rarity_list.append("ur")
            if price_operator and price_value is not None:
                price_status_list = price_operator
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
                view = user_commands_prefix_definition.PaginatorMarketDex(interaction.user, filtered_results, passcode, wanted_page=wanted_page, items_per_page=10)
                await interaction.followup.send(embed=view.get_page_embed(), view=view)
            else:
                await interaction.followup.send("No matching cards found after filtering.")
        else:
            await interaction.followup.send("No matching cards found.")

    @app_commands.command(name="raid_lobbies", description="Get raid lobby filter depending on the selected gold value.")
    @app_commands.describe(price="Gold value, e.g., 1000 or 1k", exclude_events="Comma-separated list of event types to exclude: cl, vote, event", sell="Use .inv format instead of .rd lobbies")
    async def raidlobbies(self, interaction: discord.Interaction, price: str, exclude_events: str = None, sell: bool = False):
        await interaction.response.defer()
        alias_map = {"cl": "clan_shop", "clan": "clan_shop", "cl shop": "clan_shop", "clan shop": "clan_shop",
                     "vote": "monthly_vote", "monthly": "monthly_vote", "monthly vote": "monthly_vote",
                     "calendar": "monthly_vote", "event": "event"}
        user_price = re.match(r"^\s*(\d+(?:\.\d+)?)(k?)\s*$", price.lower())
        if not user_price:
            await interaction.followup.send("Please enter a valid gold price like `1000` or `1k`.")
            return
        number_str, k_suffix = user_price.groups()
        try:
            user_gold_price = float(number_str)
            if k_suffix == "k":
                user_gold_price *= 1000
            user_gold_price = int(user_gold_price)
        except ValueError:
            await interaction.followup.send("Please enter a valid number.")
            return
        parsed_excludes = []
        if exclude_events:
            terms = [term.strip().lower() for term in re.split(r"[,_ ]+", exclude_events)]
            for term in terms:
                if term in alias_map:
                    parsed_excludes.append(alias_map[term])
        card_list = await cards.raid_search_list_from_db(user_gold_price, parsed_excludes)
        player_setting = await players.get_settings_from_player_by_discord_id(interaction.user.id)
        if player_setting["raid_lobby_status"] == "long":
            max_length = 4000
        else:
            max_length = 2000
        if len(card_list) >= max_length:
            await interaction.followup.send("Too many characters. Please use a different gold number.", ephemeral=True)
            return
        if sell:
            text = f".inv -r sr -evo 1 -n {card_list}"
        else:
            text = f".rd lobbies -r r,sr,ur -n {card_list}"
        await user_commands_slash_definition_v2.raid_lobby_search_builder(interaction, text)

    @app_commands.command(name="set_team_warning", description="Option to toggle the team check!")
    async def setteamwarning(self, interaction: discord.Interaction):
        team_check_embed = discord.Embed(title=None, description="Option to toggle the team check!\nTo update your status simply click one of the buttons below.", color=0x71368A)
        team_check_embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")
        author_avatar = interaction.user.avatar.url if interaction.user.avatar else None
        team_check_embed.set_author(name=interaction.user.name, icon_url=author_avatar)
        view = user_commands_prefix_definition.ButtonsForStatusTeamWarning(author=interaction.user, is_slash=True)
        await interaction.response.send_message(embed=team_check_embed, view=view)

    @app_commands.command(name="daily_watch", description="Shows the current daily shop cards and their market value")
    async def daily_watch(self, interaction: discord.Interaction):
        await user_commands_prefix_definition.send_daily_watch_embed(interaction)

    @app_commands.command(name="set_location", description="Enable / Disable the ping for those locations.")
    async def setlocation(self, interaction: discord.Interaction):
        locations_data = await runtime.retrieve_data("locations")
        locations_list = list(locations_data.items())
        page_size = 25
        max_pages = (len(locations_list) - 1) // page_size + 1
        selected_ids = await players.get_player_selected_locations_by_player_id_in_players(interaction.user.id)
        view = user_commands_prefix_definition.LocationPaginationView(locations_list, page_size, 0, max_pages, selected_ids)
        await interaction.response.send_message("Selecting any option will enable/disable the ping. The pings are exclusive on the official Discord server.", view=view)

    async def boss_autocomplete(self, interaction: discord.Interaction, current: str):
        bosses = await runtime.retrieve_data("raid comps")
        current = current.lower()
        if current == "event":
            return [
                app_commands.Choice(name=boss, value=boss)
                for boss, data in bosses.items()
                if data.get("raid_type", "normal").lower() == "event"
            ][:50]
        return [
            app_commands.Choice(name=boss, value=boss)
            for boss in bosses.keys()
            if current in boss.lower()
        ][:5]

    @app_commands.command(name="raid_guide", description="Shows possible raid teams for the selected boss.")
    @app_commands.describe(boss="name of the boss", rarity="filter for rarity (Rare, SR, UR)")
    @app_commands.autocomplete(boss=boss_autocomplete)
    async def raidguide(self, interaction: discord.Interaction, boss: str, rarity: str = None):
        boss_query = boss
        rarity_filter = rarity.lower() if rarity else None
        rare_string = ""
        sr_string = f"{super_rare_1}{super_rare_2} __**Super Rare**__\n"
        ur_string = f"{ultra_rare_1}{ultra_rare_2} __**Ultra Rare**__\n"
        boss_found = None
        bosses = await runtime.retrieve_data("raid comps")
        for b in bosses.keys():
            if boss_query.lower() in b.lower():
                boss_found = b
                if "R" in bosses[b]:
                    for level, entry in bosses[b]["R"].items():
                        rare_string += f"{rare_emote} **- Rare {level} :**\n"
                        for team in entry.get("teams", []):
                            team = re.sub(r"\{([^}]*)\}", r"\n -# (\1)", team).strip()
                            rare_string += f"- {team}\n"
                if "SR" in bosses[b]:
                    for level, entry in bosses[b]["SR"].items():
                        for team in entry.get("teams", []):
                            team = re.sub(r"\{([^}]*)\}", r"\n -# (\1)", team).strip()
                            sr_string += f"- {team}\n"
                if "UR" in bosses[b]:
                    for level, entry in bosses[b]["UR"].items():
                        for team in entry.get("teams", []):
                            team = re.sub(r"\{([^}]*)\}", r"\n -# (\1)", team).strip()
                            ur_string += f"- {team}\n"
                break
        if not boss_found:
            await interaction.response.send_message(f"No boss found with this name: **{boss_query}**")
            return
        card_data = await cards.get_card_data_by_name(boss_found)
        card_element = await definitions.element_converter_from_database(card_data[0]["card_element"])
        card_talent = await definitions.skill_converter_from_database(card_data[0]["card_talent"])
        await user_commands_slash_definition_v2.raid_guide_builder(boss_found, rare_string, sr_string, ur_string,
                                                        rarity_filter, card_element, card_talent, interaction)

    @app_commands.command(name="rulesets", description="Shows the most common used ruleset codes.")
    async def rulesets(self, interaction: discord.Interaction):
        await user_commands_slash_definition_v2.rulesets_builder(interaction)

    @app_commands.command(name="update", description="Update your unique username and discord id in the database.")
    async def update(self, interaction: discord.Interaction):
        discord_id = interaction.user.id
        discord_name = interaction.user.name
        await players.update_player(discord_id, discord_name)
        await user_commands_slash_definition_v2.update_builder(interaction)

    @app_commands.command(name="settings", description="toggle a variety of options on/off")
    async def settings(self, interaction: discord.Interaction):
        await user_commands_slash_definition_v2.settings_builder(interaction)

    @guild.command(name="create", description="Create a guild within this server.")
    @app_commands.describe(name="The name of the guild you want to create.")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_guild(self, interaction: discord.Interaction, name: str):
        guild_id = interaction.guild.id
        guild_name = name
        guild_check, guild_name_db = await guilds.get_guild_id_from_guilds(guild_id)
        if guild_check == "no guild found":
            await guilds.create_guild_in_collection(guild_id, guild_name)
            await interaction.response.send_message(f"Created the guild: ``{guild_name}`` with the server id ``{guild_id}``")
        else:
            await interaction.response.send_message(f"There already is a guild for this server. Guild name: ``{guild_name_db}``", ephemeral=True)

    @guild.command(name="delete", description="Delete your guild with a confirmation.")
    @app_commands.checks.has_permissions(administrator=True)
    async def delete_guild(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        view = user_commands_slash_definition_v2.DeleteGuildLayoutView(guild_id=guild_id, author=interaction.user)
        await interaction.response.send_message(view=view)

    @guild_member.command(name="add", description="Add a member to the guild")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_member(self, interaction: discord.Interaction, member: discord.User):
        guild_id = interaction.guild.id
        result = await guilds.add_guild_member_by_guild_id_and_discord_name_from_guilds(guild_id, member)
        if result == "added":
            await interaction.response.send_message(f"The guild member ``{member.name}`` was added to the guild.")
        elif result == "exists":
            await interaction.response.send_message(f"An error occurred while adding ``{member.name}``. Please check if the player is already in the guild.")
        else:
            await interaction.response.send_message("An unknown error occurred.")

    @guild_member.command(name="remove", description="Remove a member from the guild")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_member(self, interaction: discord.Interaction, member: discord.User):
        guild_id = interaction.guild.id
        view = user_commands_slash_definition_v2.RemoveGuildMemberLayoutView(guild_id=guild_id,guild_member=member, author=interaction.user)
        await interaction.response.send_message(view=view)

    @guild_member.command(name="update", description="Update the selected members name or discord id.")
    @app_commands.checks.has_permissions(administrator=True)
    async def update_member(self, interaction: discord.Interaction, member: discord.User):
        guild_id = interaction.guild.id
        guild_member_name = member.name
        guild_member_id = member.id
        result = await guilds.update_guild_member_in_guilds(guild_id, guild_member_name, guild_member_id)
        if result == "updated id by name":
            await interaction.response.send_message(f"Player: ``{guild_member_name}`` updated the ID.")
        elif result == "updated name by id":
            await interaction.response.send_message(f"Player: ``{guild_member_name}`` updated the Name.")
        else:
            await interaction.response.send_message("No changes were made. Either the player is not in the guild or is already up to date.")

    @guild.command(name="debt", description="Select if debt is available for the guild.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(debt=[app_commands.Choice(name="Yes", value="True"),
                                app_commands.Choice(name="No", value="False")])
    async def debt(self, interaction: discord.Interaction, debt: app_commands.Choice[str]):
        guild_id = interaction.guild.id
        if debt.value == "True":
            value = True
        else:
            value = False
        result = await guilds.set_guild_debt(guild_id, value)
        if result == "no guild found":
            await interaction.response.send_message("Please create a guild first before setting up the debt.")
        elif result == "edited":
            await interaction.response.send_message(f"The debt was set to: ``{debt.name}``")
        elif result == "no changes":
            await interaction.response.send_message("No changes were made.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to change the debt status.")

    @guild.command(name="donations", description="Shows your guild donations.")
    @app_commands.describe(old_donations="View the last rotation of donations.")
    @app_commands.choices(old_donations=[app_commands.Choice(name="0", value=0), app_commands.Choice(name="1", value=1),
                                         app_commands.Choice(name="2", value=2), app_commands.Choice(name="3", value=3),
                                         app_commands.Choice(name="4", value=4), app_commands.Choice(name="5", value=5),
                                         app_commands.Choice(name="6", value=6), app_commands.Choice(name="7", value=7),
                                         app_commands.Choice(name="8", value=8), app_commands.Choice(name="9", value=9),
                                         app_commands.Choice(name="10", value=10), app_commands.Choice(name="11", value=11),
                                         app_commands.Choice(name="12", value=12)])
    async def donations(self, interaction: discord.Interaction, old_donations: app_commands.Choice[int] = None):
        guild_id = interaction.guild.id
        guild_result, start_unix, end_unix = await guilds.get_guild_data(guild_id, old_donations)
        if guild_result == "no guild found":
            await interaction.followup.send("Please create a guild first.")
            return
        view = user_commands_slash_definition_v2.GuildMemberOverviewLayoutView(interaction.user.id, guild_result, start_unix, end_unix, old_donations)
        await interaction.response.send_message(view=view)

    @guild.command(name="noidcheck", description="Gets a list of all members with no ID in the database.")
    @app_commands.checks.has_permissions(administrator=True)
    async def noidcheck(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        guild_members = await guilds.get_guild_member_names_without_discord_id(guild_id)
        view = user_commands_slash_definition_v2.NoIDCheckLayoutView(guild_members)
        await interaction.response.send_message(view=view)

    @archive.command(name="add", description="Archive a member in the guild")
    @app_commands.checks.has_permissions(administrator=True)
    async def archive_add(self, interaction: discord.Interaction, member: discord.User):
        guild_id = interaction.guild.id
        result = await guilds.add_member_to_archived_list(guild_id, member)
        if result == "guild not found or member not in guild":
            await interaction.response.send_message("There was no guild found, the member is not within the guild or the member has no ID within the database.")
        elif result == "already in archive":
            await interaction.response.send_message(f"The guild member ``{member.name}`` with ID ``{member.id}`` is already archived.")
        elif result == "added to archive":
            await interaction.response.send_message(f"The guild member ``{member.name}`` with ID ``{member.id}`` has been archived.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to add ``{member.name}`` with ID ``{member.id}`` to the archive.")

    @archive.command(name="remove", description="Activate a member from the archive")
    @app_commands.checks.has_permissions(administrator=True)
    async def archive_remove(self, interaction: discord.Interaction, member: discord.User):
        guild_id = interaction.guild.id
        result = await guilds.remove_member_from_archived_list(guild_id, member)
        if result == "no guild found":
            await interaction.response.send_message("Please create a guild first before trying to activate a member.")
        elif result == "not in archive":
            await interaction.response.send_message(f"The guild member ``{member.name}`` with ID ``{member.id}`` is not in the archive.")
        elif result == "removed":
            await interaction.response.send_message(f"The guild member ``{member.name}`` with ID ``{member.id}`` has been removed from the archive.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to remove ``{member.name}`` with ID ``{member.id}`` from the archive.")

    @archive.command(name="view", description="View archived members in the guild")
    @app_commands.checks.has_permissions(administrator=True)
    async def archive_view(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        archived_members = await guilds.get_archived_members(guild_id)
        if archived_members == "no guild found":
            await interaction.response.send_message("Please create a guild first.")
            return
        if len(archived_members) == 0:
            archived_members = "No Members in archive found."
        else:
            archived_members = " ; ".join(archived_members)
        await interaction.response.send_message(f"Currently these members are in the archive: **{archived_members}**")

    @donation.command(name="limit", description="Set the weekly/monthly donation threshold limit for the guild")
    @app_commands.checks.has_permissions(administrator=True)
    async def donation_limit(self, interaction: discord.Interaction, donation_amount: int):
        guild_id = interaction.guild.id
        result = await guilds.update_guild_threshold_by_guild_id_in_guilds(guild_id, donation_amount)
        if result == "no guild found":
            await interaction.response.send_message("Please create a guild first before setting up a threshold limit.")
        elif result == "edited":
            await interaction.response.send_message(f"Weekly threshold limit was set to: **{donation_amount:,}** gold {gold_emote}", ephemeral=False)
        elif result == "no changes":
            await interaction.response.send_message("No changes were made.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to set the threshold limit.")

    @donation.command(name="reset", description="Select the reset interval for the guild.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(interval=[app_commands.Choice(name="Monthly", value="monthly"),
                                    app_commands.Choice(name="Weekly", value="weekly")])
    async def donation_reset(self, interaction: discord.Interaction, interval: app_commands.Choice[str]):
        guild_id = interaction.guild.id
        result = await guilds.set_guild_reset(guild_id, interval.value)
        if result == "no guild found":
            await interaction.response.send_message("Please create a guild first before setting up the interval.")
        elif result == "edited":
            await interaction.response.send_message(f"The interval was set to: ``{interval.value}``")
        elif result == "no changes":
            await interaction.response.send_message("No changes were made.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to change the reset interval.")

    @donation.command(name="add", description="Manually add a donation amount for a guild member.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(member="Name of the guild member", donation_amount="Amount donated (use 'k' for thousand, e.g., 5k)", dono_inc="Standard if no choice = Yes.")
    @app_commands.choices(dono_inc=[app_commands.Choice(name="Yes", value="True"),
                                    app_commands.Choice(name="No", value="False")])
    async def donation_add(self, interaction: discord.Interaction, member: discord.User, donation_amount: str, dono_inc: app_commands.Choice[str] = None):
        guild_id = interaction.guild.id
        if dono_inc is None or dono_inc.value == "True":
            dono_inc = True
        else:
            dono_inc = False
        if "k" in donation_amount.lower():
            donation_amount = donation_amount.lower().replace("k", "")
            try:
                donation_amount = int(donation_amount) * 1000
            except ValueError:
                await interaction.response.send_message(f"Please check your input again. Error with: ``{donation_amount}``")
                return
        else:
            try:
                donation_amount = int(donation_amount)
            except ValueError:
                await interaction.response.send_message(f"Please check your input again. Error with: ``{donation_amount}``")
                return
        result = await guilds.update_donation_amount_by_player_name_manually(member, donation_amount, "manually", guild_id, dono_inc)
        if result == "no guild found":
            await interaction.response.send_message(f"No Guild was found or the user ``{member.name}`` is archived.")
        elif result == "added":
            await interaction.response.send_message(f"Added Donation for **{member.name}** with **{donation_amount:,}** gold {gold_emote}")
        elif result == "no changes":
            await interaction.response.send_message("No changes were made.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to add the donation.")

    @donation.command(name="remove", description="Remove a donation from a guild by donation ID (Admin only).")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(donation_id="The ID of the donation you want to remove")
    async def donation_remove(self, interaction: discord.Interaction, donation_id: str):
        guild_id = interaction.guild.id
        result = await guilds.remove_player_donation_by_donation_id_in_one_guild(donation_id, guild_id)
        if result == "no guild found":
            await interaction.response.send_message(f"No Guild was found or the donation ID is incorrect: ``{donation_id}``.")
        elif result == "donation removed successfully":
            await interaction.response.send_message("Donation successfully removed.")
        elif result == "no changes":
            await interaction.response.send_message(f"No donation found with ID ``{donation_id}``.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to remove the donation.")

    @donation.command(name="edit", description="Edit a donation by ID and set a new amount.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(donation_id="The ID of the donation you want to edit", new_amount="The new amount of the donation (use 'k' for thousands, e.g., '5k')")
    async def donation_edit(self, interaction: discord.Interaction, donation_id: str, new_amount: str):
        guild_id = interaction.guild.id
        if "k" in new_amount.lower():
            new_amount = new_amount.lower().replace("k", "")
            try:
                new_amount = int(new_amount) * 1000
            except ValueError:
                await interaction.response.send_message("Invalid donation amount format.")
                return
        else:
            try:
                new_amount = int(new_amount)
            except ValueError:
                await interaction.response.send_message("Invalid donation amount format.")
                return
        result = await guilds.update_donation_by_donation_id_manually(donation_id, new_amount, guild_id)
        if result == "no guild found":
            await interaction.response.send_message(f"No guild was found or invalid donation ID ``{donation_id}``.")
        elif result == "edited":
            await interaction.response.send_message(f"Successfully updated ``{donation_id}`` to new gold amount ``{new_amount:,}``.")
        elif result == "no changes":
            await interaction.response.send_message(f"No changes to donation ID: ``{donation_id}``.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to remove the donation.")

    @donation.command(name="cleanse", description="Removes / cleanses a debt of a specific guild member")
    @app_commands.checks.has_permissions(administrator=True)
    async def donation_cleanse(self, interaction: discord.Interaction, member: discord.User):
        guild_id = interaction.guild.id
        result = await guilds.cleanse_donations_for_user(guild_id, member)
        if result == "no guild found":
            await interaction.response.send_message("Please create a guild first or check if the user is within the guild.")
        elif result == "edited":
            await interaction.response.send_message(f"The debt of the user ``{member.name}`` has been set to 0.")
        elif result == "no changes":
            await interaction.response.send_message("No changes were made.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to change the debt status.")

    @donation.command(name="profile", description="Show all donations for a specific user in the guild.")
    @app_commands.describe(member="Guild member name")
    async def donation_profile(self, interaction: discord.Interaction, member: discord.User):
        guild_id = interaction.guild.id
        donations = await guilds.get_recent_donations_with_id_by_member_and_guild(guild_id, member)
        if donations == "no guild found":
            await interaction.response.send_message("Please create a guild first.", ephemeral=True)
            return
        elif donations == "no member found":
            await interaction.response.send_message(f"Please check the name with correct casing: **{member.name}**", ephemeral=True)
            return
        elif donations == "no donations found":
            await interaction.response.send_message(f"No Donations found for member: **{member.name}**", ephemeral=True)
            return
        donations.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        view = user_commands_slash_definition_v2.GuildDonationsLayoutView(interaction.user.id, member, donations)
        await interaction.response.send_message(view=view)

    @donation.command(name="tracker", description="View your donation tracker per guild")
    async def donation_tracker(self, interaction: discord.Interaction):
        member = interaction.user
        last_monday = await time_calculations.get_last_monday_berlin_time_from_current_time_in_unix()
        guild_donations = await guilds.get_donations_per_guild(member, last_monday)
        print(guild_donations)
        if not guild_donations:
            await interaction.response.send_message("No donations found in any guild.")
            return
        view = user_commands_slash_definition_v2.GuildDonoForUserLayoutView(member, guild_donations)
        await interaction.response.send_message(view=view)

    @donation.command(name="advanced", description="Enabled / Disable advanced donations for the guild.")
    @app_commands.choices(advanced=[app_commands.Choice(name="Yes", value="True"),
                                    app_commands.Choice(name="No", value="False")])
    async def donation_advanced(self, interaction: discord.Interaction, advanced: app_commands.Choice[str]):
        guild_id = interaction.guild.id
        if advanced.value == "True":
            value = True
        else:
            value = False
        result = await guilds.enable_advanced_dono_per_guild(guild_id, value)
        if result == "no guild found":
            await interaction.response.send_message(f"No guild was found.")
        elif result == "edited":
            await interaction.response.send_message(f"Successfully updated the __advanced donation__ status to: ``{advanced.name}``")
        elif result == "no changes":
            await interaction.response.send_message(f"No changes to the advanced donation were made.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to change the advanced donation.")

    @donation.command(name="channel_stats", description="Xem thống kê donate kênh 50k (tháng này / all-time)")
    async def donation_channel_stats(self, interaction: discord.Interaction):
        if MONTHLY_DONATION_CHANNEL_ID == 0:
            await interaction.response.send_message("Kênh donate 50k chưa được cấu hình.", ephemeral=True)
            return
        stats = await channel_donations.get_channel_stats(MONTHLY_DONATION_CHANNEL_ID)
        view = user_commands_slash_definition_v2.ChannelDonationStatsView(
            channel_id=MONTHLY_DONATION_CHANNEL_ID,
            stats=stats,
            mode="monthly",
        )
        await interaction.response.send_message(view=view)

    @threshold.command(name="add", description="add a member to the threshold list")
    @app_commands.checks.has_permissions(administrator=True)
    async def threshold_add(self, interaction: discord.Interaction, member: discord.User):
        guild_id = interaction.guild.id
        result = await guilds.add_member_to_threshold_list(guild_id, member)
        if result == "guild not found or member not in guild":
            await interaction.response.send_message("There was no guild found, the member is not within the guild or the member has no ID within the database.")
        elif result == "already in threshold":
            await interaction.response.send_message(f"The guild member ``{member.name}`` with ID ``{member.id}`` is already in the threshold list.")
        elif result == "added to threshold":
            await interaction.response.send_message(f"The guild member ``{member.name}`` with ID ``{member.id}`` has been added to the threshold list.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to add ``{member.name}`` with ID ``{member.id}`` to the threshold list.")

    @threshold.command(name="remove", description="remove a member from the threshold list")
    @app_commands.checks.has_permissions(administrator=True)
    async def threshold_remove(self, interaction: discord.Interaction, member: discord.User):
        guild_id = interaction.guild.id
        result = await guilds.remove_member_from_threshold_list(guild_id, member)
        if result == "no guild found":
            await interaction.response.send_message("Please create a guild first before trying to activate a member.")
        elif result == "not in threshold":
            await interaction.response.send_message(f"The guild member ``{member.name}`` with ID ``{member.id}`` is not in the threshold list.")
        elif result == "removed":
            await interaction.response.send_message(f"The guild member ``{member.name}`` with ID ``{member.id}`` has been removed from the threshold list.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to remove ``{member.name}`` with ID ``{member.id}`` from the threshold list.")

    @threshold.command(name="view", description="View threshold members in the guild")
    @app_commands.checks.has_permissions(administrator=True)
    async def threshold_view(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        threshold_members = await guilds.get_threshold_members(guild_id)
        if threshold_members == "no guild found":
            await interaction.response.send_message("Please create a guild first.")
            return
        if len(threshold_members) == 0:
            threshold_members = "No Members in threshold list found."
        else:
            threshold_members = " ; ".join(threshold_members)
        await interaction.response.send_message(f"Currently these members are in the threshold list: **{threshold_members}**")

    # ---------------------------------------------------------------------------
    # Card instance custom picture commands (admin only)
    # ---------------------------------------------------------------------------

    @app_commands.command(name="set_card_picture", description="Set a custom picture for a specific card instance by card ID and name.")
    @app_commands.describe(
        card_id="The Card ID shown in the .info footer (e.g. 2480776512)",
        card_name="The exact card name (e.g. Shizuku Murasaki)",
        picture_url="Direct image URL to use as the custom picture",
        ascend="Number of ascensions (0-6, default 0)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_card_picture(self, interaction: discord.Interaction, card_id: str, card_name: str, picture_url: str, ascend: int = 0):
        await cards.set_custom_card_instance_picture(card_id, card_name, picture_url, ascend)
        verify_url, verify_ascend = await cards.get_custom_card_instance_picture(card_id, card_name)
        await interaction.response.send_message(
            f"Custom picture set for **{card_name}** (ID: `{card_id}`) | Ascend: `{verify_ascend}`\nDB verify: `{verify_url}`", ephemeral=True)

    @app_commands.command(name="remove_card_picture", description="Remove the custom picture for a specific card instance.")
    @app_commands.describe(
        card_id="The Card ID shown in the .info footer",
        card_name="The exact card name")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_card_picture(self, interaction: discord.Interaction, card_id: str, card_name: str):
        await cards.remove_custom_card_instance_picture(card_id, card_name)
        await interaction.response.send_message(
            f"Custom picture removed for **{card_name}** (ID: `{card_id}`).", ephemeral=True)

    @app_commands.command(name="set_raid_afk_channel", description="Set the channel where raid AFK ping reminders will be sent.")
    @app_commands.describe(channel="The text channel to send raid AFK reminders in")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_raid_afk_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await guilds.set_raid_afk_ping_channel(interaction.guild.id, channel.id)
        await interaction.response.send_message(
            f"Raid AFK ping channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="set_weekly_donation_channel", description="Đặt kênh nhận thông báo kiểm tra đóng tiền hàng tuần (gửi vào sáng Chủ Nhật).")
    @app_commands.describe(channel="Kênh text để bot gửi bảng kiểm tra đóng tiền")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_weekly_donation_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await guilds.set_weekly_donation_channel(interaction.guild.id, channel.id)
        await interaction.response.send_message(
            f"Kênh kiểm tra đóng tiền weekly đã được đặt thành {channel.mention}.", ephemeral=True)

    @app_commands.command(name="breach_comp_add", description="Share a Breach team comp/playbook with your clan.")
    @app_commands.describe(
        comp="Team comp, e.g. A4 Totoro, A2H Chisa Kotegawa, A5 Clara Valac",
        phase="Breach phase this plan is for",
        difficulty="Breach difficulty this plan is for",
        title="Short name for this playbook, e.g. All in Chisa",
        rng="RNG notes, e.g. r1 crit loses the run",
        description="Setup/details, e.g. Chisa needs 1k gold before r8",
        result="Result achieved, e.g. 430k dmg / stable 400k+")
    @app_commands.choices(
        phase=[
            app_commands.Choice(name="Docile", value="Docile"),
            app_commands.Choice(name="Chaos", value="Chaos"),
            app_commands.Choice(name="Herald - Damnation", value="Herald - Damnation"),
            app_commands.Choice(name="Herald - Salvation", value="Herald - Salvation"),
            app_commands.Choice(name="Gambit", value="Gambit"),
            app_commands.Choice(name="Enraged", value="Enraged"),
            app_commands.Choice(name="Collapse", value="Collapse"),
        ],
        difficulty=[
            app_commands.Choice(name="Easy", value="Easy"),
            app_commands.Choice(name="Medium", value="Medium"),
            app_commands.Choice(name="Hard", value="Hard"),
            app_commands.Choice(name="Impossible", value="Impossible"),
        ],
    )
    async def breach_comp_add(
        self,
        interaction: discord.Interaction,
        comp: str,
        phase: app_commands.Choice[str],
        difficulty: app_commands.Choice[str],
        title: str = None,
        rng: str = None,
        description: str = None,
        result: str = None,
    ):
        if not interaction.guild:
            await interaction.response.send_message("Command n\u00e0y ch\u1ec9 d\u00f9ng trong server.", ephemeral=True)
            return

        avatar_url = interaction.user.display_avatar.url if interaction.user.display_avatar else None
        default_title = f"Gi\u00e1o \u00e1n c\u1ee7a {interaction.user.display_name}"
        comp_id = await breach_comps.add_breach_comp(
            guild_id=interaction.guild.id,
            author_id=interaction.user.id,
            author_name=interaction.user.display_name,
            author_avatar_url=avatar_url,
            title=title,
            comp=comp,
            phase=phase.value,
            difficulty=difficulty.value,
            rng=rng,
            description=description,
            result=result,
        )
        await interaction.response.send_message(
            f"\u0110\u00e3 l\u01b0u gi\u00e1o \u00e1n Breach `{title or default_title}`. ID: `{comp_id}`\n"
            "D\u00f9ng `/breach_comp_board` \u0111\u1ec3 m\u1edf b\u1ea3ng gi\u00e1o \u00e1n c\u1ee7a clan.",
            ephemeral=True,
        )

    @app_commands.command(name="breach_comp_board", description="Open the clan Breach Playbook board.")
    async def breach_comp_board(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("Command n\u00e0y ch\u1ec9 d\u00f9ng trong server.", ephemeral=True)
            return

        entries = await breach_comps.get_breach_comps(interaction.guild.id)
        clan_image_url = await guilds.get_breach_playbook_image_url(interaction.guild.id)
        view = breach_comp_views.BreachCompBoardView(entries, clan_image_url=clan_image_url)
        await interaction.response.send_message(view=view)


    @threshold.command(name="limit", description="Set the SECOND threshold limit for the guild.")
    @app_commands.checks.has_permissions(administrator=True)
    async def threshold_limit(self, interaction: discord.Interaction, donation_amount: int):
        guild_id = interaction.guild.id
        result = await guilds.update_guild_threshold_2_by_guild_id_in_guilds(guild_id, donation_amount)
        if result == "no guild found":
            await interaction.response.send_message("Please create a guild first before setting up the second threshold limit.")
        elif result == "edited":
            await interaction.response.send_message(f"__Second__ threshold limit was set to: **{donation_amount:,}** gold {gold_emote}")
        elif result == "no changes":
            await interaction.response.send_message("No changes were made.")
        else:
            await interaction.response.send_message(f"An error occurred while trying to set the second threshold limit.")


async def setup(bot: commands.Bot):
    await bot.add_cog(UserCommandsSlash(bot))
