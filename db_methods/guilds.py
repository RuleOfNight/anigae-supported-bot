from db_methods.general import get_guilds_collection
from misc import time_calculations
import time, discord


# ---------------
# Create
# ---------------


async def create_guild_in_collection(guild_id, guild_name):
    guilds_collection = get_guilds_collection()
    new_guild = {"guild_id": guild_id, "guild_name": guild_name, "guild_reset": "weekly", "guild_threshold": 0, "guild_threshold_2": 0, "threshold_members": [], "archived_members": [], "guild_member": [], "guild_advanced_donation": True}
    await guilds_collection.insert_one(new_guild)


async def add_guild_member_by_guild_id_and_discord_name_from_guilds(guild_id, guild_member):
    guilds_collection = get_guilds_collection()
    guild_member_data = {"guild_member_name": guild_member.name,
                         "guild_member_id": guild_member.id,
                         "guild_member_donation": 0,
                         "donations": 0}
    result = await guilds_collection.update_one({"guild_id": guild_id, "guild_member": {"$not": {"$elemMatch": {"$or": [{"guild_member_name": guild_member.name},
                                                                                                                        {"guild_member_id": guild_member.id}]}}}},
                                                {"$push": {"guild_member": guild_member_data}})
    if result.modified_count == 1:
        return "added"
    else:
        return "exists"


# ---------------
# Gets
# ---------------


async def get_guild_id_from_guilds(guild_id):
    guilds_collection = get_guilds_collection()
    found_guild_id = await guilds_collection.find_one({"guild_id": guild_id})
    if found_guild_id is None:
        return "no guild found", None
    guild_name = found_guild_id.get("guild_name", "")
    return "guild found", guild_name

