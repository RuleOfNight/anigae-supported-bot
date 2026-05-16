"""
Xử lý embed message từ AniGame bot:
- Raid lobby đang diễn ra (in_raid_lobby)
- Phòng chờ raid (raid_lobby_waiting_room)
- Theo dõi donation clan (clan_donation_tracker)
- Theo dõi profile player (profile_tracker)
"""

import re
import time
import discord
from discord.ui import View, Button
from Commands import definitions, user_commands_slash_definition_v2
from db_methods import cards, players, guilds, weekly_donations, channel_donations

# In-memory tracker: raid_code → {last_time, last_attacks, observed_rate}
raid_tracker: dict = {}

# ─── Emotes ───────────────────────────────────────────────────────────────────
gold_emote         = "<a:GOLD:1503359399438319716>"
element_null_emote = "<:NULL:1338512039156645992>"
rubies_emote       = "<:ruby:1503731817629618267> "
ultra_rare_1       = "<a:ultra:1503300387917004850>"
ultra_rare_2       = "<a:rare3:1503300751496057017>"
super_rare_1       = "<:super:1503299742753361974>"
super_rare_2       = "<:rare:1503300937396129852>"
rare_emote         = "<:r_rare:1378150486573580308>"
uncommon_emote_1   = "<:u_uncommon:1378150471126225077>"
uncommon_emote_2   = "<:c_uncommon:1378150446543142934>"
common_emote_1     = "<:c_common:1378150629545082941>"
ascension_emote    = "<:RedStar:1503299407720747119>"

# ─── Constants ────────────────────────────────────────────────────────────────
WEEKLY_DONATION_CHANNEL_ID  = 925618781777199114
WEEKLY_DONATION_AMOUNT      = 100_000
MONTHLY_DONATION_CHANNEL_ID = 1504949108664700998

_RARITY_SCALING: dict[str, float] = {
    "Common":     1.2,
    "Uncommon":   1.4,
    "Rare":       1.6,
    "Super Rare": 1.8,
    "Ultra Rare": 2.0,
}

_DIFFICULTY_MULTIPLIER: dict[str, float] = {
    "Impossible": 1.0,
    "Hard":       1.33333333333,
    "Medium":     2.0,
    "Easy":       4.0,
}

# ─── Private helpers ──────────────────────────────────────────────────────────

def _get_rarity_scaling(rarity_name: str) -> float:
    """Return the base damage-scaling factor for a raid boss rarity tier."""
    return _RARITY_SCALING.get(rarity_name, 1.0)


def _get_talent_multiplier(card_talent: str, rarity_scaling: float) -> float:
    """
    Return the talent-based damage multiplier for a raid boss.

    Some talents scale with rarity (Transformation, Miracle Injection);
    the rest use a flat 1.75 multiplier.
    """
    if card_talent in ("Devour", "Rising Resolve", "Foul Play"):
        return 1.75
    if card_talent == "Transformation":
        return 1 + int(0.30 * rarity_scaling)
    if card_talent == "Miracle Injection":
        return 1 - int(0.10 * rarity_scaling)
    return 1.0


def _get_difficulty_multiplier(difficulty: str) -> float:
    """Return the damage multiplier for a raid difficulty tier."""
    return _DIFFICULTY_MULTIPLIER.get(difficulty, 1.0)


def _assign_ranking_emote(
    player_damage: str,
    sorted_damages: list,
    total_attacks: int,
    current_embed: str,
) -> str:
    """
    Return the next available medal emote (:first_place:, :second_place:, :third_place:)
    for this player based on their damage rank.

    Medals already present in current_embed are skipped to avoid duplicates.
    Returns an empty string if the player has no attacks or no medal applies.
    """
    if total_attacks == 0:
        return ""
    medals = [":first_place:", ":second_place:", ":third_place:"]
    for medal, threshold in zip(medals, sorted_damages):
        if player_damage == threshold and medal not in current_embed:
            return medal
    return ""


