"""Independent Dredeem rotation and per-player subscriptions."""
import logging
import time

import discord
from discord import app_commands
from discord.ext import commands, tasks

import runtime
from db_methods import general
from Commands.admin_commands import admins

INTERVAL = 43200
HOT = {14: 'Masami', 28: 'Ryusui', 53: 'Kenma', 57: 'Mito',
       65: 'Sukuna', 71: 'Damian', 85: 'Bjorn', 88: 'Aza Chobei',
       89: 'Miyuki Shiba', 94: 'Kasuka, Mika Harima',
       97: 'Clara Valac', 100: 'Yami Yugi, Dark Magician Girl'}


def rotation(config, now, total):
    tick = max(0, (now - config['anchor']) // INTERVAL)
    latest = (config['latest'] - 1 + tick) % total + 1
    window = [(latest - 1 - offset) % total + 1 for offset in (2, 1, 0)]
    return tick, window, config['anchor'] + (tick + 1) * INTERVAL


class SeriesSelect(discord.ui.Select):
    def __init__(self, ids, names, selected, label):
        self.ids = set(ids)
        super().__init__(placeholder=label, min_values=0, max_values=len(ids), options=[
            discord.SelectOption(label=f'[Loc {i}] {names[str(i)]}'[:100], value=str(i),
                                 description=HOT.get(i), default=i in selected) for i in ids])

    async def callback(self, interaction):
        view = self.view
        view.selected.difference_update(self.ids)
        view.selected.update(map(int, self.values))
        view.build()
        await interaction.response.edit_message(view=view)


class WatchView(discord.ui.LayoutView):
    def __init__(self, owner, names, selected, config):
        super().__init__(timeout=600)
        self.owner, self.names, self.selected = owner, names, set(selected)
        self.config, self.page = config, 0
        self.other = [int(i) for i in names if int(i) not in HOT]
        self.other.sort()
        self.build()

    async def interaction_check(self, interaction):
        if interaction.user.id == self.owner:
            return True
        await interaction.response.send_message('Open your own /dredeem_watch menu.', ephemeral=True)
        return False

    def build(self):
        self.clear_items()
        panel = discord.ui.Container(accent_colour=0x71368A)
        panel.add_item(discord.ui.TextDisplay('## 🔔 Dredeem Watch'))
        if self.config:
            _, window, next_tick = rotation(self.config, int(time.time()), len(self.names))
            panel.add_item(discord.ui.TextDisplay('**Current shop**\n' + '\n'.join(
                f'[Loc {i}] {self.names[str(i)]}' for i in window) + f'\nNext rotation: <t:{next_tick}:R>'))
        else:
            panel.add_item(discord.ui.TextDisplay('Timer not configured yet. Subscriptions can still be saved.'))
        panel.add_item(discord.ui.Separator())
        panel.add_item(discord.ui.ActionRow(SeriesSelect(
            [i for i in HOT if str(i) in self.names], self.names, self.selected, '🔥 Hot Series — select multiple')))
        page_ids = self.other[self.page * 25:(self.page + 1) * 25]
        if page_ids:
            panel.add_item(discord.ui.ActionRow(SeriesSelect(
                page_ids, self.names, self.selected, f'📚 Other Series — page {self.page + 1}/{self.pages}')))
        nav = discord.ui.ActionRow()
        for label, delta in [('Previous', -1), ('Next', 1)]:
            button = discord.ui.Button(label=label, disabled=not 0 <= self.page + delta < self.pages)
            async def move(interaction, step=delta):
                self.page += step
                self.build()
                await interaction.response.edit_message(view=self)
            button.callback = move
            nav.add_item(button)
        panel.add_item(nav)
        selected = ', '.join(f'Loc {i}' for i in sorted(self.selected)) or 'None'
        panel.add_item(discord.ui.TextDisplay(f'**Selected ({len(self.selected)})**: {selected}\n'
            'Selections persist across pages. Save to apply. Ping at each of the 3 consecutive rotations.'))
        actions = discord.ui.ActionRow()
        save = discord.ui.Button(label='Save', style=discord.ButtonStyle.success)
        save.callback = self.save
        clear = discord.ui.Button(label='Clear selection', style=discord.ButtonStyle.secondary)
        clear.callback = self.clear
        actions.add_item(save)
        actions.add_item(clear)
        panel.add_item(actions)
        self.add_item(panel)

    @property
    def pages(self):
        return max(1, (len(self.other) + 24) // 25)

    async def clear(self, interaction):
        self.selected.clear()
        self.build()
        await interaction.response.edit_message(view=self)

    async def save(self, interaction):
        await interaction.response.defer(ephemeral=True)
        await general.get_players_collection().update_one(
            {'discord_id': self.owner}, {'$set': {'dredeem_locations': sorted(self.selected)}}, upsert=True)
        await interaction.followup.send(f'Saved {len(self.selected)} series. Notifications go to the configured Dredeem channel.', ephemeral=True)


class Dredeem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notify.start()

    def cog_unload(self):
        self.notify.cancel()

    @app_commands.command(name='dredeem_watch', description='Choose series for Dredeem notifications.')
    async def watch(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        doc = await general.get_players_collection().find_one({'discord_id': interaction.user.id}) or {}
        config = await general.get_config_collection().find_one({'_id': 'dredeem'})
        await interaction.followup.send(view=WatchView(interaction.user.id, runtime.bot.locations,
            doc.get('dredeem_locations', []), config), ephemeral=True)

    @commands.command()
    async def set_dredeem(self, ctx, latest: int, next_rotation: int):
        """Set newest location and next rotation UNIX timestamp; use this channel for pings."""
        if ctx.author.id not in admins:
            return
        now = int(time.time())
        if str(latest) not in runtime.bot.locations or not now < next_rotation <= now + INTERVAL:
            await ctx.send('Use a valid location and next rotation UNIX timestamp within the next 12 hours.')
            return
        await general.get_config_collection().update_one({'_id': 'dredeem'}, {'$set': {
            'latest': latest, 'anchor': next_rotation - INTERVAL, 'channel_id': ctx.channel.id,
            'last_notified_tick': 0}}, upsert=True)
        await ctx.send(f'Dredeem configured: latest Loc {latest}; next <t:{next_rotation}:F>. Pings in this channel.')

    @tasks.loop(seconds=30)
    async def notify(self):
        if not runtime.db_ready or not runtime.bot.locations:
            return
        try:
            collection = general.get_config_collection()
            config = await collection.find_one({'_id': 'dredeem'})
            if not config:
                return
            tick, window, next_tick = rotation(config, int(time.time()), len(runtime.bot.locations))
            if tick <= config.get('last_notified_tick', 0):
                return
            channel = self.bot.get_channel(config['channel_id']) or await self.bot.fetch_channel(config['channel_id'])
            cursor = general.get_players_collection().find({'dredeem_locations': {'$in': window}},
                {'discord_id': 1, '_id': 0})
            users = [int(doc['discord_id']) async for doc in cursor]
            header = '**Dredeem available**\n' + '\n'.join(
                f'[Loc {i}] {runtime.bot.locations[str(i)]}' for i in window) + f'\nNext rotation: <t:{next_tick}:R>\n'
            for start in range(0, len(users), 50):
                await channel.send(header + ' '.join(f'<@{i}>' for i in users[start:start + 50]),
                    allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
            await collection.update_one({'_id': 'dredeem', 'anchor': config['anchor']},
                {'$set': {'last_notified_tick': tick}})
        except Exception:
            logging.exception('Dredeem notification failed; retrying next poll')

    @notify.before_loop
    async def ready(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Dredeem(bot))
