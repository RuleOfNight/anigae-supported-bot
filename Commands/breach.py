import discord


BREACH_BATTLES = {
    "Docile": {
        "Hard": "/dg battle rarity:Ultra Rare evo:3 ascension:5 lvl:1600 cards:2b",
        "Imp": "/dg battle rarity:Ultra Rare evo:3 ascension:5 lvl:1950 cards:2b",
    },
    "Chaos": {
        "Hard": "/dg battle rarity:Ultra Rare evo:3 ascension:5 lvl:1800 cards:2b",
        "Imp": "/dg battle rarity:Ultra Rare evo:3 ascension:5 lvl:2205 cards:2b",
    },
    "Herald": {
        "Medium": "/dg battle rarity:Ultra Rare evo:3 ascension:5 lvl:900 cards:Salvation",
        "Hard": "/dg battle rarity:Ultra Rare evo:3 ascension:5 lvl:1175 cards:Salvation",
        "Imp": "/dg battle rarity:Ultra Rare evo:3 ascension:5 lvl:1450 cards:Salvation",
    },
    "Enraged": {
        "Hard": "/dg battle rarity:Ultra Rare evo:3 ascension:5 lvl:2200 cards:2b",
        "Imp": "/dg battle rarity:Ultra Rare evo:3 ascension:5 lvl:2700 cards:2b",
    },
    "Collapse": {
        "Imp": "/dg battle rarity:Ultra Rare evo:3 ascension:5 lvl:990 cards:2b",
    },
}


class BreachView(discord.ui.LayoutView):
    def __init__(self, phase: str | None = None):
        super().__init__(timeout=300)
        self.phase = phase
        container = discord.ui.Container(id=1, accent_colour=0x71368A)
        container.add_item(discord.ui.TextDisplay("## Breach Battle\n-# Level may vary depending on the boss's base stats."))

        phase_select = discord.ui.Select(
            placeholder="Select phase...",
            options=[discord.SelectOption(label=name, value=name, default=name == phase) for name in BREACH_BATTLES],
            custom_id="breach_battle_phase",
        )
        self.phase_select = phase_select
        phase_select.callback = self._phase_callback
        container.add_item(discord.ui.ActionRow(phase_select))

        difficulties = BREACH_BATTLES.get(phase, {})
        difficulty_select = discord.ui.Select(
            placeholder="Select difficulty..." if phase else "Select a phase first...",
            options=[discord.SelectOption(label=name, value=name) for name in difficulties] or [discord.SelectOption(label="Select a phase first", value="none")],
            custom_id="breach_battle_difficulty",
            disabled=not phase,
        )
        self.difficulty_select = difficulty_select
        difficulty_select.callback = self._difficulty_callback
        container.add_item(discord.ui.ActionRow(difficulty_select))
        self.add_item(container)

    async def _phase_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=BreachView(self.phase_select.values[0]))

    async def _difficulty_callback(self, interaction: discord.Interaction):
        difficulty = self.difficulty_select.values[0]
        await interaction.response.send_message(BREACH_BATTLES[self.phase][difficulty])
