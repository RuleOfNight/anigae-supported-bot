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
    "Max": "max",
    "🗑️": "delete",
}


def _walk_components(component):
    yield component
    for attr in ("children", "items"):
        for child in getattr(component, attr, None) or []:
            yield from _walk_components(child)


def _option_labels(component):
    return {
        option.label
        for option in getattr(component, "options", None) or []
        if getattr(option, "label", None)
    }


def is_compare_message(message) -> bool:
    """Recognise AniGame's Components V2 compare result without relying on card text."""
    components = [
        item
        for root in getattr(message, "components", [])
        for item in _walk_components(root)
    ]
    labels = {getattr(item, "label", None) for item in components}
    option_groups = [_option_labels(item) for item in components]
    return (
        {"Rarity", "Level", "Evo", "Ascension", "Familiarity"} <= labels
        and any({"Brief", "Detailed"} <= options for options in option_groups)
        and any("Adjust All" in options for options in option_groups)
    )


def _button_key(button) -> str | None:
    label = getattr(button, "label", None)
    if label:
        return _BUTTON_KEYS.get(label)
    emoji = getattr(button, "emoji", None)
    return _BUTTON_KEYS.get(str(emoji)) if emoji is not None else None


class CompareOptionView(discord.ui.LayoutView):
    def __init__(self, owner_id: int, editor: str):
        super().__init__(timeout=180)
        self.owner_id = owner_id
        rows = []
        options = _EDITOR_OPTIONS[editor]
        for start in range(0, len(options), 5):
            rows.append(discord.ui.ActionRow(*[
                discord.ui.Button(
                    label=label,
                    style=discord.ButtonStyle.primary,
                    custom_id=f"compare:option:{editor}:{start + index}",
                )
                for index, label in enumerate(options[start:start + 5])
            ]))
        self.add_item(discord.ui.Container(
            discord.ui.TextDisplay("Please select one of the options below:"),
            *rows,
            accent_colour=0x71368A,
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Chỉ chủ tin nhắn compare mới dùng được.", ephemeral=True
            )
            return False

        custom_id = interaction.data.get("custom_id", "")
        _, _, editor, index = custom_id.split(":")
        selected = _EDITOR_OPTIONS[editor][int(index)]
        await interaction.response.send_message(
            f"Đã chọn **{selected}**. Bản preview chưa áp dụng thay đổi.",
            ephemeral=True,
        )
        return False


class ComparePreviewView(discord.ui.LayoutView):
    def __init__(self, owner_id: int):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.message = None

    @classmethod
    def from_original(cls, message, owner_id: int):
        converted = discord.ui.LayoutView.from_message(message, timeout=300)
        view = cls(owner_id)
        for child in list(converted.children):
            converted.remove_item(child)
            view.add_item(child)
        view._bind_controls()
        return view

    def _bind_controls(self):
        delete_button = None
        for item in self.walk_children():
            if isinstance(item, discord.ui.Select):
                options = {option.label for option in item.options}
                if {"Brief", "Detailed"} <= options:
                    item.custom_id = "compare:mode"
                elif "Adjust All" in options:
                    item.custom_id = "compare:adjust"
            elif isinstance(item, discord.ui.Button):
                key = _button_key(item)
                if key:
                    item.custom_id = f"compare:{key}"
                if key == "delete":
                    delete_button = item

        max_button = discord.ui.Button(
            label="Max",
            style=discord.ButtonStyle.primary,
            custom_id="compare:max",
        )
        delete_row = next((
            item
            for item in self.walk_children()
            if isinstance(item, discord.ui.ActionRow)
            and delete_button in item.children
        ), None)
        if delete_row:
            row = delete_row
            row.remove_item(delete_button)
            row.add_item(max_button)
            row.add_item(delete_button)
            return

        container = next(
            (item for item in self.children if isinstance(item, discord.ui.Container)), None
        )
        if container:
            container.add_item(discord.ui.ActionRow(max_button))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Chỉ chủ tin nhắn compare mới dùng được.", ephemeral=True
            )
            return False

        custom_id = interaction.data.get("custom_id", "")
        action = custom_id.removeprefix("compare:")
        if action in {"mode", "adjust"}:
            selected = interaction.data.get("values", [""])[0]
            await interaction.response.send_message(
                f"Đã chọn **{selected}**. Bản preview chưa áp dụng thay đổi.",
                ephemeral=True,
            )
        elif action in _EDITOR_OPTIONS:
            await interaction.response.send_message(
                view=CompareOptionView(self.owner_id, action), ephemeral=True
            )
        elif action == "delete":
            await interaction.response.defer()
            await interaction.message.delete()
        else:
            await interaction.response.defer(ephemeral=True)
        return False

    async def on_timeout(self):
        for item in self.walk_children():
            if isinstance(item, (discord.ui.Button, discord.ui.Select)):
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
    return getattr(user, "id", None)


async def v2_compare_preview(message):
    if not is_compare_message(message):
        return False

    owner_id = await _find_owner_id(message)
    if owner_id is None:
        return False

    view = ComparePreviewView.from_original(message, owner_id)
    view.message = await message.reply(view=view, mention_author=False)
    return True
