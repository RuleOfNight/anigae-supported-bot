import json
import os
from bson import ObjectId
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

client_db = None
cards_collection = None
players_collection = None
guilds_collection = None
misc_collection = None
weekly_donation_tracker_collection = None
channel_donations_collection = None


async def connect_to_db():
    global client_db, cards_collection, players_collection, guilds_collection, misc_collection, weekly_donation_tracker_collection, channel_donations_collection
    db_connection = os.getenv("MONGODB_URI")
    client_db = AsyncIOMotorClient(db_connection)
    bot_db = client_db["discordbot"]
    cards_collection = bot_db["cards"]
    players_collection = bot_db["players"]
    guilds_collection = bot_db["guilds"]
    misc_collection = bot_db["misc"]
    weekly_donation_tracker_collection = bot_db["weekly_donation_tracker"]
    channel_donations_collection = bot_db["channel_donations"]
    from db_methods import weekly_donations, channel_donations
    weekly_donations.init_collection(weekly_donation_tracker_collection)
    channel_donations.init_collection(channel_donations_collection)
    print("[DATABASE] Database successfully connected.")

def get_players_collection():
    return players_collection

def get_cards_collection():
    return cards_collection

def get_guilds_collection():
    return guilds_collection

def get_misc_collection():
    return misc_collection

def save_prefixes(prefixes):
    with open("data/prefixes.json", "w") as f:
        json.dump(prefixes, f, indent=4)


def set_global_energy_timer(unix_timestamp):
    _id = ObjectId("67ae69c3cf53d633cb1cd358")
    found_misc_collection = misc_collection.find({"_id": _id})
    if found_misc_collection:
        misc_collection.update_one({"_id": _id}, {"$set": {"energy_reset_timer": unix_timestamp}})
    else:
        return


async def get_global_daily_watch_timer():
    _id = ObjectId("67ae69c3cf53d633cb1cd358")
    found_misc_collection = await misc_collection.find_one({"_id": _id})
    if found_misc_collection:
        daily_watch_timer = found_misc_collection.get("daily_watch_timer")
        if not daily_watch_timer:
            return None
        return int(daily_watch_timer)


async def increase_daily_watch_counter():
    _id = ObjectId("67ae69c3cf53d633cb1cd358")
    found_misc_collection = await misc_collection.find_one({"_id": _id})
    if not found_misc_collection:
        return
    daily_watch_counter = found_misc_collection.get("daily_watch_counter", 0)
    max_location_highest_loc = await cards_collection.find_one({"location": {"$type": "int"}}, sort=[("location", -1)])
    if int(daily_watch_counter) >= int(max_location_highest_loc["location"]):
        await misc_collection.update_one({"_id": _id}, {"$set": {"daily_watch_counter": 1}})
    else:
        await misc_collection.update_one({"_id": _id}, {"$inc": {"daily_watch_counter": 1}})


async def get_daily_watch_counter():
    _id = ObjectId("67ae69c3cf53d633cb1cd358")
    found_misc_collection = await misc_collection.find_one({"_id": _id})
    if not found_misc_collection:
        return
    daily_watch_counter = found_misc_collection.get("daily_watch_counter", 0)
    return daily_watch_counter
