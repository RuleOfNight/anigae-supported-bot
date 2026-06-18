import discord
import os
from discord.ext import commands
from discord import MediaGalleryItem

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")

class SimulatorContainer(discord.ui.Container):
    header = discord.ui.TextDisplay("## Boss DMG Simulator\nThống kê DMG 8 combo (Energy = 60)")
    gallery = discord.ui.MediaGallery(
        MediaGalleryItem(media="attachment://chart.png"),
        MediaGalleryItem(media="attachment://table.png")
    )

class SimulatorView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__()
        self.container = SimulatorContainer(id=1, accent_colour=0x71368A)

class SimulatorCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def simulator(self, ctx):
        chart_path = os.path.join(DATA_DIR, "simulator_chart.png")
        table_path = os.path.join(DATA_DIR, "simulator_table.png")
        
        if not os.path.exists(chart_path) or not os.path.exists(table_path):
            await ctx.send("Đéo có ảnh.")
            return

        file_chart = discord.File(fp=chart_path, filename="chart.png")
        file_table = discord.File(fp=table_path, filename="table.png")
        
        view = SimulatorView()
        await ctx.send(files=[file_chart, file_table], view=view)

async def setup(bot):
    await bot.add_cog(SimulatorCommand(bot))
