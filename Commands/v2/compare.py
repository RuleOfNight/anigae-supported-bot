import re

import discord

from Commands import definitions
from db_methods import cards as cards_db


_EDITOR_OPTIONS = {
    "rarity": ["Base", "Common", "Uncommon", "Rare", "Super Rare", "Ultra Rare"],
    "level": ["1", "20", "30", "40", "50", "60", "Max LVL"],
    "evo": ["1", "2", "3"],
    "ascension": ["0", "1", "2", "3", "4", "5"],
    "familiarity": ["Holorized", "0", "1", "2", "3"],
    "max": ["Max SR", "Max UR"],
}

_BUTTON_KEYS = {
    "Rarity": "rarity",
    "Level": "level",
    "Evo": "evo",
    "Ascension": "ascension",
    "Familiarity": "familiarity",
}

_MAX_LEVELS = {
    "Base": 1,
    "Common": 20,
    "Uncommon": 30,
    "Rare": 40,
    "Super Rare": 50,
    "Ultra Rare": 60,
}

_MAX_STATES = {
    "Max SR": {"rarity": "Super Rare", "level": 50, "evo": 3, "ascension": 4},
    "Max UR": {"rarity": "Ultra Rare", "level": 60, "evo": 3, "ascension": 5},
}


def _walk_components(component):
    yield component
    for attr in ("children", "items"):
        for child in getattr(component, attr, None) or []:
            yield from _walk_components(child)


def is_compare_message(message) -> bool:
    """Recognise AniGame's compare controls on classic or V2 messages."""
    labels = {
        getattr(item, "label", None)
        for root in getattr(message, "components", [])
        for item in _walk_components(root)
    }
    return _BUTTON_KEYS.keys() <= labels


def _parse_base_stats(description: str) -> dict[str, int]:
    stats = {}
    for key in ("HP", "ATK", "DEF", "SPD"):
        match = re.search(rf"(?im)^\s*(?:\*\*)?{key}:(?:\*\*)?\s*(\d+)", description or "")
        if match:
            stats[key.lower()] = int(match.group(1))
    return stats


def _extract_talent_emote(description: str) -> str:
    match = re.search(
        r"(?im)^\s*(?:\*\*)?TALENT:(?:\*\*)?\s*(<a?:[^>]+>)",
        description or "",
    )
    return match.group(1) if match else ""


def _replace_line(lines, label: str, value) -> bool:
    pattern = re.compile(
        rf"^(\s*(?:\*\*)?{re.escape(label)}:(?:\*\*)?\s*).*$",
        re.IGNORECASE,
    )
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            lines[index] = f"{match.group(1)}{value}"
            return True
    return False


def _editor_buttons(editor: str):
    return [
        discord.ui.Button(
            label=label,
            style=discord.ButtonStyle.primary,
            custom_id=f"compare:option:{editor}:{index}",
            row=index // 5,
        )
        for index, label in enumerate(_EDITOR_OPTIONS[editor])
    ]


async def _load_cards(message):
    titles = [embed.title or "" for embed in message.embeds]
    db_cards = (
        await cards_db.get_compare_data_from_cards([titles], [], [], [])
        if all(titles)
        else []
    )
    loaded = []
    for index, embed in enumerate(message.embeds):
        card_data = db_cards[index] if index < len(db_cards) else {}
        parsed = _parse_base_stats(embed.description or "")
        base = {
            key: parsed[key] if key in parsed else int(card_data.get(f"card_{key}") or 0)
            for key in ("hp", "atk", "def", "spd")
        }
        source_talent = _extract_talent_emote(embed.description or "")
        talent_emote = await definitions.skill_converter_from_emote(source_talent)
        if not talent_emote:
            talent_emote = await definitions.skill_converter_from_database(
                card_data.get("card_talent", "")
            )
        familiarity = re.search(
            r"FAMILIARITY:.*?Level\s+(\d+)", embed.description or "", re.IGNORECASE
        )
        loaded.append({
            "base": base,
            "embed": embed.to_dict(),
            "talent_emote": talent_emote or source_talent,
            "state": {
                "rarity": "Base",
                "level": 0,
                "evo": 1,
                "ascension": 0,
                "familiarity": familiarity.group(1) if familiarity else "0",
            },
        })
    return loaded


