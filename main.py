import re
import discord
import asyncio
import json
import os
import random
import runtime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from dotenv import load_dotenv

load_dotenv()
from discord.ext import commands, tasks
from discord import app_commands, Container
from db_methods import general, players, guilds
from Commands import changelog, help_def_v2, user_commands_on_message, user_commands_on_message_v2
from Commands.admin_commands import AdminCommands
from Commands.user_commands_prefix import UserCommandsPrefix
from Commands.user_commands_prefix_v2 import UserCommandsPrefix_v2
from Commands.user_commands_simulator import SimulatorCommand
import pytz
from pytz import utc
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from scheduler_jobs import (
    monthly_guild, monthly_channel_donations,
    weekly_guild, daily_update, weekly_donation_check,
)
from raid_afk import check_raid_afk, check_raid_bt_pending
from web_server import start_web_server


# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------

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


async def _changelog_tree_interaction_check(interaction: discord.Interaction) -> bool:
    await changelog.maybe_schedule_changelog_for_interaction(bot, interaction)
    return True


tree.interaction_check = _changelog_tree_interaction_check
scheduler = AsyncIOScheduler(timezone=pytz.UTC)

own_bot_id = 1213054068197560331
target_bot_id = 571027211407196161

# Keywords for on_message routing
# Title changed: "Raid Challenge Timer" → "Raid Challenge Party" (bot gốc update)
keyword_raid_lobby_title_old = "Raid Challenge Timer"
keyword_raid_lobby_title_new = "Raid Challenge Party"
keyword_raid_lobby_2_part_2  = "Current Raid Participants"
keyword_raid_lobby_3   = "Raid Boss Battle"
# These keywords may now appear in description instead of footer
keyword_raid_lobby_4   = "Type .rd battle when you have Energy!"
keyword_raid_lobby_5   = "confirm the battle!"
keyword_raid_lobby_9   = ".rd lobbies -"
keyword_10_1 = " currently has "
keyword_10_2 = "gold"
keyword_10_3 = "Clan Rubies"
keyword_11_1 = " you currently have "
keyword_11_2 = "stamina"
keyword_12  = "to your clan, and received"
keyword_13  = "Summoner ID:"
keyword_14  = "Raid Pass(es)"
keyword_15  = "EXP"
keyword_16  = "you have dealt:"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

@bot.event
async def on_ready():
    print(f"✅ Startup complete. Bot running on {len(bot.guilds)} server with {bot.shard_count} shards.")
    print("on_ready")
    await general.connect_to_db()
    runtime.db_ready = True
    await bot.add_cog(UserCommandsPrefix(bot))
    await bot.add_cog(UserCommandsPrefix_v2(bot))
    await bot.add_cog(SimulatorCommand(bot))
    await bot.load_extension("Commands.user_commands_slash")
    admin_cog = AdminCommands(bot)
    await bot.add_cog(admin_cog)
    bot.add_listener(reaction_add_listener, "on_raw_reaction_add")

    if not scheduler.running:
        scheduler.add_job(monthly_guild,              CronTrigger(day=1,           hour=1, minute=0, timezone=utc), id="monthly_guild")
        scheduler.add_job(monthly_channel_donations,  CronTrigger(day=1,           hour=1, minute=0, timezone=utc), id="monthly_channel_donations")
        scheduler.add_job(weekly_guild,               CronTrigger(day_of_week=0,   hour=1, minute=0, timezone=utc), id="weekly_guild")
        scheduler.add_job(weekly_donation_check,      CronTrigger(day_of_week=0,   hour=0, minute=0, timezone=ZoneInfo("Asia/Bangkok")), id="weekly_donation_check")
        scheduler.add_job(daily_update,               CronTrigger(                 hour=1, minute=0, timezone=utc), id="daily_update")
        scheduler.add_job(check_raid_afk,             "interval", minutes=10,  id="check_raid_afk")
        scheduler.add_job(check_raid_bt_pending,      "interval", minutes=3,   id="check_raid_bt_pending")
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
    return


@bot.after_invoke
async def send_changelog_after_prefix_command(ctx):
    await changelog.maybe_send_changelog_for_message(ctx.message)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    message = "An error occurred while executing the command."
    if isinstance(error, app_commands.MissingPermissions):
        message = "You are missing Administrator permissions."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


@bot.event
async def on_message_edit(before, after):
    if after.author.bot and after.author.id == target_bot_id:
        if after.components and isinstance(after.components[0], Container):
            await user_commands_on_message_v2.discord_components_v2(after, "on_edit")


