import math

import discord
from discord import ui

from db_methods import breach_comps

PLAYBOOK_TITLE = "## \U0001f4d8 Breach Playbook"
PLAYBOOK_DESCRIPTION = (
    "-# N\u01a1i clan gom team comp, RNG note, \u0111i\u1ec1u ki\u1ec7n setup v\u00e0 k\u1ebft qu\u1ea3 th\u1ef1c chi\u1ebfn cho Breach.\n"
    "-# D\u00f9ng `/breach_comp_add` \u0111\u1ec3 chia s\u1ebb gi\u00e1o \u00e1n. Upvote nh\u1eefng gi\u00e1o \u00e1n \u0111\u00e1ng th\u1eed \u0111\u1ec3 \u0111\u1ea9y l\u00ean \u0111\u1ea7u b\u1ea3ng."
)
DEFAULT_CLAN_GIF_URL = "https://media.discordapp.net/attachments/922869644648411236/1528002562240942121/gZXC8lKd4XcjtL9F.gif?ex=6a5cb6c7&is=6a5b6547&hm=993dadcdf9db44ef373c88e520220d561ca3542e64b1c2518acad6237d4da833&="
EMPTY_AVATAR_URL = "https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif"
PER_PAGE = 3
PHASE_FILTERS = [
    "Docile",
    "Chaos",
    "Herald - Damnation",
    "Herald - Salvation",
    "Gambit",
    "Enraged",
    "Collapse",
]


