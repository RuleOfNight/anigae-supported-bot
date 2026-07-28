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
            {"$set": {"total_weeks_credited": new_total,
                       "ping_due_unix": new_ping_due,
                       "last_donation_unix": now,
                       "coverage_start_unix": min(existing.get("coverage_start_unix", week_start), week_start)}}
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
        "coverage_start_unix": week_start,
        "total_weeks_credited": total,
        "ping_due_unix": week_start + total * WEEK_SECONDS,
        "pinged": False
    })
    return total


async def grant_next_week_waiver(
    player_name: str,
    discord_id,
    channel_id: int,
    damage: int,
    source: str = "breach",
) -> bool:
    """
    Grant one weekly donation coverage for the next weekly interval.

    This is tracked as a waiver/credit, not as a fake gold donation in guild
    donation history. Returns True when a new waiver key was applied, False
    when the same waiver was already recorded.
    """
    now = int(time.time())
    current_week_start = await get_last_monday_berlin_time_from_current_time_in_unix()
    next_week_start = current_week_start + WEEK_SECONDS
    waiver_until = next_week_start + WEEK_SECONDS
    waiver_key = f"{source}:{channel_id}:{next_week_start}:{player_name.casefold()}"

    existing = await _collection.find_one({
        "player_name": player_name,
        "channel_id": channel_id,
        "pinged": False,
    })

    waiver_entry = {
        "key": waiver_key,
        "source": source,
        "damage": int(damage),
        "timestamp": now,
        "coverage_start_unix": next_week_start,
        "coverage_until_unix": waiver_until,
    }

    if existing:
        already_waived = any(
            waiver.get("source") == source
            and waiver.get("coverage_start_unix") == next_week_start
            for waiver in existing.get("waivers", [])
        )
        if waiver_key in existing.get("waiver_keys", []) or already_waived:
            return False

        current_ping_due = existing.get("ping_due_unix", 0)
        # Preserve prepaid weeks instead of replacing one the player paid for.
        new_ping_due = max(current_ping_due + WEEK_SECONDS, waiver_until)
        coverage_start = existing.get("coverage_start_unix", current_week_start)
        total_weeks = max(1, (new_ping_due - current_week_start) // WEEK_SECONDS)

        await _collection.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "discord_id": discord_id,
                "last_donation_unix": now,
                "ping_due_unix": new_ping_due,
                "coverage_start_unix": min(coverage_start, next_week_start),
                "total_weeks_credited": total_weeks,
            },
             "$addToSet": {"waiver_keys": waiver_key},
             "$push": {"waivers": waiver_entry}}
        )
        return True

    await _collection.insert_one({
        "player_name": player_name,
        "discord_id": discord_id,
        "channel_id": channel_id,
        "first_donation_unix": now,
        "last_donation_unix": now,
        "coverage_start_unix": next_week_start,
        "total_weeks_credited": 1,
        "ping_due_unix": waiver_until,
        "pinged": False,
        "waiver_keys": [waiver_key],
        "waivers": [waiver_entry],
    })
    return True


async def get_weekly_donors(channel_id: int, week_start_unix: int) -> set:
    """Trả về set player_name còn coverage từ week_start_unix (donate bội số vẫn tính)."""
    docs = await _collection.find(
        {"channel_id": channel_id,
         "pinged": False,
         "ping_due_unix": {"$gt": week_start_unix},
         "$or": [
             {"coverage_start_unix": {"$exists": False}},
             {"coverage_start_unix": {"$lte": week_start_unix}},
         ]}
    ).to_list(length=None)
    return {doc["player_name"] for doc in docs}


async def get_weekly_waivers(channel_id: int, week_start_unix: int) -> set:
    """Return players whose Breach waiver covers the requested weekly reset."""
    docs = await _collection.find({
        "channel_id": channel_id,
        "waivers": {"$elemMatch": {
            "coverage_start_unix": {"$lte": week_start_unix},
            "coverage_until_unix": {"$gt": week_start_unix},
        }},
    }).to_list(length=None)
    return {doc["player_name"] for doc in docs}


async def get_due_pings():
    now = int(time.time())
    return await _collection.find(
        {"pinged": False, "ping_due_unix": {"$lte": now}}
    ).to_list(length=None)


async def mark_pinged(record_id):
    await _collection.update_one({"_id": record_id}, {"$set": {"pinged": True}})
