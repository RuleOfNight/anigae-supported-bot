import re
import time
import asyncio
import discord
import json
import pygsheets
import os
import psutil
import runtime
from bson import ObjectId
from datetime import datetime, timezone
from db_methods import general, players
from discord.ext import commands
from Commands import user_commands_prefix_definition
LOG_FILE = "data/command_log.txt" # Logging the guide commands to prevent malicious editing - just in case...
admins = () # List for all admins
raid_guide_editors = () # List for all users to be able to access the commands


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.energy_tick_interval = 120         # 2min
        self.daily_watch_tick_interval = 43200  # 12h
        self.daily_watch_channel_id_shop_view = 1376249740748128256
        self.daily_watch_message_id_shop_view = 1376530332676784288
        self.daily_watch_channel_id_shop_ping = 1376249501400043620
        self.gc = None
        self.sheet_name_raid = ""
        self.sheet_name_floor = ""

    @commands.command()
    async def ram(self, ctx):
        if ctx.author.id in admins:
            process = psutil.Process(os.getpid())
            mem = process.memory_info().rss / 1024 ** 2  # in MB
            await ctx.send(f"Ram usage: {mem:.2f} MB")
        else:
            await ctx.channel.send("You don't have that permission peasant.")

    @commands.command()
    async def cl_shop_start(self, ctx):
        if ctx.author.id in admins:
            current_timestamp = int(time.time())
            misc_information = general.get_misc_collection()
            update_values = {"$set": {"clan_shop_start_timer": f"{current_timestamp}", "clan_shop_counter": "0"}}
            misc_information.update_one({"_id": ObjectId("67ae69c3cf53d633cb1cd358")}, update_values)
            await ctx.channel.send(f"cl shop successfully updated to: {current_timestamp}")
        else:
            await ctx.channel.send("You don't have that permission peasant.")

    @commands.command()
    async def set_energy_timer(self, ctx):
        if ctx.author.id in admins:
            await ctx.channel.send("Waiting for message...")

            def check(msg):
                return msg.author.id == 571027211407196161
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=20)
            except asyncio.TimeoutError:
                await ctx.channel.send("Command timeout.")
            else:
                embed_title = msg.embeds[0].title
                match = re.search(r"<t:(\d+):", embed_title)
                raid_energy_timer = int(match.group(1))
                energy_global_timer = raid_energy_timer + 12 - 21600
                general.set_global_energy_timer(energy_global_timer)
                await ctx.channel.send(f"Timer set to: <t:{energy_global_timer}:T>\n"
                                       f"from raid timer: <t:{raid_energy_timer}:T>\n"
                                       f"unix timer: 1) {energy_global_timer} 2) {raid_energy_timer}")
        else:
            await ctx.channel.send("You don't have that permission peasant.")

    def get_next_tick_from_base_daily_watch(self, base_tick):
        now = int(time.time())
        while base_tick <= now:
            base_tick += self.daily_watch_tick_interval
        return base_tick

    async def sync_and_start_rotation_task(self, base_tick, bot):
        if base_tick is None:
            return
        next_tick = self.get_next_tick_from_base_daily_watch(base_tick)
        wait_time = next_tick - int(time.time())
        print(f"[DAILY WATCH ROTATION] Sync on tick {next_tick} (in {wait_time} sec.)")
        await asyncio.sleep(wait_time)
        while True:
            await self.daily_watch_rotation(bot, base_tick)
            await asyncio.sleep(self.daily_watch_tick_interval)

    async def daily_watch_rotation(self, bot, base_tick):
        await general.increase_daily_watch_counter()
        channel_id_shop_view = self.bot.get_channel(self.daily_watch_channel_id_shop_view)
        if not channel_id_shop_view:
            return
        channel_id_shop_ping = self.bot.get_channel(self.daily_watch_channel_id_shop_ping)
        if not channel_id_shop_ping:
            return
        current_counter = await general.get_daily_watch_counter()
        users_to_ping = await players.get_users_to_ping_by_daily_counter_in_players(current_counter)
        if users_to_ping:
            user_mention_list = " ".join(f"<@{user_id}>" for user_id in users_to_ping)
            await channel_id_shop_ping.send(f"It's now Location {current_counter} daily!\n{user_mention_list}")
            await user_commands_prefix_definition.send_daily_watch_embed(channel_id_shop_ping)
        else:
            pass
        next_tick = self.get_next_tick_from_base_daily_watch(base_tick)
        embeds = await self.create_daily_watch_embeds(next_tick, current_counter)
        try:
            if self.daily_watch_message_id_shop_view:
                message = channel_id_shop_view.get_partial_message(self.daily_watch_message_id_shop_view)
                await message.edit(embeds=embeds)
            else:
                message = await channel_id_shop_view.send(embeds=embeds)
                self.daily_watch_message_id_shop_view = message.id
        except Exception as e:
            print(f"[DAILY WATCH ROTATION] Error: {e}")

    async def create_daily_watch_embeds(self, base_tick: int, current_counter: int) -> list:
        locations = await runtime.retrieve_data("locations")
        total_locations = len(locations)
        embeds = []
        embed = discord.Embed(title="Location Overview", color=0x71368A)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg")
        field_count = 0
        for loc_index in range(1, total_locations + 1):
            name = locations[str(loc_index)]
            relative_offset = (loc_index - current_counter - 1) % total_locations
            start_time = base_tick + (relative_offset * self.daily_watch_tick_interval)
            embed.add_field(name=f"Loc {loc_index} {name}", value=f"[Start: <t:{start_time}:f>]", inline=False)
            field_count += 1
            if field_count == 20:
                embed.set_image(url="https://cdn.discordapp.com/attachments/790277741642776598/1376101487553544304/oie_YUqPXdSd03Y4.png")
                embeds.append(embed)
                embed = discord.Embed(color=0x71368A)
                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg")
                field_count = 0
        if field_count > 0:
            embed.set_image(url="https://cdn.discordapp.com/attachments/790277741642776598/1376101487553544304/oie_YUqPXdSd03Y4.png")
            embeds.append(embed)
        return embeds

    async def log_command(self, ctx):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write_log, ctx)

    def _write_log(self, ctx):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        user = f"{ctx.author} ({ctx.author.id})"
        server = f"{ctx.guild.name} ({ctx.guild.id})"
        channel = f"{ctx.channel.name} ({ctx.channel.id})"
        line = f"[{timestamp}] Command: {ctx.command.qualified_name} | User: {user} | Server: {server} | Channel: {channel}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)

    async def _get_gc(self):
        if self.gc is None:
            try:
                project_root = os.path.dirname(os.path.dirname(__file__))
                service_file = os.path.join(project_root, "data", "google_api_login.json")
                loop = asyncio.get_running_loop()
                self.gc = await loop.run_in_executor(None, lambda: pygsheets.authorize(service_file=service_file))
            except Exception as e:
                raise e
        return self.gc

    @commands.command()
    async def update_raidguide(self, ctx):
        if ctx.author.id not in raid_guide_editors:
            await ctx.send("You don't have that permission peasant.")
            return
        await self.log_command(ctx)
        try:
            gc = await self._get_gc()
        except Exception:
            await ctx.send("Error on the connection to the google sheets.")
            return
        try:
            sh = gc.open(self.sheet_name_raid)
            ws = sh.worksheet('title', 'RaidDB')
        except Exception as e:
            await ctx.send(f"Error while opening the sheet: {e}")
            return
        loop = asyncio.get_running_loop()
        try:
            rows = await loop.run_in_executor(None, ws.get_values, 'A2', 'E2000')
        except Exception as e:
            await ctx.send(f"Error while loading the values: {e}")
            return
        bosses = {}
        for row in rows:
            a, b, c, d, e = (row + ["", "", "", "", ""])[:5]
            boss = a.strip()
            team = b.strip()
            rarity = c.strip().upper()
            level = d.strip()
            raid_type = e.strip() or "Normal"
            if not boss or not team or not rarity:
                continue
            if not level:
                if rarity == "UR":
                    level = "1400"
                elif rarity == "SR":
                    level = "1600"
                else:
                    level = "1000"
            if boss not in bosses:
                bosses[boss] = {"raid_type": raid_type}
            if raid_type.lower() == "event":
                bosses[boss]["raid_type"] = "Event"
            if rarity not in bosses[boss]:
                bosses[boss][rarity] = {}
            if level not in bosses[boss][rarity]:
                bosses[boss][rarity][level] = {"teams": []}
            team_variants = [t.strip() for t in team.split("\n") if t.strip()]
            bosses[boss][rarity][level]["teams"].extend(team_variants)
        project_root = os.path.dirname(os.path.dirname(__file__))
        save_path = os.path.join(project_root, "data", "raid_comps.json")
        await loop.run_in_executor(None, self._save_json, save_path, bosses)
        await ctx.send(f"Raid comps saved: `{save_path}`")

    def _save_json(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @commands.command()
    async def update_floorguide(self, ctx):
        if ctx.author.id not in raid_guide_editors:
            await ctx.send("You don't have that permission peasant.")
            return
        await self.log_command(ctx)
        try:
            gc = await self._get_gc()
        except Exception:
            await ctx.send("Error on the connection to the google sheets.")
            return
        try:
            sh = gc.open(self.sheet_name_floor)
            ws = sh.worksheet('title', 'Caeser data')
        except Exception as e:
            await ctx.send(f"Error while opening the sheet: {e}")
            return
        loop = asyncio.get_running_loop()
        try:
            rows = await loop.run_in_executor(None, ws.get_values, 'A2', 'K4000')
        except Exception as e:
            await ctx.send(f"Error while loading the values: {e}")
            return
        data = {}
        for row in rows:
            a, b, c, d, e, f, g, h, i, j, k = (row + [""] * 11)[:11]
            loc_num = a.strip()
            series = c.strip()
            boss = d.strip()
            rarity = g.strip().upper()
            team = h.strip()
            note = j.strip()
            difficulty = k.strip()
            if not boss or not rarity or not team:
                continue
            if boss not in data:
                data[boss] = {"location_id": loc_num, "series": series, "teams": []}
            data[boss]["teams"].append({"rarity": rarity, "team": team, "note": note, "difficulty": difficulty})
        project_root = os.path.dirname(os.path.dirname(__file__))
        save_path = os.path.join(project_root, "data", "floor_comps.json")
        await loop.run_in_executor(None, self._save_json, save_path, data)
        await ctx.send(f"Floor teams saved: `{save_path}`")
