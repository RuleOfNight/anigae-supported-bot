from db_methods.general import get_cards_collection, misc_collection, get_misc_collection
import time
import re
import json
import runtime
from bson import ObjectId


def remove_special_cases(name):
    return re.sub(r"[\(\)]", "", name)


def name_check_card_list(name_to_check, full_name_list):
    full_name_list.remove(name_to_check)
    name_list_string = ",".join(full_name_list)
    name_to_check_clean = re.sub(r"[()]", "", name_to_check)
    name_word_list = name_to_check_clean.split()
    used_words = []
    final_name = ""
    for word in name_word_list:
        if word in name_list_string:
            used_words.append(word)
        else:
            final_name += word
            break
    if final_name == "":
        final_name = name_to_check
    final_name = final_name.strip()
    return final_name


# ---------------
# Create
# ---------------


async def create_card_in_collection(card_id, card_name, card_element, location, floors, card_hp, card_atk, card_def, card_spd, card_talent, card_talent_description, card_series,
                                    card_price_sr, card_price_ur, card_picture):
    cards_collection = get_cards_collection()
    current_timestamp = int(time.time())
    await cards_collection.delete_one({"card_name": card_name})
    if location != "None":
        location = int(location)
    new_card = {"card_id": card_id,
                "card_name": card_name,
                "card_series": card_series,
                "card_element": card_element,
                "location": location,
                "floors": floors,
                "card_hp": card_hp,
                "card_atk": card_atk,
                "card_def": card_def,
                "card_spd": card_spd,
                "card_talent": card_talent,
                "card_talent_description": card_talent_description,
                "card_picture": card_picture,
                "market_price_sr": card_price_sr,
                "market_price_ur": card_price_ur,
                "market_price_sr_timestamp": current_timestamp,
                "market_price_ur_timestamp": current_timestamp}
    await cards_collection.insert_one(new_card)


# ---------------
# Gets
# ---------------