async def get_guild_data(guild_id, old_interval=None):
    guilds_collection = get_guilds_collection()
    if old_interval is not None:
        old_interval = old_interval.value
    guild_reset = await guilds_collection.find_one({"guild_id": guild_id},
                                                   {"guild_reset": 1, "guild_debt": 1})
    guild_debt = guild_reset.get("guild_debt", True)
    if not guild_reset:
        return "no guild found"
    if guild_reset["guild_reset"] == "weekly":
        interval = 604800
        start_unix = await time_calculations.get_last_monday_berlin_time_from_current_time_in_unix()
        if old_interval is not None:
            start_unix -= interval * old_interval
        end_unix = start_unix + interval
    elif guild_reset["guild_reset"] == "monthly":
        start_unix, end_unix = await time_calculations.get_current_month_start_unix(old_interval)
    else:
        start_unix = 0
        end_unix = int(time.time())
    if guild_debt and old_interval is None:
        pipeline = [{"$match": {"guild_id": guild_id}},
                    {"$project": {
                        "guild_id": 1,
                        "guild_name": 1,
                        "guild_reset": 1,
                        "guild_threshold": 1,
                        "guild_threshold_2": 1,
                        "guild_debt": {"$ifNull": ["$guild_debt", True]},
                        "guild_advanced_donation": {"$ifNull": ["$guild_advanced_donation", True]},
                        "threshold_members": {"$ifNull": ["$threshold_members", []]},
                        "archived_members_safe": {"$ifNull": ["$archived_members", []]},
                        "guild_member": {"$sortArray": {"input": {"$map": {"input": {"$filter": {"input": "$guild_member",
                                                                                                 "as": "member",
                                                                                                 "cond": {"$and": [{"$not": {"$in": ["$$member.guild_member_id", {"$ifNull": ["$archived_members", []]}]}},
                                                                                                                   {"$not": {"$in": ["$$member.guild_member_name", {"$ifNull": ["$archived_members", []]}]}}]}}},
                                                                           "as": "member",
                                                                           "in": {"$let": {"vars": {"donations": {"$ifNull": ["$$member.donations", 0]},
                                                                                                    "threshold_used": {"$cond": [{"$in": ["$$member.guild_member_id", "$threshold_members"]}, "$guild_threshold_2", "$guild_threshold"]}},
                                                                                           "in": {"guild_member_name": "$$member.guild_member_name",
                                                                                                  "guild_member_donation": "$$donations",
                                                                                                  "threshold_used": "$$threshold_used"}}}}},
                                                        "sortBy": {"guild_member_donation": -1}}}}}]
    else:
        pipeline = [{"$match": {"guild_id": guild_id}},
                    {"$project": {"guild_id": 1,
                                  "guild_name": 1,
                                  "guild_reset": 1,
                                  "guild_threshold": 1,
                                  "guild_threshold_2": 1,
                                  "guild_debt": {"$ifNull": ["$guild_debt", True]},
                                  "guild_advanced_donation": {"$ifNull": ["$guild_advanced_donation", True]},
                                  "threshold_members": {"$ifNull": ["$threshold_members", []]},
                                  "archived_members_safe": {"$ifNull": ["$archived_members", []]},
                                  "guild_member": {"$sortArray": {"input": {"$map": {"input": {"$filter": {"input": "$guild_member",
                                                                                                           "as": "member",
                                                                                                           "cond": {"$and": [{"$not": {"$in": ["$$member.guild_member_id", {"$ifNull": ["$archived_members", []]}]}},
                                                                                                                             {"$not": {"$in": ["$$member.guild_member_name", {"$ifNull": ["$archived_members", []]}]}}]}}},
                                                                                     "as": "member",
                                                                                     "in": {"$let": {"vars": {"donations": {"$ifNull": ["$$member.donations", 0]},
                                                                                                              "threshold_used": {"$cond": [{"$in": ["$$member.guild_member_id", "$threshold_members"]}, "$guild_threshold_2", "$guild_threshold"]},
                                                                                                              "current_period": {"$sum": {"$map": {"input": {"$filter": {"input": {"$ifNull": ["$$member.recent_donations", []]},
                                                                                                                                                                         "as": "donation",
                                                                                                                                                                         "cond": {"$and": [{"$gte": ["$$donation.timestamp", start_unix]},
                                                                                                                                                                                           {"$lte": ["$$donation.timestamp", end_unix]}]}}},
                                                                                                                                                   "as": "donation",
                                                                                                                                                   "in": "$$donation.donation_amount"}}}},
                                                                                                     "in": {"guild_member_name": "$$member.guild_member_name",
                                                                                                            "guild_member_donation": "$$donations",
                                                                                                            "current_period_donation": "$$current_period",
                                                                                                            "threshold_used": "$$threshold_used",
                                                                                                            "recent_donations": {"$filter": {"input": {"$ifNull": ["$$member.recent_donations", []]},
                                                                                                                                             "as": "donation",
                                                                                                                                             "cond": {"$and": [{"$gte": ["$$donation.timestamp", start_unix]},
                                                                                                                                                               {"$lte": ["$$donation.timestamp", end_unix]}]}}}}}}}},
                                                                  "sortBy": {"current_period_donation": -1}}}}}]
    result = await guilds_collection.aggregate(pipeline).to_list(length=1)
    return result[0] if result else None, start_unix, end_unix


async def get_archived_members(guild_id):
    guilds_collection = get_guilds_collection()
    pipeline = [{"$match": {"guild_id": guild_id}},
                {"$project": {"_id": 0,
                              "resolved_members": {"$map": {"input": "$archived_members",
                                                            "as": "entry",
                                                            "in": {"$cond": [{"$isNumber": "$$entry"},
                                                                             {"$let": {"vars": {"member": {"$first": {"$filter": {"input": "$guild_member",
                                                                                                                                  "as": "m",
                                                                                                                                  "cond": {"$eq": ["$$m.guild_member_id", "$$entry"]}}}}},
                                                                                       "in": {"$ifNull": ["$$member.guild_member_name", {"$concat": ["(", {"$toString": "$$entry"}, ")"]}]}}},
                                                                             "$$entry"]}}}}}]
    result = await guilds_collection.aggregate(pipeline).to_list(length=1)
    if not result:
        return "guild not found"
    return result[0].get("resolved_members", [])


