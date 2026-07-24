import time
from bson import ObjectId
from misc.time_calculations import get_last_monday_berlin_time_from_current_time_in_unix

_collection = None


def init_collection(col):
    global _collection
    _collection = col


def get_collection():
    return _collection


def _short_id_from_object_id(object_id) -> str:
    return str(object_id)[-6:]


def _public_doc(doc: dict) -> dict:
    doc = dict(doc)
    object_id = doc.pop("_id")
    doc["id"] = str(object_id)
    doc["short_id"] = doc.get("short_id") or _short_id_from_object_id(object_id)
    doc["upvote_count"] = len(doc.get("upvotes", []))
    return doc


async def add_breach_comp(
    guild_id: int,
    author_id: int,
    author_name: str,
    author_avatar_url: str | None,
    title: str | None,
    comp: str,
    phase: str | None = None,
    difficulty: str | None = None,
    rng: str | None = None,
    description: str | None = None,
    result: str | None = None,
) -> str:
    now = int(time.time())
    week_start = await get_last_monday_berlin_time_from_current_time_in_unix()
    clean_title = (title or "").strip() or f"Gi\u00e1o \u00e1n c\u1ee7a {author_name}"
    doc = {
        "guild_id": guild_id,
        "breach_week_start": week_start,
        "author_id": author_id,
        "author_name": author_name,
        "author_avatar_url": author_avatar_url,
        "title": clean_title[:80],
        "comp": comp.strip()[:900],
        "phase": (phase or "").strip()[:80],
        "difficulty": (difficulty or "").strip()[:80],
        "rng": (rng or "").strip()[:500],
        "description": (description or "").strip()[:900],
        "result": (result or "").strip()[:500],
        "upvotes": [],
        "created_at": now,
        "updated_at": now,
        "archived": False,
    }
    result_insert = await _collection.insert_one(doc)
    short_id = _short_id_from_object_id(result_insert.inserted_id)
    await _collection.update_one(
        {"_id": result_insert.inserted_id},
        {"$set": {"short_id": short_id}},
    )
    return short_id


async def get_breach_comps(guild_id: int) -> list[dict]:
    week_start = await get_last_monday_berlin_time_from_current_time_in_unix()
    pipeline = [
        {"$match": {"guild_id": guild_id,
                    "breach_week_start": week_start,
                    "archived": {"$ne": True}}},
        {"$addFields": {"upvote_count": {"$size": {"$ifNull": ["$upvotes", []]}}}},
        {"$sort": {"upvote_count": -1, "created_at": -1}},
    ]
    docs = await _collection.aggregate(pipeline).to_list(length=None)
    return [_public_doc(doc) for doc in docs]


async def toggle_upvote(comp_id: str, user_id: int) -> tuple[bool, int] | None:
    try:
        object_id = ObjectId(comp_id)
    except Exception:
        return None

    doc = await _collection.find_one({"_id": object_id, "archived": {"$ne": True}}, {"upvotes": 1})
    if not doc:
        return None

    upvotes = doc.get("upvotes", [])
    if user_id in upvotes:
        await _collection.update_one({"_id": object_id}, {"$pull": {"upvotes": user_id}})
        return False, max(0, len(upvotes) - 1)

    await _collection.update_one({"_id": object_id}, {"$addToSet": {"upvotes": user_id}})
    return True, len(set(upvotes + [user_id]))


async def update_breach_comp(
    comp_id: str,
    user_id: int,
    *,
    title: str | None = None,
    comp: str | None = None,
    phase: str | None = None,
    difficulty: str | None = None,
    rng: str | None = None,
    description: str | None = None,
    result: str | None = None,
) -> str:
    try:
        object_id = ObjectId(comp_id)
    except Exception:
        return "invalid_id"

    doc = await _collection.find_one({"_id": object_id, "archived": {"$ne": True}}, {"author_id": 1})
    if not doc:
        return "not_found"
    if doc.get("author_id") != user_id:
        return "not_owner"

    update_fields = {"updated_at": int(time.time())}
    if title is not None:
        update_fields["title"] = title.strip()[:80]
    if comp is not None:
        update_fields["comp"] = comp.strip()[:900]
    if phase is not None:
        update_fields["phase"] = phase.strip()[:80]
    if difficulty is not None:
        update_fields["difficulty"] = difficulty.strip()[:80]
    if rng is not None:
        update_fields["rng"] = rng.strip()[:500]
    if description is not None:
        update_fields["description"] = description.strip()[:900]
    if result is not None:
        update_fields["result"] = result.strip()[:500]

    await _collection.update_one({"_id": object_id}, {"$set": update_fields})
    return "updated"


