import json
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

client_db = None
cards_collection = None
players_collection = None
guilds_collection = None
config_collection = None          # global bot config: energy timer, daily watch, clan shop
card_pictures_collection = None   # custom card instance pictures
raid_snapshots_collection = None  # raid activity tracker snapshots
weekly_donation_tracker_collection = None
channel_donations_collection = None
breach_comps_collection = None

_CONFIG_ID = "global"


async def connect_to_db():
    global client_db, cards_collection, players_collection, guilds_collection
    global config_collection, card_pictures_collection, raid_snapshots_collection
    global weekly_donation_tracker_collection, channel_donations_collection, breach_comps_collection
    db_connection = os.getenv("MONGODB_URI")
    client_db = AsyncIOMotorClient(db_connection)
    bot_db = client_db["discordbot"]
    cards_collection = bot_db["cards"]
    players_collection = bot_db["players"]
    guilds_collection = bot_db["guilds"]
    config_collection = bot_db["config"]
    card_pictures_collection = bot_db["card_pictures"]
    raid_snapshots_collection = bot_db["raid_snapshots"]
    weekly_donation_tracker_collection = bot_db["weekly_donation_tracker"]
    channel_donations_collection = bot_db["channel_donations"]
    breach_comps_collection = bot_db["breach_comps"]
    from db_methods import weekly_donations, channel_donations, breach_comps
    weekly_donations.init_collection(weekly_donation_tracker_collection)
    channel_donations.init_collection(channel_donations_collection)
    breach_comps.init_collection(breach_comps_collection)
    print("[DATABASE] Database successfully connected.")


def get_players_collection():
    return players_collection


def get_cards_collection():
    return cards_collection


def get_guilds_collection():
    return guilds_collection


def get_config_collection():
    return config_collection


def get_breach_comps_collection():
    return breach_comps_collection


def get_card_pictures_collection():
    return card_pictures_collection


def save_prefixes(prefixes):
    with open("data/prefixes.json", "w") as f:
        json.dump(prefixes, f, indent=4)


async def set_global_energy_timer(unix_timestamp):
    await config_collection.update_one(
        {"_id": _CONFIG_ID},
        {"$set": {"energy_reset_timer": unix_timestamp}},
        upsert=True,
    )


async def get_global_daily_watch_timer():
    doc = await config_collection.find_one({"_id": _CONFIG_ID})
    if not doc:
        return None
    timer = doc.get("daily_watch_timer")
    return int(timer) if timer else None


async def increase_daily_watch_counter():
    doc = await config_collection.find_one({"_id": _CONFIG_ID})
    if not doc:
        return
    daily_watch_counter = doc.get("daily_watch_counter", 0)
    max_loc = await cards_collection.find_one({"location": {"$type": "int"}}, sort=[("location", -1)])
    if int(daily_watch_counter) >= int(max_loc["location"]):
        await config_collection.update_one({"_id": _CONFIG_ID}, {"$set": {"daily_watch_counter": 1}})
    else:
        await config_collection.update_one({"_id": _CONFIG_ID}, {"$inc": {"daily_watch_counter": 1}})


async def get_daily_watch_counter():
    doc = await config_collection.find_one({"_id": _CONFIG_ID})
    if not doc:
        return None
    return doc.get("daily_watch_counter", 0)


async def get_raid_snapshot(raid_code: str) -> dict | None:
    doc = await raid_snapshots_collection.find_one({"_id": raid_code})
    if not doc:
        return None
    return {"last_time": doc["last_time"], "last_attacks": doc["last_attacks"], "observed_rate": doc.get("observed_rate")}


async def save_raid_snapshot(raid_code: str, data: dict):
    await raid_snapshots_collection.update_one(
        {"_id": raid_code},
        {"$set": {**data}},
        upsert=True,
    )
