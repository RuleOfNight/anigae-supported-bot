import re
import time
import discord
from db_methods import players


# ---------------------------------------------------------------------------
# Player Stamina
# ---------------------------------------------------------------------------

async def player_stamina_v2(message):
    """Parse stamina message và reply embed tính toán thời gian hồi stamina."""
    m = re.search(r"\*\*(.*)\*\*, you currently have __(\d+)/(\d+)__ stamina", message.content)
    if not m:
        return
    player_name = m.group(1)
    current     = int(m.group(2))
    maximum     = int(m.group(3))
    days_left, player_id = await players.get_premium_days_left_by_discord_name(player_name)
    if days_left == "player not found":
        return
    view = PlayerStaminaView(message, player_name, player_id, current, maximum, days_left)
    try:
        await message.reply(view=view)
    except discord.HTTPException:
        await message.channel.send(view=view)


class PlayerStaminaView(discord.ui.LayoutView):
    REGEN_NORMAL = 2  # stamina per tick
    REGEN_VIP    = 3
    REGEN_TICK   = 240  # seconds

    def __init__(self, message, player_name, player_id, current, maximum, premium_days_left, timeout=120):
        super().__init__(timeout=timeout)
        self.message           = message
        self.player_name       = player_name
        self.player_id         = player_id
        self.current           = current
        self.maximum           = maximum
        self.premium_days_left = premium_days_left
        self.now               = int(time.time())
        self.add_item(self._build_container())

    def _build_container(self):
        container = discord.ui.Container(accent_colour=0x71368A)
        container.add_item(discord.ui.TextDisplay(
            f"Player** {self.player_name}** currently has **{self.current:,}/{self.maximum}** stamina."))

        if self.current >= self.maximum:
            full_at = self.now
        else:
            missing    = self.maximum - self.current
            regen_rate = self.REGEN_VIP if self.premium_days_left > 0 else self.REGEN_NORMAL
            full_at    = self.now + missing * (self.REGEN_TICK // regen_rate)

        battles = self.current // 5
        vip_timer = self.now + self.premium_days_left * 86400
        status    = "<a:check:1380797984979030016>" if self.premium_days_left > 0 else "<a:cross:1380797973373521962>"

        container.add_item(discord.ui.TextDisplay(f"Full in: <t:{full_at}:S> [<t:{full_at}:R>]"))
        container.add_item(discord.ui.TextDisplay(f"[**Battles:** {battles}] [**EXP / FAM:** {battles * 2}]"))
        container.add_item(discord.ui.TextDisplay(
            f"-# [VIP active: {status}] [VIP Days left: {self.premium_days_left} <t:{vip_timer}:d>]"))
        btn = discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger)
        btn.callback = self._delete
        container.add_item(discord.ui.ActionRow(btn))
        return container

    async def _delete(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id == self.player_id:
            await interaction.message.delete()


# ---------------------------------------------------------------------------
# Player Raid Passes
# ---------------------------------------------------------------------------

async def raid_pass_v2(message):
    """Parse raid pass message và reply embed tính thời gian refill."""
    m = re.search(
        r"\*\*(.*)\*\* currently has __(\d+)/10__ Raid Pass\(es\) <:raidpass:861860078742929428>\. \[Refills \*\*<t:(\d+):R>",
        message.content)
    if not m:
        return
    player_name    = m.group(1)
    current_passes = int(m.group(2))
    unix_timer     = int(m.group(3))
    days_left, player_id = await players.get_premium_days_left_by_discord_name(player_name)
    if days_left == "player not found":
        return
    view = PlayerRaidPassesView(message, player_name, player_id, current_passes, unix_timer, days_left)
    try:
        await message.reply(view=view)
    except discord.HTTPException:
        await message.channel.send(view=view)


class PlayerRaidPassesView(discord.ui.LayoutView):
    REGEN_TIMER = 18000  # seconds per raid pass

    def __init__(self, message, player_name, player_id, current, unix_timer, premium_days_left, timeout=120):
        super().__init__(timeout=timeout)
        self.message           = message
        self.player_name       = player_name
        self.player_id         = player_id
        self.current           = current
        self.unix_timer        = unix_timer
        self.premium_days_left = premium_days_left
        self.now               = int(time.time())
        self.add_item(self._build_container())

    def _build_container(self):
        container = discord.ui.Container(accent_colour=0x71368A)
        container.add_item(discord.ui.TextDisplay(
            f"Player** {self.player_name}** currently has **{self.current}/10** Raid Pass(es) <:raidpass:1503616319915032666>."))

        if self.current < 10:
            needed   = 10 - (self.current + 1)
            full_at  = self.unix_timer + needed * self.REGEN_TIMER
        else:
            full_at = self.now

        vip_timer = self.now + self.premium_days_left * 86400
        status    = "<a:check:1380797984979030016>" if self.premium_days_left > 0 else "<a:cross:1380797973373521962>"

        container.add_item(discord.ui.TextDisplay(
            f"[**Refill in:** <t:{self.unix_timer}:R>] [**Full in:** <t:{full_at}:R>]"))
        container.add_item(discord.ui.TextDisplay(
            f"-# [VIP active: {status}] [VIP Days left: {self.premium_days_left} <t:{vip_timer}:d>]"))
        btn = discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger)
        btn.callback = self._delete
        container.add_item(discord.ui.ActionRow(btn))
        return container

    async def _delete(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id == self.player_id:
            await interaction.message.delete()


# ---------------------------------------------------------------------------
# Player Level
# ---------------------------------------------------------------------------

async def player_lvl_v2(message):
    """Parse level message và reply embed tính số battle cần để lên level."""
    player_m = re.search(r"\*\*(.*)\*\*: Level (\d+)\s+", message.content)
    if not player_m:
        return
    exp_m = re.search(r"\[(\d+) / (\d+) EXP", message.content.replace(",", ""))
    if not exp_m:
        return
    player_name  = player_m.group(1)
    player_lvl   = int(player_m.group(2))
    current_exp  = int(exp_m.group(1))
    max_exp      = int(exp_m.group(2))
    days_left, player_id = await players.get_premium_days_left_by_discord_name(player_name)
    if days_left == "player not found":
        return
    view = PlayerLevelView(message, player_name, player_id, player_lvl, current_exp, max_exp, days_left)
    try:
        await message.reply(view=view)
    except discord.HTTPException:
        await message.channel.send(view=view)


class PlayerLevelView(discord.ui.LayoutView):
    def __init__(self, message, player_name, player_id, lvl, current_exp, max_exp, premium_days_left, timeout=120):
        super().__init__(timeout=timeout)
        self.message           = message
        self.player_name       = player_name
        self.player_id         = player_id
        self.lvl               = lvl
        self.current_exp       = current_exp
        self.max_exp           = max_exp
        self.premium_days_left = premium_days_left
        self.now               = int(time.time())
        self.add_item(self._build_container())

    def _build_container(self):
        container = discord.ui.Container(accent_colour=0x71368A)
        container.add_item(discord.ui.TextDisplay(
            f"Player **{self.player_name}** is currently Level **{self.lvl}** [{self.current_exp:,}/{self.max_exp:,}]"))

        battles = (self.max_exp - self.current_exp) // 2 + 1 if self.current_exp < self.max_exp else 0
        vip_timer = self.now + self.premium_days_left * 86400
        status    = "<a:check:1380797984979030016>" if self.premium_days_left > 0 else "<a:cross:1380797973373521962>"

        container.add_item(discord.ui.TextDisplay(
            f"[**Battles for level up:** {battles:,}] [**Needed Stamina:** {battles * 5:,}]"))
        container.add_item(discord.ui.TextDisplay(
            f"**Raid Level Spawn Range:** {self.lvl * 18:,}/{self.lvl * 26:,}"))
        container.add_item(discord.ui.TextDisplay(
            f"-# [VIP active: {status}] [VIP Days left: {self.premium_days_left} <t:{vip_timer}:d>]"))
        btn = discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger)
        btn.callback = self._delete
        container.add_item(discord.ui.ActionRow(btn))
        return container

    async def _delete(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id == self.player_id:
            await interaction.message.delete()