def _replace_hp_bar_emojis(description: str, new_hp_bar: str) -> str:
    """
    Replace the 10 consecutive AniGame HP-bar emojis (<:1:id>) with new_hp_bar.

    Returns description unchanged if fewer than 10 matching emojis are found.
    """
    old_emojis = re.findall(r"(<:1:\d+>)", description)
    if len(old_emojis) < 10:
        return description
    return description.replace("".join(old_emojis[:10]), new_hp_bar)


# ─── Raid functions ───────────────────────────────────────────────────────────

async def in_raid_lobby(
    embed_title: str, embed_description: str, embed_footer: str,
    guild_id: int | None = None,
) -> tuple[str, str, str]:
    """
    Augment a Raid Challenge Timer embed with enhanced stats and time estimates.

    Processing steps:
    1. Strip boilerplate lines added by the original AniGame bot.
    2. Rebuild the boss HP bar and reformat HP numbers with commas.
    3. Annotate each player row with per-attack damage, damage tier,
       ranking medal, and AFK status.
    4. Append a Raid Estimate block showing attacks needed, regen time,
       and observed activity rate.
    5. Save raid history to the database.

    Returns the (possibly modified) title, description, and footer tuple.
    """
    boss_hp: list[tuple[str, str]] = []
    afk_player: list = []

    # ── Strip boilerplate estimate lines from original bot ────────────────────
    embed_description = await definitions.mask_single_underscores(embed_description)
    embed_description = re.sub(
        r"[^\n]*(Est\. Completion Time:|Current Status:|Party Avg\.? Damage:|Avg Required Damage[^:]*:|Min\. Players Required:|Live Raid Metrics:|Your Avg\.? Damage:)[^\n]*\n?",
        "",
        embed_description,
    )
    desc = embed_description.replace(",", "")

    # ── Aggregate party-wide stats ────────────────────────────────────────────
    energy_values  = [int(x) for x in re.findall(r"Energy:\s*(\d+)/", desc)]
    damage_strings = re.findall(r"Total Damage:\s*(\d+)", desc)
    attack_values  = [int(x) for x in re.findall(r"Total Attacks:\s*(\d+)", desc)]

    total_energy  = sum(energy_values)
    total_damage  = sum(int(d) for d in damage_strings)
    total_attacks = sum(attack_values)
    sorted_damage_list = sorted(damage_strings, key=int, reverse=True)

    # ── Boss HP bar ───────────────────────────────────────────────────────────
    hp_match = re.search(r"\*\*(-?\d+)\s*/\s*(\d+)\*\*", desc)
    if hp_match:
        current_hp, max_hp = hp_match.group(1), hp_match.group(2)
        boss_hp.append((current_hp, max_hp))
        hp_bar = await definitions.build_boss_hp_bar(current_hp, max_hp)
        desc = _replace_hp_bar_emojis(desc, hp_bar)
        desc = desc.replace("❤️", "❤️")
        desc = desc.replace(
            f"{int(current_hp)} / {int(max_hp)}",
            f"{int(current_hp):,} / {int(max_hp):,}",
        )

    # ── Footer: replace generic hint with drop-range threshold ───────────────
    if boss_hp and embed_footer:
        drop_threshold = int(boss_hp[-1][1]) // 10
        embed_footer = embed_footer.replace(
            "Type .rd battle when you have Energy!",
            f"Deal {drop_threshold:,} Damage to reach Drop range!",
        )
    else:
        drop_threshold = 0

    # ── Player count & lobby damage multiplier ────────────────────────────────
    player_match = re.search(r"(\d)/(\d)", embed_footer)
    # 2-player lobbies deal ~2.45× more damage per attack than solo
    lobby_multiplier = 2.45 if (player_match and player_match.group(2) == "2") else 1.0

    # ── Boss rarity & talent multipliers ─────────────────────────────────────
    boss_name_match = re.search(
        r"__(Common|Uncommon|Rare|Super Rare|Ultra Rare)__\sLevel\s\d+\s(.+)\s\[Evo 3]",
        desc,
    )
    rarity_scaling    = _get_rarity_scaling(boss_name_match.group(1)) if boss_name_match else 1.0
    talent_multiplier = 1.0
    if boss_name_match:
        boss_data = await cards.get_card_data_by_name(boss_name_match.group(2))
        if boss_data:
            talent_multiplier = _get_talent_multiplier(boss_data[0]["card_talent"], rarity_scaling)

    # ── Difficulty multiplier ─────────────────────────────────────────────────
    difficulty_match = re.findall(r"\[\w+]", desc)
    difficulty_multiplier = (
        _get_difficulty_multiplier(difficulty_match[0].strip("[]"))
        if difficulty_match else 1.0
    )

    # Combined threshold divisor used to classify per-attack damage quality
    combined_mult = difficulty_multiplier * talent_multiplier * lobby_multiplier

    # ── Per-player row annotation ─────────────────────────────────────────────
    player_pattern = (
        r"\((\d+)\)\s*\|\s*Level\s*(\d+)\s*\|\s*Power Level:\s*(\d+)\**\n"
        r"Energy:\s*(\d+)\s*\/\s*\d+\n"
        r"Total Damage:\s*(\d+)\n"
        r"Total Attacks:\s*(\d+)\n"
        r"Last Attack:\s*(\d+)"
    )
    for match in re.findall(player_pattern, desc):
        player_id, player_level, player_power = match[0], match[1], match[2]
        player_energy, player_damage_str     = match[3], match[4]
        player_attacks_str, player_afk_str   = match[5], match[6]
        player_attacks = int(player_attacks_str)

        try:
            damage_per_attack = int(player_damage_str) // player_attacks
        except ZeroDivisionError:
            damage_per_attack = 0

        damage_percent = round(100 / int(max_hp) * int(player_damage_str), 2) if boss_hp else 0.0

        # Classify damage quality relative to boss HP thresholds
        hp_int = int(max_hp) if boss_hp else 1
        if   damage_per_attack >= (hp_int // 100)           * combined_mult: damage_tier = "MAX "
        elif damage_per_attack >= (hp_int // 100 // 1.25)   * combined_mult: damage_tier = "Great "
        elif damage_per_attack >= (hp_int // 100 // 1.5)    * combined_mult: damage_tier = "Good "
        elif damage_per_attack >= (hp_int // 100 // 2)      * combined_mult: damage_tier = "Average "
        elif player_attacks == 0:                                             damage_tier = "waiting for attacks "
        else:                                                                 damage_tier = "Leeching "

        ranking_emote = _assign_ranking_emote(player_damage_str, sorted_damage_list, player_attacks, desc)

        threshold_status = "✅" if int(player_damage_str) >= drop_threshold else "❌"
        afk_text         = "**[AFK]**" if int(player_afk_str) >= 30 else " "

        enhanced_row = (
            f"\nEnergy: {player_energy}/25"
            f"\nTotal Damage: {int(player_damage_str):,} ({damage_per_attack:,}) ({damage_percent}%)"
            f"\nDamage Status: {damage_tier}{ranking_emote}"
            f"\nTotal Attacks: {player_attacks_str}"
            f"\nLast Attack: {player_afk_str}m ago {afk_text}"
            f"\nThreshold Status: {threshold_status}"
        )
        old_row = (
            f"({player_id}) | Level {player_level} | Power Level: {player_power}**\n"
            f"Energy: {player_energy}/25\n"
            f"Total Damage: {player_damage_str}\n"
            f"Total Attacks: {player_attacks_str}\n"
            f"Last Attack: {player_afk_str}m ago"
        )
        desc = desc.replace(
            old_row,
            f"({player_id}) | Level {player_level} | Power Level: {player_power}**" + enhanced_row,
        )

    embed_description = desc

    # ── Raid history DB update ────────────────────────────────────────────────
    history_desc = embed_description.replace("\\", "").replace(",", "")
    timer_match  = re.findall(r"<t:(\d+):R>", embed_title)
    code_match   = re.findall(r"\|\s(\d+)\s\|", embed_footer)
    # guild_id is the stable key; footer code kept for DB unique_code only
    raid_code    = guild_id if guild_id else (code_match[0] if code_match else None)

    boss_data_pattern = (
        r"__(?:(Uncommon|Rare|Super Rare|Ultra Rare))__\sLevel"
        r"\s(\d+)\s([\w\W\d\D]+)\s\[Evo 3\]"
        r"\s\[(?:(Easy|Medium|Hard|Impossible))\]"
    )
    player_data_pattern = (
        r"\*\*#(\d+)\s\|\s([\w._\\]+)\s\((\d+)\)\s\|\sLevel\s(\d+)\s\|\s"
        r"Power Level:\s(\d+)\*\*\nEnergy:\s\d+\/\d+\nTotal Damage:\s(\d+)\s\((\d+)\)\s\((\d+\.\d{2})(?=%)\%\)\n"
        r"Damage Status:\s([\w\s]+)\s(?::first_place:|:second_place:|:third_place:)?\n"
        r"Total Attacks:\s(\d+)\nLast Attack:\s(\d+)m ago"
    )
    boss_history   = re.findall(boss_data_pattern, history_desc)
    player_history = re.findall(player_data_pattern, history_desc)

    if code_match and timer_match:
        unique_code = code_match[0] + timer_match[0]
        await players.update_raid_history_for_players_by_player_data(
            player_history, boss_history, unique_code
        )

    # ── Raid estimate block ───────────────────────────────────────────────────
    now = time.time()
    attacks_needed   = 0
    regen_str        = "N/A"
    regen_unix       = ""
    regen_afk_str    = "N/A"
    regen_afk_unix   = ""
    activity_str     = "N/A (first observation)"
    activity_unix    = ""
    observed_rate    = None
    count_afk        = 0

    if total_attacks > 0:
        average_damage = total_damage / total_attacks
        if average_damage > 0 and boss_hp:
            attacks_needed = int(int(boss_hp[-1][0]) / average_damage)

        afk_count_match = re.findall(r"\[AFK\]", embed_description)
        afk_player.extend(afk_count_match)
        count_afk = len(afk_player)

        # Observed attack rate from previous snapshot in raid_tracker
        if raid_code:
            prev = raid_tracker.get(raid_code)
            if prev:
                delta_attacks = total_attacks - prev["last_attacks"]
                delta_minutes = (now - prev["last_time"]) / 60
                if delta_attacks > 0 and delta_minutes > 0:
                    observed_rate = delta_attacks / delta_minutes
                elif prev.get("observed_rate"):
                    observed_rate = prev["observed_rate"]

        # Regen estimate (energy-based formula)
        if player_match:
            regen_str, regen_unix = await definitions.calculate_end_time(
                attacks_needed, total_energy, player_match.group(1), count_afk
            )

        # Separate regen estimate excluding AFK players
        if count_afk > 0:
            energy_excl_afk = total_energy - (25 * count_afk)
            regen_afk_str, regen_afk_unix = await definitions.calculate_end_time_including_afk(
                attacks_needed, energy_excl_afk, player_match.group(1), count_afk
            )

        # Activity estimate from observed rate
        if observed_rate and attacks_needed > 0:
            remaining_minutes = attacks_needed / observed_rate
            activity_str  = await definitions.convert_to_hours_minutes(int(remaining_minutes))
            activity_unix = f"[<t:{int(now + remaining_minutes * 60)}:T>]"

    # Save current snapshot for next update's rate calculation
    if raid_code:
        raid_tracker[raid_code] = {
            "last_time":     now,
            "last_attacks":  total_attacks,
            "observed_rate": observed_rate,
        }

    # Build estimates text block
    if total_attacks == 0:
        estimates_block = (
            "\n\n**─── Raid Estimate ───**\n"
            "⚔️ Attacks needed: **—**\n"
            "⏱️ Regen: *waiting for attacks*\n"
            "🏃 Activity: *waiting for attacks*"
        )
    else:
        rate_label = f" `{observed_rate:.2f} atk/min`" if observed_rate else ""
        activity_display = (
            f"**{activity_str}** {activity_unix}"
            if observed_rate and attacks_needed > 0
            else "N/A *(first observation)*"
        )
        estimates_block = (
            f"\n\n**─── Raid Estimate ───**\n"
            f"⚔️ Attacks needed: **{attacks_needed}**\n"
            f"⏱️ Regen: **{regen_str}** {regen_unix}"
        )
        if count_afk > 0:
            estimates_block += f"\n⏱️ Regen (excl. AFK): **{regen_afk_str}** {regen_afk_unix}"
        estimates_block += f"\n🏃 Activity: {activity_display}{rate_label}"

    # Inject estimates after the HP bar's right-end emoji
    _hp_right_green = "<:hp_right_head_green:1503375620183294092>"
    _hp_right_empty = "<:hp_right_head_empty:1503378097054023760>"
    new_desc = embed_description.replace(_hp_right_green, _hp_right_green + estimates_block, 1)
    if new_desc == embed_description:
        new_desc = embed_description.replace(_hp_right_empty, _hp_right_empty + estimates_block, 1)
    embed_description = new_desc

    return embed_title, embed_description, embed_footer


async def raid_lobby_waiting_room(
    embed_title: str, embed_description: str, embed_footer: str
) -> tuple[str, str, str]:
    """
    Augment a Raid Lobby Timer (waiting room) embed.

    Rebuilds the boss HP bar with the custom format and rewrites the footer
    to show the join command and current player count.

    Returns the (possibly modified) title, description, and footer tuple.
    """
    # ── Clean description ─────────────────────────────────────────────────────
    embed_description = await definitions.mask_single_underscores(embed_description)
    embed_description = re.sub(
        r"[^\n]*(Est\. Completion Time:|Current Status:|Party Avg\.? Damage:|Avg Required Damage[^:]*:|Min\. Players Required:|Live Raid Metrics:|Your Avg\.? Damage:)[^\n]*\n?",
        "",
        embed_description,
    )
    desc = embed_description.replace(",", "")

    # ── Boss HP bar ───────────────────────────────────────────────────────────
    hp_match = re.search(r"\*\*(\d+)\s*/\s*(\d+)\*\*", desc)
    if hp_match:
        current_hp, max_hp = hp_match.group(1), hp_match.group(2)
        hp_bar = await definitions.build_boss_hp_bar(current_hp, max_hp)
        desc = _replace_hp_bar_emojis(desc, hp_bar)
        desc = desc.replace("❤️", "❤️")
        desc = desc.replace(
            f"{int(current_hp)} / {int(max_hp)}",
            f"{int(current_hp):,} / {int(max_hp):,}",
        )
        embed_description = desc

    # ── Footer: show join command ─────────────────────────────────────────────
    numbers = re.findall(r"(\d+)", embed_footer)
    # numbers[0]=current players, numbers[1]=max players, numbers[2]=raid code
    embed_footer = f".rd join {numbers[2]} | {numbers[0]} / {numbers[1]} Players in Raid Party"

    return embed_title, embed_description, embed_footer


# ─── Battle / team helpers ────────────────────────────────────────────────────

class EmbedProxy:
    """Lightweight wrapper around an embed field value for string coercion."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


async def raid_team_check(proxy_embed_field_1, proxy_embed_field_2) -> int:
    """
    Determine which battle team (1 or 2) has the advantage.

    Compares element emojis and power levels from two embed fields that
    represent each team's card lineup. Returns 1 if team 1 has the advantage
    (or is the weaker team that needs more players), 2 otherwise.
    """
    null = "<:Null:1329746549382582285>"
    emoji_list = ["☀", "🌙", "⛰", "🍃", "🔥", "💧", "⚡", "✨", null]

    field_1 = str(EmbedProxy(proxy_embed_field_1))
    field_2 = str(EmbedProxy(proxy_embed_field_2))
    clean_1 = field_1.replace(",", "")
    clean_2 = field_2.replace(",", "")

    power_levels_1 = re.findall(r"\*\*PL:\*\* (\d+)", clean_1)

    # Team 2 has a null card — team 1 wins by default
    if null in field_2:
        return 1

    emojis_1 = [ch for ch in field_1 if ch in emoji_list]
    emojis_2 = [ch for ch in field_2 if ch in emoji_list]

    effectiveness = 0
    count_emojis_1 = len(emojis_1)

    # Null in team 1 counts as one extra element slot
    if null in clean_1:
        count_emojis_1 += 1
        effectiveness += 1

    # Very small teams: single-card team 1 is disadvantaged
    if count_emojis_1 == 1:
        return 2
    if count_emojis_1 == 2:
        return 1 if int(power_levels_1[0]) >= 1100 else 2

    # Full team: compare element match-ups
    for e1 in emojis_1:
        for e2 in emojis_2:
            effectiveness += await definitions.element_effectiveness(e1, e2)

    return 1 if effectiveness >= 3 else 2


# ─── UI components ────────────────────────────────────────────────────────────

class DeleteButtonView(View):
    """A View containing a single red trash-can button that deletes the message."""

    def __init__(self):
        super().__init__(timeout=180)
        self.delete_button = Button(label="", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.delete_button.callback = self.delete_callback
        self.add_item(self.delete_button)

    async def delete_callback(self, interaction: discord.Interaction):
        """Delete the message this view is attached to."""
        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass


# ─── Player stat commands ─────────────────────────────────────────────────────

async def player_gold_and_rubies_command(message) -> tuple[str, str]:
    """
    Parse a gold or clan-rubies balance message and update the database.

    Detects whether the message reports gold or Clan Rubies, extracts the
    player name and amount, updates the DB, and returns a display string
    with the new balance and gain/loss (for gold) or purchase analysis
    (for rubies).

    Returns a (player_name, embed_text) tuple.
    """
    if "gold" in message.content:
        gold_match = re.search(
            r"\*\*(.*)\*\*\scurrently has\s\*\*([\d,]+)\*\*\sgold <a:gold:1219941344450052187>",
            message.content,
        )
        player_name  = gold_match.group(1)
        player_gold  = int(gold_match.group(2).replace(",", ""))

        old_gold = await players.update_player_gold_by_player_name(player_name, player_gold)
        if old_gold == "player not found":
            return player_name, "player not found"

        delta = player_gold - int(old_gold)
        change_label = f"+{delta:,} gain." if delta >= 0 else f"{delta:,} loss."
        embed_text = f"**{player_gold:,}** {gold_emote}\n**{change_label}**"
        return player_name, embed_text

    elif "Clan Rubies" in message.content:
        rubies_match = re.search(
            r"\*\*(.*)\*\*\scurrently has\s\*\*([\d,]+)\*\*\sClan Rubies <:CLAN_RUBIES:713100255536742450>",
            message.content,
        )
        player_name   = rubies_match.group(1)
        player_rubies = int(rubies_match.group(2).replace(",", ""))

        result = await players.update_player_rubies_by_player_name(player_name, player_rubies)
        if result == "player not found":
            return player_name, "player not found"

        sr_cost = 20_000
        ur_cost = 200_000

        if player_rubies != 0:
            till_sr = max(0, sr_cost - (player_rubies % sr_cost))
            till_ur = max(0, ur_cost - (player_rubies % ur_cost))
            can_buy_sr = player_rubies // sr_cost
            can_buy_ur = player_rubies // ur_cost
            embed_text = (
                f"{player_rubies:,} {rubies_emote}\n\n"
                f"{till_sr:,} {rubies_emote} till next {super_rare_1}{super_rare_2}\n"
                f"{till_ur:,} {rubies_emote} till next {ultra_rare_1}{ultra_rare_2}\n\n"
                f"Currently purchasable {super_rare_1}{super_rare_2}: {can_buy_sr:,}\n"
                f"Currently purchasable {ultra_rare_1}{ultra_rare_2}: {can_buy_ur:,}"
            )
        else:
            embed_text = (
                f"0 {rubies_emote}\n\n"
                f"{sr_cost:,} {rubies_emote} till next {super_rare_1}{super_rare_2}\n"
                f"{ur_cost:,} {rubies_emote} till next {ultra_rare_1}{ultra_rare_2}\n\n"
                f"Currently purchasable {super_rare_1}{super_rare_2}: 0\n"
                f"Currently purchasable {ultra_rare_1}{ultra_rare_2}: 0"
            )
        return player_name, embed_text


# ─── Donation & profile trackers ─────────────────────────────────────────────

async def clan_donation_tracker(embed_description: str, message) -> None:
    """
    Parse a clan donation embed and update guild donation records.

    Also tracks weekly donations when the message is posted in the designated
    weekly donation channel and the amount is a whole multiple of
    WEEKLY_DONATION_AMOUNT.
    """
    clean_desc  = embed_description.replace(",", "")
    player_data = re.findall(
        r"Summoner \*\*(.*)\*\* you have donated \*\*(\d+)\*\* Gold", clean_desc
    )
    if not player_data:
        await message.reply("Could not parse donation information from message.")
        return

    player_name, amount_str = player_data[0]
    donate_amount = int(amount_str)

    try:
        updated_guilds = await guilds.update_donation_amount_by_player_name_in_guilds(
            player_name, donate_amount, "auto"
        )
        view = user_commands_slash_definition_v2.DonationResultLayoutView(
            player_name, donate_amount, updated_guilds
        )
        await message.reply(view=view)
    except Exception as e:
        error_view = user_commands_slash_definition_v2.DonationResultLayoutView(
            player_name, donate_amount, []
        )
        await message.reply(
            f"<a:cross:1380797973373521962> Error while processing donation: {e}",
            view=error_view,
        )

    # ── Weekly donation tracking (kênh 1) ────────────────────────────────────
    if message.channel.id == WEEKLY_DONATION_CHANNEL_ID:
        if donate_amount != 50_000 and donate_amount % WEEKLY_DONATION_AMOUNT == 0:
            weeks = donate_amount // WEEKLY_DONATION_AMOUNT
            try:
                discord_id  = await weekly_donations.get_discord_id_by_player_name(player_name)
                total_weeks = await weekly_donations.create_or_update_tracking(
                    player_name, discord_id, message.channel.id, weeks
                )
                await message.add_reaction("✅")
                ping_text = f"<@{discord_id}>" if discord_id else f"**{player_name}**"
                await message.reply(
                    f"✅ Ghi nhận **{donate_amount:,}** gold ({weeks} tuần) cho {ping_text}. "
                    f"Tổng: **{total_weeks} tuần** — sẽ được nhắc sau {total_weeks} tuần.",
                    mention_author=False,
                )
            except Exception as e:
                print(f"[WEEKLY DONATION] Error tracking {player_name}: {e}")

    # ── Monthly 50k donation tracking (kênh 2) ───────────────────────────────
    # Chấp nhận bội số của 50k: 50k=1 lần, 100k=2 lần, v.v.
    if message.channel.id == MONTHLY_DONATION_CHANNEL_ID and donate_amount % 50_000 == 0:
        times = donate_amount // 50_000
        try:
            discord_id = await weekly_donations.get_discord_id_by_player_name(player_name)
            monthly, alltime = await channel_donations.record_donation(
                MONTHLY_DONATION_CHANNEL_ID, player_name, discord_id, count=times
            )
            monthly_total, alltime_total = await channel_donations.get_channel_totals(
                MONTHLY_DONATION_CHANNEL_ID
            )
            ping_text = f"<@{discord_id}>" if discord_id else f"**{player_name}**"
            times_label = f"{times} lần ({donate_amount:,} gold)" if times > 1 else "1 lần"
            await message.add_reaction("✅")
            await message.reply(
                f"✅ Ghi nhận {times_label} cho {ping_text}\n"
                f"Tháng này: **{monthly} lần** | All-time: **{alltime} lần**\n"
                f"Tổng kênh tháng này: **{monthly_total}** | All-time: **{alltime_total}**",
                mention_author=False,
            )
        except Exception as e:
            print(f"[CHANNEL DONATION] Error tracking {player_name}: {e}")


async def profile_tracker(embed_fields, embed_footer: str) -> None:
    """
    Extract premium days remaining from a profile embed and update the database.

    Looks for a field named "Premium Days" among the embed fields and writes
    the value to the player record identified by the Summoner ID in the footer.
    """
    for field in embed_fields:
        if "Premium Days" not in field.name:
            continue
        try:
            player_id        = int(embed_footer.replace("Summoner ID: ", ""))
            premium_days     = int(field.value)
        except ValueError:
            return
        try:
            await players.update_player_premium_days_left_by_discord_id(player_id, premium_days)
        except Exception:
            pass
        break  # only one "Premium Days" field expected
