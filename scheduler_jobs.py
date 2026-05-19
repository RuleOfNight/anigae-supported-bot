import discord
from datetime import datetime, timezone, timedelta
import runtime
from db_methods import guilds, players


async def monthly_guild():
    await guilds.update_donations_monthly_automated()


async def monthly_channel_donations():
    from db_methods import channel_donations
    from Commands.user_commands_on_message import MONTHLY_DONATION_CHANNEL_ID

    if MONTHLY_DONATION_CHANNEL_ID == 0:
        return

    channel = runtime.bot.get_channel(MONTHLY_DONATION_CHANNEL_ID)
    if channel:
        stats = await channel_donations.get_channel_stats(MONTHLY_DONATION_CHANNEL_ID)
        sorted_stats = sorted(stats, key=lambda d: d["monthly_count"], reverse=True)
        month_label = datetime.now(timezone.utc).strftime("%m/%Y")

        if sorted_stats:
            lines = []
            for i, doc in enumerate(sorted_stats, start=1):
                ping = f"<@{doc['discord_id']}>" if doc.get("discord_id") else f"`{doc['player_name']}`"
                lines.append(f"`#{i:>2}` {ping} — **{doc['monthly_count']} lần**")
            total = sum(d["monthly_count"] for d in sorted_stats)
            description = "\n".join(lines) + f"\n\n**Tổng kênh: {total} lần**"
        else:
            description = "*Không có dữ liệu trong tháng này.*"

        embed = discord.Embed(
            title=f"📅 Leaderboard Donate 50k — Tháng {month_label}",
            description=description,
            color=0x71368A,
        )
        embed.set_footer(text="Reset tháng mới bắt đầu.")
        await channel.send(embed=embed)

    await channel_donations.reset_monthly(MONTHLY_DONATION_CHANNEL_ID)


async def weekly_guild():
    await guilds.update_donations_weekly_automated()


async def daily_update():
    await players.decrement_all_premium_days()


async def weekly_donation_check():
    from db_methods import weekly_donations as wd
    from misc.time_calculations import get_last_monday_berlin_time_from_current_time_in_unix

    week_start = await get_last_monday_berlin_time_from_current_time_in_unix()
    guild_docs = await guilds.get_guilds_with_weekly_channel()

    for guild_doc in guild_docs:
        channel_id = guild_doc.get("weekly_donation_channel_id")
        guild_id = guild_doc["guild_id"]
        channel = runtime.bot.get_channel(channel_id)
        if not channel:
            continue

        members = await guilds.get_active_members(guild_id)
        if not members:
            continue

        paid_set = await wd.get_weekly_donors(channel_id, week_start)
        paid   = [m for m in members if m["guild_member_name"] in paid_set]
        unpaid = [m for m in members if m["guild_member_name"] not in paid_set]

        lines = []
        for m in paid:
            ping = f"<@{m['guild_member_id']}>" if m.get("guild_member_id") else f"**{m['guild_member_name']}**"
            lines.append(f"✅ {ping}")
        for m in unpaid:
            ping = f"<@{m['guild_member_id']}>" if m.get("guild_member_id") else f"**{m['guild_member_name']}**"
            lines.append(f"❌ {ping}")

        week_start_dt = datetime.fromtimestamp(week_start, tz=timezone.utc)
        week_end_dt   = week_start_dt + timedelta(days=6)
        week_label    = f"{week_start_dt.strftime('%d/%m')} – {week_end_dt.strftime('%d/%m')}"

        msg = (
            f"📋 **Kiểm tra đóng tiền tuần {week_label}**\n\n"
            + "\n".join(lines)
            + f"\n\nĐã đóng: **{len(paid)}/{len(members)}** | Chưa đóng: **{len(unpaid)}**"
        )
        await channel.send(msg)
