import os

import discord
from discord.ext import commands


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")


class SimulatorView(discord.ui.LayoutView):
    def __init__(self, *, timeout=120):
        super().__init__(timeout=timeout)
        self.add_item(self._build_container())

    def _build_container(self):
        container = discord.ui.Container(accent_colour=0x71368A)
        container.add_item(discord.ui.TextDisplay(
            "## Boss DMG Simulator\n"
            "DMG stats for 8 combos | Energy = 60"
        ))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay("**Damage chart**"))
        container.add_item(discord.ui.MediaGallery(
            discord.MediaGalleryItem(media="attachment://simulator_chart.png", spoiler=False)
        ))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay("**Combo table**"))
        container.add_item(discord.ui.MediaGallery(
            discord.MediaGalleryItem(media="attachment://simulator_table.png", spoiler=False)
        ))
        return container


class SimulatorCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def simulator(self, ctx):
        chart_path = os.path.join(DATA_DIR, "simulator_chart.png")
        table_path = os.path.join(DATA_DIR, "simulator_table.png")

        if not os.path.exists(chart_path) or not os.path.exists(table_path):
            await ctx.send("Simulator images are missing.")
            return

        file_chart = discord.File(fp=chart_path, filename="simulator_chart.png")
        file_table = discord.File(fp=table_path, filename="simulator_table.png")

        await ctx.send(files=[file_chart, file_table], view=SimulatorView())


async def setup(bot):
    await bot.add_cog(SimulatorCommand(bot))
