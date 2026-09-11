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
        # Lấy tháng trước — scheduler chạy ngày 1 tháng mới nên cần tháng vừa kết thúc
        now = datetime.now(timezone.utc)
        last_month_dt = (now.replace(day=1) - timedelta(days=1))
        last_month_str = last_month_dt.strftime("%Y-%m")
        month_label = last_month_dt.strftime("%m/%Y")

        stats = await channel_donations.get_month_stats(MONTHLY_DONATION_CHANNEL_ID, last_month_str)
        sorted_stats = sorted(stats, key=lambda d: d["monthly_count"], reverse=True)

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
            title=f"📅 Bảng vàng UR — Tháng {month_label}",
            description=description,
            color=0x71368A,
        )
        embed.set_footer(text="Reset tháng mới bắt đầu.")
        await channel.send(embed=embed)

    await channel_donations.reset_monthly(MONTHLY_DONATION_CHANNEL_ID)


async def weekly_guild():
    from db_methods import weekly_donations as wd
    from misc.time_calculations import get_last_monday_berlin_time_from_current_time_in_unix

    week_start = await get_last_monday_berlin_time_from_current_time_in_unix()
    for guild_doc in await guilds.get_weekly_guilds():
        channel_id = guild_doc.get("weekly_donation_channel_id")
        waived = await guilds.get_breach_manual_waivers(guild_doc["guild_id"], week_start)
        if waived is None:
            waived = await wd.get_weekly_waivers(channel_id, week_start) if channel_id else set()
        await guilds.update_donations_weekly_automated(guild_doc["guild_id"], waived)


async def daily_update():
    await players.decrement_all_premium_days()


async def weekly_donation_check():
    from db_methods import weekly_donations as wd
    from misc.time_calculations import get_last_monday_berlin_time_from_current_time_in_unix

    # Runs at 00:00 Monday in Vietnam, before the 01:00 UTC clan reset.
    # The report is for the incoming week targeted by Sunday's Breach result.
    week_start = (
        await get_last_monday_berlin_time_from_current_time_in_unix()
    ) + wd.WEEK_SECONDS
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

        waived_set = await guilds.get_breach_manual_waivers(guild_id, week_start)
        if waived_set is None:
            covered_set = await wd.get_weekly_donors(channel_id, week_start)
            waived_set = await wd.get_weekly_waivers(channel_id, week_start)
        else:
            covered_set = waived_set
        covered = [m for m in members if m["guild_member_name"] in covered_set]
        needs_payment = [m for m in members if m["guild_member_name"] not in covered_set]

        lines = []
        for member in covered:
            ping = f"<@{member['guild_member_id']}>" if member.get("guild_member_id") else f"**{member['guild_member_name']}**"
            reason = "miễn nhờ Breach" if member["guild_member_name"] in waived_set else "đã đóng trước"
            lines.append(f"✅ {ping} — {reason}")
        for member in needs_payment:
            ping = f"<@{member['guild_member_id']}>" if member.get("guild_member_id") else f"**{member['guild_member_name']}**"
            lines.append(f"❌ {ping} — cần đóng tuần này")

        week_start_dt = datetime.fromtimestamp(week_start, tz=timezone.utc)
        week_end_dt = week_start_dt + timedelta(days=6)
        week_label = f"{week_start_dt.strftime('%d/%m')} – {week_end_dt.strftime('%d/%m')}"

        msg = (
            f"📋 **Donate clan tuần {week_label}**\n\n"
            + "\n".join(lines)
            + f"\n\nKhông cần đóng: **{len(covered)}/{len(members)}**"
            + f" | Cần đóng: **{len(needs_payment)}**"
        )
        await channel.send(msg)
