import re
import time
from fractions import Fraction
from decimal import Decimal, ROUND_CEILING
from math import floor


async def mask_single_underscores(text):
    return re.sub(r'(?<!_)_(?!_)', '\\_', text)


async def calculate_end_time(total_attacks_needed, current_energy, current_player_number, count_afk_player, attack_energy_cost=5, energy_regen_rate=2, regen_interval=2):
    total_energy_needed = total_attacks_needed * attack_energy_cost
    energy_needed = int(total_energy_needed) - current_energy
    if energy_needed <= 0:
        return "ending soon", ""
    if current_player_number == count_afk_player:
        return "At least one player has to be active.", ""
    try:
        regen_time_needed = (energy_needed / (energy_regen_rate * (int(current_player_number) - int(count_afk_player))) * regen_interval)
    except ZeroDivisionError:
        return "lobby afk", ""
    remaining_minutes = max(0, regen_time_needed)
    if remaining_minutes < 5:
        return "ending soon", ""
    else:
        current_unix_time = int(time.time())
        additional_seconds = remaining_minutes * 60
        final_unix_time = f"[<t:{int(current_unix_time + additional_seconds)}:T>]"
        time_converted = await convert_to_hours_minutes(int(remaining_minutes))
        return time_converted, final_unix_time


async def calculate_end_time_including_afk(total_attacks_needed, current_energy, current_player_number, count_afk_player, attack_energy_cost=5, energy_regen_rate=2, regen_interval=2):
    if current_player_number == count_afk_player:
        return "please attack", ""
    total_energy_needed = total_attacks_needed * attack_energy_cost
    energy_needed = int(total_energy_needed) - current_energy
    if energy_needed <= 0:
        return "ending soon", ""
    regen_time_needed = (energy_needed / (energy_regen_rate * int(current_player_number)) * regen_interval)
    remaining_minutes = max(0, regen_time_needed)
    if remaining_minutes < 5:
        return "ending soon", ""
    else:
        current_unix_time = int(time.time())
        additional_seconds = remaining_minutes * 60
        final_unix_time = f"[<t:{int(current_unix_time + additional_seconds)}:T>]"
        time_converted = await convert_to_hours_minutes(int(remaining_minutes))
        return time_converted, final_unix_time


async def convert_to_hours_minutes(time_in_minutes):
    hours = time_in_minutes // 60
    minutes = time_in_minutes % 60
    return f"{hours} hour(s), {minutes} minutes"


_LG = "<:hp_left_head_green:1503375587350417528>"
_MG = "<:hp_green:1503367723852501164>"
_RG = "<:hp_right_head_green:1503375620183294092>"
_LY = "<:hp_left_head_yellow:1503375545277087756>"
_MY = "<:hp_yellow:1503375563111272458>"
_RE = "<:hp_right_head_empty:1503378097054023760>"
_LR = "<:hp_left_head_red:1503375481045647362>"
_ME = "<:hp_empty:1503378081845350472>"

_HP_BAR_FULL = _LG + _MG * 8 + _RG

# Each entry: (missing_hp_ratio_threshold, bar_emoji)
# Iterated from highest to lowest; first match wins.
_HP_BAR_THRESHOLDS = [
    (0.9, _LR + _ME * 8 + _RE),
    (0.8, _LY + _MY * 1 + _ME * 7 + _RE),
    (0.7, _LY + _MY * 2 + _ME * 6 + _RE),
    (0.6, _LY + _MY * 3 + _ME * 5 + _RE),
    (0.5, _LY + _MY * 4 + _ME * 4 + _RE),
    (0.4, _LG + _MG * 4 + _ME * 4 + _RE),
    (0.3, _LG + _MG * 5 + _ME * 3 + _RE),
    (0.2, _LG + _MG * 6 + _ME * 2 + _RE),
    (0.1, _LG + _MG * 7 + _ME * 1 + _RE),
    (0.0, _LG + _MG * 8 + _RE),
]


