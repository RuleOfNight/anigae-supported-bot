from db_methods.general import get_players_collection, get_misc_collection
from bson import ObjectId
import time

# ---------------
# Create
# ---------------


async def create_player_in_collection(discord_id, discord_name):
    players_collection = get_players_collection()
    new_player = {"discord_id": discord_id, "discord_name": discord_name}
    await players_collection.insert_one(new_player)


async def update_player(discord_id, discord_name):
    players_collection = get_players_collection()
    await players_collection.update_one({"discord_id": discord_id}, {"$set": {"discord_id": discord_id, "discord_name": discord_name}}, upsert=True)


# ---------------
# Gets
# ---------------


async def get_player_info_for_floors_from_players_by_discord_id(discord_id, discord_name):
    players_collection = get_players_collection()
    found_player_id = await players_collection.find_one({"discord_id": discord_id})
    if found_player_id is None:
        await create_player_in_collection(discord_id, discord_name)
        found_player_id = await players_collection.find_one({"discord_id": discord_id})
    player_max_location = found_player_id.get("location_max", "not_set")
    player_max_floor = found_player_id.get("floor_max", "not_set")
    return player_max_location, player_max_floor


async def get_raid_search_history_delete_for_players_by_player_id(discord_id, discord_name):
    players_collection = get_players_collection()
    found_player_id = await players_collection.find_one({"discord_id": discord_id})
    if found_player_id is None:
        await create_player_in_collection(discord_id, discord_name)
        found_player_id = await players_collection.find_one({"discord_id": discord_id})
    raid_search_history_value = found_player_id.get("raid_search_history", "not_set")
    return raid_search_history_value


async def get_raid_history_from_db(user_id):
    players_collection = get_players_collection()
    user_data = await players_collection.find_one({"discord_id": user_id})
    if user_data and "raid_history" in user_data:
        return user_data["raid_history"]
    return None


async def get_player_status_team_check(discord_name):
    players_collection = get_players_collection()
    found_player_id = await players_collection.find_one({"discord_name": discord_name})
    if found_player_id is None:
        return "None"
    found_player_status = found_player_id.get("status_team_check", "no")
    if found_player_status == "yes":
        return "Yes"
    return "None"


async def get_player_selected_locations_by_player_id_in_players(discord_id):
    players_collection = get_players_collection()
    user_entry = await players_collection.find_one({"discord_id": discord_id})
    if user_entry and "selected_locations" in user_entry:
        return set(user_entry["selected_locations"])
    return set()


async def get_users_to_ping_by_daily_counter_in_players(daily_counter):
    players_collection = get_players_collection()
    query = {"selected_locations": str(daily_counter)}
    cursor = players_collection.find(query)
    users_to_ping = [doc["discord_id"] async for doc in cursor]
    return users_to_ping


async def get_settings_from_player_by_discord_id(discord_id):
    players_collection = get_players_collection()
    user_entry = await players_collection.find_one({"discord_id": discord_id})
    if user_entry:
        player_settings = {"raid_lobby_status": user_entry.get("raid_lobby_status", "short"),
                           "raid_search_history": user_entry.get("raid_search_history", "no"),
                           "cinfo_delete": user_entry.get("cinfo_delete", "no"),
                           "cinfo_stat_display": user_entry.get("cinfo_stat_display", "original"),
                           "cinfo_picture": user_entry.get("cinfo_picture", "original"),
                           "cselect_delete": user_entry.get("cselect_delete", "no")}
        return player_settings
    else:
        return "No Player found."


async def get_selected_card_info_from_player_by_discord_id(discord_id):
    players_collection = get_players_collection()
    user_entry = await players_collection.find_one({"discord_id": discord_id})
    if user_entry:
        selected_card_setting = user_entry.get("cselect_delete", "no")
        return selected_card_setting
    else:
        return "no."


