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


_HP_BAR_FULL = (
    "<:hp_g_l:1325526952462778368><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
    "<:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
    "<:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
    "<:hp_g_r:1325526982938595489>"
)

# Each entry: (missing_hp_ratio_threshold, bar_emoji)
# Iterated from highest to lowest; first match wins.
_HP_BAR_THRESHOLDS = [
    (0.9, ("<:hp_r_l:1325527025062117586><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_r:1325527015381663754>")),
    (0.8, ("<:hp_y_l:1325527035044560907><:hp_y_m:1325527047405310022><:hp_b_m:1325526996612022322>"
           "<:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_r:1325527015381663754>")),
    (0.7, ("<:hp_y_l:1325527035044560907><:hp_y_m:1325527047405310022><:hp_y_m:1325527047405310022>"
           "<:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_r:1325527015381663754>")),
    (0.6, ("<:hp_y_l:1325527035044560907><:hp_y_m:1325527047405310022><:hp_y_m:1325527047405310022>"
           "<:hp_y_m:1325527047405310022><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_r:1325527015381663754>")),
    (0.5, ("<:hp_y_l:1325527035044560907><:hp_y_m:1325527047405310022><:hp_y_m:1325527047405310022>"
           "<:hp_y_m:1325527047405310022><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_r:1325527015381663754>")),
    (0.4, ("<:hp_g_l:1325526952462778368><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
           "<:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295><:hp_b_m:1325526996612022322>"
           "<:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_r:1325527015381663754>")),
    (0.3, ("<:hp_g_l:1325526952462778368><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
           "<:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
           "<:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_r:1325527015381663754>")),
    (0.2, ("<:hp_g_l:1325526952462778368><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
           "<:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
           "<:hp_g_m:1325526971995787295><:hp_b_m:1325526996612022322><:hp_b_m:1325526996612022322>"
           "<:hp_b_r:1325527015381663754>")),
    (0.1, ("<:hp_g_l:1325526952462778368><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
           "<:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
           "<:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295><:hp_b_m:1325526996612022322>"
           "<:hp_b_r:1325527015381663754>")),
    (0.0, ("<:hp_g_l:1325526952462778368><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
           "<:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
           "<:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295><:hp_g_m:1325526971995787295>"
           "<:hp_b_r:1325527015381663754>")),
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


_ELEMENT_NULL = "<:Null:1329746549382582285>"

_ELEMENT_TABLE = {
    "⚡": {"⚡": 1,  "⛰": -1, "🍃": 0,  "🔥": 0,  "💧": 2,  "🌙": 0,  "☀": 0,  "✨": 1, _ELEMENT_NULL: -0.5},
    "⛰": {"⚡": 2,  "⛰": 1,  "🍃": -1, "🔥": 0,  "💧": 0,  "🌙": 0,  "☀": 0,  "✨": 1, _ELEMENT_NULL: -0.5},
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


_ELEMENT_NULL_DB = "<:NULL:1338512039156645992>"

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
    "Lucky Coin":                  "<:Lucky_Coin:1503140731873919107>",               #done
    "Amplifier":                   "<:AMPLIFIER:1335617081013440573>",
    "Arcane Affinity":             "<:Arcane_Affinity:1335617073505636372>",
    "Balancing Strike":            "<:Balancing_Strike:1503134979851292814>",          #done
    "Berserker":                   "<:Berserker:1503151540792332458>",                 #done
    "Blaze":                       "<:Blaze:1503151560228601876>",                     #done
    "Blood Surge":                 "<:Blood_Surge:1335617034632953949>",
    "Bloodthirster":               "<:Bloodthirster:1335617024134610944>",
    "Breaker":                     "<:Breaker:1503151656466907136>",                   #done
    "Brutality":                   "<:Brutality:1503151583066718389>",                 #done
    "Celestial Blessing":          "<:Celestial_Blessing:1503140689959976980>",        #done
    "Celestial Influence":         "<:Celestial_Influence:1335616977707733084>",
    "Cursed":                      "<:Cursed:1503151604709462186>",                    #done
    "Devour":                      "<:Devour:1503151621029363853>",                    #done
    "Dexterity Drive":             "<:Dexterity_Drive:1503152073200373780>",           #done
    "Divine Blessing":             "<:Divine_Blessing:1335616933323608125>",
    "Dominance":                   "<:Dominance:1335616923668451368>",
    "Double-edged Strike":         "<:Double_edged_Strike:1335616913484677231>",
    "Elemental Drain":             "<:Elemental_Drain:1503152871149932634>",           #done
    "Elemental Manipulation":      "<:Elemental_Manipulation:1503152791797895379>",    #done
    "Elemental Strike":            "<:Elemental_Strike:1335616878931873822>",
    "Endurance":                   "<:Endurance:1335616869138169856>",
    "Executioner":                 "<:Executioner:1503152379749728409>",               #done
    "Foul Play":                   "<:Foul_Play:1503152361030422659>",                 #done
    "Vengeance":                   "<:Vengeance:1335616408347873283>",
    "Yin Yang":                    "<:Yin_Yang:1335616388567531661>",
    "Offensive Stance":            "<:Offensive_Stance:1335616767300468846>",
    "Overload":                    "<:Overload:1503139900797489252>",                  #done
    "Pain For Power":              "<:Pain_For_Power:1503154402884845730>",            #done
    "Paralysis":                   "<:Paralysis:1335616727312109589>",
    "Poison":                      "<:Poison:1503140041038495847>",                    #done
    "Precision":                   "<:Precision:1503151684090859710>",                 #done
    "Protector":                   "<:Protector:1503151721487011931>",                 #done
    "Recoil":                      "<:Recoil:1503151480365121730>",                    #done
    "Life Sap":                    "<:Life_Sap:1335616663382528091>",
    "Reflector":                   "<:Reflector:1335616644092919879>",
    "Regeneration":                "<:Regeneration:1503140091969929446>",              #done
    "Rejuvenation":                "<:Rejuvenation:1335616621724831876>",
    "Restricted Instinct":         "<:Restricted_Instinct:1335616611045998705>",
    "Reversion":                   "<:Reversion:1335616600602316881>",
    "Rising Resolve":              "<:Rising_Resolve:1335616590577926225>",
    "Smokescreen":                 "<:Smokescreen:1335616580318658592>",
    "Soul Stealer":                "<:Soul_Stealer:1335616569694359603>",
    "Temporal Rewind":             "<:Temporal_Rewind:1335616556058804255>",
    "Time Attack":                 "<:Time_Attack:1503140758302232576>",               #done
    "Time Bomb":                   "<:Time_Bomb:1335616525352308839>",
    "Trick Room":                  "<:Trick_Room:1503140789310718002>",                #done
    "Transformation":              "<:Transformation:1335616512152567901>",
    "Ultimate Combo":              "<:Ultimate_Combo:1335616472709333023>",
    "Undying Will":                "<:Undying_Will:1335616441176555580>",
    "Unlucky Coin":                "<:Unlucky_Coin:1503140641494794302>",              #done
    "Omniscient Hack":             "<:Omniscient_Hack:1503152467687243796>",           #done
    "Miracle Injection":           "<:Miracle_Injection:1335616777895284776>",
    "Mana Reaver":                 "<:Mana_Reaver:1335616788196753408>",
    "Lethal Clarity":              "<:Lethal_Clarity:1503152260073394236>",            #done
    "Grievous Limiter":            "<:Grievous_Limiter:1335616818483691580>",
    "Underdog":                    "<:Underdog:1336428564739915837>",
    "Freeze":                      "<:Freeze:1503151744832639078>",                    #done
    "Evasion":                     "<:Evasion:1503140708859646103>",                   #done
    "Atmospheric Acceleration":    "<:ATMOSPHERIC_ACCELERATION:1503151946251636787>",  #done
    "Aegis":                       "<:Aegis:1503151510530298017>",                     #done
    "Divine Fortune":              "<:DivineFortune:1483474576657616937>",
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
