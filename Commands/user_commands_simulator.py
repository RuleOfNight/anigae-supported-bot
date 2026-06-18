import discord
from discord.ext import commands
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def generate_chart(end_round=None):
    plt.figure(figsize=(9, 5))
    
    rounds = np.arange(1, 21)
    buffs = np.maximum(0, 0.50 - (rounds - 1) * 0.05)
    
    combos = [
        ("Impossible Solo", 20, 1.000, 1.25, "red", "-"),
        ("Impossible Duo", 15, 1.125, 1.25, "red", "--"),
        ("Hard Solo", 20, 1.000, 1.10, "orange", "-"),
        ("Hard Duo", 15, 1.125, 1.10, "orange", "--"),
        ("Medium Solo", 20, 1.000, 1.00, "blue", "-"),
        ("Medium Duo", 15, 1.125, 1.00, "blue", "--"),
        ("Easy Solo", 20, 1.000, 0.85, "green", "-"),
        ("Easy Duo", 15, 1.125, 0.85, "green", "--"),
    ]
    
    for name, hits, play_mult, obj_mult, color, linestyle in combos:
        dmg = hits * play_mult * obj_mult * (1 + buffs)
        plt.plot(rounds, dmg, label=name, color=color, linestyle=linestyle)
    
    plt.axvspan(11, 20, color='gray', alpha=0.2, label='No Buff (R11+)')
    
    if end_round is not None:
        plt.axvline(x=end_round, color='black', linestyle=':', label=f'End Round: {end_round}')
        
    plt.title("Boss DMG Simulator  |  Energy = 60")
    plt.xlabel("Round")
    plt.ylabel("DMG")
    plt.xticks(np.arange(1, 21, 1))
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()
    return buf

def generate_ranking_text(end_round):
    buff = max(0, 0.50 - (end_round - 1) * 0.05)
    
    combos = [
        ("Impossible Solo", 20, 1.000, 1.25),
        ("Impossible Duo", 15, 1.125, 1.25),
        ("Hard Solo", 20, 1.000, 1.10),
        ("Hard Duo", 15, 1.125, 1.10),
        ("Medium Solo", 20, 1.000, 1.00),
        ("Medium Duo", 15, 1.125, 1.00),
        ("Easy Solo", 20, 1.000, 0.85),
        ("Easy Duo", 15, 1.125, 0.85),
    ]
    
    results = []
    for name, hits, play_mult, obj_mult in combos:
        dmg = hits * play_mult * obj_mult * (1 + buff)
        results.append((name, dmg, hits, play_mult, obj_mult))
        
    results.sort(key=lambda x: x[1], reverse=True)
    
    lines = []
    lines.append(f"Round kết thúc: R{end_round}  |  Buff: +{int(buff * 100)}%")
    lines.append("")
    lines.append(f"{'Rank':<5} {'Combo':<18} {'DMG':<7} {'Hits':<5} {'PlayMult':<9} {'ObjMult':<7}")
    lines.append("─" * 58)
    
    for i, (name, dmg, hits, play_mult, obj_mult) in enumerate(results, 1):
        star = "  ◆◆◆" if i <= 3 else ""
        lines.append(f" #{i:<3} {name:<18} {dmg:<7.2f} {hits:<5} ×{play_mult:<8.3f} ×{obj_mult:<7.2f}{star}")
        
    return "```\n" + "\n".join(lines) + "\n```"

class SimulatorInputModal(discord.ui.Modal, title="Nhập round end"):
    round_input = discord.ui.TextInput(
        label="Round kết thúc (1–20)",
        placeholder="VD: 7",
        min_length=1,
        max_length=2,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.round_input.value)
            if not 1 <= val <= 20:
                raise ValueError()
        except ValueError:
            await interaction.response.send_message("Vui lòng nhập số nguyên từ 1–20", ephemeral=True)
            return

        buf = generate_chart(val)
        file = discord.File(fp=buf, filename="chart.png")
        
        new_view = build_simulator_view(end_round=val)
        await interaction.response.edit_message(attachments=[file], view=new_view)

def build_simulator_view(end_round=None):
    if end_round is not None:
        rank_text_str = generate_ranking_text(end_round)
        class SimulatorContainer(discord.ui.Container):
            rank_text = discord.ui.TextDisplay(rank_text_str)
            button_rows = discord.ui.ActionRow(
                discord.ui.Button(label="Nhập round end", style=discord.ButtonStyle.primary, custom_id="InputRound")
            )
    else:
        class SimulatorContainer(discord.ui.Container):
            button_rows = discord.ui.ActionRow(
                discord.ui.Button(label="Nhập round end", style=discord.ButtonStyle.primary, custom_id="InputRound")
            )

    class SimulatorView(discord.ui.LayoutView):
        container = SimulatorContainer(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            button_id = interaction.data.get("custom_id")
            if button_id == "InputRound":
                await interaction.response.send_modal(SimulatorInputModal())
            return True

    return SimulatorView()

class SimulatorCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def simulator(self, ctx):
        buf = generate_chart()
        file = discord.File(fp=buf, filename="chart.png")
        view = build_simulator_view()
        await ctx.send(file=file, view=view)

async def setup(bot):
    await bot.add_cog(SimulatorCommand(bot))
