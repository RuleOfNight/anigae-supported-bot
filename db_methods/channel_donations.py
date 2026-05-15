"""
CRUD cho collection `channel_donations`.

Mỗi document theo dõi số lần donate của 1 player trong 1 channel cụ thể,
bao gồm cả monthly count (tự reset theo tháng) và all-time count.
"""

from datetime import datetime, timezone

_collection = None


def init_collection(col) -> None:
    """Nhận collection từ general.connect_to_db."""
    global _collection
    _collection = col


def _current_month() -> str:
    """Trả về chuỗi tháng hiện tại dạng 'YYYY-MM'."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


async def record_donation(channel_id: int, player_name: str, discord_id, count: int = 1) -> tuple[int, int]:
    """
    Ghi nhận số lần donate của player trong channel.

    count = donate_amount // 50_000 (ví dụ 100k → count=2).

    - Nếu chưa có record → tạo mới.
    - Cùng tháng → tăng cả monthly và alltime theo count.
    - Khác tháng → reset monthly=count, cập nhật tháng, tăng alltime theo count.

    Trả về (monthly_count, alltime_count) sau khi cập nhật.
    """
    now_month = _current_month()
    existing = await _collection.find_one({"channel_id": channel_id, "player_name": player_name})

    if not existing:
        await _collection.insert_one({
            "channel_id":    channel_id,
            "player_name":   player_name,
            "discord_id":    discord_id,
            "alltime_count": count,
            "current_month": now_month,
            "monthly_count": count,
        })
        return count, count

    if existing["current_month"] == now_month:
        await _collection.update_one(
            {"_id": existing["_id"]},
            {"$inc": {"monthly_count": count, "alltime_count": count}},
        )
        return existing["monthly_count"] + count, existing["alltime_count"] + count

    # New month — reset monthly counter, keep alltime running
    new_alltime = existing["alltime_count"] + count
    await _collection.update_one(
        {"_id": existing["_id"]},
        {"$set": {
            "current_month": now_month,
            "monthly_count": count,
        }, "$inc": {"alltime_count": count}},
    )
    return count, new_alltime


async def get_channel_stats(channel_id: int) -> list[dict]:
    """
    Trả về tất cả record của channel, đã căn chỉnh monthly_count
    cho những player thuộc tháng cũ (count = 0 nếu tháng khác).

    Dùng để render embed stats.
    """
    now_month = _current_month()
    docs = await _collection.find({"channel_id": channel_id}).to_list(length=None)
    for doc in docs:
        if doc.get("current_month") != now_month:
            doc["monthly_count"] = 0
    return docs


async def get_channel_totals(channel_id: int) -> tuple[int, int]:
    """
    Trả về (tổng monthly, tổng alltime) của toàn bộ channel.

    monthly_count của player ở tháng cũ được tính là 0.
    """
    stats = await get_channel_stats(channel_id)
    monthly_total = sum(d["monthly_count"] for d in stats)
    alltime_total = sum(d["alltime_count"] for d in stats)
    return monthly_total, alltime_total


async def reset_monthly(channel_id: int) -> None:
    """
    Reset toàn bộ monthly_count về 0 cho channel.

    Được gọi bởi APScheduler vào ngày 1 hàng tháng.
    Việc reset monthly_count thực ra là lazy (tự reset khi có donate mới),
    nhưng hàm này đảm bảo totals hiển thị đúng ngay từ đầu tháng.
    """
    now_month = _current_month()
    await _collection.update_many(
        {"channel_id": channel_id, "current_month": {"$ne": now_month}},
        {"$set": {"monthly_count": 0, "current_month": now_month}},
    )