@bot.event
async def on_raw_message_edit(payload):
    # on_message_edit only fires for cached messages. Fetch uncached page edits so
    # every Breach standings page is still processed in busy channels.
    if payload.cached_message is not None or not runtime.db_ready:
        return
    try:
        channel = bot.get_channel(payload.channel_id) or await bot.fetch_channel(payload.channel_id)
        after = await channel.fetch_message(payload.message_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return
    if after.author.id == target_bot_id and after.components and isinstance(after.components[0], Container):
        await user_commands_on_message_v2.discord_components_v2(after, "on_edit")


@bot.event
async def on_close():
    general.client_db.close()
    print("[DATABASE] Database connection closed.")


# ---------------------------------------------------------------------------
# Slash commands
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# on_message router
# ---------------------------------------------------------------------------

@bot.event
async def on_message(message):
    if not runtime.db_ready:
        return

    if message.author.bot:
        if message.author.id != target_bot_id:
            await bot.process_commands(message)
            return

        if message.components and isinstance(message.components[0], Container):
            await user_commands_on_message_v2.discord_components_v2(message, "on_message")

        if message.embeds:
            await _handle_embed(message)
        elif "has already been defeated" in message.content:
            await _handle_raid_already_defeated(message)
        elif keyword_10_1 in message.content:
            await _handle_gold_rubies_or_raid_pass(message)
        elif keyword_11_1 in message.content and keyword_11_2 in message.content:
            await user_commands_on_message_v2.player_stamina_v2(message)
            await bot.process_commands(message)
        elif keyword_15 in message.content:
            await user_commands_on_message_v2.player_lvl_v2(message)
        else:
            await bot.process_commands(message)
        return

    # Non-bot messages
    if re.match(r'^\.rd\s+bt(\s+(all|max|\d+))?$', message.content.strip(), re.IGNORECASE):
        await _handle_rd_bt(message)
        await changelog.maybe_send_changelog_for_message(message)
    elif keyword_raid_lobby_9 in message.content:
        await _handle_rd_lobbies(message)
        await changelog.maybe_send_changelog_for_message(message)
    elif bot.user.mentioned_in(message) and "@everyone" not in message.content and "@here" not in message.content:
        if message.reference is None:
            view = await help_def_v2.help_v2(message)
            await message.channel.send(view=view)
            await changelog.maybe_send_changelog_for_message(message)
    else:
        await bot.process_commands(message)


async def _handle_embed(message):
    embed = message.embeds[0]
    embed_title       = embed.title or ""
    embed_description = embed.description or ""
    embed_footer      = embed.footer.text if embed.footer else ""
    embed_fields      = embed.fields
    embed_image_url   = embed.image.url if embed.image else None
    embed_thumb_url   = embed.thumbnail.url if embed.thumbnail else None

    # Combine all text for keyword searching (bot gốc moves keywords between fields)
    _all_text = f"{embed_title}\n{embed_description}\n{embed_footer}"

    if keyword_13 in embed_footer:
        await user_commands_on_message.profile_tracker(embed_fields, embed_footer)
        await user_commands_on_message.replace_profile_embed(message)
        await bot.process_commands(message)
        return

    # Detect raid embed: title or description contains raid keywords
    is_raid_embed = (keyword_raid_lobby_title_old in _all_text
                     or keyword_raid_lobby_title_new in _all_text)

    if is_raid_embed:
        has_battle_hint = keyword_raid_lobby_4 in _all_text  # "Type .rd battle when you have Energy!"
        has_participants = keyword_raid_lobby_2_part_2 in _all_text  # "Current Raid Participants"

        if has_battle_hint:
            # Active raid lobby (players are attacking)
            import time as _time
            runtime.active_raid_guilds[message.guild.id] = _time.time()
            t, d, f = await user_commands_on_message.in_raid_lobby(
                embed_title, embed_description, embed_footer
            )
            await _replace_embed(message, t, d, f, embed_image_url, embed_thumb_url)
        elif has_participants:
            # Waiting room (lobby not started yet)
            t, d, f = await user_commands_on_message.raid_lobby_waiting_room(
                embed_title, embed_description, embed_footer
            )
            await _replace_embed(message, t, d, f, embed_image_url, embed_thumb_url)
        else:
            await bot.process_commands(message)

    elif keyword_raid_lobby_5 in _all_text and keyword_raid_lobby_3 in _all_text:
        embed_field_2 = embed_fields[1] if len(embed_fields) > 1 else None
        player_status = await players.get_player_status_team_check(embed.author.name)
        if player_status == "Yes":
            team_value = await user_commands_on_message.raid_team_check(embed_fields[0] if embed_fields else None, embed_field_2)
            if team_value == 2:
                warning_text = (
                    "# <a:police_blue:1332801472894603294><a:police_red:1332801457006710794>"
                    "<a:police_blue:1332801472894603294><a:police_red:1332801457006710794>"
                    "<a:police_blue:1332801472894603294><a:police_red:1332801457006710794>"
                    "<a:police_blue:1332801472894603294><a:police_red:1332801457006710794>"
                    "<a:police_blue:1332801472894603294><a:police_red:1332801457006710794>\n"
                    "# <a:police_blue:1332801472894603294> **Are you sure about this?** <a:police_red:1332801457006710794>\n"
                    "# <a:police_blue:1332801472894603294><a:police_red:1332801457006710794>"
                    "<a:police_blue:1332801472894603294><a:police_red:1332801457006710794>"
                    "<a:police_blue:1332801472894603294><a:police_red:1332801457006710794>"
                    "<a:police_blue:1332801472894603294><a:police_red:1332801457006710794>"
                    "<a:police_blue:1332801472894603294><a:police_red:1332801457006710794>\n"
                )
                await message.channel.send(warning_text)
        await bot.process_commands(message)

    elif keyword_16 in embed_description or any(keyword_16 in (f.value or "") for f in embed_fields):
        await _handle_rd_bt_confirm(message, embed_description, embed_fields)

    elif keyword_12 in embed_description:
        await user_commands_on_message.clan_donation_tracker(embed_description, message)

    else:
        await bot.process_commands(message)


async def _replace_embed(message, title, description, footer, image_url, thumb_url):
    new_embed = create_embed(title, description, footer, image_url, thumb_url)
    view = user_commands_on_message.DeleteButtonView()
    await message.channel.send(embed=new_embed, view=view)
    try:
        await message.delete()
    except (discord.errors.NotFound, discord.errors.Forbidden):
        pass
    await bot.process_commands(message)


async def _handle_gold_rubies_or_raid_pass(message):
    if keyword_10_2 in message.content or keyword_10_3 in message.content:
        player_name, embed_text = await user_commands_on_message.player_gold_and_rubies_command(message)
        if embed_text == "player not found":
            await bot.process_commands(message)
            return
        embed = discord.Embed(title=None, description=None, color=0x71368A)
        embed.add_field(name=f"**{player_name}** currently has:", value=embed_text, inline=False)
        embed.set_footer(text="There can be issues with the displayed amount! Please double check if the amount is correct.")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg")
        view = user_commands_on_message.DeleteButtonView()
        try:
            await message.reply(embed=embed, view=view)
        except discord.HTTPException:
            await message.channel.send(embed=embed, view=view)
        await bot.process_commands(message)
    elif keyword_14 in message.content:
        await user_commands_on_message_v2.raid_pass_v2(message)
    else:
        await bot.process_commands(message)


async def _handle_rd_bt_confirm(message, embed_description, embed_fields):
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


async def _handle_raid_already_defeated(message):
    """Raid đã kết thúc trước khi lượt của user hoàn tất — hủy ping .rd bt pending."""
    uid = None
    # Ưu tiên: bot reply vào message của user
    if message.reference and message.reference.resolved:
        ref = message.reference.resolved
        if not ref.author.bot:
            uid = ref.author.id
    # Fallback: tìm theo channel
    if uid is None:
        for pending_uid, data in list(runtime.raid_bt_pending.items()):
            if data.get("channel_id") == message.channel.id:
                uid = pending_uid
                break
    if uid and uid in runtime.raid_bt_pending:
        del runtime.raid_bt_pending[uid]
    await bot.process_commands(message)


async def _handle_rd_bt(message):
    import time as _time
    _now = _time.time()
    runtime.raid_battle_tracker[message.author.id] = _now
    runtime.raid_afk_pinged.pop(message.author.id, None)
    game_name = await guilds.get_member_game_name_by_discord_id(message.author.id)
    runtime.raid_bt_pending[message.author.id] = {
        "timestamp":  _now,
        "channel_id": message.channel.id,
        "game_name":  game_name,
    }
    await bot.process_commands(message)


async def _handle_rd_lobbies(message):
    delete_value = await players.get_raid_search_history_delete_for_players_by_player_id(message.author.id, message.author.name)
    if delete_value == "yes":
        try:
            await message.delete()
        except (discord.errors.NotFound, discord.errors.Forbidden):
            pass
    await bot.process_commands(message)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    await start_web_server()
    await bot.start(os.getenv("DISCORD_TOKEN"))


asyncio.run(main())

# local debugging
#bot.run(os.getenv("DISCORD_TOKEN"))