class CompareOptionView(discord.ui.View):
    def __init__(self, parent, editor: str):
        super().__init__(timeout=180)
        self.parent_view = parent
        for button in _editor_buttons(editor):
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.parent_view.owner_id:
            await interaction.response.send_message(
                "Chỉ chủ tin nhắn compare mới dùng được.", ephemeral=True
            )
            return False

        try:
            _, _, editor, index = interaction.data.get("custom_id", "").split(":")
            selected = _EDITOR_OPTIONS[editor][int(index)]
        except (KeyError, ValueError, IndexError):
            await interaction.response.defer(ephemeral=True)
            return False

        await interaction.response.defer(ephemeral=True)
        self.parent_view.apply_option(editor, selected)
        await self.parent_view.refresh()
        await interaction.followup.send(f"Đã áp dụng **{selected}**.", ephemeral=True)
        return False


class ComparePreviewView(discord.ui.View):
    def __init__(self, owner_id: int, cards):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.cards = cards
        self.selected_index = None
        self.mode = "Brief"
        self.message = None

        self.mode_select = discord.ui.Select(
            placeholder="Brief",
            options=[
                discord.SelectOption(label="Brief", description="Show brief comparison"),
                discord.SelectOption(label="Detailed", description="Show detailed comparison"),
            ],
            custom_id="compare:mode",
            row=0,
        )
        self.adjust_select = discord.ui.Select(
            placeholder="Adjust All Cards",
            options=[
                discord.SelectOption(
                    label="Adjust All", value="all", description="Adjust all cards"
                ),
                *[
                    discord.SelectOption(
                        label=f"Adjust Card #{index}",
                        value=str(index - 1),
                        description=f"Adjust only card #{index}",
                    )
                    for index in range(1, len(cards) + 1)
                ],
            ],
            custom_id="compare:adjust",
            row=1,
        )
        self.add_item(self.mode_select)
        self.add_item(self.adjust_select)
        for label, editor in _BUTTON_KEYS.items():
            self.add_item(discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.primary,
                custom_id=f"compare:{editor}",
                row=2,
            ))
        self.add_item(discord.ui.Button(
            label="Max",
            style=discord.ButtonStyle.primary,
            custom_id="compare:max",
            row=3,
        ))
        self.add_item(discord.ui.Button(
            emoji="🗑️",
            style=discord.ButtonStyle.danger,
            custom_id="compare:delete",
            row=3,
        ))

    def apply_option(self, editor: str, selected: str):
        cards = self.cards if self.selected_index is None else [self.cards[self.selected_index]]
        for card in cards:
            state = card["state"]
            if editor == "rarity":
                state["rarity"] = selected
            elif editor == "level":
                state["level"] = (
                    _MAX_LEVELS[state["rarity"]] if selected == "Max LVL" else int(selected)
                )
            elif editor == "evo":
                state["evo"] = int(selected)
            elif editor == "ascension":
                state["ascension"] = int(selected)
            elif editor == "familiarity":
                state["familiarity"] = selected
            elif editor == "max":
                state.update(_MAX_STATES[selected])

    async def build_embeds(self):
        embeds = []
        for card in self.cards:
            state = card["state"]
            base = card["base"]
            hp, atk, def_, spd = await definitions.calc_card_stats_compare(
                base["hp"], base["atk"], base["def"], base["spd"],
                state["rarity"], state["level"], state["evo"], state["ascension"],
                state["familiarity"], 0, 0, 0, 0,
            )
            embed = discord.Embed.from_dict(card["embed"])
            lines = (embed.description or "").splitlines()
            for label, value in (
                ("HP", hp), ("ATK", atk), ("DEF", def_), ("SPD", spd),
                ("TOTAL", hp + atk + def_ + spd),
            ):
                _replace_line(lines, label, value)
            if card["talent_emote"]:
                _replace_line(lines, "TALENT", card["talent_emote"])
            familiarity = state["familiarity"]
            fam_text = familiarity if familiarity == "Holorized" else f"Level {familiarity}"
            _replace_line(lines, "FAMILIARITY", fam_text)
            if self.mode == "Detailed":
                rarity_mult = definitions._RARITY_CONFIG[state["rarity"]][0]
                lines.extend([
                    "",
                    f"**Multipliers:** Rarity x{rarity_mult:g} | "
                    f"Level x{1 + state['level'] * 0.005:g} | "
                    f"Evo x{1 + 0.15 * (state['evo'] - 1):g} | "
                    f"Asc x{1 + state['ascension'] * 0.05:g} | "
                    f"Fam x{definitions.familiarity_multiplier(familiarity):g}",
                ])
            embed.description = "\n".join(lines)
            embed.set_footer(text=(
                f"{state['rarity']} • Level {state['level']} • "
                f"Evo {state['evo']} • Ascension {state['ascension']}"
            ))
            embeds.append(embed)
        return embeds

    async def refresh(self):
        await self.message.edit(embeds=await self.build_embeds(), view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Chỉ chủ tin nhắn compare mới dùng được.", ephemeral=True
            )
            return False

        action = interaction.data.get("custom_id", "").removeprefix("compare:")
        if action == "mode":
            await interaction.response.defer(ephemeral=True)
            self.mode = interaction.data.get("values", ["Brief"])[0]
            self.mode_select.placeholder = self.mode
            await self.refresh()
            await interaction.followup.send(f"Đã chọn **{self.mode}**.", ephemeral=True)
        elif action == "adjust":
            selected = interaction.data.get("values", ["all"])[0]
            self.selected_index = None if selected == "all" else int(selected)
            label = "Adjust All Cards" if selected == "all" else f"Adjust Card #{int(selected) + 1}"
            self.adjust_select.placeholder = label
            await interaction.response.send_message(f"Đã chọn **{label}**.", ephemeral=True)
        elif action in _EDITOR_OPTIONS:
            await interaction.response.send_message(
                "Please select one of the options below:",
                view=CompareOptionView(self, action),
                ephemeral=True,
            )
        elif action == "delete":
            await interaction.response.defer()
            await interaction.message.delete()
        else:
            await interaction.response.defer(ephemeral=True)
        return False

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


async def _find_owner_id(message) -> int | None:
    reference = getattr(message, "reference", None)
    resolved = getattr(reference, "resolved", None)
    author = getattr(resolved, "author", None)
    if author:
        return author.id

    message_id = getattr(reference, "message_id", None)
    if message_id:
        try:
            command_message = await message.channel.fetch_message(message_id)
            return command_message.author.id
        except (discord.HTTPException, discord.NotFound, discord.Forbidden):
            pass

    metadata = getattr(message, "interaction_metadata", None)
    user = getattr(metadata, "user", None)
    if user:
        return user.id

    try:
        async for candidate in message.channel.history(limit=10, before=message):
            content = candidate.content.strip().lower()
            if (
                not candidate.author.bot
                and (content == ".compare" or content.startswith(".compare "))
            ):
                return candidate.author.id
    except (discord.HTTPException, discord.Forbidden):
        pass
    return None


async def v2_compare_preview(message):
    if not is_compare_message(message):
        return False

    owner_id = await _find_owner_id(message)
    if owner_id is None:
        return False

    cards = await _load_cards(message)
    view = ComparePreviewView(owner_id, cards)
    view.message = await message.reply(
        embeds=await view.build_embeds(),
        view=view,
        mention_author=False,
    )
    return True