async def get_premium_days_left_by_discord_name(discord_name):
    players_collection = get_players_collection()
    found_player_name = await players_collection.find_one({"discord_name": discord_name})
    if found_player_name is None:
        return "player not found", "None"
    premium_days_left = found_player_name.get("premium_days_left", 0)
    player_id = found_player_name.get("discord_id", 0)
    return premium_days_left, player_id


# ------------
# Updates
# ------------


async def update_location_floor_players_by_player_id(discord_id, discord_name, location_max, floor_max):
    players_collection = get_players_collection()
    found_player_id = await players_collection.find_one({"discord_id": discord_id})
    if found_player_id is None:
        await create_player_in_collection(discord_id, discord_name)
    await players_collection.update_one({"discord_id": discord_id}, {"$set": {"location_max": int(location_max), "floor_max": int(floor_max)}})


async def update_raid_history_for_players_by_player_data(player_data, raid_boss_data, raid_unique_code):
    players_collection = get_players_collection()
    raid_code_min = int(raid_unique_code) - 15
    raid_code_max = int(raid_unique_code) + 15
    for data in raid_boss_data:
        raid_boss_rarity = data[0]
        raid_boss_level = data[1]
        raid_boss_name = data[2]
        raid_boss_difficulty = data[3]
    for player_info in player_data:
        rh_player_id = int(player_info[2])
        player_data_dict = {"raid_unique_code": int(raid_unique_code),
                            "player_number": int(player_info[0]),
                            "player_name": player_info[1],
                            "player_level": int(player_info[3]),
                            "player_power_level": int(player_info[4]),
                            "player_max_dmg": int(player_info[5]),
                            "player_dmg_per_atk": int(player_info[6]),
                            "player_damage_percent": player_info[7],
                            "player_dmg_status": player_info[8],
                            "player_total_atk": int(player_info[9]),
                            "player_last_atk": int(player_info[10]),
                            "raid_boss_rarity": raid_boss_rarity,
                            "raid_boss_level": int(raid_boss_level),
                            "raid_boss_name": raid_boss_name,
                            "raid_boss_difficulty": raid_boss_difficulty,
                            "raid_timer": int(time.time())}
        found_player = await players_collection.find_one({"discord_id": rh_player_id})
        if found_player:
            found_raid = next((raid for raid in found_player.get("raid_history", []) if raid_code_min <= raid["raid_unique_code"] <= raid_code_max), None)
            if found_raid:
                await players_collection.update_one({"discord_id": rh_player_id, "raid_history.raid_unique_code": found_raid["raid_unique_code"]}, {"$set": {"raid_history.$": player_data_dict}})
            else:
                await players_collection.update_one({"discord_id": rh_player_id}, {"$push": {"raid_history": player_data_dict}})
        else:
            await create_player_in_collection(rh_player_id, player_info[1])
            await players_collection.update_one({"discord_id": rh_player_id}, {"$push": {"raid_history": player_data_dict}})


async def update_player_gold_by_player_name(player_name, player_gold):
    players_collection = get_players_collection()
    found_player_name = await players_collection.find_one({"discord_name": player_name})
    if found_player_name is None:
        return "player not found"
    old_player_gold = found_player_name.get("player_gold", "0")
    await players_collection.update_one({"discord_name": player_name}, {"$set": {"player_gold": player_gold}})
    return old_player_gold


async def update_player_rubies_by_player_name(player_name, player_rubies):
    players_collection = get_players_collection()
    found_player_name = await players_collection.find_one({"discord_name": player_name})
    if found_player_name is None:
        return "player not found"
    await players_collection.update_one({"discord_name": player_name}, {"$set": {"player_rubies": player_rubies}})
    return "player found"


async def update_status_team_check_by_player_id_in_players(discord_id, discord_name, update_value):
    players_collection = get_players_collection()
    found_player_id = await players_collection.find_one({"discord_id": discord_id})
    if found_player_id is None:
        await create_player_in_collection(discord_id, discord_name)
    if update_value == "yes":
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"status_team_check": "yes"}})
    elif update_value == "no":
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"status_team_check": "no"}})