async def get_all_card_location_floor_element_for_shards_display(max_location, max_floor):
    cards_collection = get_cards_collection()
    pipeline = [
        {"$match": {"location": {"$type": "int"}, "floors": {"$exists": True, "$not": {"$size": 0}}}},
        {"$addFields": {"floors_int": {"$map": {"input": "$floors", "as": "floor", "in": {"$toInt": "$$floor"}}}, "location_int": {"$toInt": "$location"}}},
        {"$addFields": {"max_floor_int": {"$max": "$floors_int"}}},
        {"$addFields": {"value": {"$add": [{"$multiply": ["$location_int", 2]}, {"$multiply": ["$max_floor_int", 1]}]}}},]
    if max_location != "not_set":
        pipeline.append({"$match": {"location_int": {"$lte": max_location}}})
    if max_floor != "not_set" and max_location != "not_set":
        pipeline.append({"$match": {"$or": [{"location_int": {"$lt": max_location}}, {"location_int": max_location, "max_floor_int": {"$lte": max_floor}}]}})
    pipeline.extend([
        {"$sort": {"value": -1}},
        {"$group": {"_id": "$card_element", "best_card": {"$max": "$value"}, "card": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$card"}},
        {"$project": {"_id": 0, "card_element": 1, "card_name": 1, "location": 1, "floor": "$max_floor_int", "value": 1}},
        {"$sort": {"value": -1}}])
    cursor = cards_collection.aggregate(pipeline)
    return [doc async for doc in cursor]


async def get_card_market_price_sr_by_cards_name(card_name):
    cards_collection = get_cards_collection()
    normalized_name = remove_special_cases(card_name)
    regex = re.compile(re.escape(card_name), re.IGNORECASE)
    cursor = cards_collection.find({"card_name": {"$regex": regex}})
    found_card = [doc async for doc in cursor]
    if found_card:
        found_card.sort(key=lambda x: len(x["card_name"]))
        found_market_price_sr = found_card[0].get("market_price_sr", "")
        return found_market_price_sr
    regex = re.compile(re.escape(normalized_name), re.IGNORECASE)
    cursor = cards_collection.find({"card_name": {"$regex": regex}})
    found_cards = [doc async for doc in cursor]
    found_cards.sort(key=lambda x: len(x["card_name"]))
    found_market_price_sr = found_cards[0].get("market_price_sr", "")
    return found_market_price_sr


async def get_card_data_by_series_name():
    cards_collection = get_cards_collection()
    misc_collection = get_misc_collection()
    _id = ObjectId("67ae69c3cf53d633cb1cd358")
    found_misc_collection = await misc_collection.find_one({"_id": _id})
    if found_misc_collection:
        series_name = found_misc_collection.get("clan_shop_series", "")
    normalized_series_name = remove_special_cases(series_name)
    regex = re.compile(re.escape(series_name), re.IGNORECASE)
    cursor = cards_collection.find({"card_series": {"$regex": regex}})
    found_series = [doc async for doc in cursor]
    if not found_series:
        regex = re.compile(re.escape(normalized_series_name), re.IGNORECASE)
        cursor = cards_collection.find({"card_series": {"$regex": regex}})
        found_series = [doc async for doc in cursor]
    if found_series:
        card_data = [{"card_name": card.get("card_name", ""),
                      "card_price_sr": card.get("market_price_sr", ""),
                      "market_price_sr_timer": card.get("market_price_sr_timestamp", ""),
                      "card_price_ur": card.get("market_price_ur", ""),
                      "market_price_ur_timer": card.get("market_price_ur_timestamp", ""),
                      "card_element": card.get("card_element", ""),
                      "card_talent": card.get("card_talent", "")} for card in found_series]
        return card_data
    return []


async def get_card_data_by_name(card_name):
    cards_collection = get_cards_collection()
    normalized_card_name = remove_special_cases(card_name)
    regex = re.compile(re.escape(card_name), re.IGNORECASE)
    cursor = cards_collection.find({"card_name": {"$regex": regex}})
    found_cards = [doc async for doc in cursor]
    if not found_cards:
        regex = re.compile(re.escape(normalized_card_name), re.IGNORECASE)
        cursor = cards_collection.find({"card_name": {"$regex": regex}})
        found_cards = [doc async for doc in cursor]
    if found_cards:
        found_cards.sort(key=lambda x: len(x["card_name"]))
        card_data = [{"card_name": found_cards[0].get("card_name", ""),
                      "card_price_sr": found_cards[0].get("market_price_sr", ""),
                      "market_price_sr_timer": found_cards[0].get("market_price_sr_timestamp", ""),
                      "card_price_ur": found_cards[0].get("market_price_ur", ""),
                      "market_price_ur_timer": found_cards[0].get("market_price_ur_timestamp", ""),
                      "card_element": found_cards[0].get("card_element", ""),
                      "card_talent": found_cards[0].get("card_talent", "")}]
        return card_data
    return []


async def get_cinfo_card_data_by_name(card_name):
    cards_collection = get_cards_collection()
    cursor = cards_collection.find({
        "card_name": {"$regex": f"^{re.escape(card_name)}$", "$options": "i"}})
    found_cards = [doc async for doc in cursor]
    if found_cards:
        card = found_cards[0]
        return [{
            "card_name": card.get("card_name", ""),
            "card_price_sr": card.get("market_price_sr", ""),
            "market_price_sr_timer": card.get("market_price_sr_timestamp", ""),
            "card_price_ur": card.get("market_price_ur", ""),
            "market_price_ur_timer": card.get("market_price_ur_timestamp", ""),
            "card_element": card.get("card_element", ""),
            "card_talent": card.get("card_talent", ""),
            "card_picture": card.get("card_picture", "")}]
    return []


async def raid_search_list_from_db(price_limit, excluded_events=None):
    if excluded_events is None:
        excluded_events = []
    event_card_data = await runtime.retrieve_data("event cards")
    excluded_event_cards = []
    for event in excluded_events:
        excluded_event_cards.extend(event_card_data.get(event, []))
    name_list = []
    card_list = []
    cards_collection = get_cards_collection()
    cursor = cards_collection.find({}, {"card_name": 1, "market_price_sr": 1, "location": 1, "_id": 0})
    card_data = [doc async for doc in cursor]
    for name in card_data:
        card_name = name["card_name"]
        name_list.append(card_name)
    for card in card_data:
        card_name = card["card_name"]
        card_price = card["market_price_sr"]
        card_location = card["location"]
        if card_name in excluded_event_cards:
            continue
        if card_price == "N/A":
            if card_location == "None":
                card_short_name = name_check_card_list(card_name, name_list)
                card_list.append(card_short_name)
        elif int(card_price) >= price_limit:
            card_short_name = name_check_card_list(card_name, name_list)
            card_list.append(card_short_name)
    card_names_string = ",".join(card_list)
    return card_names_string


async def get_compare_data_from_cards(name_list=None, series_list=None, element_list=None, talent_list=None):
    cards_collection = get_cards_collection()
    filter_query = {}
    for card_name in name_list:
        filter_query["card_name"] = {"$regex": "|".join(card_name), "$options": "i"}
    for series_name in series_list:
        filter_query["card_series"] = {"$regex": "|".join(series_name), "$options": "i"}
    for element in element_list:
        filter_query["card_element"] = {"$regex": "|".join(element), "$options": "i"}
    for talent in talent_list:
        filter_query["card_talent"] = {"$regex": "|".join(talent), "$options": "i"}
    results = [doc async for doc in cards_collection.find(filter_query)]
    if not name_list:
        return results
    results_sorted = sorted(results, key=lambda card: card["card_name"].lower())
    results_name_list = []
    for name in name_list:
        for n in name:
            n = n.lower()
            found_match = False
            for card in results_sorted:
                if n == card["card_name"].lower():
                    results_name_list.append(card)
                    found_match = True
                    break
            if found_match:
                continue
            for card in results_sorted:
                card_name_parts = card["card_name"].split()
                if n in (part.lower() for part in card_name_parts):
                    results_name_list.append(card)
                    found_match = True
                    break
            if found_match:
                continue
            for card in results_sorted:
                if n in card["card_name"].lower():
                    results_name_list.append(card)
                    break
    return results_name_list


async def get_market_dex_data_from_cards(full_list=None, name_list=None, series_list=None, element_list=None, talent_list=None, rarity_list=None):
    cards_collection = get_cards_collection()
    filter_query = {}
    if full_list == "all":
        results = cards_collection.find(filter_query)
        return [doc async for doc in results]
    for card_name in name_list:
        filter_query["card_name"] = {"$regex": "|".join(card_name), "$options": "i"}
    for series_name in series_list:
        filter_query["card_series"] = {"$regex": "|".join(series_name), "$options": "i"}
    for element in element_list:
        filter_query["card_element"] = {"$regex": "|".join(element), "$options": "i"}
    for talent in talent_list:
        filter_query["card_talent"] = {"$regex": "|".join(talent), "$options": "i"}
    for rarity in rarity_list:
        if rarity == "sr":
            filter_query["market_price_sr"] = {"$regex": "|".join(""), "$options": "i", "$ne": "N/A"}
        elif rarity == "ur":
            filter_query["market_price_ur"] = {"$regex": "|".join(""), "$options": "i", "$ne": "N/A"}
    results = [doc async for doc in cards_collection.find(filter_query)]
    if not name_list:
        return results
    results_sorted = sorted(results, key=lambda card: card["card_name"].lower())
    results_name_list = []
    matched_names = set()
    for name in name_list:
        for n in name:
            if n.lower() in matched_names:
                continue
            found_match = False
            for card in results_sorted:
                if n.lower() == card["card_name"].lower():
                    results_name_list.append(card)
                    matched_names.add(n.lower())
                    found_match = True
                    break
            if found_match:
                continue
            for card in results_sorted:
                card_name_parts = card["card_name"].split()
                if n.lower() == card["card_name"].lower():
                    results_name_list.append(card)
                    matched_names.add(n.lower())
                    found_match = True
                    break
                elif n.lower() in (part.lower() for part in card_name_parts):
                    if card not in results_name_list:
                        results_name_list.append(card)
                        matched_names.add(n.lower())
                        found_match = True
                        break
            if found_match:
                continue
            for card in results_sorted:
                if n.lower() in card["card_name"].lower():
                    results_name_list.append(card)
                    break
    return results_name_list


async def get_cards_from_daily_watch_counter(daily_watch_counter):
    cards_collection = get_cards_collection()
    cursor = cards_collection.find({"location": daily_watch_counter}, {"card_name": 1, "card_element": 1, "card_talent": 1, "market_price_ur": 1, "market_price_sr": 1, "location": 1, "_id": 0})
    card_data = [doc async for doc in cursor]
    return card_data


# ------------
# Updates
# ------------


async def update_market_price_sr_by_cards_name(card_name, card_market_price_sr):
    cards_collection = get_cards_collection()
    current_timestamp = int(time.time())
    await cards_collection.update_one({"card_name": card_name}, {"$set": {"market_price_sr": str(card_market_price_sr)}})
    await cards_collection.update_one({"card_name": card_name}, {"$set": {"market_price_sr_timestamp": str(current_timestamp)}})


async def update_market_price_ur_by_cards_name(card_name, card_market_price_ur):
    cards_collection = get_cards_collection()
    current_timestamp = int(time.time())
    await cards_collection.update_one({"card_name": card_name}, {"$set": {"market_price_ur": str(card_market_price_ur)}})
    await cards_collection.update_one({"card_name": card_name}, {"$set": {"market_price_ur_timestamp": str(current_timestamp)}})


# ------------------
# Delete
# ------------------