async def get_donations_per_guild(member, min_timestamp):
    guilds_collection = get_guilds_collection()
    pipeline = [{"$unwind": "$guild_member"},
                {"$match": { "$or": [{"guild_member.guild_member_id": member.id},
                                     {"guild_member.guild_member_name": member.name}]}},
                {"$unwind": {"path": "$guild_member.recent_donations", "preserveNullAndEmptyArrays": True}},
                {"$group": {"_id": "$guild_id",
                            "guild_name": {"$first": "$guild_name"},
                            "guild_threshold": {"$first": "$guild_threshold"},
                            "guild_threshold_2": {"$first": "$guild_threshold_2"},
                            "threshold_members": {"$first": "$threshold_members"},
                            "total_donations": {"$sum": {"$ifNull": ["$guild_member.recent_donations.donation_amount", 0]}},
                            "weekly_donations": {"$sum": {"$cond": [{"$gte": ["$guild_member.recent_donations.timestamp", min_timestamp]},
                                                                    {"$ifNull": ["$guild_member.recent_donations.donation_amount", 0]}, 0]}}}},
                {"$sort": {"guild_name": 1}}]
    results = await guilds_collection.aggregate(pipeline).to_list(length=None)
    return results


async def get_member_game_name_by_discord_id(discord_id) -> str | None:
    """Trả về AniGame username của member có discord_id khớp, hoặc None."""
    guilds_collection = get_guilds_collection()
    pipeline = [
        {"$unwind": "$guild_member"},
        {"$match": {"guild_member.guild_member_id": discord_id}},
        {"$project": {"_id": 0, "name": "$guild_member.guild_member_name"}},
        {"$limit": 1},
    ]
    result = await guilds_collection.aggregate(pipeline).to_list(length=1)
    return result[0]["name"] if result else None


async def get_recent_donations_with_id_by_member_and_guild(guild_id, member):
    guilds_collection = get_guilds_collection()
    pipeline = [{"$match": {"guild_id": guild_id}},
                {"$project": {"guild_member": {"$filter": {"input": "$guild_member",
                                                           "as": "m",
                                                           "cond": {"$or": [{"$eq": ["$$m.guild_member_name", member.name]},
                                                                            {"$eq": ["$$m.guild_member_id", member.id]}]}}}}},
                {"$project": {"member": {"$arrayElemAt": ["$guild_member", 0]}}},
                {"$project": {"recent_donations": {"$filter": {"input": {"$ifNull": ["$member.recent_donations", []]},
                                                               "as": "d",
                                                               "cond": {"$ne": ["$$d.donation_id", None]}}}}}]
    cursor = guilds_collection.aggregate(pipeline)
    results = await cursor.to_list(length=1)
    if not results:
        return "no guild found"
    data = results[0]
    donations = data.get("recent_donations")
    if donations is None:
        return "no member found"
    if not donations:
        return "no donations found"
    return donations


async def get_guild_member_names_without_discord_id(guild_id):
    guilds_collection = get_guilds_collection()
    pipeline = [{"$match": {"guild_id": guild_id}},
                {"$project": {
                    "guild_member": {"$filter": {"input": "$guild_member",
                                                 "as": "member",
                                                 "cond": {"$or": [{"$eq": ["$$member.guild_member_id", None]}, {"$not": ["$$member.guild_member_id"]}]}}}}}]
    result = await guilds_collection.aggregate(pipeline).to_list(length=None)
    if not result:
        return "no guild found"
    member_names = [m["guild_member_name"] for m in result[0].get("guild_member", [])]
    return member_names


async def get_threshold_members(guild_id):
    guilds_collection = get_guilds_collection()
    pipeline = [{"$match": {"guild_id": guild_id}},
                {"$project": {"_id": 0,
                              "resolved_members": {"$map": {"input": "$threshold_members",
                                                            "as": "entry",
                                                            "in": {"$cond": [{"$isNumber": "$$entry"},
                                                                             {"$let": {"vars": {"member": {"$first": {"$filter": {"input": "$guild_member",
                                                                                                                                  "as": "m",
                                                                                                                                  "cond": {"$eq": ["$$m.guild_member_id", "$$entry"]}}}}},
                                                                                       "in": {"$ifNull": ["$$member.guild_member_name", {"$concat": ["(", {"$toString": "$$entry"}, ")"]}]}}},
                                                                             "$$entry"]}}}}}]
    result = await guilds_collection.aggregate(pipeline).to_list(length=1)
    if not result:
        return "guild not found"
    return result[0].get("resolved_members", [])


# ------------
# Updates
# ------------