async def build_boss_hp_bar(current_boss_hp, max_boss_hp):
    missing_boss_hp = int(max_boss_hp) - int(current_boss_hp)
    if missing_boss_hp == 0:
        return _HP_BAR_FULL
    max_hp = int(max_boss_hp)
    for threshold, emoji in _HP_BAR_THRESHOLDS:
        if missing_boss_hp > max_hp * threshold:
            return emoji
    return _HP_BAR_THRESHOLDS[-1][1]


_ELEMENT_NULL = "<:Null:1503313357426528298>"

_ELEMENT_TABLE = {
    "⚡": {"⚡": 1,  "⛰": -1, "🍃": 0,  "🔥": 0,  "💧": 2,  "🌙": 0,  "☀": 0,  "✨": 1, _ELEMENT_NULL: -0.5},
    "⛰":  {"⚡": 2,  "⛰": 1,  "🍃": -1, "🔥": 0,  "💧": 0,  "🌙": 0,  "☀": 0,  "✨": 1, _ELEMENT_NULL: -0.5},
    "🍃": {"⚡": 0,  "⛰": 2,  "🍃": 1,  "🔥": -1, "💧": 0,  "🌙": 0,  "☀": 0,  "✨": 1, _ELEMENT_NULL: -0.5},
    "🔥": {"⚡": 0,  "⛰": 0,  "🍃": 2,  "🔥": 1,  "💧": -1, "🌙": 0,  "☀": 0,  "✨": 1, _ELEMENT_NULL: -0.5},
    "💧": {"⚡": -1, "⛰": 0,  "🍃": 0,  "🔥": 2,  "💧": 1,  "🌙": 0,  "☀": 0,  "✨": 1, _ELEMENT_NULL: -0.5},
    "🌙": {"⚡": 0,  "⛰": 0,  "🍃": 0,  "🔥": 0,  "💧": 0,  "🌙": 2,  "☀": -1, "✨": 1, _ELEMENT_NULL: -0.5},
    "☀":  {"⚡": 0,  "⛰": 0,  "🍃": 0,  "🔥": 0,  "💧": 0,  "🌙": -1, "☀": 2,  "✨": 1, _ELEMENT_NULL: -0.5},
    "✨": {"⚡": 0,  "⛰": 0,  "🍃": 0,  "🔥": 0,  "💧": 0,  "🌙": 0,  "☀": 0,  "✨": 1, _ELEMENT_NULL: -0.5},
}


async def element_effectiveness(element_1, element_2):
    if element_1 == _ELEMENT_NULL:
        return 1
    return _ELEMENT_TABLE[element_1][element_2]


_ELEMENT_NULL_DB = "<:Null:1503313357426528298>"

_ELEMENT_NAME_MAP = {
    "Null":     _ELEMENT_NULL_DB,
    "Neutral":  ":sparkles:",
    "Electric": ":zap:",
    "Ground":   ":mountain:",
    "Grass":    ":leaves:",
    "Fire":     ":fire:",
    "Water":    ":droplet:",
    "Light":    ":sunny:",
    "Dark":     ":crescent_moon:",
}


async def element_converter_from_database(card_element_name):
    return _ELEMENT_NAME_MAP.get(card_element_name, "")


