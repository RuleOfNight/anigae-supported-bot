import time
from db_methods.general import get_guilds_collection
from misc.time_calculations import get_last_monday_berlin_time_from_current_time_in_unix

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
    week_start = await get_last_monday_berlin_time_from_current_time_in_unix()
    existing = await get_active_tracking(player_name)
    # Cộng dồn chỉ khi donation trước nằm trong tuần hiện tại
    if existing and existing.get("last_donation_unix", 0) >= week_start:
        new_total = existing["total_weeks_credited"] + weeks_to_add
        new_ping_due = week_start + new_total * WEEK_SECONDS
        await _collection.update_one(
            {"_id": existing["_id"]},
            {"$set": {"total_weeks_credited": new_total, "ping_due_unix": new_ping_due, "last_donation_unix": now}}
        )
        return new_total
    # Tuần mới hoặc lần đầu → record mới, giữ lại coverage còn dư từ record cũ
    carry_over = 0
    if existing:
        old_ping_due = existing.get("ping_due_unix", 0)
        # Tính số tuần coverage còn dư (ping_due vượt qua week_start bao nhiêu tuần)
        remaining = old_ping_due - week_start
        if remaining > 0:
            carry_over = remaining // WEEK_SECONDS
        await _collection.update_one({"_id": existing["_id"]}, {"$set": {"pinged": True}})
    total = weeks_to_add + carry_over
    await _collection.insert_one({
        "player_name": player_name,
        "discord_id": discord_id,
        "channel_id": channel_id,
        "first_donation_unix": now,
        "last_donation_unix": now,
        "total_weeks_credited": total,
        "ping_due_unix": week_start + total * WEEK_SECONDS,
        "pinged": False
    })
    return total


async def get_weekly_donors(channel_id: int, week_start_unix: int) -> set:
    """Trả về set player_name còn coverage từ week_start_unix (donate bội số vẫn tính)."""
    docs = await _collection.find(
        {"channel_id": channel_id, "pinged": False, "ping_due_unix": {"$gt": week_start_unix}}
    ).to_list(length=None)
    return {doc["player_name"] for doc in docs}


async def get_due_pings():
    now = int(time.time())
    return await _collection.find(
        {"pinged": False, "ping_due_unix": {"$lte": now}}
    ).to_list(length=None)


async def mark_pinged(record_id):
    await _collection.update_one({"_id": record_id}, {"$set": {"pinged": True}})
