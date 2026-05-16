import re
import discord
import asyncio
import json
import io
import os
import random
import runtime
from aiohttp import web

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from dotenv import load_dotenv

load_dotenv()
from discord.ext import commands, tasks
from discord import app_commands, Container
from db_methods import cards, general, players, guilds
from Commands import help_def_v2, user_commands_on_message, user_commands_on_message_v2
from Commands.admin_commands import AdminCommands
from Commands.user_commands_prefix import UserCommandsPrefix
from Commands.user_commands_prefix_v2 import UserCommandsPrefix_v2
from Commands.user_commands_slash import UserCommandsSlash
import pytz
from pytz import utc
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


async def get_prefix(bot, message):
    prefixes = await runtime.retrieve_data("prefixes")
    return prefixes.get(str(message.guild.id), default_prefix)


intents = discord.Intents.default()
intents.message_content = True
default_prefix = "5"
bot = commands.AutoShardedBot(command_prefix=get_prefix, intents=intents, help_command=None, max_messages=100)
bot.prefixes = {}
bot.event_cards = {}
bot.locations = {}
bot.raid_comps = {}
runtime.bot = bot
tree = bot.tree
scheduler = AsyncIOScheduler(timezone=pytz.UTC)

own_bot_id = 1213054068197560331
target_bot_id = 571027211407196161
keyword_raid_lobby_1 = "Raid Challenge Timer"
keyword_raid_lobby_2 = "Raid Lobby Timer"
keyword_raid_lobby_2_part_2 = "Raid Party"
keyword_raid_lobby_4 = "Energy"
keyword_raid_lobby_5 = "confirm the battle!"
keyword_raid_lobby_3 = "Raid Boss Battle"
keyword_raid_lobby_9 = ".rd lobbies -"
keyword_10_1 = " currently has "
keyword_10_2 = "gold"
keyword_10_3 = "Clan Rubies"
keyword_11_1 = " you currently have "
keyword_11_2 = "stamina"
keyword_12 = "to your clan, and received"
keyword_13 = "Summoner ID:"
keyword_14 = "Raid Pass(es)"
keyword_15 = "EXP"
keyword_16 = "you have dealt:"  # xác nhận .rd bt hoàn thành


@bot.command()
@commands.has_permissions(administrator=True)
async def setprefix(ctx, new_prefix):
    prefixes = await runtime.retrieve_data("prefixes")
    prefixes[str(ctx.guild.id)] = new_prefix
    general.save_prefixes(prefixes)
    await ctx.send(f"Prefix changed to `{new_prefix}` !")


def create_embed(title, description, footer, image_url=None, thumbnail_url=None):
    embed = discord.Embed(title=title, description=description, color=0x71368A)
    if footer:
        embed.set_footer(text=footer)
    if image_url:
        embed.set_image(url=image_url)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    return embed


async def reaction_add_listener(payload):
    await user_commands_on_message_v2.on_raw_reaction_add(payload, bot)

async def monthly_guild():
    await guilds.update_donations_monthly_automated()

async def monthly_channel_donations():
    from db_methods import channel_donations
    from Commands.user_commands_on_message import MONTHLY_DONATION_CHANNEL_ID
    from datetime import datetime, timezone
    if MONTHLY_DONATION_CHANNEL_ID == 0:
        return

    # Gửi leaderboard tháng này trước khi reset
    channel = bot.get_channel(MONTHLY_DONATION_CHANNEL_ID)
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
    import time as _time
    now = _time.time()
    confirm_timeout = 6 * 60

    expired = {
        uid: data for uid, data in list(runtime.raid_bt_pending.items())
        if now - data["timestamp"] > confirm_timeout
    }
    for uid, data in expired.items():
        del runtime.raid_bt_pending[uid]
        channel = bot.get_channel(data["channel_id"])
        if not channel:
            continue
        member = channel.guild.get_member(uid) if channel.guild else None
        mention = member.mention if member else f"<@{uid}>"
        await channel.send(
            f"⚔️ {mention} Mắt mũi để đâu mà không ấn confirm raid?",
        )


