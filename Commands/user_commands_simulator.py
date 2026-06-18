import discord
from discord.ext import commands
import io
import urllib.parse
import json
from playwright.async_api import async_playwright

async def generate_chart(end_round=None):
    # Prepare data
    rounds = list(range(1, 21))
    buffs = [max(0, 0.50 - (r - 1) * 0.05) for r in rounds]
    
    combos = [
        ("Impossible Solo", 20, 1.000, 1.25, "#ef4444", False),
        ("Impossible Duo", 15, 1.125, 1.25, "#ef4444", [5, 5]),
        ("Hard Solo", 20, 1.000, 1.10, "#f97316", False),
        ("Hard Duo", 15, 1.125, 1.10, "#f97316", [5, 5]),
        ("Medium Solo", 20, 1.000, 1.00, "#3b82f6", False),
        ("Medium Duo", 15, 1.125, 1.00, "#3b82f6", [5, 5]),
        ("Easy Solo", 20, 1.000, 0.85, "#22c55e", False),
        ("Easy Duo", 15, 1.125, 0.85, "#22c55e", [5, 5]),
    ]
    
    datasets = []
    for name, hits, play_mult, obj_mult, color, dash in combos:
        data = [hits * play_mult * obj_mult * (1 + b) for b in buffs]
        datasets.append({
            "label": name,
            "data": data,
            "borderColor": color,
            "backgroundColor": color,
            "borderDash": dash if dash else [],
            "fill": False,
            "tension": 0.1,
            "borderWidth": 2,
            "pointRadius": 0,
            "pointHoverRadius": 0
        })

    datasets_json = json.dumps(datasets)

    # Render HTML template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{
                background-color: #1e1e2e;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                width: 900px;
                height: 500px;
                color: #cdd6f4;
                font-family: sans-serif;
            }}
            canvas {{
                background-color: #1e1e2e;
            }}
        </style>
    </head>
    <body>
        <canvas id="myChart"></canvas>
        <script>
            const ctx = document.getElementById('myChart').getContext('2d');
            const end_round = {end_round if end_round is not None else 'null'};
            const plugins = [];
            
            // Add custom plugin for shading R11+ and drawing end round vertical line
            plugins.push({{
                id: 'customCanvasBackground',
                beforeDraw: (chart) => {{
                    const ctx = chart.ctx;
                    const xAxis = chart.scales.x;
                    const yAxis = chart.scales.y;
                    
                    // Shade R11 to R20
                    const startX = xAxis.getPixelForValue(10); // R11 is index 10 (0-indexed)
                    const endX = xAxis.getPixelForValue(19);
                    ctx.save();
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
                    ctx.fillRect(startX, yAxis.top, endX - startX, yAxis.bottom - yAxis.top);
                    
                    // Draw End Round line
                    if (end_round !== null) {{
                        const lineX = xAxis.getPixelForValue(end_round - 1);
                        ctx.beginPath();
                        ctx.strokeStyle = '#f38ba8';
                        ctx.lineWidth = 2;
                        ctx.setLineDash([5, 5]);
                        ctx.moveTo(lineX, yAxis.top);
                        ctx.lineTo(lineX, yAxis.bottom);
                        ctx.stroke();
                        
                        ctx.fillStyle = '#f38ba8';
                        ctx.font = 'bold 12px sans-serif';
                        ctx.fillText('R' + end_round, lineX + 5, yAxis.top + 15);
                    }}
                    ctx.restore();
                }}
            }});
            
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(["R" + str(r) for r in rounds])},
                    datasets: {datasets_json}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Boss DMG Simulator | Energy = 60',
                            color: '#cdd6f4',
                            font: {{ size: 18 }}
                        }},
                        legend: {{
                            labels: {{ color: '#cdd6f4' }},
                            position: 'bottom'
                        }}
                    }},
                    scales: {{
                        x: {{
                            grid: {{ color: '#313244' }},
                            ticks: {{ color: '#a6adc8' }}
                        }},
                        y: {{
                            grid: {{ color: '#313244' }},
                            ticks: {{ color: '#a6adc8' }},
                            title: {{ display: true, text: 'DMG', color: '#cdd6f4' }}
                        }}
                    }}
                }},
                plugins: plugins
            }});
        </script>
    </body>
    </html>
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 940, "height": 540})
        await page.set_content(html_content, wait_until="networkidle")
        
        screenshot_bytes = await page.locator("body").screenshot()
        await browser.close()

    buf = io.BytesIO(screenshot_bytes)
    buf.seek(0)
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
    
    lines = []
    lines.append(f"**Round kết thúc:** R{end_round}  |  **Buff:** +{int(buff * 100)}%")
    lines.append("")
    
    # Fixed rank mapping
    for i, (name, hits, play_mult, obj_mult) in enumerate(combos, 1):
        dmg = hits * play_mult * obj_mult * (1 + buff)
        
        # Highlight top 3 (Impossible Solo, Impossible Duo, Hard Solo based on base DMG)
        # Assuming the fixed order is inherently sorted by max DMG potential.
        rank_label = f"**#{i}**" if i <= 3 else f"#{i}"
        name_label = f"**{name}**" if i <= 3 else name
        star = " 🔥" if i <= 3 else ""
        
        lines.append(f"{rank_label} {name_label}: **{dmg:.2f}** DMG (Hits: {hits}, M.Play: ×{play_mult:.3f}, M.Obj: ×{obj_mult:.2f}){star}")
        
    return "\n".join(lines)

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

        buf = await generate_chart(val)
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
        buf = await generate_chart()
        file = discord.File(fp=buf, filename="chart.png")
        view = build_simulator_view()
        await ctx.send(file=file, view=view)

async def setup(bot):
    await bot.add_cog(SimulatorCommand(bot))