_SKILL_EMOJI_MAP = {
    "Lucky Coin":                  "<:Lucky_Coin:1503397077575663877>",               #done
    "Amplifier":                   "<:AMPLIFIER:1503408066966585414> ",               #done
    "Arcane Affinity":             "<:Arcane_Affinity:1503312702100209756>",          #done
    "Balancing Strike":            "<:Balancing_Strike:1503378775889412197>",         #done
    "Berserker":                   "<:Berserker:1503380628165365833>",                #done
    "Blaze":                       "<:Blaze:1503381143783870494>",                    #done
    "Blood Surge":                 "<:Blood_Surge:1503313188261859359>",              #done
    "Bloodthirster":               "<:Bloodthirster:1503314241372033035>",            #done
    "Breaker":                     "<:Breaker:1503381473657360464>",                  #done
    "Brutality":                   "<:Brutality:1503382068216991754>",                #done
    "Celestial Blessing":          "<:Celestial_Blessing:1503383124271304764>",       #done
    "Celestial Influence":         "<:Celestial_Influence:1503408225339310111>",      #done
    "Cursed":                      "<:Cursed:1503383448499523784>",                   #done
    "Devour":                      "<:Devour:1503383579978108959>",                   #done
    "Dexterity Drive":             "<:Dexterity_Drive:1503383848652636190>",          #done
    "Divine Blessing":             "<:Divine_Blessing:1503398806484418691>",          #done
    "Dominance":                   "<:Dominance:1503398788558094516>",                #done
    "Double-edged Strike":         "<:Double_edged_Strike:1503399030217248888>",      #done
    "Elemental Drain":             "<:Elemental_Drain:1503384401055186944>",          #done
    "Elemental Manipulation":      "<:Elemental_Manipulation:1503384884134023289>",   #done
    "Elemental Strike":            "<:Elemental_Strike:1503313097199194192>",         #done
    "Endurance":                   "<:Endurance:1503390994979229847>",                #done
    "Executioner":                 "<:Executioner:1503385327853764760>",              #done
    "Foul Play":                   "<:Foul_Play:1503385750224502814>",                #done
    "Vengeance":                   "<:Vengeance:1503392342630072390>",                #done
    "Yin Yang":                    "<:Yin_Yang:1503313229751783596>",                 #done
    "Offensive Stance":            "<:Offensive_Stance:1503397270991933440>",         #done
    "Overload":                    "<:Overload:1503397302537031893>",                 #done
    "Pain For Power":              "<:Pain_For_Power:1503397361874112674>",           #done
    "Paralysis":                   "<:Paralysis:1503389270809907332>",                #done
    "Poison":                      "<:Poison:1503396280305455144>",                   #done
    "Precision":                   "<:Precision:1503396747752374395>",                #done
    "Protector":                   "<:Protector:1503397455981576242>",                #done
    "Recoil":                      "<:Recoil:1503397132231512106>",                   #done
    "Life Sap":                    "<:Life_Sap:1503312924410908774>",                 #done
    "Reflector":                   "<:Reflector:1503312970388869191>",                #done
    "Regeneration":                "<:Regeneration:1503140091969929446>",             #done
    "Rejuvenation":                "<:Rejuvenation:1503313451043520583>",             #done
    "Restricted Instinct":         "<:Restricted_Instinct:1503391863368056942>",      #done
    "Reversion":                   "<:Reversion:1503313135287668867>",                #done
    "Rising Resolve":              "<:Rising_Resolve:1503313022586851328>",           #done
    "Smokescreen":                 "<:Smokescreen:1503388127367266364>",              #done
    "Soul Stealer":                "<:Soul_Stealer:1503388387283959858>",             #done
    "Temporal Rewind":             "<:Temporal_Rewind:1503388665928224798>",          #done
    "Time Attack":                 "<:Time_Attack:1503140758302232576>",              #done
    "Time Bomb":                   "<:Time_Bomb:1503388871914819657>",                #done
    "Trick Room":                  "<:Trick_Room:1503397702342545418>",               #done
    "Transformation":              "<:Transformation:1503389480567050240>",           #done
    "Ultimate Combo":              "<:Ultimate_Combo:1503389940669612153>",           #done
    "Undying Will":                "<:Undying_Will:1503390242588200970>",             #done
    "Unlucky Coin":                "<:Unlucky_Coin:1503397771384979476>",             #done
    "Omniscient Hack":             "<:Omniscient_Hack:1503397245251485798>",          #done
    "Miracle Injection":           "<:Miracle_Injection:1503313331858178174>",        #done
    "Mana Reaver":                 "<:Mana_Reaver:1503400009666924675>",              #done
    "Lethal Clarity":              "<:Lethal_Clarity:1503399712785567786>",           #done
    "Grievous Limiter":            "<:Grievous_Limiter:1503391367328436405>",         #done
    "Underdog":                    "<:Underdog:1503400563734351973>",                 #done
    "Freeze":                      "<:Freeze:1503385910983655618>",                   #done
    "Evasion":                     "<:Evasion:1503385050815660142>",                  #done
    "Atmospheric Acceleration":    "<:ATMOSPHERIC_ACCELERATION:1503396632102965268>", #done
    "Aegis":                       "<:Aegis:1503379066600816710>",                    #done
    "Divine Fortune":              "<:DivineFortune:1503314557597257808>",            #done
    "Final Verdict":               "<:Final_Verdict:1503405518105088010>",            #done
}


