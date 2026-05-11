import asyncio, re, time, discord
from datetime import datetime, timezone
from aiohttp.web_routedef import options
from discord.ui import View, Select, Button
from Commands import definitions, user_commands_slash_definition_v2
from db_methods import cards, players, guilds, general, weekly_donations
from misc import time_calculations, skills

raid_tracker = {}

gold_emote = "<:GOLD:1338511775448043541>"
element_null_emote = "<:NULL:1338512039156645992>"
rubies_emote = "<:RUBIES:1339686347715252275>"
ultra_rare_1 = "<:ultra:1339690444216467557>"
ultra_rare_2 = "<:u_rare:1339690459466960986>"
super_rare_1 = "<:super:1339690471873577071>"
super_rare_2 = "<:s_rare:1339690481692704928>"
rare_emote = "<:r_rare:1378150486573580308>"
uncommon_emote_1 = "<:u_uncommon:1378150471126225077>"
uncommon_emote_2 = "<:c_uncommon:1378150446543142934>"
common_emote_1 = "<:c_common:1378150629545082941>"
ascension_emote = "<:red_star:1336062483730796685>"


async def in_raid_lobby(embed_title, embed_description, embed_footer): #TODO check it
    energy_list = []
    boss_hp = []
    attacks_list = []
    damage_list = []
    current_player = []
    afk_player = []
    embed_description = await definitions.mask_single_underscores(embed_description)
    embed_description_cleaned = embed_description.replace(",", "")
    total_energy_match = re.findall(r"Energy:\s*(\d+)/", embed_description_cleaned)
    total_damage_match = re.findall(r"Total Damage:\s*(\d+)", embed_description_cleaned)
    total_attacks_match = re.findall(r"Total Attacks:\s*(\d+)", embed_description_cleaned)
    energy_list.extend(total_energy_match)
    energy_list_int = [int(energy) for energy in energy_list]
    total_energy = sum(energy_list_int)
    damage_list.extend(total_damage_match)
    damage_list_int = [int(damage) for damage in damage_list]
    total_damage = sum(damage_list_int)
    attacks_list.extend(total_attacks_match)
    attacks_list_int = [int(attacks) for attacks in attacks_list]
    total_attacks = sum(attacks_list_int)
    sorted_damage_list = sorted(damage_list, key=int, reverse=True)
    hp_pattern = r"\*\*(-?\d+)\s*/\s*(\d+)\*\*"
    match = re.search(hp_pattern, embed_description_cleaned)
    if match:
        current_hp = match.group(1)
        max_hp = match.group(2)
        boss_hp.append((current_hp, max_hp))
        boss_hp_bar = await definitions.build_boss_hp_bar(current_hp, max_hp)
        old_emoji_list = re.findall(r"(<:1:\d+>)", embed_description)
        old_emoji_pattern = (old_emoji_list[0] + old_emoji_list[1] + old_emoji_list[2] +
                             old_emoji_list[3] + old_emoji_list[4] + old_emoji_list[5] +
                             old_emoji_list[6] + old_emoji_list[7] + old_emoji_list[8] +
                             old_emoji_list[9])
        embed_description_cleaned = embed_description_cleaned.replace(old_emoji_pattern, boss_hp_bar)
        old_heart = "<:HP\\_HEART:696453924902928536>"
        new_heart = "<:hp_heart:1325532335482863677>"
        embed_description_cleaned = embed_description_cleaned.replace(old_heart, new_heart)
        embed_description_cleaned = embed_description_cleaned.replace(f"{int(current_hp)} / {int(max_hp)}",
                                                                      f"{int(current_hp):,} / {int(max_hp):,}")
    if len(boss_hp) > 0:
        max_hp = int(boss_hp[-1][1])
        boss_hp_threshold = max_hp // 10
        boss_hp_threshold_text = f"{boss_hp_threshold:,} Damage to reach Drop range"
        if embed_footer:
            embed_footer = embed_footer.replace("Type .rd battle when you have Energy!",
                                                f"Deal {boss_hp_threshold_text}!")
    master_filter = r"\((\d+)\)\s*\|\s*Level\s*(\d+)\s*\|\s*Power Level:\s*(\d+)\**\nEnergy:\s*(\d+)\s*\/\s*\s*\d+\nTotal Damage:\s*(\d+)\nTotal Attacks:\s*(\d+)\nLast Attack:\s*(\d+)"
    master_filter_search = re.findall(master_filter, embed_description_cleaned)
    difficulty_search = re.findall(r"\[\w+]", embed_description_cleaned)
    player_search_pattern = r"(\d)/(\d)"
    current_player_match = re.search(player_search_pattern, embed_footer)
    if current_player_match:
        current_player_number_1 = current_player_match.group(1)
        max_player_number_1 = current_player_match.group(2)
        current_player.extend((current_player_number_1, max_player_number_1))
    if max_player_number_1 == "2":
        lobby_multiplicator = 2.45
    else:
        lobby_multiplicator = 1
    raid_boss_rarity_name = re.search(r"__(Common|Uncommon|Rare|Super Rare|Ultra Rare)__\sLevel\s\d+\s(.+)\s\[Evo 3]", embed_description_cleaned)
    rarity_scaling = 1
    if raid_boss_rarity_name.group(1) == "Common":
        rarity_scaling = 1.2
    elif raid_boss_rarity_name.group(1) == "Uncommon":
        rarity_scaling = 1.4
    elif raid_boss_rarity_name.group(1) == "Rare":
        rarity_scaling = 1.6
    elif raid_boss_rarity_name.group(1) == "Super Rare":
        rarity_scaling = 1.8
    elif raid_boss_rarity_name.group(1) == "Ultra Rare":
        rarity_scaling = 2
    raid_boss_data = await cards.get_card_data_by_name(raid_boss_rarity_name.group(2))
    if raid_boss_data and raid_boss_data[0]["card_talent"] in ["Devour", "Rising Resolve", "Foul Play", "Transformation", "Miracle Injection"]:
        if raid_boss_data[0]["card_talent"] == "Devour":
            rarity_multiplier = 1.75
        elif raid_boss_data[0]["card_talent"] == "Rising Resolve":
            rarity_multiplier = 1.75
        elif raid_boss_data[0]["card_talent"] == "Foul Play":
            rarity_multiplier = 1.75
        elif raid_boss_data[0]["card_talent"] == "Transformation":
            base_scaling = 0.30
            rarity_multiplier = (1 + int(base_scaling * rarity_scaling))
        elif raid_boss_data[0]["card_talent"] == "Miracle Injection":
            base_scaling = 0.10
            rarity_multiplier = (1 - int(base_scaling * rarity_scaling))
    else:
        rarity_multiplier = 1
    if difficulty_search:
        difficulty_value = difficulty_search[0].strip("[]")
        if difficulty_value == "Impossible":
            damage_multiplier = 1
        elif difficulty_value == "Hard":
            damage_multiplier = 1.33333333333
        elif difficulty_value == "Medium":
            damage_multiplier = 2
        elif difficulty_value == "Easy":
            damage_multiplier = 4
    for match in master_filter_search:
        player_id = match[0]
        player_level = match[1]
        player_power_level = match[2]
        player_energy = match[3]
        player_max_damage = match[4]
        player_total_attacks = match[5]
        player_afk_timer = match[6]
        if player_total_attacks == 0:
            return embed_title, embed_description, embed_footer
        try:
            damage_per_attack = int(player_max_damage) // int(player_total_attacks)
        except ZeroDivisionError:
            damage_per_attack = 0
        player_damage_percent = round((100 / int(max_hp) * int(player_max_damage)), 2)
        if damage_per_attack >= (int(max_hp) // 100) * damage_multiplier * rarity_multiplier * lobby_multiplicator:
            threshold_damage_text = "MAX "
        elif damage_per_attack >= (int(max_hp) // 100 // 1.25) * damage_multiplier * rarity_multiplier * lobby_multiplicator:
            threshold_damage_text = "Great "
        elif damage_per_attack >= (int(max_hp) // 100 // 1.5) * damage_multiplier * rarity_multiplier * lobby_multiplicator:
            threshold_damage_text = "Good "
        elif damage_per_attack >= (int(max_hp) // 100 // 2) * damage_multiplier * rarity_multiplier * lobby_multiplicator:
            threshold_damage_text = "Average "
        elif damage_per_attack < (int(max_hp) // 100 // 2) * damage_multiplier * rarity_multiplier * lobby_multiplicator:
            if int(player_total_attacks) == 0:
                threshold_damage_text = "waiting for attacks "
            else:
                threshold_damage_text = "Leeching "
        if ":first_place:" not in embed_description:
            if player_max_damage == sorted_damage_list[0] and int(player_total_attacks) != 0:
                ranking_emote = ":first_place:"
            elif ":second_place:" not in embed_description:
                if len(sorted_damage_list) > 1 and player_max_damage == sorted_damage_list[1] and int(player_total_attacks) != 0:
                    ranking_emote = ":second_place:"
                elif len(sorted_damage_list) > 2 and player_max_damage == sorted_damage_list[2] and int(player_total_attacks) != 0:
                    ranking_emote = ":third_place:"
                else:
                    ranking_emote = ""
            elif ":second_place:" in embed_description:
                if ":third_place:" not in embed_description:
                    if len(sorted_damage_list) > 2 and player_max_damage == sorted_damage_list[2] and int(player_total_attacks) != 0:
                        ranking_emote = ":third_place:"
                    else:
                        ranking_emote = ""
                elif ":third_place:" in embed_description:
                    ranking_emote = ""
            else:
                ranking_emote = ""
        elif ":first_place:" in embed_description:
            if ":second_place:" not in embed_description:
                if len(sorted_damage_list) > 1 and player_max_damage == sorted_damage_list[1] and int(player_total_attacks) != 0:
                    ranking_emote = ":second_place:"
                elif len(sorted_damage_list) > 2 and player_max_damage == sorted_damage_list[2] and int(player_total_attacks) != 0:
                    ranking_emote = ":third_place:"
                else:
                    ranking_emote = ""
            elif ":second_place:" in embed_description:
                if ":third_place:" not in embed_description:
                    if len(sorted_damage_list) > 2 and player_max_damage == sorted_damage_list[2] and int(player_total_attacks) != 0:
                        ranking_emote = ":third_place:"
                    else:
                        ranking_emote = ""
                elif ":third_place:" in embed_description:
                    ranking_emote = ""
            else:
                ranking_emote = ""
        else:
            ranking_emote = ""
        if int(player_max_damage) >= boss_hp_threshold:
            threshold_status_text = "✅"
        else:
            threshold_status_text = "❌"
        if int(player_afk_timer) >= 30:
            afk_text = "**[AFK]**"
        else:
            afk_text = " "
        replace_text = f"\nEnergy: {player_energy}/25\nTotal Damage: {int(player_max_damage):,} ({int(damage_per_attack):,}) ({player_damage_percent}%)\nDamage Status: {threshold_damage_text}{ranking_emote}\nTotal Attacks: {player_total_attacks}\nLast Attack: {player_afk_timer}m ago {afk_text}\nThreshold Status: {threshold_status_text}"
        embed_description_cleaned = embed_description_cleaned.replace(
            f"({player_id}) | Level {player_level} | Power Level: {player_power_level}**\nEnergy: {player_energy}/25\nTotal Damage: {player_max_damage}\nTotal Attacks: {player_total_attacks}\nLast Attack: {player_afk_timer}m ago",
            f"({player_id}) | Level {player_level} | Power Level: {player_power_level}**" + replace_text)
        embed_description = embed_description_cleaned
    # Extract raid_code early so we can look up observed rate before building the embed
    _early_code_search = re.findall(r"\|\s(\d+)\s\|", embed_footer)
    raid_code = _early_code_search[0] if _early_code_search else None
    now = time.time()

    debug_attacks_needed = 0
    debug_end_time_str = "N/A"
    debug_unix_end_code = ""
    debug_end_time_afk_str = "N/A"
    debug_unix_end_code_afk = ""
    debug_average_damage = 0
    debug_count_afk = 0
    debug_activity_str = "N/A (first observation)"
    debug_activity_unix = ""
    debug_observed_rate = None

    if total_attacks == 0:
        embed_description = embed_description.replace("<:hp_g_r:1325526982938595489>",
                                                      "<:hp_g_r:1325526982938595489>\n\n__End time:__ \n waiting for attacks")
        embed_description = embed_description.replace("<:hp_b_r:1325527015381663754>",
                                                      "<:hp_b_r:1325527015381663754>\n\n__End time:__ \n waiting for attacks")
    elif total_attacks != 0:
        average_damage = int(total_damage) / total_attacks
        debug_average_damage = average_damage
        if average_damage > 0:
            attacks_needed = int(current_hp) / average_damage
        else:
            attacks_needed = 0
        debug_attacks_needed = attacks_needed
        afk_player_search = re.findall(r'\[AFK\]', embed_description)
        afk_player.extend(afk_player_search)
        count_afk_player = len(afk_player)
        debug_count_afk = count_afk_player

        # Compute observed attack rate from tracker snapshot
        observed_rate = None
        if raid_code:
            prev = raid_tracker.get(raid_code)
            if prev:
                delta_attacks = total_attacks - prev["last_attacks"]
                delta_time_minutes = (now - prev["last_time"]) / 60
                if delta_attacks > 0 and delta_time_minutes > 0:
                    observed_rate = delta_attacks / delta_time_minutes
                elif prev.get("observed_rate"):
                    observed_rate = prev["observed_rate"]
        debug_observed_rate = observed_rate

        # Primary: observed rate (requires ≥3 attacks for reliable data)
        # Fallback: regen-based estimate
        if observed_rate and total_attacks >= 3 and attacks_needed > 0:
            remaining_minutes = attacks_needed / observed_rate
            end_time_str = await definitions.convert_to_hours_minutes(int(remaining_minutes))
            unix_end_code = f"[<t:{int(now + remaining_minutes * 60)}:T>]"
            estimate_source = ""
        else:
            end_time_str, unix_end_code = await definitions.calculate_end_time(attacks_needed, total_energy,
                                                                               current_player_match.group(1),
                                                                               count_afk_player)
            estimate_source = " (early est.)"
        debug_end_time_str = end_time_str
        debug_unix_end_code = unix_end_code

        excluding_afk = ""
        if count_afk_player > 0:
            excluding_afk = " excl. afk"
            total_energy_with_afk = total_energy - (25 * count_afk_player)
            time_with_afk_player, unix_end_code_with_afk = await definitions.calculate_end_time_including_afk(
                attacks_needed, total_energy_with_afk, current_player_match.group(1), count_afk_player)
            debug_end_time_afk_str = time_with_afk_player
            debug_unix_end_code_afk = unix_end_code_with_afk
            embed_description = embed_description.replace("<:hp_g_r:1325526982938595489>",
                                                          f"<:hp_g_r:1325526982938595489>\n\n__End time (all players):__ \n {time_with_afk_player} {unix_end_code_with_afk}")
            embed_description = embed_description.replace("<:hp_b_r:1325527015381663754>",
                                                          f"<:hp_b_r:1325527015381663754>\n\n__End time (all players):__ \n {time_with_afk_player} {unix_end_code_with_afk}")
            total_energy = total_energy_with_afk
        embed_description = embed_description.replace("<:hp_g_r:1325526982938595489>",
                                                      f"<:hp_g_r:1325526982938595489>\n\n__End time{excluding_afk}{estimate_source}:__ \n {end_time_str} {unix_end_code}")
        embed_description = embed_description.replace("<:hp_b_r:1325527015381663754>",
                                                      f"<:hp_b_r:1325527015381663754>\n\n__End time{excluding_afk}{estimate_source}:__ \n {end_time_str} {unix_end_code}")

    raid_history_description = embed_description.replace("\\", "")
    raid_history_description = raid_history_description.replace(",", "")
    raid_history_search_pattern_timer = (r"<t:(\d+):R>")
    raid_history_search_timer = re.findall(raid_history_search_pattern_timer, embed_title)
    raid_history_search_pattern_raid_boss_data = (r"__(?:(Uncommon|Rare|Super Rare|Ultra Rare))__\sLevel"
                                                  r"\s(\d+)\s([\w\W\d\D]+)\s\[Evo 3\]"
                                                  r"\s\[(?:(Easy|Medium|Hard|Impossible))\]")
    raid_history_search_raid_boss_data = re.findall(raid_history_search_pattern_raid_boss_data,
                                                    raid_history_description)
    raid_history_search_pattern_player_data = (r"\*\*#(\d+)\s\|\s([\w._\\]+)\s\((\d+)\)\s\|\sLevel\s(\d+)\s\|\s"
                                               r"Power Level:\s(\d+)\*\*\nEnergy:\s\d+\/\d+\nTotal Damage:\s(\d+)\s\((\d+)\)\s\((\d+\.\d{2})(?=%)\%\)\n"
                                               r"Damage Status:\s([\w\s]+)\s(?::first_place:|:second_place:|:third_place:)?\n"
                                               r"Total Attacks:\s(\d+)\nLast Attack:\s(\d+)m ago")
    raid_history_search_player_data = re.findall(raid_history_search_pattern_player_data, raid_history_description)
    raid_history_search_pattern_raid_code = (r"\|\s(\d+)\s\|")
    raid_history_search_raid_code = re.findall(raid_history_search_pattern_raid_code, embed_footer)
    raid_history_unique_code = raid_history_search_raid_code[0] + raid_history_search_timer[0]
    await players.update_raid_history_for_players_by_player_data(raid_history_search_player_data,
                                                                 raid_history_search_raid_boss_data,
                                                                 raid_history_unique_code)

    # Update debug display and tracker
    if debug_observed_rate and debug_attacks_needed > 0:
        remaining_minutes_activity = debug_attacks_needed / debug_observed_rate
        debug_activity_str = await definitions.convert_to_hours_minutes(int(remaining_minutes_activity))
        debug_activity_unix = f"[<t:{int(now + remaining_minutes_activity * 60)}:T>]"
    if raid_code:
        raid_tracker[raid_code] = {
            "last_time": now,
            "last_attacks": total_attacks,
            "observed_rate": debug_observed_rate,
        }

    current_player_number = int(current_player_match.group(1)) if current_player_match else 0
    active_players = current_player_number - debug_count_afk
    debug_embed = discord.Embed(title="[DEBUG] Raid Estimate Details", color=0x2B2D31)
    debug_embed.add_field(
        name="Players",
        value=f"Total: **{current_player_number}** | Active: **{active_players}** | AFK: **{debug_count_afk}**",
        inline=False
    )
    debug_embed.add_field(
        name="Attacks",
        value=(
            f"Total so far: **{total_attacks}**\n"
            f"Attacks still needed: **{int(debug_attacks_needed)}**\n"
            f"Avg damage/attack: **{int(debug_average_damage):,}**"
        ),
        inline=False
    )
    debug_embed.add_field(
        name="Estimate (energy regen — current method)",
        value=f"{debug_end_time_str} {debug_unix_end_code}",
        inline=False
    )
    if debug_count_afk > 0:
        debug_embed.add_field(
            name="Estimate (including AFK in regen)",
            value=f"{debug_end_time_afk_str} {debug_unix_end_code_afk}",
            inline=False
        )
    rate_text = f"{debug_observed_rate:.2f} attacks/min" if debug_observed_rate else "not enough data yet"
    debug_embed.add_field(
        name="Estimate (activity-based — observed rate)",
        value=f"{debug_activity_str} {debug_activity_unix}\nObserved rate: **{rate_text}**",
        inline=False
    )
    debug_embed.set_footer(text=f"Raid code: {raid_code} | Updated: {int(now)}")

    return embed_title, embed_description, embed_footer, debug_embed


async def raid_lobby_waiting_room(embed_title, embed_description, embed_footer): #TODO check it
    boss_hp = []
    embed_description = await definitions.mask_single_underscores(embed_description)
    embed_description_cleaned = embed_description.replace(",", "")
    hp_pattern = r"\*\*(\d+)\s*/\s*(\d+)\*\*"
    match = re.search(hp_pattern, embed_description_cleaned)
    if match:
        current_hp = match.group(1)
        max_hp = match.group(2)
        boss_hp.append((current_hp, max_hp))
        boss_hp_bar = await definitions.build_boss_hp_bar(current_hp, max_hp)
        old_emoji_list = re.findall(r"(<:1:\d+>)", embed_description)
        old_emoji_pattern = (old_emoji_list[0] + old_emoji_list[1] + old_emoji_list[2] +
                             old_emoji_list[3] + old_emoji_list[4] + old_emoji_list[5] +
                             old_emoji_list[6] + old_emoji_list[7] + old_emoji_list[8] +
                             old_emoji_list[9])
        embed_description_cleaned = embed_description_cleaned.replace(old_emoji_pattern, boss_hp_bar)
        old_heart = "<:HP\\_HEART:696453924902928536>"
        new_heart = "<:hp_heart:1325532335482863677>"
        embed_description_cleaned = embed_description_cleaned.replace(old_heart, new_heart)
        embed_description_cleaned = embed_description_cleaned.replace(
            f"{int(current_hp)} / {int(max_hp)}",
            f"{int(current_hp):,} / {int(max_hp):,}")
        embed_description = embed_description_cleaned
    raid_code = []
    raid_lobby_code = re.findall(r"(\d+)", embed_footer)
    raid_code.extend(raid_lobby_code)
    embed_footer = f".rd join {raid_code[2]} | {raid_code[0]} / {raid_code[1]} Players in Raid Party"
    return embed_title, embed_description, embed_footer


class EmbedProxy:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


async def raid_team_check(proxy_embed_field_1, proxy_embed_field_2): #TODO check it
    power_level_list_team_1 = []
    power_level_list_team_2 = []
    effectiveness = 0
    null = "<:Null:1329746549382582285>"
    emoji_list = ["☀", "🌙", "⛰", "🍃", "🔥", "💧", "⚡", "✨", null]
    embed_field_1 = EmbedProxy(value=proxy_embed_field_1)
    embed_field_2 = EmbedProxy(value=proxy_embed_field_2)
    text_field_1 = str(embed_field_1.value)
    text_field_2 = str(embed_field_2.value)
    clean_text_field_1 = text_field_1.replace(",", "")
    clean_text_field_2 = text_field_2.replace(",", "")
    power_level_team_1 = re.findall(r"\*\*PL:\*\* (\d+)", clean_text_field_1)
    power_level_list_team_1.extend(power_level_team_1)
    power_level_team_2 = re.findall(r"\*\*PL:\*\* (\d+)", clean_text_field_2)
    power_level_list_team_2.extend(power_level_team_2)
    if null in text_field_2:
        return 1
    emojis_field_1 = [ch for ch in text_field_1 if ch in emoji_list]
    emojis_field_2 = [ch for ch in text_field_2 if ch in emoji_list]
    count_emoji_field_1 = len(emojis_field_1)
    if null in clean_text_field_1:
        count_emoji_field_1 += 1
        effectiveness += 1
    if count_emoji_field_1 == 1:
        return 2
    elif count_emoji_field_1 == 2:
        if int(power_level_list_team_1[0]) < 1100:
            return 1
        else:
            return 2
    for emoji1 in emojis_field_1:
        for emoji2 in emojis_field_2:
            status = await definitions.element_effectiveness(emoji1, emoji2)
            effectiveness += status
    if effectiveness >= 3:
        return 1
    elif effectiveness < 3:
        return 2


class DeleteButtonView(View):
    def __init__(self):
        super().__init__(timeout=180)
        self.delete_button = Button(label="", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.delete_button.callback = self.delete_callback
        self.add_item(self.delete_button)

    async def delete_callback(self, interaction: discord.Interaction):
        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass


async def player_gold_and_rubies_command(message): #TODO check it
    if "gold" in message.content:
        gold_data = re.search(r"\*\*(.*)\*\*\scurrently has\s\*\*([\d,]+)\*\*\sgold <a:gold:1219941344450052187>",
                              message.content)
        player_name = gold_data.group(1)
        player_gold = gold_data.group(2)
        player_gold = player_gold.replace(",", "")
        old_player_gold = await players.update_player_gold_by_player_name(player_name, int(player_gold))
        if old_player_gold == "player not found":
            player_not_found = "player not found"
            return player_name, player_not_found
        if int(old_player_gold) <= int(player_gold):
            embed_text = f"**{int(player_gold):,}** {gold_emote}\n**+{(int(player_gold) - int(old_player_gold)):,}** gain."
        else:
            embed_text = f"**{int(player_gold):,}** {gold_emote}\n**{(int(player_gold) - int(old_player_gold)):,}** loss."
        return player_name, embed_text
    elif "Clan Rubies" in message.content:
        rubies_data = re.search(
            r"\*\*(.*)\*\*\scurrently has\s\*\*([\d,]+)\*\*\sClan Rubies <:CLAN_RUBIES:713100255536742450>",
            message.content)
        player_name = rubies_data.group(1)
        player_rubies = rubies_data.group(2)
        player_rubies = player_rubies.replace(",", "")
        player_rubies_update = await players.update_player_rubies_by_player_name(player_name, int(player_rubies))
        if player_rubies_update == "player not found":
            player_not_found = "player not found"
            return player_name, player_not_found
        rubies_cost_for_sr = 20000
        rubies_cost_for_ur = 200000
        if int(player_rubies) != 0:
            needed_amount_sr = max(0, rubies_cost_for_sr - (int(player_rubies) % rubies_cost_for_sr))
            needed_amount_ur = max(0, rubies_cost_for_ur - (int(player_rubies) % rubies_cost_for_ur))
            purchasable_amount_sr = int(player_rubies) // rubies_cost_for_sr
            purchasable_amount_ur = int(player_rubies) // rubies_cost_for_ur
            embed_text = (f"{int(player_rubies):,} {rubies_emote}\n\n"
                          f"{needed_amount_sr:,} {rubies_emote} till next {super_rare_1}{super_rare_2}\n"
                          f"{needed_amount_ur:,} {rubies_emote} till next {ultra_rare_1}{ultra_rare_2}\n\n"
                          f"Currently purchasable {super_rare_1}{super_rare_2}: {purchasable_amount_sr:,}\n"
                          f"Currently purchasable {ultra_rare_1}{ultra_rare_2}: {purchasable_amount_ur:,}")
        else:
            embed_text = (f"{int(player_rubies)} {rubies_emote}\n\n"
                          f"{rubies_cost_for_sr:,} {rubies_emote} till next {super_rare_1}{super_rare_2}\n"
                          f"{rubies_cost_for_ur:,} {rubies_emote} till next {ultra_rare_1}{ultra_rare_2}\n\n"
                          f"Currently purchasable {super_rare_1}{super_rare_2}: 0\n"
                          f"Currently purchasable {ultra_rare_1}{ultra_rare_2}: 0")
        return player_name, embed_text


WEEKLY_DONATION_CHANNEL_ID = 925618781777199114
WEEKLY_DONATION_AMOUNT = 100_000


async def clan_donation_tracker(embed_description, message):
    embed_description = embed_description.replace(",", "")
    player_data = re.findall(r"Summoner \*\*(.*)\*\* you have donated \*\*(\d+)\*\* Gold", embed_description)
    if not player_data:
        await message.reply("Could not parse donation information from message.")
        return
    player_name, player_donate_amount = player_data[0]
    player_donate_amount = int(player_donate_amount)
    try:
        updated_guilds = await guilds.update_donation_amount_by_player_name_in_guilds(player_name, player_donate_amount, "auto")
        view = user_commands_slash_definition_v2.DonationResultLayoutView(player_name, player_donate_amount, updated_guilds)
        await message.reply(view=view)
    except Exception as e:
        error_view = user_commands_slash_definition_v2.DonationResultLayoutView(player_name, player_donate_amount, [])
        await message.reply(f"<a:cross:1380797973373521962> Error while processing donation: {str(e)}", view=error_view)

    if message.channel.id != WEEKLY_DONATION_CHANNEL_ID:
        return
    if player_donate_amount == 50_000 or player_donate_amount % WEEKLY_DONATION_AMOUNT != 0:
        return
    weeks = player_donate_amount // WEEKLY_DONATION_AMOUNT
    try:
        discord_id = await weekly_donations.get_discord_id_by_player_name(player_name)
        total_weeks = await weekly_donations.create_or_update_tracking(
            player_name, discord_id, message.channel.id, weeks
        )
        await message.add_reaction("✅")
        ping_text = f"<@{discord_id}>" if discord_id else f"**{player_name}**"
        await message.reply(
            f"✅ Ghi nhận **{player_donate_amount:,}** gold ({weeks} tuần) cho {ping_text}. "
            f"Tổng: **{total_weeks} tuần** — sẽ được nhắc sau {total_weeks} tuần.",
            mention_author=False
        )
    except Exception as e:
        print(f"[WEEKLY DONATION] Error tracking {player_name}: {e}")


async def profile_tracker(embed_fields, embed_footer):
    for field in embed_fields:
        if "Premium Days" in field.name:
            premium_days_left = field.value
            player_id = embed_footer.replace("Summoner ID: ", "")
            try:
                player_id = int(player_id)
                premium_days_left = int(premium_days_left)
            except ValueError:
                return
            try:
                await players.update_player_premium_days_left_by_discord_id(player_id, premium_days_left)
            except Exception:
                pass
