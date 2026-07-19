import time
from bson import ObjectId
from misc.time_calculations import get_last_monday_berlin_time_from_current_time_in_unix

_collection = None


def init_collection(col):
    global _collection
    _collection = col


def get_collection():
    return _collection


def _public_doc(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
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
    return str(result_insert.inserted_id)


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