async def update_guild_member_in_guilds(guild_id, guild_member_name, guild_member_id):
    guilds_collection = get_guilds_collection()
    result_name_update = await guilds_collection.update_one( {"guild_id": guild_id, "guild_member.guild_member_name": guild_member_name},
                                                             {"$set": {"guild_member.$.guild_member_id": guild_member_id}})
    if result_name_update.modified_count > 0:
        return "updated id by name"
    result_id_update = await guilds_collection.update_one({"guild_id": guild_id, "guild_member.guild_member_id": guild_member_id},
                                                          {"$set": {"guild_member.$.guild_member_name": guild_member_name}})
    if result_id_update.modified_count > 0:
        return "updated name by id"
    else:
        return "no changes made"

async def add_member_to_archived_list(guild_id, guild_member):
    guilds_collection = get_guilds_collection()
    result = await guilds_collection.update_one({"guild_id": guild_id, "guild_member.guild_member_id": guild_member.id},
                                                {"$addToSet": {"archived_members": guild_member.id}})
    if result.matched_count == 0:
        return "guild not found or member not in guild"
    if result.modified_count == 0:
        return "already in archive"
    return "added to archive"


async def update_guild_threshold_by_guild_id_in_guilds(guild_id, threshold_amount):
    guilds_collection = get_guilds_collection()
    result = await guilds_collection.update_one({"guild_id": guild_id}, {"$set": {"guild_threshold": threshold_amount}})
    if result.modified_count > 0:
        return "edited"
    if result.matched_count == 0:
        return "no guild found"
    return "no changes"


async def update_guild_threshold_2_by_guild_id_in_guilds(guild_id, threshold_amount):
    guilds_collection = get_guilds_collection()
    result = await guilds_collection.update_one({"guild_id": guild_id}, {"$set": {"guild_threshold_2": threshold_amount}})
    if result.modified_count > 0:
        return "edited"
    if result.matched_count == 0:
        return "no guild found"
    return "no changes"

async def get_guild_member_balance(player_name: str) -> int:
    guilds_collection = get_guilds_collection()
    matching_guild = await guilds_collection.find_one(
        {"archived_members": {"$ne": player_name}, "guild_member.guild_member_name": player_name},
        {"guild_member.$": 1}
    )
    if matching_guild and "guild_member" in matching_guild and len(matching_guild["guild_member"]) > 0:
        return matching_guild["guild_member"][0].get("guild_member_donation", 0)
    return 0


async def update_donation_amount_by_player_name_in_guilds(player_name: str, donated_amount: int, donation_status: str):
    guilds_collection = get_guilds_collection()
    donated_amount = int(donated_amount)
    current_unix = int(time.time())
    donation_id = player_name + str(current_unix)
    matching_guilds = await guilds_collection.find({"archived_members": {"$ne": player_name},
                                                    "guild_member.guild_member_name": player_name},
                                                   {"guild_name": 1}).to_list(length=None)
    guild_names = [g["guild_name"] for g in matching_guilds]
    if not guild_names:
        return []
    await guilds_collection.update_many( {"archived_members": {"$ne": player_name},
                                          "guild_member.guild_member_name": player_name},
                                         {"$inc": {"guild_member.$[elem].guild_member_donation": donated_amount, "guild_member.$[elem].donations": donated_amount},
                                          "$push": {"guild_member.$[elem].recent_donations": {"donation_amount": donated_amount,
                                                                                              "timestamp": current_unix,
                                                                                              "donation_id": donation_id,
                                                                                              "donation_status": donation_status}}},
                                         array_filters=[{"elem.guild_member_name": player_name}])
    return guild_names


async def update_donation_amount_by_player_name_manually(member, donated_amount, donation_status, guild_id, dono_inc):
    guilds_collection = get_guilds_collection()
    donated_amount = int(donated_amount)
    current_unix = int(time.time())
    donation_id = member.name + str(current_unix)
    result = await guilds_collection.update_one({"guild_id": guild_id},
                                                [{"$set": {"guild_member": {"$map": {"input": "$guild_member",
                                                                                     "as": "m",
                                                                                     "in": {"$cond": [{"$or": [{"$eq": ["$$m.guild_member_name", member.name]},
                                                                                                               {"$eq": ["$$m.guild_member_id", member.id]}]},
                                                                                                      {"$mergeObjects": ["$$m",
                                                                                                                         {"recent_donations": {"$concatArrays": [{"$ifNull": ["$$m.recent_donations", []]},
                                                                                                                                                                 [{"donation_amount": donated_amount,
                                                                                                                                                                   "timestamp": current_unix,
                                                                                                                                                                   "donation_id": donation_id,
                                                                                                                                                                   "donation_status": donation_status}]]},
                                                                                                                          "donations": {"$cond": [dono_inc,
                                                                                                                                                  {"$add": [{"$ifNull": ["$$m.donations", 0]}, donated_amount ]},
                                                                                                                                                  {"$ifNull": ["$$m.donations", 0]}]},
                                                                                                                          "guild_member_id": member.id,
                                                                                                                          "guild_member_name": member.name } ]},
                                                                                                      "$$m"]}}}}}])
    if result.modified_count > 0:
        return "added"
    if result.matched_count == 0:
        return "no guild found"
    return "no changes"