def _clip(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "\u2026"


def _entry_short_id(entry: dict) -> str:
    return entry.get("short_id") or entry.get("id", "")[-6:]


def _entry_text(entry: dict, absolute_index: int) -> str:
    title = entry.get("title") or "Untitled Breach plan"
    author = entry.get("author_name") or "unknown"
    comp = _clip(entry.get("comp", ""), 260)
    phase = _clip(entry.get("phase", ""), 80)
    difficulty = _clip(entry.get("difficulty", ""), 80)
    rng = _clip(entry.get("rng", ""), 180)
    description = _clip(entry.get("description", ""), 260)
    result = _clip(entry.get("result", ""), 180)
    upvotes = entry.get("upvote_count", 0)

    lines = [
        f"### #{absolute_index} \u00b7 **{title}**",
        f"-# shared by **{author}** \u00b7 \u25b2 **{upvotes}**",
        f"**Team:** {comp or '*ch\u01b0a ghi team*'}",
    ]
    if phase or difficulty:
        meta = []
        if phase:
            meta.append(f"**Phase:** {phase}")
        if difficulty:
            meta.append(f"**Difficulty:** {difficulty}")
        lines.append(" \u00b7 ".join(meta))
    if rng:
        lines.append(f"**RNG:** {rng}")
    if description:
        lines.append(f"**Ghi ch\u00fa:** {description}")
    if result:
        lines.append(f"**K\u1ebft qu\u1ea3:** {result}")
    return "\n".join(lines)


def _phase_key(phase: str | None) -> str:
    return (phase or "").strip().casefold()


def _filter_entries_by_phase(entries: list[dict], phase_filter: str | None) -> list[dict]:
    if not phase_filter:
        return entries
    wanted = _phase_key(phase_filter)
    return [entry for entry in entries if _phase_key(entry.get("phase")) == wanted]


def _phase_select_options(selected_phase: str | None) -> list[discord.SelectOption]:
    options = [
        discord.SelectOption(
            label="All phases",
            value="all",
            description="Xem t\u1ea5t c\u1ea3 gi\u00e1o \u00e1n Breach tu\u1ea7n n\u00e0y.",
            emoji="\U0001f4da",
            default=selected_phase is None,
        )
    ]
    phase_emojis = {
        "Docile": "\U0001f331",
        "Chaos": "\U0001f300",
        "Herald - Damnation": "\U0001f525",
        "Herald - Salvation": "\U0001f6e1\ufe0f",
        "Gambit": "\U0001f3b2",
        "Enraged": "\U0001f4a2",
        "Collapse": "\U0001f480",
    }
    for phase in PHASE_FILTERS:
        options.append(discord.SelectOption(
            label=phase,
            value=phase,
            description=f"Ch\u1ec9 xem gi\u00e1o \u00e1n phase {phase}.",
            emoji=phase_emojis.get(phase),
            default=selected_phase == phase,
        ))
    return options


def _boss_heading(boss_info: dict) -> str:
    boss_name = (boss_info or {}).get("boss_name")
    boss_phase = (boss_info or {}).get("phase")
    if boss_name:
        phase_text = f" \u00b7 Phase hi\u1ec7n t\u1ea1i: **{boss_phase}**" if boss_phase else ""
        return f"\n-# Boss tu\u1ea7n n\u00e0y: **{boss_name}**{phase_text} \u00b7 Gi\u00e1o \u00e1n t\u1ef1 reset theo tu\u1ea7n Breach."
    return "\n-# Boss tu\u1ea7n n\u00e0y ch\u01b0a \u0111\u01b0\u1ee3c c\u1eadp nh\u1eadt. D\u00f9ng `.br` \u0111\u1ec3 Caeser \u0111\u1ecdc boss m\u1edbi."



class BreachCompBoardView(discord.ui.LayoutView):
    def __init__(
        self,
        entries: list[dict],
        page: int = 0,
        clan_image_url: str | None = None,
        boss_info: dict | None = None,
        phase_filter: str | None = None,
        *,
        timeout: int = 300,
    ):
        super().__init__(timeout=timeout)
        self.all_entries = entries
        self.phase_filter = phase_filter if phase_filter in PHASE_FILTERS else None
        self.entries = _filter_entries_by_phase(entries, self.phase_filter)
        self.boss_info = boss_info or {}
        self.clan_image_url = self.boss_info.get("image_url") or clan_image_url or DEFAULT_CLAN_GIF_URL
        self.page = max(0, page)
        self.max_pages = max(1, math.ceil(len(self.entries) / PER_PAGE))
        if self.page >= self.max_pages:
            self.page = self.max_pages - 1
        self.visible_entries = self.entries[self.page * PER_PAGE:(self.page + 1) * PER_PAGE]
        self._build()

    def _build(self):
        container = ui.Container(id=1, accent_colour=0x71368A)
        container.add_item(ui.Section(
            ui.TextDisplay(f"{PLAYBOOK_TITLE}\n{PLAYBOOK_DESCRIPTION}{_boss_heading(self.boss_info)}"),
            accessory=ui.Thumbnail(media=self.clan_image_url),
        ))
        container.add_item(ui.Separator())
        self._add_phase_select(container)
        container.add_item(ui.Separator())

        if not self.entries:
            container.add_item(ui.TextDisplay(
                "### Ch\u01b0a c\u00f3 gi\u00e1o \u00e1n n\u00e0o\n"
                "H\u00e3y m\u1edf h\u00e0ng b\u1eb1ng `/breach_comp_add` \u2014 n\u1ebfu \u0111ang l\u1ecdc theo phase, th\u1eed chuy\u1ec3n sang phase kh\u00e1c ho\u1eb7c All nh\u00e9."
            ))
        else:
            for offset, entry in enumerate(self.visible_entries):
                absolute_index = self.page * PER_PAGE + offset + 1
                avatar_url = entry.get("author_avatar_url") or EMPTY_AVATAR_URL
                short_id = _entry_short_id(entry)
                container.add_item(ui.Section(
                    ui.TextDisplay(_entry_text(entry, absolute_index)),
                    accessory=ui.Thumbnail(media=avatar_url),
                ))
                container.add_item(ui.ActionRow(
                    ui.Button(
                        label=f"\u25b2 Upvote ({entry.get('upvote_count', 0)})",
                        style=discord.ButtonStyle.success,
                        custom_id=f"breach_upvote:{offset}",
                    ),
                    ui.Button(
                        label=f"ID {short_id}",
                        style=discord.ButtonStyle.secondary,
                        disabled=True,
                    ),
                ))
                if offset != len(self.visible_entries) - 1:
                    container.add_item(ui.Separator())

        container.add_item(ui.Separator())
        phase_text = self.phase_filter or "All phases"
        container.add_item(ui.TextDisplay(
            f"-# Phase: **{phase_text}** \u00b7 Page **{self.page + 1}/{self.max_pages}** "
            f"\u00b7 Showing: **{len(self.entries)}** / **{len(self.all_entries)}** plans"
        ))
        container.add_item(ui.ActionRow(
            ui.Button(label="\u25c0 Previous", style=discord.ButtonStyle.secondary, custom_id="breach_prev", disabled=self.page <= 0),
            ui.Button(label="Next \u25b6", style=discord.ButtonStyle.secondary, custom_id="breach_next", disabled=self.page >= self.max_pages - 1),
            ui.Button(label="Refresh", style=discord.ButtonStyle.primary, custom_id="breach_refresh"),
        ))
        self.add_item(container)

    def _add_phase_select(self, container: ui.Container):
        container.add_item(ui.ActionRow(
            ui.Select(
                placeholder="Ch\u1ecdn phase \u0111\u1ec3 l\u1ecdc gi\u00e1o \u00e1n...",
                min_values=1,
                max_values=1,
                options=_phase_select_options(self.phase_filter),
                custom_id="breach_phase_select",
            )
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        custom_id = interaction.data.get("custom_id", "")
        page = self.page

        phase_filter = self.phase_filter

        if custom_id == "breach_prev":
            page -= 1
        elif custom_id == "breach_next":
            page += 1
        elif custom_id == "breach_phase_select":
            selected_value = (interaction.data.get("values") or ["all"])[0]
            phase_filter = None if selected_value == "all" else selected_value
            page = 0
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

        from db_methods import guilds
        entries = await breach_comps.get_breach_comps(interaction.guild.id)
        clan_image_url = await guilds.get_breach_playbook_image_url(interaction.guild.id)
        boss_info = await guilds.get_breach_boss_info(interaction.guild.id)
        new_view = BreachCompBoardView(
            entries,
            page=page,
            clan_image_url=clan_image_url,
            boss_info=boss_info,
            phase_filter=phase_filter,
        )
        await interaction.response.edit_message(view=new_view)
        return True
