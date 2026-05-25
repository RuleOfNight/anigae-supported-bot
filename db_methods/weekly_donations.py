import time
from db_methods.general import get_guilds_collection

_collection = None
WEEK_SECONDS = 604800


def init_collection(col):
    global _collection
    _collection = col


def get_collection():
    return _collection


async def get_discord_id_by_player_name(player_name: str):
    guilds_col = get_guilds_collection()
    pipeline = [
        {"$unwind": "$guild_member"},
        {"$match": {"guild_member.guild_member_name": player_name,
                    "guild_member.guild_member_id": {"$ne": None}}},
        {"$project": {"_id": 0, "discord_id": "$guild_member.guild_member_id"}},
        {"$limit": 1}
    ]
    result = await guilds_col.aggregate(pipeline).to_list(length=1)
    return result[0]["discord_id"] if result else None


async def get_active_tracking(player_name: str):
    return await _collection.find_one({"player_name": player_name, "pinged": False})


async def create_or_update_tracking(player_name: str, discord_id, channel_id: int, weeks_to_add: int):
    now = int(time.time())
    existing = await get_active_tracking(player_name)
    # Nếu record cũ đã hết hạn (ping_due đã qua), coi như chu kỳ mới
    if existing and existing.get("ping_due_unix", 0) > now:
        new_total = existing["total_weeks_credited"] + weeks_to_add
        new_ping_due = existing["first_donation_unix"] + new_total * WEEK_SECONDS
        await _collection.update_one(
            {"_id": existing["_id"]},
            {"$set": {"total_weeks_credited": new_total, "ping_due_unix": new_ping_due, "last_donation_unix": now}}
        )
        return new_total
    # Tạo record mới (lần đầu, hoặc chu kỳ cũ đã hết hạn)
    if existing:
        await _collection.update_one({"_id": existing["_id"]}, {"$set": {"pinged": True}})
    await _collection.insert_one({
        "player_name": player_name,
        "discord_id": discord_id,
        "channel_id": channel_id,
        "first_donation_unix": now,
        "last_donation_unix": now,
        "total_weeks_credited": weeks_to_add,
        "ping_due_unix": now + weeks_to_add * WEEK_SECONDS,
        "pinged": False
    })
    return weeks_to_add


async def get_weekly_donors(channel_id: int, week_start_unix: int) -> set:
    """Trả về set player_name đã donate trong channel_id từ week_start_unix đến nay."""
    docs = await _collection.find(
        {"channel_id": channel_id, "last_donation_unix": {"$gte": week_start_unix}}
    ).to_list(length=None)
    return {doc["player_name"] for doc in docs}


async def get_due_pings():
    now = int(time.time())
    return await _collection.find(
        {"pinged": False, "ping_due_unix": {"$lte": now}}
    ).to_list(length=None)


async def mark_pinged(record_id):
    await _collection.update_one({"_id": record_id}, {"$set": {"pinged": True}})