async def set_guild_reset(guild_id, interval):
    guilds_collection = get_guilds_collection()
    result = await guilds_collection.update_one({"guild_id": guild_id}, {"$set": {"guild_reset": interval}})
    if result.modified_count > 0:
        return "edited"
    if result.matched_count == 0:
        return "no guild found"
    return "no changes"


async def set_guild_debt(guild_id, status):
    guilds_collection = get_guilds_collection()
    result = await guilds_collection.update_one({"guild_id": guild_id}, {"$set": {"guild_debt": status}})
    if result.modified_count > 0:
        return "edited"
    if result.matched_count == 0:
        return "no guild found"
    return "no changes"


async def update_donation_by_donation_id_manually(donation_id, new_amount, guild_id):
    guilds_collection = get_guilds_collection()
    donation_exists = await guilds_collection.find_one({"guild_id": guild_id, "guild_member.recent_donations.donation_id": donation_id})
    if not donation_exists:
        return "donation_id not found"
    result = await guilds_collection.update_one({"guild_id": guild_id, "guild_member.recent_donations.donation_id": donation_id},
                                                {"$set": {"guild_member.$[member].recent_donations.$[don].donation_amount": int(new_amount), "guild_member.$[member].recent_donations.$[don].donation_status": "manually"}},
                                                array_filters=[{"member.recent_donations.donation_id": donation_id},{"don.donation_id": donation_id}])
    if result.modified_count > 0:
        return "edited"
    if result.matched_count == 0:
        return "no guild found"
    return "no changes"


async def update_donations_weekly_automated():
    guilds_collection = get_guilds_collection()
    await guilds_collection.update_many({"guild_reset": "weekly"},
                                        [{"$set": {"guild_member": {"$map": {"input": "$guild_member",
                                                                             "as": "member",
                                                                             "in": {"$let": {"vars": {"is_threshold_2": {"$in": ["$$member.guild_member_id", {"$ifNull": ["$threshold_members", []]}]},
                                                                                                      "threshold_value": {"$cond": [{"$in": ["$$member.guild_member_id", {"$ifNull": ["$threshold_members", []]}]}, "$guild_threshold_2", "$guild_threshold"]}},
                                                                                             "in": {"$mergeObjects": ["$$member", {"donations": {"$cond": [{"$eq": [{"$ifNull": ["$guild_advanced_donation", True]}, True]},
                                                                                                                                                           {"$subtract": [{"$ifNull": ["$$member.donations", 0]},"$$threshold_value"]},
                                                                                                                                                           {"$cond": [{"$gte": [{"$ifNull": ["$$member.donations", 0]}, "$$threshold_value"]}, 0,
                                                                                                                                                                       {"$subtract": [{"$ifNull": ["$$member.donations", 0]}, "$$threshold_value"]}]}]}}]}}}}}}}])


async def update_donations_monthly_automated():
    guilds_collection = get_guilds_collection()
    await guilds_collection.update_many({"guild_reset": "monthly"},
                                        [{"$set": {"guild_member": {"$map": {"input": "$guild_member",
                                                                             "as": "member",
                                                                             "in": {"$let": {"vars": {"is_threshold_2": {"$in": ["$$member.guild_member_id", {"$ifNull": ["$threshold_members", []]}]},
                                                                                                      "threshold_value": {"$cond": [{"$in": ["$$member.guild_member_id", {"$ifNull": ["$threshold_members", []]}]}, "$guild_threshold_2", "$guild_threshold"]}},
                                                                                             "in": {"$mergeObjects": ["$$member", {"donations": {"$cond": [{"$eq": [{"$ifNull": ["$guild_advanced_donation", True]}, True]},
                                                                                                                                                           {"$subtract": [{"$ifNull": ["$$member.donations", 0]},"$$threshold_value"]},
                                                                                                                                                           {"$cond": [{"$gte": [{"$ifNull": ["$$member.donations", 0]}, "$$threshold_value"]}, 0,
                                                                                                                                                                       {"$subtract": [{"$ifNull": ["$$member.donations", 0]}, "$$threshold_value"]}]}]}}]}}}}}}}])