async def archive_breach_comp(comp_id: str, user_id: int) -> str:
    try:
        object_id = ObjectId(comp_id)
    except Exception:
        return "invalid_id"

    doc = await _collection.find_one({"_id": object_id, "archived": {"$ne": True}}, {"author_id": 1})
    if not doc:
        return "not_found"
    if doc.get("author_id") != user_id:
        return "not_owner"

    await _collection.update_one(
        {"_id": object_id},
        {"$set": {"archived": True, "updated_at": int(time.time())}},
    )
    return "archived"


async def _find_breach_comp_by_plan_id(guild_id: int, plan_id: str, projection: dict | None = None) -> dict | None:
    plan_id = (plan_id or "").strip().lower()
    if not plan_id:
        return None

    week_start = await get_last_monday_berlin_time_from_current_time_in_unix()
    base_filter = {
        "guild_id": guild_id,
        "breach_week_start": week_start,
        "archived": {"$ne": True},
    }

    doc = None
    if len(plan_id) == 24:
        try:
            doc = await _collection.find_one({**base_filter, "_id": ObjectId(plan_id)}, projection)
        except Exception:
            doc = None
        if doc:
            return doc

    doc = await _collection.find_one({**base_filter, "short_id": plan_id}, projection)
    if doc:
        return doc

    candidates = await _collection.find(base_filter, projection).to_list(length=None)
    matches = [candidate for candidate in candidates if str(candidate.get("_id", "")).lower().endswith(plan_id)]
    if len(matches) == 1:
        return matches[0]
    return None


async def get_breach_comp_by_plan_id(guild_id: int, plan_id: str) -> dict | None:
    doc = await _find_breach_comp_by_plan_id(guild_id, plan_id)
    return _public_doc(doc) if doc else None


async def update_breach_comp_by_plan_id(
    guild_id: int,
    plan_id: str,
    user_id: int,
    *,
    title: str | None = None,
    comp: str | None = None,
    phase: str | None = None,
    difficulty: str | None = None,
    rng: str | None = None,
    description: str | None = None,
    result: str | None = None,
) -> str:
    doc = await _find_breach_comp_by_plan_id(guild_id, plan_id, {"author_id": 1})
    if not doc:
        return "not_found"
    if doc.get("author_id") != user_id:
        return "not_owner"

    update_fields = {"updated_at": int(time.time())}
    if title is not None:
        update_fields["title"] = title.strip()[:80]
    if comp is not None:
        update_fields["comp"] = comp.strip()[:900]
    if phase is not None:
        update_fields["phase"] = phase.strip()[:80]
    if difficulty is not None:
        update_fields["difficulty"] = difficulty.strip()[:80]
    if rng is not None:
        update_fields["rng"] = rng.strip()[:500]
    if description is not None:
        update_fields["description"] = description.strip()[:900]
    if result is not None:
        update_fields["result"] = result.strip()[:500]

    await _collection.update_one({"_id": doc["_id"]}, {"$set": update_fields})
    return "updated"


async def archive_breach_comp_by_plan_id(guild_id: int, plan_id: str, user_id: int) -> str:
    doc = await _find_breach_comp_by_plan_id(guild_id, plan_id, {"author_id": 1})
    if not doc:
        return "not_found"
    if doc.get("author_id") != user_id:
        return "not_owner"

    await _collection.update_one(
        {"_id": doc["_id"]},
        {"$set": {"archived": True, "updated_at": int(time.time())}},
    )
    return "archived"
