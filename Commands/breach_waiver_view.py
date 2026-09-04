import asyncio
import math

import discord

from db_methods import guilds, weekly_donations


AUTHORIZED_BREACH_REVIEWERS = {703335523925753903, 634761405299556352, 798523920747724800}
PER_PAGE = 5
DEFAULT_AVATAR_URL = "https://cdn.discordapp.com/embed/avatars/0.png"


async def load_breach_members(guild: discord.Guild) -> list[dict]:
    members = await guilds.get_active_members(guild.id)

    async def add_avatar(member: dict) -> dict:
        discord_id = member.get("guild_member_id")
        discord_member = guild.get_member(discord_id) if discord_id else None
        if discord_member is None and discord_id:
            try:
                discord_member = await guild.fetch_member(discord_id)
            except discord.HTTPException:
                pass
        member["avatar_url"] = str(discord_member.display_avatar.url) if discord_member else DEFAULT_AVATAR_URL
        return member

    return await asyncio.gather(*(add_avatar(member) for member in members))


class BreachWaiverView(discord.ui.LayoutView):
    def __init__(self, guild_id: int, members: list[dict], qualified: set | None = None, page: int = 0):
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.members = members
        self.qualified = qualified if qualified is not None else set(range(len(members)))
        self.page = max(0, page)
        self.max_pages = max(1, math.ceil(len(members) / PER_PAGE))
        self.page = min(self.page, self.max_pages - 1)
        self._build()

    def _build(self):
        container = discord.ui.Container(accent_colour=0x71368A)
        container.add_item(discord.ui.TextDisplay(
            "## Breach — duyệt damage\n"
            "✅ = đủ damage, miễn donate tuần sau. Bỏ check = phải donate như thường."
        ))

        start = self.page * PER_PAGE
        visible_members = self.members[start:start + PER_PAGE]
        for offset, member in enumerate(visible_members):
            index = start + offset
            qualified = index in self.qualified
            button = discord.ui.Button(
                label="✅ Đủ damage" if qualified else "❌ Chưa đủ damage",
                style=discord.ButtonStyle.success if qualified else discord.ButtonStyle.danger,
                custom_id=f"breach_waiver_toggle:{index}",
            )
            button.callback = self._toggle
            container.add_item(discord.ui.Section(
                discord.ui.TextDisplay(f"**{member['guild_member_name']}**"),
                accessory=discord.ui.Thumbnail(media=member["avatar_url"]),
            ))
            container.add_item(discord.ui.ActionRow(button))

        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            f"Đủ damage: **{len(self.qualified)}/{len(self.members)}** · Page **{self.page + 1}/{self.max_pages}**"
        ))
        previous = discord.ui.Button(label="◀", style=discord.ButtonStyle.secondary, disabled=self.page == 0)
        previous.callback = self._previous
        next_page = discord.ui.Button(label="▶", style=discord.ButtonStyle.secondary, disabled=self.page >= self.max_pages - 1)
        next_page.callback = self._next
        apply = discord.ui.Button(label="Lưu miễn donate", style=discord.ButtonStyle.primary)
        apply.callback = self._apply
        container.add_item(discord.ui.ActionRow(previous, next_page, apply))
        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in AUTHORIZED_BREACH_REVIEWERS:
            return True
        await interaction.response.send_message("Không có quyền duyệt Breach.", ephemeral=True)
        return False

    async def _replace(self, interaction: discord.Interaction, page: int | None = None):
        await interaction.response.edit_message(view=BreachWaiverView(
            self.guild_id, self.members, self.qualified, self.page if page is None else page
        ))

    async def _toggle(self, interaction: discord.Interaction):
        index = int(interaction.data["custom_id"].rsplit(":", 1)[1])
        if index in self.qualified:
            self.qualified.remove(index)
        else:
            self.qualified.add(index)
        await self._replace(interaction)

    async def _previous(self, interaction: discord.Interaction):
        await self._replace(interaction, self.page - 1)

    async def _next(self, interaction: discord.Interaction):
        await self._replace(interaction, self.page + 1)

    async def _apply(self, interaction: discord.Interaction):
        channel_id = await guilds.get_weekly_donation_channel(self.guild_id) or interaction.channel_id
        applied = 0
        for index in self.qualified:
            member = self.members[index]
            if await weekly_donations.grant_next_week_waiver(
                player_name=member["guild_member_name"],
                discord_id=member.get("guild_member_id"),
                channel_id=channel_id,
                damage=0,
                source="breach_manual_review",
            ):
                applied += 1
        await interaction.response.send_message(
            f"Đã lưu **{applied}** miễn donate. {len(self.members) - len(self.qualified)} người phải donate bình thường.",
            ephemeral=True,
        )