async def cleanse_donations_for_user(guild_id, member):
    guilds_collection = get_guilds_collection()
    result = await guilds_collection.update_one({"guild_id": guild_id,
                                                 "guild_member": {"$elemMatch": {"$or": [{"guild_member_name": member.name},
                                                                                         {"guild_member_id": member.id}]}}},
                                                {"$set": {"guild_member.$.donations": 0}})
    if result.modified_count > 0:
        return "edited"
    if result.matched_count == 0:
        return "no guild found"
    return "no changes"


async def enable_advanced_dono_per_guild(guild_id, status):
    guilds_collection = get_guilds_collection()
    result = await guilds_collection.update_one({"guild_id": guild_id}, {"$set": {"guild_advanced_donation": status}})
    if result.modified_count > 0:
        return "edited"
    if result.matched_count == 0:
        return "no guild found"
    return "no changes"


async def add_member_to_threshold_list(guild_id, guild_member):
    guilds_collection = get_guilds_collection()
    result = await guilds_collection.update_one({"guild_id": guild_id, "guild_member.guild_member_id": guild_member.id},
                                                {"$addToSet": {"threshold_members": guild_member.id}})
    if result.matched_count == 0:
        return "guild not found or member not in guild"
    if result.modified_count == 0:
        return "already in threshold"
    return "added to threshold"


# ------------------
# Delete
# ------------------


async def delete_guild_by_guild_id_from_guilds(guild_id):
    guilds_collection = get_guilds_collection()
    found_guild = await guilds_collection.find_one({"guild_id": guild_id})
    if found_guild is None:
        return "no guild found"
    else:
        await guilds_collection.delete_one({"guild_id": guild_id})
        return "guild deleted"


async def remove_guild_member(guild_id, guild_member: discord.User):
    guilds_collection = get_guilds_collection()
    result = await guilds_collection.update_one({"guild_id": guild_id},
                                                {"$pull": {"guild_member": {"guild_member_id": guild_member.id}}})
    if result.modified_count > 0:
        return "removed"
    if result.matched_count == 0:
        return "no guild found"
    result = await guilds_collection.update_one({"guild_id": guild_id},
                                                {"$pull": {"guild_member": {"guild_member_name": guild_member.name}}})
    if result.modified_count > 0:
        return "removed"
    return "member not found"


async def remove_member_from_archived_list(guild_id, guild_member):
    guilds_collection = get_guilds_collection()
    result = await guilds_collection.update_one({"guild_id": guild_id},
                                                {"$pull": {"archived_members": guild_member.id}})
    if result.modified_count > 0:
        return "removed"
    if result.matched_count == 0:
        return "no guild found"
    result = await guilds_collection.update_one({"guild_id": guild_id},
                                                {"$pull": {"archived_members": guild_member.name}})
    if result.modified_count > 0:
        return "removed"
    return "not in archive"


async def remove_player_donation_by_donation_id_in_one_guild(donation_id, guild_id):
    guilds_collection = get_guilds_collection()
    result = await guilds_collection.update_one({"guild_id": guild_id, "guild_member.recent_donations.donation_id": donation_id},
                                                {"$pull": {"guild_member.$[].recent_donations": {"donation_id": donation_id}}})
    if result.modified_count > 0:
        return "donation removed successfully"
    if result.matched_count == 0:
        return "no guild found"
    return "no changes"

async def remove_member_from_threshold_list(guild_id, guild_member):
    guilds_collection = get_guilds_collection()
    result = await guilds_collection.update_one({"guild_id": guild_id},
                                                {"$pull": {"threshold_members": guild_member.id}})
    if result.modified_count > 0:
        return "removed"
    if result.matched_count == 0:
        return "no guild found"
    result = await guilds_collection.update_one({"guild_id": guild_id},
                                                {"$pull": {"threshold_members": guild_member.name}})
    if result.modified_count > 0:
        return "removed"
    return "not in threshold"


