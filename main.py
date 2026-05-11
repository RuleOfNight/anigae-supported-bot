import re
import discord
import asyncio
import json
import io
import os
import runtime

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

own_bot_id = 1012793992359972977
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

async def weekly_guild():
    await guilds.update_donations_weekly_automated()

async def daily_update():
    await players.decrement_all_premium_days()


@bot.event
async def on_ready():
    print(f"✅ Startup complete. Bot running on {len(bot.guilds)} server with {bot.shard_count} shards.")
    print("on_ready")
    await general.connect_to_db()
    await bot.add_cog(UserCommandsPrefix(bot))
    await bot.add_cog(UserCommandsPrefix_v2(bot))
    await bot.load_extension("Commands.user_commands_slash")
    admin_cog = AdminCommands(bot)
    await bot.add_cog(admin_cog)
    bot.add_listener(reaction_add_listener, "on_raw_reaction_add")
    if not scheduler.running:
        scheduler.add_job(monthly_guild, CronTrigger(day=1, hour=1, minute=0, timezone=utc), id="monthly_guild")
        scheduler.add_job(weekly_guild, CronTrigger(day_of_week=0, hour=1, minute=0, timezone=utc), id="weekly_guild")
        scheduler.add_job(daily_update, CronTrigger(hour=1, minute=0, timezone=utc), id="daily_update")
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
                        embed_title, embed_description, embed_footer, debug_embed = await user_commands_on_message.in_raid_lobby(embed_title, embed_description, embed_footer)
                        new_embed = create_embed(embed_title, embed_description, embed_footer, embed_image_url, embed_thumbnail_url)
                        view = user_commands_on_message.DeleteButtonView()
                        await message.channel.send(embed=new_embed, view=view)
                        await message.channel.send(embed=debug_embed)
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

# Caeser's
bot.run(os.getenv("DISCORD_TOKEN"))