async def check_raid_afk():
    import time as _time
    now = _time.time()
    afk_threshold  = 35 * 60   # ping sau 35 phút không dùng .rd bt
    tracker_ttl    = 3 * 60 * 60  # xóa khỏi tracker sau 3 giờ (raid đã xong)
    ping_cooldown  = 35 * 60   # không ping lại cùng 1 người trong vòng 35 phút
    raid_timeout   = 90 * 60   # xóa guild khỏi active_raid sau 90 phút không thấy embed

    # Dọn guild raid hết hạn
    for gid in [g for g, t in list(runtime.active_raid_guilds.items()) if now - t > raid_timeout]:
        del runtime.active_raid_guilds[gid]

    # Dọn user tracker hết hạn
    for uid in [u for u, t in list(runtime.raid_battle_tracker.items()) if now - t > tracker_ttl]:
        del runtime.raid_battle_tracker[uid]
        runtime.raid_afk_pinged.pop(uid, None)

    if not runtime.active_raid_guilds:
        return

    # Tìm user đã dùng .rd bt nhưng không đánh lại trong 35 phút và chưa bị ping gần đây
    candidates = [
        uid for uid, t in runtime.raid_battle_tracker.items()
        if now - t > afk_threshold
        and now - runtime.raid_afk_pinged.get(uid, 0) > ping_cooldown
    ]
    if not candidates:
        return

    # Lọc những user đã opt-in
    opted_in = await players.get_opted_in_discord_ids(candidates)
    if not opted_in:
        return

    for guild_id in list(runtime.active_raid_guilds.keys()):
        channel_id = await guilds.get_raid_afk_ping_channel(guild_id)
        if not channel_id:
            continue
        channel = bot.get_channel(channel_id)
        if not channel:
            continue
        guild_obj = bot.get_guild(guild_id)
        if not guild_obj:
            continue
        mentions = []
        for uid in opted_in:
            member = guild_obj.get_member(uid)
            if member:
                mentions.append(member.mention)
                runtime.raid_afk_pinged[uid] = now  # ghi nhận đã ping
        if mentions:
            msg = random.choice(_RAID_AFK_MESSAGES)
            await channel.send(f"⚔️ {' '.join(mentions)}\n{msg}")


@bot.event
async def on_ready():
    print(f"✅ Startup complete. Bot running on {len(bot.guilds)} server with {bot.shard_count} shards.")
    print("on_ready")
    await general.connect_to_db()
    runtime.db_ready = True
    await bot.add_cog(UserCommandsPrefix(bot))
    await bot.add_cog(UserCommandsPrefix_v2(bot))
    await bot.load_extension("Commands.user_commands_slash")
    admin_cog = AdminCommands(bot)
    await bot.add_cog(admin_cog)
    bot.add_listener(reaction_add_listener, "on_raw_reaction_add")
    if not scheduler.running:
        scheduler.add_job(monthly_guild, CronTrigger(day=1, hour=1, minute=0, timezone=utc), id="monthly_guild")
        scheduler.add_job(monthly_channel_donations, CronTrigger(day=1, hour=1, minute=0, timezone=utc), id="monthly_channel_donations")
        scheduler.add_job(weekly_guild, CronTrigger(day_of_week=0, hour=1, minute=0, timezone=utc), id="weekly_guild")
        scheduler.add_job(daily_update, CronTrigger(hour=1, minute=0, timezone=utc), id="daily_update")
        scheduler.add_job(check_raid_afk, "interval", minutes=10, id="check_raid_afk")
        scheduler.add_job(check_raid_bt_pending, "interval", minutes=3, id="check_raid_bt_pending")
        scheduler.start()
        print("[GUILD SCHEDULER] Guild scheduler has been started successfully.")
        print(f"[GUILD SCHEDULER] Jobs: {scheduler.get_jobs()}")
    try:
        with open(os.path.join(BASE_DIR, "data/event_cards.json"), "r", encoding="utf-8") as f:
            bot.event_cards = json.load(f)
        with open(os.path.join(BASE_DIR, "data/locations.json"), "r", encoding="utf-8") as f:
            bot.locations = json.load(f)
        with open(os.path.join(BASE_DIR, "data/prefixes.json"), "r", encoding="utf-8") as f:
            bot.prefixes = json.load(f)
        with open(os.path.join(BASE_DIR, "data/raid_comps.json"), "r", encoding="utf-8") as f:
            bot.raid_comps = json.load(f)
        print("[JSON] Files loaded into memory.")
    except Exception as e:
        print(f"[JSON] Failed to load JSON files: {e}")
    try:
        base_tick_daily_watch = await general.get_global_daily_watch_timer()
        bot.loop.create_task(admin_cog.sync_and_start_rotation_task(base_tick_daily_watch, bot))
        print("[DAILY WATCH] Daily watch timer started.")
    except Exception as e:
        print(f"[DAILY WATCH] An error occurred while starting daily watch timer: {e}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"An error occurred while syncing: {e}")
    await update_activity.start()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error.original, NotFound):
        return
    elif isinstance(error, MissingPermissions):
        return
    else:
        return

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    message = "An error occurred while executing the command."
    if isinstance(error, app_commands.MissingPermissions):
        message = "You are missing Administrator permissions."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


