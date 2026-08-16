import discord


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


class CompareOptionView(discord.ui.View):
    def __init__(self, owner_id: int, editor: str):
        super().__init__(timeout=180)
        self.owner_id = owner_id
        for button in _editor_buttons(editor):
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Chỉ chủ tin nhắn compare mới dùng được.", ephemeral=True
            )
            return False

        custom_id = interaction.data.get("custom_id", "")
        try:
            _, _, editor, index = custom_id.split(":")
            selected = _EDITOR_OPTIONS[editor][int(index)]
        except (KeyError, ValueError, IndexError):
            await interaction.response.defer(ephemeral=True)
            return False

        await interaction.response.send_message(
            f"Đã chọn **{selected}**. Bản preview chưa áp dụng thay đổi.",
            ephemeral=True,
        )
        return False


class ComparePreviewView(discord.ui.View):
    def __init__(self, owner_id: int, card_count: int):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.message = None

        self.add_item(discord.ui.Select(
            placeholder="Brief",
            options=[
                discord.SelectOption(label="Brief", description="Show brief comparison"),
                discord.SelectOption(label="Detailed", description="Show detailed comparison"),
            ],
            custom_id="compare:mode",
            row=0,
        ))
        self.add_item(discord.ui.Select(
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
                    for index in range(1, max(card_count, 2) + 1)
                ],
            ],
            custom_id="compare:adjust",
            row=1,
        ))
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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Chỉ chủ tin nhắn compare mới dùng được.", ephemeral=True
            )
            return False

        action = interaction.data.get("custom_id", "").removeprefix("compare:")
        if action in {"mode", "adjust"}:
            selected = interaction.data.get("values", [""])[0]
            if action == "adjust":
                selected = (
                    "Adjust All Cards"
                    if selected == "all"
                    else f"Adjust Card #{int(selected) + 1}"
                )
            await interaction.response.send_message(
                f"Đã chọn **{selected}**. Bản preview chưa áp dụng thay đổi.",
                ephemeral=True,
            )
        elif action in _EDITOR_OPTIONS:
            await interaction.response.send_message(
                "Please select one of the options below:",
                view=CompareOptionView(self.owner_id, action),
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

    embeds = [discord.Embed.from_dict(embed.to_dict()) for embed in message.embeds]
    view = ComparePreviewView(owner_id, len(embeds))
    view.message = await message.reply(
        embeds=embeds,
        view=view,
        mention_author=False,
    )
    return True
