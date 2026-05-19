import random
import time as _time
import runtime
from db_methods import players, guilds


_RAID_AFK_MESSAGES = [
    "30 phút rồi chưa đánh raid, lề mề như này bao giờ có người yêu?",
    "Chết rồi hay gì mà không đánh raid?",
    "Không đánh tí drop được đúng cái nịt thì chịu",
    "Đánh raid when",
    "Boss nắc cho ngất rồi hay gì mà không đánh",
    "Raid chứ có phải người yêu đâu mà không đánh?",
    "Friendly remind: không đánh raid thì ăn kick",
    "Có quên cái gì không nhỉ",
    "Ăn ngủ có quên không mà quên không đánh raid?",
    "Hội đồng xét xử tuyên án bị cáo không chịu đánh raid với tội danh chậm tiến độ, đề nghị phạt bắt donate 100k",
    "Thanh kiếm chỉ sắc khi được rèn, còn bạn thì chỉ giá trị khi chịu đánh raid",
    "Không đánh raid thì để slot đấy cho người khác vào train, rảnh quá à?",
    "?",
    "Lại có mặt trong này rồi",
    "Fun fact: mấy người afk thường được cái nịt",
    "Đánh raid đi, không ai thương hại cho đâu",
    "Có biết thời gian là vàng bạc không?",
    "Thấy tôi rảnh lắm à? Đánh raid ngay",
    "Lại thấy tên này rồi",
]


async def check_raid_bt_pending():
    """Ping user nếu dùng .rd bt nhưng không confirm trong 6 phút."""
    now = _time.time()
    confirm_timeout = 6 * 60

    expired = {
        uid: data for uid, data in list(runtime.raid_bt_pending.items())
        if now - data["timestamp"] > confirm_timeout
    }
    for uid, data in expired.items():
        del runtime.raid_bt_pending[uid]
        channel = runtime.bot.get_channel(data["channel_id"])
        if not channel:
            continue
        member = channel.guild.get_member(uid) if channel.guild else None
        mention = member.mention if member else f"<@{uid}>"
        await channel.send(f"⚔️ {mention} Mắt mũi để đâu mà không ấn confirm raid?")


async def check_raid_afk():
    now = _time.time()
    afk_threshold  = 35 * 60
    tracker_ttl    = 3 * 60 * 60
    ping_cooldown  = 35 * 60
    raid_timeout   = 90 * 60

    for gid in [g for g, t in list(runtime.active_raid_guilds.items()) if now - t > raid_timeout]:
        del runtime.active_raid_guilds[gid]

    for uid in [u for u, t in list(runtime.raid_battle_tracker.items()) if now - t > tracker_ttl]:
        del runtime.raid_battle_tracker[uid]
        runtime.raid_afk_pinged.pop(uid, None)

    if not runtime.active_raid_guilds:
        return

    candidates = [
        uid for uid, t in runtime.raid_battle_tracker.items()
        if now - t > afk_threshold
        and now - runtime.raid_afk_pinged.get(uid, 0) > ping_cooldown
    ]
    if not candidates:
        return

    opted_in = await players.get_opted_in_discord_ids(candidates)
    if not opted_in:
        return

    for guild_id in list(runtime.active_raid_guilds.keys()):
        channel_id = await guilds.get_raid_afk_ping_channel(guild_id)
        if not channel_id:
            continue
        channel = runtime.bot.get_channel(channel_id)
        if not channel:
            continue
        guild_obj = runtime.bot.get_guild(guild_id)
        if not guild_obj:
            continue
        mentions = []
        for uid in opted_in:
            member = guild_obj.get_member(uid)
            if member:
                mentions.append(member.mention)
                runtime.raid_afk_pinged[uid] = now
        if mentions:
            msg = random.choice(_RAID_AFK_MESSAGES)
            await channel.send(f"⚔️ {' '.join(mentions)}\n{msg}")