async def update_raid_energy_timer_by_player_id_in_players(discord_id, discord_name, update_value, energy_timer=None):
    players_collection = get_players_collection()
    found_player_id = await players_collection.find_one({"discord_id": discord_id})
    if found_player_id is None:
        await create_player_in_collection(discord_id, discord_name)
    if update_value == "yes":
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"energy_timer_check": update_value, "energy_timer": int(energy_timer)}})
    elif update_value == "no":
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"energy_timer_check": update_value}})


async def toggle_selected_location_for_player(discord_id, location_id: str) -> bool:
    players_collection = get_players_collection()
    user = await players_collection.find_one({"discord_id": discord_id})
    already_selected = user and "selected_locations" in user and location_id in user["selected_locations"]
    if already_selected:
        await players_collection.update_one({"discord_id": discord_id}, {"$pull": {"selected_locations": location_id}})
        return False
    else:
        await players_collection.update_one({"discord_id": discord_id}, {"$addToSet": {"selected_locations": location_id}}, upsert=True)
        return True


async def update_player_settings_rl_by_discord_id(discord_id):
    players_collection = get_players_collection()
    user_entry = await players_collection.find_one({"discord_id": discord_id})
    raid_lobby_status = user_entry.get("raid_lobby_status", "short")
    if raid_lobby_status == "short":
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"raid_lobby_status": "long"}})
    else:
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"raid_lobby_status": "short"}})


async def update_player_settings_rsh_by_discord_id(discord_id):
    players_collection = get_players_collection()
    user_entry = await players_collection.find_one({"discord_id": discord_id})
    raid_search_history = user_entry.get("raid_search_history", "no")
    if raid_search_history == "no":
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"raid_search_history": "yes"}})
    else:
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"raid_search_history": "no"}})


async def update_player_settings_cinfo_del_by_discord_id(discord_id):
    players_collection = get_players_collection()
    user_entry = await players_collection.find_one({"discord_id": discord_id})
    cinfo_delete = user_entry.get("cinfo_delete", "no")
    if cinfo_delete == "no":
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"cinfo_delete": "yes"}})
    else:
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"cinfo_delete": "no"}})


async def update_player_settings_cinfo_stat_by_discord_id(discord_id):
    players_collection = get_players_collection()
    user_entry = await players_collection.find_one({"discord_id": discord_id})
    cinfo_stat_display = user_entry.get("cinfo_stat_display", "original")
    if cinfo_stat_display == "original":
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"cinfo_stat_display": "compact"}})
    else:
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"cinfo_stat_display": "original"}})


async def update_player_settings_cinfo_pic_by_discord_id(discord_id):
    players_collection = get_players_collection()
    user_entry = await players_collection.find_one({"discord_id": discord_id})
    cinfo_picture = user_entry.get("cinfo_picture", "original")
    if cinfo_picture == "original":
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"cinfo_picture": "thumbnail"}})
    else:
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"cinfo_picture": "original"}})


async def update_player_settings_cselect_delete_by_discord_id(discord_id):
    players_collection = get_players_collection()
    user_entry = await players_collection.find_one({"discord_id": discord_id})
    cselect_delete = user_entry.get("cselect_delete", "no")
    if cselect_delete == "no":
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"cselect_delete": "yes"}})
    else:
        await players_collection.update_one({"discord_id": discord_id}, {"$set": {"cselect_delete": "no"}})


async def update_player_premium_days_left_by_discord_id(discord_id, premium_days_left):
    players_collection = get_players_collection()
    await players_collection.update_one({"discord_id": discord_id}, {"$set": {"premium_days_left": premium_days_left}})


async def decrement_all_premium_days():
    players_collection = get_players_collection()
    await players_collection.update_many({"premium_days_left": {"$gt": 0}}, {"$inc": {"premium_days_left": -1}})


# ------------------
# Delete
# ------------------

