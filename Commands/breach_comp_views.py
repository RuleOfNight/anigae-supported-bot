import math

import discord
from discord import ui

from db_methods import breach_comps

PLAYBOOK_TITLE = "## \U0001f4d8 Breach Playbook \u2014 Gi\u00e1o \u00c1n Cu\u1ed1i Tu\u1ea7n"
PLAYBOOK_DESCRIPTION = (
    "-# N\u01a1i clan gom team comp, RNG note, \u0111i\u1ec1u ki\u1ec7n setup v\u00e0 k\u1ebft qu\u1ea3 th\u1ef1c chi\u1ebfn cho Breach.\n"
    "-# D\u00f9ng `/breach_comp_add` \u0111\u1ec3 chia s\u1ebb gi\u00e1o \u00e1n. Upvote nh\u1eefng gi\u00e1o \u00e1n \u0111\u00e1ng th\u1eed \u0111\u1ec3 \u0111\u1ea9y l\u00ean \u0111\u1ea7u b\u1ea3ng."
)
EMPTY_AVATAR_URL = "https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif"
PER_PAGE = 5


def _clip(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "\u2026"


def _entry_text(entry: dict, absolute_index: int) -> str:
    title = entry.get("title") or "Untitled Breach plan"
    author = entry.get("author_name") or "unknown"
    comp = _clip(entry.get("comp", ""), 260)
    rng = _clip(entry.get("rng", ""), 180)
    description = _clip(entry.get("description", ""), 260)
    result = _clip(entry.get("result", ""), 180)
    upvotes = entry.get("upvote_count", 0)

    lines = [
        f"### #{absolute_index} \u00b7 Gi\u00e1o \u00e1n **{title}**",
        f"-# shared by **{author}** \u00b7 \u25b2 **{upvotes}**",
        f"**Team:** {comp or '*ch\u01b0a ghi team*'}",
    ]
    if rng:
        lines.append(f"**RNG:** {rng}")
    if description:
        lines.append(f"**Ghi ch\u00fa:** {description}")
    if result:
        lines.append(f"**K\u1ebft qu\u1ea3:** {result}")
    return "\n".join(lines)


class BreachCompBoardView(discord.ui.LayoutView):
    def __init__(self, entries: list[dict], page: int = 0, *, timeout: int = 300):
        super().__init__(timeout=timeout)
        self.entries = entries
        self.page = max(0, page)
        self.max_pages = max(1, math.ceil(len(entries) / PER_PAGE))
        if self.page >= self.max_pages:
            self.page = self.max_pages - 1
        self.visible_entries = self.entries[self.page * PER_PAGE:(self.page + 1) * PER_PAGE]
        self._build()

    def _build(self):
        container = ui.Container(id=1, accent_colour=0x71368A)
        container.add_item(ui.TextDisplay(PLAYBOOK_TITLE))
        container.add_item(ui.TextDisplay(PLAYBOOK_DESCRIPTION))
        container.add_item(ui.Separator())

        if not self.entries:
            container.add_item(ui.TextDisplay(
                "### Ch\u01b0a c\u00f3 gi\u00e1o \u00e1n n\u00e0o\n"
                "H\u00e3y m\u1edf h\u00e0ng b\u1eb1ng `/breach_comp_add` \u2014 m\u1ed9t comp t\u1ed1t h\u00f4m nay c\u00f3 th\u1ec3 c\u1ee9u c\u1ea3 clan cu\u1ed1i tu\u1ea7n sau."
            ))
        else:
            for offset, entry in enumerate(self.visible_entries):
                absolute_index = self.page * PER_PAGE + offset + 1
                avatar_url = entry.get("author_avatar_url") or EMPTY_AVATAR_URL
                container.add_item(ui.Section(
                    ui.TextDisplay(_entry_text(entry, absolute_index)),
                    accessory=ui.Thumbnail(media=avatar_url),
                ))
                container.add_item(ui.ActionRow(
                    ui.Button(
                        label=f"\u25b2 Upvote ({entry.get('upvote_count', 0)})",
                        style=discord.ButtonStyle.success,
                        custom_id=f"breach_upvote:{offset}",
                    )
                ))
                if offset != len(self.visible_entries) - 1:
                    container.add_item(ui.Separator())

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# Page **{self.page + 1}/{self.max_pages}** \u00b7 Total plans: **{len(self.entries)}**"))
        container.add_item(ui.ActionRow(
            ui.Button(label="\u25c0 Previous", style=discord.ButtonStyle.secondary, custom_id="breach_prev", disabled=self.page <= 0),
            ui.Button(label="Next \u25b6", style=discord.ButtonStyle.secondary, custom_id="breach_next", disabled=self.page >= self.max_pages - 1),
            ui.Button(label="Refresh", style=discord.ButtonStyle.primary, custom_id="breach_refresh"),
        ))
        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        custom_id = interaction.data.get("custom_id", "")
        page = self.page

        if custom_id == "breach_prev":
            page -= 1
        elif custom_id == "breach_next":
            page += 1
        elif custom_id.startswith("breach_upvote:"):
            try:
                offset = int(custom_id.split(":", 1)[1])
                entry = self.visible_entries[offset]
            except (ValueError, IndexError):
                await interaction.response.send_message("Kh\u00f4ng t\u00ecm th\u1ea5y gi\u00e1o \u00e1n n\u00e0y n\u1eefa, th\u1eed Refresh nh\u00e9.", ephemeral=True)
                return True
            result = await breach_comps.toggle_upvote(entry["id"], interaction.user.id)
            if result is None:
                await interaction.response.send_message("Gi\u00e1o \u00e1n n\u00e0y kh\u00f4ng c\u00f2n t\u1ed3n t\u1ea1i.", ephemeral=True)
                return True
        elif custom_id != "breach_refresh":
            return True

        entries = await breach_comps.get_breach_comps(interaction.guild.id)
        new_view = BreachCompBoardView(entries, page=page)
        await interaction.response.edit_message(view=new_view)
        return True