# -------------------
# Slash Command for Developer Badge
# -------------------
@bot.tree.command(name="ping", description="Show's the ping of the bot.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! 🏓 ({round(bot.latency * 1000)} ms)")


@tasks.loop(minutes=30)
async def update_activity():
    try:
        server_count = len(bot.guilds)
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"{server_count} Server")
        await bot.change_presence(activity=activity)
    except Exception as e:
        print("Error updating activity:", e)


@bot.event
async def on_message(message):
    if not runtime.db_ready:
        return
    if message.author.bot:
        if message.author.id == target_bot_id:
            if message.components:
                if message.components and isinstance(message.components[0], Container):
                    await user_commands_on_message_v2.discord_components_v2(message, "on_message")
            if message.embeds:
                embed = message.embeds[0]
                embed_title = embed.title if embed.title else ""
                embed_description = embed.description if embed.description else ""
                embed_footer = embed.footer.text if embed.footer else ""
                embed_fields = embed.fields
                embed_image_url = embed.image.url if embed.image else None
                embed_thumbnail_url = embed.thumbnail.url if embed.thumbnail else None
                if keyword_13 in embed_footer:
                    await user_commands_on_message.profile_tracker(embed_fields, embed_footer)
                    await bot.process_commands(message)
                if keyword_raid_lobby_1 in embed_title:
                    if keyword_raid_lobby_4 in embed_footer:
                        import time as _time
                        runtime.active_raid_guilds[message.guild.id] = _time.time()
                        embed_title, embed_description, embed_footer = await user_commands_on_message.in_raid_lobby(embed_title, embed_description, embed_footer, message.guild.id)
                        new_embed = create_embed(embed_title, embed_description, embed_footer, embed_image_url, embed_thumbnail_url)
                        view = user_commands_on_message.DeleteButtonView()
                        await message.channel.send(embed=new_embed, view=view)
                        try:
                            await message.delete()
                        except (discord.errors.NotFound, discord.errors.Forbidden):
                            pass
                        finally:
                            await bot.process_commands(message)
                elif keyword_raid_lobby_2 in embed_title:
                    if keyword_raid_lobby_2_part_2 in embed_footer:
                        embed_title, embed_description, embed_footer = await user_commands_on_message.raid_lobby_waiting_room(embed_title, embed_description, embed_footer)
                        new_embed = create_embed(embed_title, embed_description, embed_footer, embed_image_url, embed_thumbnail_url)
                        view = user_commands_on_message.DeleteButtonView()
                        await message.channel.send(embed=new_embed, view=view)
                        try:
                            await message.delete()
                        except (discord.errors.NotFound, discord.errors.Forbidden):
                            pass
                        finally:
                            await bot.process_commands(message)
                elif keyword_raid_lobby_5 in embed_footer:
                    if keyword_raid_lobby_3 in embed_title:
                        embed_field_2 = embed.fields[1] if len(embed.fields) > 1 else None
                        player_status = await players.get_player_status_team_check(embed.author.name)
                        if player_status == "None":
                            await bot.process_commands(message)
                        elif player_status == "Yes":
                            team_value = await user_commands_on_message.raid_team_check(embed_fields[0] if embed_fields else None, embed_field_2)
                            if team_value == 2:
                                warning_text = ("# <a:police_blue:1332801472894603294><a:police_red:1332801457006710794><a:police_blue:1332801472894603294><a:police_red:1332801457006710794><a:police_blue:1332801472894603294><a:police_red:1332801457006710794>"
                                                "<a:police_blue:1332801472894603294><a:police_red:1332801457006710794><a:police_blue:1332801472894603294><a:police_red:1332801457006710794>\n"
                                                "# <a:police_blue:1332801472894603294> **Are you sure about this?** <a:police_red:1332801457006710794>\n"
                                                "# <a:police_blue:1332801472894603294><a:police_red:1332801457006710794><a:police_blue:1332801472894603294><a:police_red:1332801457006710794><a:police_blue:1332801472894603294><a:police_red:1332801457006710794>"
                                                "<a:police_blue:1332801472894603294><a:police_red:1332801457006710794><a:police_blue:1332801472894603294><a:police_red:1332801457006710794>\n")
                                await message.channel.send(warning_text)
                            else:
                                await bot.process_commands(message)
                        else:
                            await bot.process_commands(message)
                    else:
                        await bot.process_commands(message)
                    await bot.process_commands(message)
                elif keyword_16 in embed_description or any(keyword_16 in (f.value or "") for f in embed_fields):
                    # Xác nhận .rd bt: embed "Summoner USERNAME, you have dealt:"
                    import time as _time
                    full_text = embed_description + " ".join(f.value or "" for f in embed_fields)
                    username_match = re.search(r"Summoner (\S+),", full_text)
                    if username_match:
                        username = username_match.group(1).lower()
                        for uid, data in list(runtime.raid_bt_pending.items()):
                            game_name = data.get("game_name")
                            ch_id = data.get("channel_id")
                            if (game_name and game_name.lower() == username) or \
                               (not game_name and ch_id == message.channel.id):
                                del runtime.raid_bt_pending[uid]
                                runtime.raid_battle_tracker[uid] = _time.time()
                                runtime.raid_afk_pinged.pop(uid, None)
                                break
                    await bot.process_commands(message)
                elif keyword_12 in embed_description:
                    await user_commands_on_message.clan_donation_tracker(embed_description, message)
                else:
                    await bot.process_commands(message)
            elif keyword_10_1 in message.content:
                if keyword_10_2 in message.content or keyword_10_3 in message.content:
                    player_name, embed_text = await user_commands_on_message.player_gold_and_rubies_command(message)
                    if embed_text == "player not found":
                        await bot.process_commands(message)
                    else:
                        gold_and_rubies_embed = discord.Embed(title=None, description=None, color=0x71368A)
                        gold_and_rubies_embed.add_field(name=f"**{player_name}** currently has:", value=f"{embed_text}", inline=False)
                        gold_and_rubies_embed.set_footer(text="There can be issues with the displayed amount! Please double check if the amount is correct.")
                        gold_and_rubies_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg")
                        view = user_commands_on_message.DeleteButtonView()
                        try:
                            await message.reply(embed=gold_and_rubies_embed, view=view)
                        except discord.HTTPException:
                            await message.channel.send(embed=gold_and_rubies_embed, view=view)
                        await bot.process_commands(message)
                elif keyword_14 in message.content:
                    await user_commands_on_message_v2.raid_pass_v2(message)
                else:
                    await bot.process_commands(message)
            elif keyword_11_1 in message.content:
                if keyword_11_2 in message.content:
                    await user_commands_on_message_v2.player_stamina_v2(message)
                    await bot.process_commands(message)
                else:
                    await bot.process_commands(message)
            elif keyword_15 in message.content:
                await user_commands_on_message_v2.player_lvl_v2(message)
            else:
                await bot.process_commands(message)
        else:
            await bot.process_commands(message)
    elif re.match(r'^\.rd\s+bt(\s+(all|max|\d+))?$', message.content.strip(), re.IGNORECASE):
        import time as _time
        _now = _time.time()
        # Bắt đầu đếm 35 phút AFK ngay từ lúc gõ lệnh
        runtime.raid_battle_tracker[message.author.id] = _now
        runtime.raid_afk_pinged.pop(message.author.id, None)
        # Lưu game name để match với confirm embed (không cần DB lookup lúc confirm)
        game_name = await guilds.get_member_game_name_by_discord_id(message.author.id)
        runtime.raid_bt_pending[message.author.id] = {
            "timestamp":  _now,
            "channel_id": message.channel.id,
            "game_name":  game_name,
        }
        await bot.process_commands(message)
    elif keyword_raid_lobby_9 in message.content:
        delete_value = await players.get_raid_search_history_delete_for_players_by_player_id(message.author.id, message.author.name)
        if delete_value == "yes":
            try:
                await message.delete()
            except (discord.errors.NotFound, discord.errors.Forbidden):
                pass
            finally:
                await bot.process_commands(message)
        else:
            await bot.process_commands(message)
    elif bot.user.mentioned_in(message) and "@everyone" not in message.content and "@here" not in message.content:
        if message.reference is not None:
            return
        view = await help_def_v2.help_v2(message)
        await message.channel.send(view=view)
    else:
        await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    if after.author.bot:
        if after.author.id == target_bot_id:
            if after.components:
                if isinstance(after.components[0], Container):
                    await user_commands_on_message_v2.discord_components_v2(after, "on_edit")


@bot.event
async def on_close():
    general.client_db.close()
    print("[DATABASE] Database connection closed.")

async def health_check(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[WEB] Health check server running on port {port}")

async def main():
    await start_web_server()
    await bot.start(os.getenv("DISCORD_TOKEN"))


asyncio.run(main())

#bot.run(os.getenv("DISCORD_TOKEN"))          

