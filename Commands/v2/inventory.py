import re
import asyncio
import discord
from discord import ComponentType


# ---------------------------------------------------------------------------
# Reaction handler
# ---------------------------------------------------------------------------

async def on_raw_reaction_add(payload, bot):
    """Khi user react bằng cart emoji vào inventory message, mở InventoryHelperView."""
    if payload.user_id == bot.user.id:
        return
    if payload.emoji.id != 1495870697577250888:
        return

    message = discord.utils.get(bot.cached_messages, id=payload.message_id)
    if not message:
        channel = bot.get_channel(payload.channel_id)
        if not channel:
            return
        message = await channel.fetch_message(payload.message_id)

    if not (message.reference and message.reference.message_id):
        return

    original_message = (message.reference.resolved
                        or await message.channel.fetch_message(message.reference.message_id))
    if original_message.author.id != payload.user_id:
        return

    view = InventoryHelperView(message=message, user_id=original_message.author.id)
    await message.channel.send(view=view)


# ---------------------------------------------------------------------------
# Inventory Helper View
# ---------------------------------------------------------------------------

class InventoryHelperView(discord.ui.LayoutView):
    def __init__(self, message, user_id, timeout=120):
        super().__init__(timeout=timeout)
        self.message  = message
        self.user_id  = user_id
        self.selected_for_selling: list[str] = []
        self.captured_options = self._capture_options(message)
        self.max_value = min(4, len(self.captured_options))
        self.container = self.build_container()
        self.add_item(self.container)

    @staticmethod
    def _capture_options(message) -> list[discord.SelectOption]:
        """Trích xuất SelectOption từ inventory message gốc."""
        for component in message.components:
            for child in component.children:
                if hasattr(child, "children"):
                    for sub in child.children:
                        if sub.type == ComponentType.select:
                            return [
                                discord.SelectOption(
                                    label=o.label, value=o.value,
                                    description=o.description, emoji=o.emoji, default=o.default)
                                for o in sub.options
                            ]
        return []

    def build_container(self):
        container = discord.ui.Container(accent_colour=0x71368A)
        container.add_item(discord.ui.TextDisplay("## :notepad_spiral: Choose your action"))
        container.add_item(discord.ui.Separator())
        options = self.captured_options or [discord.SelectOption(label="No Items found", value="none")]

        # 1. Global ID selection — copy ID của card được chọn
        select_global_id = discord.ui.Select(placeholder="Global ID selection.", min_values=1, options=options)
        select_global_id.callback = self._make_global_id_callback(select_global_id)
        container.add_item(discord.ui.ActionRow(select_global_id))
        container.add_item(discord.ui.Separator())

        # 2. Selling selection — gửi lệnh sell tuần tự
        select_selling = discord.ui.Select(placeholder="Selling selection.", min_values=1, max_values=len(options), options=options)
        select_selling.callback = self._make_selling_callback(select_selling)
        container.add_item(discord.ui.ActionRow(select_selling))
        container.add_item(discord.ui.Separator())

        # 3. Building selection — tạo chuỗi lệnh evolution
        select_building = discord.ui.Select(placeholder="Building selection.", min_values=1, max_values=self.max_value, options=options)
        select_building.callback = self._make_building_callback(select_building)
        container.add_item(discord.ui.ActionRow(select_building))
        return container

    def _make_global_id_callback(self, select):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.defer(ephemeral=True)
                return
            option = next(o for o in self.captured_options if o.value == select.values[0])
            global_card_id = option.description.split("ID: ")[1]
            await interaction.response.send_message(global_card_id)
        return callback

    def _make_selling_callback(self, select):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.defer(ephemeral=True)
                return
            for v in select.values:
                option  = next(o for o in self.captured_options if o.value == v)
                card_id = option.description.split("ID: ")[1]
                if card_id not in self.selected_for_selling:
                    self.selected_for_selling.append(card_id)
            await interaction.response.defer()
            asyncio.create_task(process_selling(interaction.client, interaction.channel, self.selected_for_selling))
        return callback

    def _make_building_callback(self, select):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.defer(ephemeral=True)
                return
            selected = select.values
            if len(selected) in (1, 3):
                await interaction.response.send_message(
                    f"Please select either 2 or 4 and not {len(selected)}", ephemeral=True)
                return
            ids = sorted(
                [extract_inventory_id(next(o for o in self.captured_options if o.value == v)) for v in selected],
                key=int)
            await interaction.response.send_message("\n".join(build_evo_commands(ids)))
        return callback


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

async def process_selling(bot, channel, selected_ids: list[str]):
    """Gửi lệnh sell tuần tự và chờ xác nhận từ bot trước khi tiếp tục."""
    for card_id in selected_ids:
        await channel.send(f".mk sell {card_id}")

        def check(msg):
            if msg.author.id != 571027211407196161 or msg.channel.id != channel.id or not msg.components:
                return False
            content = extract_text_from_components(msg.components)
            return "Market Listing Complete" in content and str(card_id) in content

        try:
            await bot.wait_for("message", check=check, timeout=30)
            await asyncio.sleep(5)
        except asyncio.TimeoutError:
            await channel.send(f"❌ Timeout on ID {card_id}")
            break


def extract_text_from_components(components) -> str:
    """Gom toàn bộ text content từ cây component lồng nhau."""
    texts = []
    for comp in components:
        if hasattr(comp, "content") and isinstance(comp.content, str):
            texts.append(comp.content)
        if hasattr(comp, "children"):
            texts.append(extract_text_from_components(comp.children))
    return "\n".join(texts)


def extract_inventory_id(option: discord.SelectOption) -> str:
    """Lấy inventory ID (số sau dấu #) từ label của SelectOption."""
    m = re.match(r"#(\d+)", option.label)
    return m.group(1) if m else None


def build_evo_commands(card_ids: list[str]) -> list[str]:
    """Tạo chuỗi lệnh soulenh + evo tối ưu cho 2 hoặc 4 card."""
    ids = sorted(card_ids, key=int)
    if len(ids) == 4:
        a, b, c, d = ids
        return [
            f".soulenh {a}", f".soulenh {b}", f".soulenh {c}", f".soulenh {d}",
            f".evo {a} {d}", f".evo {b} {c}",
            f".soulenh {a}", f".soulenh {b}",
            f".evo {a} {b}",
            f".soulenh {a}",
        ]
    if len(ids) == 2:
        a, b = ids
        return [f".soulenh {a}", f".soulenh {b}", f".evo {a} {b}", f".soulenh {a}"]
    return []