async def get_raid_afk_ping_channel(guild_id) -> int | None:
    guilds_collection = get_guilds_collection()
    doc = await guilds_collection.find_one({"guild_id": guild_id}, {"raid_afk_ping_channel": 1})
    if doc:
        return doc.get("raid_afk_ping_channel")
    return None


async def set_raid_afk_ping_channel(guild_id, channel_id: int):
    guilds_collection = get_guilds_collection()
    await guilds_collection.update_one(
        {"guild_id": guild_id},
        {"$set": {"raid_afk_ping_channel": channel_id}},
        upsert=True)


async def set_weekly_donation_channel(guild_id, channel_id: int):
    guilds_collection = get_guilds_collection()
    await guilds_collection.update_one(
        {"guild_id": guild_id},
        {"$set": {"weekly_donation_channel_id": channel_id}}
    )


async def get_weekly_donation_channel(guild_id) -> int | None:
    guilds_collection = get_guilds_collection()
    doc = await guilds_collection.find_one(
        {"guild_id": guild_id},
        {"weekly_donation_channel_id": 1}
    )
    if doc:
        return doc.get("weekly_donation_channel_id")
    return None


async def set_breach_playbook_image_url(guild_id, image_url: str):
    guilds_collection = get_guilds_collection()
    await guilds_collection.update_one(
        {"guild_id": guild_id},
        {"$set": {"breach_playbook_image_url": image_url}},
        upsert=True
    )


async def get_breach_playbook_image_url(guild_id) -> str | None:
    guilds_collection = get_guilds_collection()
    doc = await guilds_collection.find_one(
        {"guild_id": guild_id},
        {"breach_playbook_image_url": 1}
    )
    if doc:
        return doc.get("breach_playbook_image_url")
    return None


async def set_breach_boss_info(guild_id, *, boss_name: str | None = None, image_url: str | None = None, phase: str | None = None, week_start: int | None = None):
    guilds_collection = get_guilds_collection()
    update_fields = {}
    if boss_name:
        update_fields["breach_boss_name"] = boss_name
    if image_url:
        update_fields["breach_boss_image_url"] = image_url
    if phase:
        update_fields["breach_boss_phase"] = phase
    if week_start is not None:
        update_fields["breach_boss_week_start"] = week_start
    if not update_fields:
        return
    await guilds_collection.update_one(
        {"guild_id": guild_id},
        {"$set": update_fields},
        upsert=True
    )


async def get_breach_boss_info(guild_id) -> dict:
    guilds_collection = get_guilds_collection()
    doc = await guilds_collection.find_one(
        {"guild_id": guild_id},
        {"breach_boss_name": 1, "breach_boss_image_url": 1, "breach_boss_phase": 1, "breach_boss_week_start": 1}
    )
    if not doc:
        return {}

    current_week_start = await time_calculations.get_last_monday_berlin_time_from_current_time_in_unix()
    if doc.get("breach_boss_week_start") != current_week_start:
        return {}

    return {
        "boss_name": doc.get("breach_boss_name"),
        "image_url": doc.get("breach_boss_image_url"),
        "phase": doc.get("breach_boss_phase"),
        "week_start": doc.get("breach_boss_week_start"),
    }

async def get_guilds_with_weekly_channel() -> list:
    """Trả về tất cả guild document có cấu hình weekly_donation_channel_id."""
    guilds_collection = get_guilds_collection()
    return await guilds_collection.find(
        {"weekly_donation_channel_id": {"$exists": True, "$ne": None}}
    ).to_list(length=None)


async def get_active_members(guild_id) -> list:
    """Trả về danh sách member chưa bị archive của guild."""
    guilds_collection = get_guilds_collection()
    pipeline = [
        {"$match": {"guild_id": guild_id}},
        {"$project": {
            "guild_member": {"$filter": {
                "input": "$guild_member",
                "as": "m",
                "cond": {"$and": [
                    {"$not": {"$in": ["$$m.guild_member_id", {"$ifNull": ["$archived_members", []]}]}},
                    {"$not": {"$in": ["$$m.guild_member_name", {"$ifNull": ["$archived_members", []]}]}}
                ]}
            }}
        }}
    ]
    result = await guilds_collection.aggregate(pipeline).to_list(length=1)
    if not result:
        return []
    return result[0].get("guild_member", [])
