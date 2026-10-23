import re
import time
import asyncio
import discord
import json
import pygsheets
import os
import psutil
import runtime
from datetime import datetime, timezone
from db_methods import general, players
from discord.ext import commands
from Commands import user_commands_prefix_definition

LOG_FILE = "data/command_log.txt"  # Log các lệnh guide để phát hiện chỉnh sửa độc hại
admins = (703335523925753903,)      # Danh sách admin
raid_guide_editors = (703335523925753903,)             # Danh sách người có quyền sửa guide


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.energy_tick_interval = 120         # 2 phút
        self.daily_watch_tick_interval = 43200  # 12 tiếng
        self.daily_watch_channel_id_shop_view = 1376249740748128256
        self.daily_watch_message_id_shop_view = 1376530332676784288
        self.daily_watch_channel_id_shop_ping = 1376249501400043620
        self.gc = None
        self.sheet_name_raid = ""
        self.sheet_name_floor = ""

    # -------------------------------------------------------------------------
    # SYSTEM - Kiểm tra tài nguyên hệ thống
    # -------------------------------------------------------------------------

    @commands.command()
    async def ram(self, ctx):
        """Hiển thị mức RAM bot đang dùng."""
        if ctx.author.id in admins:
            process = psutil.Process(os.getpid())
            mem = process.memory_info().rss / 1024 ** 2
            await ctx.send(f"Ram usage: {mem:.2f} MB")
        else:
            await ctx.channel.send("You don't have that permission peasant.")

    # -------------------------------------------------------------------------
    # CLAN SHOP - Quản lý timer clan shop
    # -------------------------------------------------------------------------

    @commands.command()
    async def cl_shop_start(self, ctx):
        """Reset timer và counter clan shop về thời điểm hiện tại."""
        if ctx.author.id in admins:
            current_timestamp = int(time.time())
            config = general.get_config_collection()
            await config.update_one(
                {"_id": "global"},
                {"$set": {"clan_shop_start_timer": str(current_timestamp), "clan_shop_counter": "0"}},
                upsert=True,
            )
            await ctx.channel.send(f"cl shop successfully updated to: {current_timestamp}")
        else:
            await ctx.channel.send("You don't have that permission peasant.")

    # -------------------------------------------------------------------------
    # ENERGY TIMER - Đặt timer hồi năng lượng raid
    # -------------------------------------------------------------------------

    @commands.command()
    async def set_energy_timer(self, ctx):
        """Lấy timestamp từ embed của bot rồi tính và lưu global energy timer."""
        if ctx.author.id in admins:
            await ctx.channel.send("Waiting for message...")

            def check(msg):
                return msg.author.id == 703335523925753903

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=20)
            except asyncio.TimeoutError:
                await ctx.channel.send("Command timeout.")
            else:
                embed_title = msg.embeds[0].title
                match = re.search(r"<t:(\d+):", embed_title)
                raid_energy_timer = int(match.group(1))
                energy_global_timer = raid_energy_timer + 12 - 21600
                await general.set_global_energy_timer(energy_global_timer)
                await ctx.channel.send(
                    f"Timer set to: <t:{energy_global_timer}:T>\n"
                    f"from raid timer: <t:{raid_energy_timer}:T>\n"
                    f"unix timer: 1) {energy_global_timer} 2) {raid_energy_timer}"
                )
        else:
            await ctx.channel.send("You don't have that permission peasant.")

    # -------------------------------------------------------------------------
    # DAILY WATCH - Lịch xoay vòng location shop hàng ngày
    # -------------------------------------------------------------------------

    @commands.command()
    async def set_daily_watch(self, ctx, timer: int, counter: int):
        """Cập nhật base timer và vị trí hiện tại của daily watch rotation."""
        await ctx.channel.send(f"[DEBUG] Received: timer={timer} counter={counter} author={ctx.author.id}")
        if ctx.author.id not in admins:
            await ctx.channel.send("You don't have that permission peasant.")
            return
        try:
            if timer <= 0 or str(counter) not in self.bot.locations:
                await ctx.send('Use a positive UNIX timestamp and a valid location.')
                return
            now = int(time.time())
            current_tick = timer + ((now - timer) // self.daily_watch_tick_interval) * self.daily_watch_tick_interval
            config = general.get_config_collection()
            await config.update_one(
                {"_id": "global"},
                {"$set": {
                    "daily_watch_timer": timer,
                    "daily_watch_counter": counter,
                    "daily_watch_last_rotation_timer": current_tick,
                }},
                upsert=True,
            )
            await ctx.channel.send(
                f"Daily watch set.\n"
                f"Timer: `{timer}` → <t:{timer}:f>\n"
                f"Counter (current location): `{counter}`"
            )
        except Exception as e:
            await ctx.channel.send(f"Error: `{type(e).__name__}: {e}`")

    def get_next_tick_from_base_daily_watch(self, base_tick):
        """Tính thời điểm tick tiếp theo từ base_tick, bỏ qua các tick đã qua."""
        now = int(time.time())
        while base_tick <= now:
            base_tick += self.daily_watch_tick_interval
        return base_tick

    async def sync_and_start_rotation_task(self, base_tick, bot):
        """Đồng bộ với tick gần nhất rồi bắt đầu vòng lặp rotation mỗi 12 tiếng."""
        if base_tick is None:
            return
        while True:
            try:
                base_tick = await general.get_global_daily_watch_timer()
                if base_tick is not None:
                    await self.daily_watch_rotation(bot, base_tick)
            except Exception as exc:
                print(f'[DAILY WATCH ROTATION] Retry next poll: {exc}')
            await asyncio.sleep(30)

    async def daily_watch_rotation(self, bot, base_tick):
        """Tăng counter, ping user đăng ký, và cập nhật embed lịch location."""
        if not await general.catch_up_daily_watch_counter(self.daily_watch_tick_interval):
            return
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
        next_tick = self.get_next_tick_from_base_daily_watch(base_tick)
        embeds = await self.create_daily_watch_embeds(
            next_tick - self.daily_watch_tick_interval,
            current_counter,
        )
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
        """Tạo danh sách embed hiển thị lịch xoay vòng tất cả location."""
        locations = await runtime.retrieve_data("locations")
        total_locations = len(locations)
        embeds = []
        embed = discord.Embed(title="Location Overview", color=0x71368A)
        embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")
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
                embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")
                field_count = 0
        if field_count > 0:
            embed.set_image(url="https://cdn.discordapp.com/attachments/790277741642776598/1376101487553544304/oie_YUqPXdSd03Y4.png")
            embeds.append(embed)
        return embeds

    # -------------------------------------------------------------------------
    # LOGGING - Ghi log lệnh admin vào file
    # -------------------------------------------------------------------------

    async def log_command(self, ctx):
        """Ghi log lệnh theo dạng async để không block event loop."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write_log, ctx)

    def _write_log(self, ctx):
        """Ghi một dòng log gồm timestamp, lệnh, user, server, channel."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        user = f"{ctx.author} ({ctx.author.id})"
        server = f"{ctx.guild.name} ({ctx.guild.id})"
        channel = f"{ctx.channel.name} ({ctx.channel.id})"
        line = f"[{timestamp}] Command: {ctx.command.qualified_name} | User: {user} | Server: {server} | Channel: {channel}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)

    # -------------------------------------------------------------------------
    # GOOGLE SHEETS - Kết nối và cập nhật dữ liệu guide từ Google Sheets
    # -------------------------------------------------------------------------

    async def _get_gc(self):
        """Trả về Google Sheets client, tạo mới nếu chưa kết nối."""
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
        """Kéo dữ liệu raid comps từ Google Sheets và lưu vào data/raid_comps.json."""
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

    @commands.command()
    async def update_floorguide(self, ctx):
        """Kéo dữ liệu floor comps từ Google Sheets và lưu vào data/floor_comps.json."""
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

    def _save_json(self, path, data):
        """Lưu dict ra file JSON, tạo thư mục nếu chưa tồn tại."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