async def skill_converter_from_database(card_skill_name):
    return _SKILL_EMOJI_MAP.get(card_skill_name, "")


_RARITY_CONFIG = {
    "Base":       (1.0, 1),
    "Common":     (1.2, 20),
    "Uncommon":   (1.4, 30),
    "Rare":       (1.6, 40),
    "Super Rare": (1.8, 50),
    "Ultra Rare": (2.0, 60),
}


async def calc_card_stats(card_hp, card_atk, card_def, card_spd, rarity, evolution, ascension, familiarity, clan_hp, clan_atk, clan_def, clan_spd):
    rarity_scaling, card_level = _RARITY_CONFIG.get(rarity, (1.0, 20))
    calc_card_hp = floor(int(card_hp) * rarity_scaling * (1 + 0.005 * card_level) * (0.85 + (0.15 * evolution)) * (1 + (0.05 * ascension)) * (1 + (familiarity / 100)) * (1 + (clan_hp / 100)))
    calc_card_atk = floor(int(card_atk) * rarity_scaling * (1 + 0.005 * card_level) * (0.85 + (0.15 * evolution)) * (1 + (0.05 * ascension)) * (1 + (familiarity / 100)) * (1 + (clan_atk / 100)))
    calc_card_def = floor(int(card_def) * rarity_scaling * (1 + 0.005 * card_level) * (0.85 + (0.15 * evolution)) * (1 + (0.05 * ascension)) * (1 + (familiarity / 100)) * (1 + (clan_def / 100)))
    calc_card_spd = floor(int(card_spd) * rarity_scaling * (1 + 0.005 * card_level) * (0.85 + (0.15 * evolution)) * (1 + (0.05 * ascension)) * (1 + (familiarity / 100)) * (1 + (clan_spd / 100)))
    return calc_card_hp, calc_card_atk, calc_card_def, calc_card_spd


async def calc_card_stats_compare(card_hp, card_atk, card_def, card_spd, rarity, card_level, evolution, ascension, familiarity, clan_hp, clan_atk, clan_def, clan_spd):
    rarity_scaling = _RARITY_CONFIG.get(rarity, (1.0, None))[0]
    calc_card_hp = floor(int(card_hp) * rarity_scaling * (1 + 0.005 * card_level) * (0.85 + (0.15 * evolution)) * (1 + (0.05 * ascension)) * (1 + (familiarity / 100)) * (1 + (clan_hp / 100)))
    calc_card_atk = floor(int(card_atk) * rarity_scaling * (1 + 0.005 * card_level) * (0.85 + (0.15 * evolution)) * (1 + (0.05 * ascension)) * (1 + (familiarity / 100)) * (1 + (clan_atk / 100)))
    calc_card_def = floor(int(card_def) * rarity_scaling * (1 + 0.005 * card_level) * (0.85 + (0.15 * evolution)) * (1 + (0.05 * ascension)) * (1 + (familiarity / 100)) * (1 + (clan_def / 100)))
    calc_card_spd = floor(int(card_spd) * rarity_scaling * (1 + 0.005 * card_level) * (0.85 + (0.15 * evolution)) * (1 + (0.05 * ascension)) * (1 + (familiarity / 100)) * (1 + (clan_spd / 100)))
    return calc_card_hp, calc_card_atk, calc_card_def, calc_card_spd
