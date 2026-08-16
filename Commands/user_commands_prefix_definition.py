import asyncio
import discord
import json
import time
import runtime
from discord.ui import View, Button, Select
from discord.ext import commands
from Commands.user_commands_on_message import gold_emote
from Commands import user_commands_prefix, definitions
from db_methods import players, guilds, general, cards

# Familiarity levels add 2% base stats per level; Holo adds 12%.
_FAM_VALUE = {"Fam 0": 0, "Fam 1": 1, "Fam 2": 2, "Fam 3": 3, "Holo": 12}

# Base categories for the Compare stat editor, mapping label to View class.
# Defined at call time (inside methods) to avoid forward-reference issues.
_CATEGORY_LABELS = ["Rarity", "Level", "Evolution", "Ascension", "Familiarity", "Clan Stats"]


def _make_card_options(card_data_db, selected_index):
    """Build a list of SelectOption for card selection dropdowns in Compare views."""
    return [
        discord.SelectOption(
            label=f"{i + 1}) {entry['card_data']['card_name']}",
            value=str(i),
            default=(i == selected_index),
        )
        for i, entry in enumerate(card_data_db)
    ]


def _make_category_select(placeholder="Choose the stat to change."):
    """Build the shared category Select used in CompareViewEditAll and CompareViewEditOne."""
    return Select(
        placeholder=placeholder,
        options=[discord.SelectOption(label=label, value=label) for label in _CATEGORY_LABELS],
    )


class PaginatorRaidHistory(discord.ui.View):
    """Paginated embed view for displaying a player's raid history.

    Supports forward/back navigation and a delete button.
    Each page is a pre-built Embed; the footer updates with current page and total raid count.
    """

    def __init__(self, ctx_or_interaction, pages, author_id):
        """
        Args:
            ctx_or_interaction: The command context or Interaction that triggered this view.
            pages: List of discord.Embed objects, one per page.
            author_id: Discord user ID of the person who ran the command (only they can navigate).
        """
        super().__init__()
        self.ctx_or_interaction = ctx_or_interaction
        self.message = None
        self.is_interaction = hasattr(ctx_or_interaction, "response")
        self.pages = pages
        self.current_page = 0
        self.author_id = author_id

        self.delete_button = discord.ui.Button(label="", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.delete_button.callback = self.delete_callback
        self.add_item(self.delete_button)

    async def send_initial_message(self):
        """Send the first page. Must be called after constructing the view."""
        if self.is_interaction:
            await self.ctx_or_interaction.response.send_message(
                embed=self.pages[self.current_page], view=self
            )
            self.message = await self.ctx_or_interaction.original_response()
        else:
            self.message = await self.ctx_or_interaction.send(
                embed=self.pages[self.current_page], view=self
            )

    async def update_message(self):
        """Re-render the current page with an updated footer showing page/total counts."""
        embed = self.pages[self.current_page]
        total_raids = sum(len(p.fields) for p in self.pages)
        raids_so_far = len(embed.fields) + (self.current_page * 5)
        embed.set_footer(text=f"Page {self.current_page + 1} | {raids_so_far} / {total_raids} Raids found")
        await self.message.edit(embed=embed, view=self)

    async def delete_callback(self, interaction: discord.Interaction):
        """Delete the paginator message. Only the original author can do this."""
        if interaction.user.id != self.author_id:
            return
        await interaction.message.delete()

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the previous page. Disabled on the first page."""
        if interaction.user.id != self.author_id:
            return
        if self.current_page > 0:
            self.current_page -= 1
            self.next_page.disabled = False
            if self.current_page == 0:
                self.previous_page.disabled = True
            await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the next page. Disabled on the last page."""
        if interaction.user.id != self.author_id:
            return
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.previous_page.disabled = False
            if self.current_page == len(self.pages) - 1:
                self.next_page.disabled = True
            await self.update_message()
        await interaction.response.defer()


class PaginatorMarketDex(discord.ui.View):
    """Paginated embed view for the global market card price list.

    Supports three display modes controlled by `passcode`:
    - "super rare": sorted by SR price, shows SR column only
    - "ultra rare": sorted by UR price, shows UR column only
    - "All": sorted by name, shows both SR and UR columns
    """

    def __init__(self, author, card_data, passcode, wanted_page=0, items_per_page=10):
        """
        Args:
            author: The discord.Member who invoked the command.
            card_data: List of tuples — (name, sr_price, sr_timer, ur_price, ur_timer, element, talent).
            passcode: Display mode — "super rare", "ultra rare", or "All".
            wanted_page: Initial page index to display.
            items_per_page: Number of cards per page.
        """
        super().__init__(timeout=180)
        self.author = author
        self.passcode = passcode
        self.items_per_page = items_per_page

        if passcode == "super rare":
            card_data.sort(key=lambda x: (int(x[1]) if x[1].isdigit() else float("inf")))
        elif passcode == "ultra rare":
            card_data.sort(key=lambda x: (int(x[3]) if x[3].isdigit() else float("inf")))
        else:
            card_data.sort(key=lambda x: x[0])

        self.card_data = card_data
        self.total_cards = len(card_data)
        self.total_pages = (len(card_data) + items_per_page - 1) // items_per_page
        self.current_page = min(max(0, wanted_page), self.total_pages - 1)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only the original author may interact with this paginator."""
        return interaction.user == self.author

    def get_page_embed(self):
        """Build and return the embed for the current page."""
        market_embed = discord.Embed(
            title="Anigame Global Market - Caeser's edition",
            description="If you want to update the market price, please use the official market command for the corresponding card/rarity",
            color=0x71368A,
        )
        start = self.current_page * self.items_per_page
        end = min(start + self.items_per_page, len(self.card_data))
        for card, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent in self.card_data[start:end]:
            formatted_sr = f"{int(card_price_sr):,}" if card_price_sr.isdigit() else card_price_sr
            formatted_ur = f"{int(card_price_ur):,}" if card_price_ur.isdigit() else card_price_ur
            field_name = f"__**{card}**__ {card_element} {card_talent}"
            if self.passcode == "super rare":
                market_embed.add_field(
                    name=field_name,
                    value=f"SR Evo1: {formatted_sr} {gold_emote}** |** last update: {market_price_sr_timer}",
                    inline=False,
                )
            elif self.passcode == "ultra rare":
                market_embed.add_field(
                    name=field_name,
                    value=f"UR Evo1: {formatted_ur} {gold_emote}** |** last update: {market_price_ur_timer}",
                    inline=False,
                )
            else:
                market_embed.add_field(
                    name=field_name,
                    value=(
                        f"SR Evo1: {formatted_sr} {gold_emote}** |** last update: {market_price_sr_timer}\n"
                        f"UR Evo1: {formatted_ur} {gold_emote}** |** last update: {market_price_ur_timer}"
                    ),
                    inline=False,
                )
        market_embed.set_footer(text=f"Page {self.current_page + 1} of {self.total_pages} | {self.total_cards} cards found")
        market_embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")
        avatar_url = self.author.avatar.url if self.author.avatar else None
        market_embed.set_author(name=self.author.name, icon_url=avatar_url)
        return market_embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the previous page."""
        if interaction.user.id != self.author.id:
            return
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.get_page_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the next page."""
        if interaction.user.id != self.author.id:
            return
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.get_page_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Delete the market dex message."""
        if interaction.user.id != self.author.id:
            return
        await interaction.message.delete()


class ButtonsForStatusTeamWarning(View):
    """Yes/No confirmation buttons for setting a player's raid team-check status.

    Replaces the original prompt with a success embed after the player chooses.
    """

    def __init__(self, author, is_slash: bool):
        """
        Args:
            author: The discord.Member who invoked the command.
            is_slash: Whether the command was a slash command (currently unused but kept for future use).
        """
        super().__init__(timeout=180)
        self.author = author
        self.is_slash = is_slash

        self.button1 = Button(label="Yes", style=discord.ButtonStyle.green)
        self.button2 = Button(label="No", style=discord.ButtonStyle.red)
        self.delete_button = discord.ui.Button(label="", style=discord.ButtonStyle.danger, emoji="🗑️")

        self.button1.callback = self.button1_callback
        self.button2.callback = self.button2_callback
        self.delete_button.callback = self.delete_callback

        self.add_item(self.button1)
        self.add_item(self.button2)
        self.add_item(self.delete_button)

    async def delete_callback(self, interaction: discord.Interaction):
        """Delete the prompt message."""
        if interaction.user.id != self.author.id:
            return
        await interaction.message.delete()

    async def button1_callback(self, interaction: discord.Interaction):
        """Set the player's status to 'yes' and confirm."""
        if interaction.user.id != self.author.id:
            return
        await players.update_status_team_check_by_player_id_in_players(interaction.user.id, interaction.user.name, "yes")
        embed = discord.Embed(title="Update successful", description='Your status was set to "yes".')
        embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")
        avatar_url = self.author.avatar.url if self.author.avatar else None
        embed.set_author(name=self.author.name, icon_url=avatar_url)
        view = user_commands_prefix.ViewDeleteButtonPrefix(author_id=self.author.id)
        await interaction.response.edit_message(embed=embed, view=view)

    async def button2_callback(self, interaction: discord.Interaction):
        """Set the player's status to 'no' and confirm."""
        if interaction.user.id != self.author.id:
            return
        await players.update_status_team_check_by_player_id_in_players(interaction.user.id, interaction.user.name, "no")
        embed = discord.Embed(title="Update successful", description='Your status was set to "no".')
        embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")
        avatar_url = self.author.avatar.url if self.author.avatar else None
        embed.set_author(name=self.author.name, icon_url=avatar_url)
        view = user_commands_prefix.ViewDeleteButtonPrefix(author_id=self.author.id)
        await interaction.response.edit_message(embed=embed, view=view)


async def send_daily_watch_embed(ctx_or_interaction_or_channel):
    """Build and send the daily watch embed showing the current location rotation.

    Can be called from a prefix command (commands.Context), a slash command (discord.Interaction),
    or directly from a channel object (e.g. the auto-rotation task in admin_commands.py).

    The embed shows the current location's cards with their market prices, and the
    next tick time computed from a hardcoded base timestamp advanced by 12-hour intervals.

    Args:
        ctx_or_interaction_or_channel: One of commands.Context, discord.Interaction, or discord.TextChannel.
    """
    daily_watch_counter = await general.get_daily_watch_counter()
    if daily_watch_counter is None:
        msg = "Daily watch chưa được khởi tạo. Admin cần chạy `.set_daily_watch <timer> <counter>`."
        if isinstance(ctx_or_interaction_or_channel, discord.Interaction):
            await ctx_or_interaction_or_channel.response.send_message(msg, ephemeral=True)
        else:
            await ctx_or_interaction_or_channel.send(msg)
        return

    daily_watch_counter = int(daily_watch_counter)
    locations_data = await runtime.retrieve_data("locations")
    location_name = locations_data.get(str(daily_watch_counter), "N/A")
    location_name_last = locations_data.get(str(daily_watch_counter - 1), "N/A")
    location_name_next = locations_data.get(str(daily_watch_counter + 1), "N/A")

    # Advance the known rotation base tick (2025-05-01 12:00 UTC) by 12h until it's in the future.
    # This gives the Unix timestamp when the current location rotation ends.
    base_tick = 1746100800
    now = int(time.time())
    while base_tick <= now:
        base_tick += 43200

    embed = discord.Embed(
        title="Caeser's Daily Watch Overview",
        description=(
            f"__Current Location__: [{daily_watch_counter}] {location_name}\n"
            f"Ending in: <t:{base_tick}:d> <t:{base_tick}:T> <t:{base_tick}:R>"
        ),
        color=0x71368A,
    )

    card_list = await cards.get_cards_from_daily_watch_counter(daily_watch_counter)
    for card in card_list:
        card_name = card["card_name"]
        card_skill = await definitions.skill_converter_from_database(card["card_talent"])
        card_element = await definitions.element_converter_from_database(card["card_element"])
        price_sr = card["market_price_sr"]
        price_ur = card["market_price_ur"]
        if price_sr != "N/A":
            price_sr = f"{int(price_sr):,}"
        if price_ur != "N/A":
            price_ur = f"{int(price_ur):,}"
        embed.add_field(
            name=f"{card_name} {card_element} {card_skill}",
            value=f"SR EVO 1: {price_sr} {gold_emote}\nUR EVO 1: {price_ur} {gold_emote}",
            inline=False,
        )

    embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")
    embed.set_footer(text=f"Last Daily: {location_name_last}\nNext Daily: {location_name_next}")

    if isinstance(ctx_or_interaction_or_channel, commands.Context):
        avatar_url = ctx_or_interaction_or_channel.author.avatar.url if ctx_or_interaction_or_channel.author.avatar else None
        embed.set_author(name=ctx_or_interaction_or_channel.author.name, icon_url=avatar_url)
        await ctx_or_interaction_or_channel.send(embed=embed)
    elif isinstance(ctx_or_interaction_or_channel, discord.Interaction):
        avatar_url = ctx_or_interaction_or_channel.user.avatar.url if ctx_or_interaction_or_channel.user.avatar else None
        embed.set_author(name=ctx_or_interaction_or_channel.user.name, icon_url=avatar_url)
        await ctx_or_interaction_or_channel.response.send_message(embed=embed)
    else:
        await ctx_or_interaction_or_channel.send(embed=embed)


class LocationDropdown(discord.ui.Select):
    """Dropdown for toggling which locations a player has registered to watch.

    Selecting an option toggles it in the database; already-selected locations show a ✅ prefix.
    """

    def __init__(self, page_data, page, max_pages, selected_ids):
        """
        Args:
            page_data: List of (location_id, location_name) tuples for this page.
            page: Current page index (0-based).
            max_pages: Total number of pages.
            selected_ids: Set of location IDs the player has already registered.
        """
        options = []
        for id_, name in page_data:
            label = f"{id_} – {name}"
            if id_ in selected_ids:
                label = f"✅ {label}"
            options.append(discord.SelectOption(label=label, value=id_))
        super().__init__(placeholder=f"Page {page + 1}/{max_pages}", min_values=1, max_values=len(options), options=options)
        self.page = page
        self.selected_ids = selected_ids

    async def callback(self, interaction: discord.Interaction):
        """Toggle each selected location and send a followup summary of what changed."""
        await interaction.response.defer(ephemeral=True)
        added, removed = [], []
        for selected_id in self.values:
            result = await players.toggle_selected_location_for_player(interaction.user.id, selected_id)
            (added if result else removed).append(selected_id)
        db_selected_ids = await players.get_player_selected_locations_by_player_id_in_players(interaction.user.id)
        new_view = LocationPaginationView(
            self.view.locations_list, self.view.page_size, self.page, self.view.max_pages, db_selected_ids
        )
        summary = (
            f"Added: {', '.join(added) if added else '–'}\n"
            f"Removed: {', '.join(removed) if removed else '–'}"
        )
        await interaction.followup.send(content=summary, ephemeral=True)


class LocationPaginationView(discord.ui.View):
    """Paginated view wrapping LocationDropdown with Previous/Next navigation buttons.

    Each page shows up to `page_size` locations. Navigation re-fetches the player's
    current selections from the DB to keep the ✅ markers accurate.
    """

    def __init__(self, locations_list, page_size, page, max_pages, selected_ids):
        """
        Args:
            locations_list: Full list of (location_id, location_name) tuples.
            page_size: Number of locations shown per page.
            page: Current page index (0-based).
            max_pages: Total number of pages.
            selected_ids: Set of currently selected location IDs for this player.
        """
        super().__init__(timeout=180)
        self.locations_list = locations_list
        self.page_size = page_size
        self.page = page
        self.max_pages = max_pages
        self.selected_ids = selected_ids
        self.update_items()

    def update_items(self):
        """Rebuild all child items for the current page."""
        self.clear_items()
        start = self.page * self.page_size
        page_data = self.locations_list[start:start + self.page_size]
        self.add_item(LocationDropdown(page_data, self.page, self.max_pages, self.selected_ids))
        if self.page > 0:
            self.add_item(self.BackButton())
        if self.page < self.max_pages - 1:
            self.add_item(self.NextButton())

    class BackButton(discord.ui.Button):
        """Navigate to the previous location page."""

        def __init__(self):
            super().__init__(label="⬅️ Previous", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            view = self.view
            view.page -= 1
            selected_ids = await players.get_player_selected_locations_by_player_id_in_players(interaction.user.id)
            new_view = LocationPaginationView(view.locations_list, view.page_size, view.page, view.max_pages, selected_ids)
            await interaction.response.edit_message(view=new_view)

    class NextButton(discord.ui.Button):
        """Navigate to the next location page."""

        def __init__(self):
            super().__init__(label="Next ➡️", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            view = self.view
            view.page += 1
            selected_ids = await players.get_player_selected_locations_by_player_id_in_players(interaction.user.id)
            new_view = LocationPaginationView(view.locations_list, view.page_size, view.page, view.max_pages, selected_ids)
            await interaction.response.edit_message(view=new_view)


# ---------------------------------------------------------------------------
# Compare tool — multi-card stat comparison with interactive editing
# ---------------------------------------------------------------------------
# The Compare tool lets a player compare up to N cards side by side with computed stats.
# They can edit rarity/level/evo/ascension/familiarity/clan stats and the embed updates live.
#
# UI flow:
#   CompareView (main embed)
#     ├─ Edit All  → CompareViewEditAll  → CompareView<Stat>  (edit_mode="all")
#     └─ Edit One  → CompareViewEditOne  → CompareView<Stat>  (edit_mode="one", selected_index=N)
#
# card_data_db structure (list of dicts):
#   {"card_data": {card stats from DB}, "card_state": {current compare state}}
# card_state keys: card_rarity, card_level, card_evo, card_asc, card_fam, card_clan
# card_clan keys:  clan_hp, clan_atk, clan_def, clan_spd


class CompareView(View):
    """Top-level view attached to the compare embed.

    Provides Edit All, Edit One, and delete buttons.
    Edit controls open an ephemeral message so the main embed stays visible.
    """

    def __init__(self, ctx, old_embed, card_data_db):
        """
        Args:
            ctx: The commands.Context or discord.Interaction that triggered the compare.
            old_embed: The original compare embed (kept for reference, not mutated here).
            card_data_db: Mutable list of card_data_db dicts shared across all sub-views.
        """
        super().__init__(timeout=180)
        self.ctx = ctx
        self.author_id = ctx.user.id if isinstance(ctx, discord.Interaction) else ctx.author.id
        self.old_embed = old_embed
        self.card_data_db = card_data_db

        self.edit_all = Button(label="Edit All", style=discord.ButtonStyle.primary)
        self.edit_one = Button(label="Edit One", style=discord.ButtonStyle.primary)
        self.delete_button = Button(label="", style=discord.ButtonStyle.danger, emoji="🗑️")

        self.edit_all.callback = self.edit_all_callback
        self.edit_one.callback = self.edit_one_callback
        self.delete_button.callback = self.delete_callback

        self.add_item(self.edit_all)
        self.add_item(self.edit_one)
        self.add_item(self.delete_button)

    async def delete_callback(self, interaction: discord.Interaction):
        """Delete the compare embed message."""
        if interaction.user.id != self.author_id:
            return
        await interaction.message.delete()

    async def edit_all_callback(self, interaction: discord.Interaction):
        """Open the Edit All panel (ephemeral) for changing a stat across all cards at once."""
        if interaction.user.id != self.author_id:
            return
        await interaction.response.defer(ephemeral=True)
        view = CompareViewEditAll(self.ctx, interaction.message, self.old_embed, self.card_data_db)
        await interaction.followup.send(view=view, ephemeral=True)

    async def edit_one_callback(self, interaction: discord.Interaction):
        """Open the Edit One panel (ephemeral) for changing a stat on a single card."""
        if interaction.user.id != self.author_id:
            return
        await interaction.response.defer(ephemeral=True)
        view = CompareViewEditOne(self.ctx, interaction.message, self.old_embed, self.card_data_db, selected_index=0)
        await interaction.followup.send(view=view, ephemeral=True)


class CompareViewEditAll(View):
    """Category picker for the 'Edit All' mode — applies the chosen stat to every card."""

    def __init__(self, ctx, old_message, old_embed, card_data_db):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db

        self.select_category = _make_category_select()
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)

    async def select_category_callback(self, interaction: discord.Interaction):
        """Route to the appropriate stat editor view for the chosen category."""
        await interaction.response.defer(ephemeral=True)
        selected_value = self.select_category.values[0]
        msg_id = interaction.message.id
        view_class = _category_to_view_class(selected_value)
        view = view_class(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="all")
        await interaction.followup.edit_message(view=view, message_id=msg_id)


class CompareViewEditOne(View):
    """Category + card picker for the 'Edit One' mode — applies the chosen stat to one card."""

    def __init__(self, ctx, old_message, old_embed, card_data_db, selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.selected_index = selected_index

        self.card_select = Select(
            placeholder="Select card to edit",
            options=_make_card_options(card_data_db, selected_index),
        )
        self.card_select.callback = self.card_select_callback
        self.add_item(self.card_select)

        self.select_category = _make_category_select()
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)

    async def card_select_callback(self, interaction: discord.Interaction):
        """Update the highlighted card and refresh the view."""
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        new_view = CompareViewEditOne(
            self.ctx, self.message, self.old_embed, self.card_data_db, selected_index=self.selected_index
        )
        await interaction.followup.edit_message(view=new_view, message_id=interaction.message.id)

    async def select_category_callback(self, interaction: discord.Interaction):
        """Route to the appropriate stat editor for the chosen category (single-card mode)."""
        await interaction.response.defer(ephemeral=True)
        selected_value = self.select_category.values[0]
        view_class = _category_to_view_class(selected_value)
        view = view_class(
            self.ctx, self.message, self.old_embed, self.card_data_db,
            edit_mode="one", selected_index=self.selected_index,
        )
        await interaction.followup.edit_message(view=view, message_id=interaction.message.id)


class CompareViewRarity(View):
    """Stat editor: choose a rarity for one or all cards in the compare."""

    def __init__(self, ctx, old_message, old_embed, card_data_db, edit_mode="all", selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_mode = edit_mode
        self.selected_index = selected_index

        if edit_mode == "one":
            self.card_select = Select(placeholder="Select card", options=_make_card_options(card_data_db, selected_index))
            self.card_select.callback = self.card_select_callback
            self.add_item(self.card_select)

        self.select_category = Select(
            placeholder="Choose the desired rarity.",
            options=[discord.SelectOption(label=r, value=r) for r in
                     ["Base", "Common", "Uncommon", "Rare", "Super Rare", "Ultra Rare"]],
        )
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)

        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary)
        self.back_button.callback = self.back_button_callback
        self.add_item(self.back_button)

    async def card_select_callback(self, interaction: discord.Interaction):
        """Switch the highlighted card."""
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        new_view = CompareViewRarity(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
        await interaction.followup.edit_message(view=new_view, message_id=interaction.message.id)

    async def back_button_callback(self, interaction: discord.Interaction):
        """Return to the Edit All or Edit One category picker."""
        await interaction.response.defer(ephemeral=True)
        view = _make_edit_back_view(self.ctx, self.message, self.old_embed, self.card_data_db, self.edit_mode, self.selected_index)
        await interaction.followup.edit_message(view=view, message_id=interaction.message.id)

    async def select_category_callback(self, interaction: discord.Interaction):
        """Apply the selected rarity to one or all cards and refresh the embed."""
        await interaction.response.defer(ephemeral=True)
        new_value = self.select_category.values[0]
        _apply_stat(self.card_data_db, "card_rarity", new_value, self.edit_mode, self.selected_index)
        embed = await compare_embed_builder(self.ctx, self.card_data_db)
        await self.message.edit(embed=embed)


class CompareViewLevel(View):
    """Stat editor: choose a level for one or all cards in the compare."""

    def __init__(self, ctx, old_message, old_embed, card_data_db, edit_mode="all", selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_mode = edit_mode
        self.selected_index = selected_index

        if edit_mode == "one":
            self.card_select = Select(placeholder="Select card", options=_make_card_options(card_data_db, selected_index))
            self.card_select.callback = self.card_select_callback
            self.add_item(self.card_select)

        self.select_category = Select(
            placeholder="Choose the desired level.",
            options=[discord.SelectOption(label=str(lvl), value=str(lvl)) for lvl in [1, 20, 30, 40, 50, 60]],
        )
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)

        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary)
        self.back_button.callback = self.back_button_callback
        self.add_item(self.back_button)

    async def card_select_callback(self, interaction: discord.Interaction):
        """Switch the highlighted card."""
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        new_view = CompareViewLevel(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
        await interaction.followup.edit_message(view=new_view, message_id=interaction.message.id)

    async def back_button_callback(self, interaction: discord.Interaction):
        """Return to the Edit All or Edit One category picker."""
        await interaction.response.defer(ephemeral=True)
        view = _make_edit_back_view(self.ctx, self.message, self.old_embed, self.card_data_db, self.edit_mode, self.selected_index)
        await interaction.followup.edit_message(view=view, message_id=interaction.message.id)

    async def select_category_callback(self, interaction: discord.Interaction):
        """Apply the selected level and refresh the embed."""
        await interaction.response.defer(ephemeral=True)
        _apply_stat(self.card_data_db, "card_level", int(self.select_category.values[0]), self.edit_mode, self.selected_index)
        embed = await compare_embed_builder(self.ctx, self.card_data_db)
        await self.message.edit(embed=embed)


class CompareViewEvolution(View):
    """Stat editor: choose an evolution (1–3) for one or all cards."""

    def __init__(self, ctx, old_message, old_embed, card_data_db, edit_mode="all", selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_mode = edit_mode
        self.selected_index = selected_index

        if edit_mode == "one":
            self.card_select = Select(placeholder="Select card", options=_make_card_options(card_data_db, selected_index))
            self.card_select.callback = self.card_select_callback
            self.add_item(self.card_select)

        self.select_category = Select(
            placeholder="Choose the desired evolution.",
            options=[discord.SelectOption(label=str(e), value=str(e)) for e in [1, 2, 3]],
        )
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)

        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary)
        self.back_button.callback = self.back_button_callback
        self.add_item(self.back_button)

    async def card_select_callback(self, interaction: discord.Interaction):
        """Switch the highlighted card."""
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        new_view = CompareViewEvolution(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
        await interaction.followup.edit_message(view=new_view, message_id=interaction.message.id)

    async def back_button_callback(self, interaction: discord.Interaction):
        """Return to the Edit All or Edit One category picker."""
        await interaction.response.defer(ephemeral=True)
        view = _make_edit_back_view(self.ctx, self.message, self.old_embed, self.card_data_db, self.edit_mode, self.selected_index)
        await interaction.followup.edit_message(view=view, message_id=interaction.message.id)

    async def select_category_callback(self, interaction: discord.Interaction):
        """Apply the selected evolution and refresh the embed."""
        await interaction.response.defer(ephemeral=True)
        _apply_stat(self.card_data_db, "card_evo", int(self.select_category.values[0]), self.edit_mode, self.selected_index)
        embed = await compare_embed_builder(self.ctx, self.card_data_db)
        await self.message.edit(embed=embed)


class CompareViewAscension(View):
    """Stat editor: choose an ascension level (0–5) for one or all cards."""

    def __init__(self, ctx, old_message, old_embed, card_data_db, edit_mode="all", selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_mode = edit_mode
        self.selected_index = selected_index

        if edit_mode == "one":
            self.card_select = Select(placeholder="Select card", options=_make_card_options(card_data_db, selected_index))
            self.card_select.callback = self.card_select_callback
            self.add_item(self.card_select)

        self.select_category = Select(
            placeholder="Choose the desired ascension.",
            options=[discord.SelectOption(label=str(a), value=str(a)) for a in range(6)],
        )
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)

        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary)
        self.back_button.callback = self.back_button_callback
        self.add_item(self.back_button)

    async def card_select_callback(self, interaction: discord.Interaction):
        """Switch the highlighted card."""
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        new_view = CompareViewAscension(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
        await interaction.followup.edit_message(view=new_view, message_id=interaction.message.id)

    async def back_button_callback(self, interaction: discord.Interaction):
        """Return to the Edit All or Edit One category picker."""
        await interaction.response.defer(ephemeral=True)
        view = _make_edit_back_view(self.ctx, self.message, self.old_embed, self.card_data_db, self.edit_mode, self.selected_index)
        await interaction.followup.edit_message(view=view, message_id=interaction.message.id)

    async def select_category_callback(self, interaction: discord.Interaction):
        """Apply the selected ascension and refresh the embed."""
        await interaction.response.defer(ephemeral=True)
        _apply_stat(self.card_data_db, "card_asc", int(self.select_category.values[0]), self.edit_mode, self.selected_index)
        embed = await compare_embed_builder(self.ctx, self.card_data_db)
        await self.message.edit(embed=embed)


class CompareViewFamiliarity(View):
    """Stat editor: choose a familiarity tier for one or all cards.

    Fam 1/2/3 add 2%/4%/6% base stats; Holo adds 12%.
    """

    def __init__(self, ctx, old_message, old_embed, card_data_db, edit_mode="all", selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_mode = edit_mode
        self.selected_index = selected_index

        if edit_mode == "one":
            self.card_select = Select(placeholder="Select card", options=_make_card_options(card_data_db, selected_index))
            self.card_select.callback = self.card_select_callback
            self.add_item(self.card_select)

        self.select_category = Select(
            placeholder="Choose the desired familiarity.",
            options=[discord.SelectOption(label=label, value=label) for label in _FAM_VALUE],
        )
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)

        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary)
        self.back_button.callback = self.back_button_callback
        self.add_item(self.back_button)

    async def card_select_callback(self, interaction: discord.Interaction):
        """Switch the highlighted card."""
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        new_view = CompareViewFamiliarity(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
        await interaction.followup.edit_message(view=new_view, message_id=interaction.message.id)

    async def back_button_callback(self, interaction: discord.Interaction):
        """Return to the Edit All or Edit One category picker."""
        await interaction.response.defer(ephemeral=True)
        view = _make_edit_back_view(self.ctx, self.message, self.old_embed, self.card_data_db, self.edit_mode, self.selected_index)
        await interaction.followup.edit_message(view=view, message_id=interaction.message.id)

    async def select_category_callback(self, interaction: discord.Interaction):
        """Apply the selected familiarity and refresh the embed."""
        await interaction.response.defer(ephemeral=True)
        new_value = _FAM_VALUE[self.select_category.values[0]]
        _apply_stat(self.card_data_db, "card_fam", new_value, self.edit_mode, self.selected_index)
        embed = await compare_embed_builder(self.ctx, self.card_data_db)
        await self.message.edit(embed=embed)


class CompareViewClan(View):
    """Stat editor: choose a clan level (0–15) for one or all cards.

    In 'one' mode there is also a stat selector (All / HP / ATK / DEF / SPD) so the
    player can update individual clan stat slots instead of all four at once.

    Clan level N translates to stat boost value N+5 (level 1 → 6, level 15 → 20).
    Level 0 means no clan stats (value = 0).
    """

    def __init__(self, ctx, old_message, old_embed, card_data_db, edit_mode="all", selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_mode = edit_mode
        self.selected_index = selected_index
        self.selected_stat = "all"  # which clan stat slot to update in "one" mode

        if edit_mode == "one":
            self.card_select = Select(
                placeholder="Select card",
                options=_make_card_options(card_data_db, selected_index),
            )
            self.card_select.callback = self.card_select_callback
            self.add_item(self.card_select)

            self.stat_select = Select(
                placeholder="Select stat mode",
                options=[
                    discord.SelectOption(label="All Stats", value="all", default=True),
                    discord.SelectOption(label="HP", value="clan_hp"),
                    discord.SelectOption(label="ATK", value="clan_atk"),
                    discord.SelectOption(label="DEF", value="clan_def"),
                    discord.SelectOption(label="SPD", value="clan_spd"),
                ],
            )
            self.stat_select.callback = self.stat_select_callback
            self.add_item(self.stat_select)

        self.select_category = Select(
            placeholder="Choose the desired clan stats.",
            options=[discord.SelectOption(label="No Clan Stats", value="Clan0")]
                    + [discord.SelectOption(label=f"Clan Level {i}", value=f"Clan{i}") for i in range(1, 16)],
        )
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)

        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary)
        self.back_button.callback = self.back_button_callback
        self.add_item(self.back_button)

    async def card_select_callback(self, interaction: discord.Interaction):
        """Switch the highlighted card."""
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        new_view = CompareViewClan(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
        await interaction.followup.edit_message(view=new_view, message_id=interaction.message.id)

    async def stat_select_callback(self, interaction: discord.Interaction):
        """Remember which clan stat slot to update when a level is chosen."""
        await interaction.response.defer(ephemeral=True)
        self.selected_stat = self.stat_select.values[0]

    async def back_button_callback(self, interaction: discord.Interaction):
        """Return to the Edit All or Edit One category picker."""
        await interaction.response.defer(ephemeral=True)
        view = _make_edit_back_view(self.ctx, self.message, self.old_embed, self.card_data_db, self.edit_mode, self.selected_index)
        await interaction.followup.edit_message(view=view, message_id=interaction.message.id)

    async def select_category_callback(self, interaction: discord.Interaction):
        """Apply the selected clan level and refresh the embed.

        Clan level N → stat value N+5 (e.g. level 1 → 6). Level 0 → 0 (no clan boost).
        """
        await interaction.response.defer(ephemeral=True)
        level = int(self.select_category.values[0].replace("Clan", ""))
        val = 0 if level == 0 else level + 5

        if self.edit_mode == "all":
            for card_entry in self.card_data_db:
                clan = card_entry["card_state"]["card_clan"]
                clan["clan_hp"] = clan["clan_atk"] = clan["clan_def"] = clan["clan_spd"] = val
        else:
            clan = self.card_data_db[self.selected_index]["card_state"]["card_clan"]
            if self.selected_stat == "all":
                clan["clan_hp"] = clan["clan_atk"] = clan["clan_def"] = clan["clan_spd"] = val
            else:
                clan[self.selected_stat] = val

        embed = await compare_embed_builder(self.ctx, self.card_data_db)
        await self.message.edit(embed=embed)


# ---------------------------------------------------------------------------
# Compare helpers (module-level, used by multiple view classes above)
# ---------------------------------------------------------------------------


def _category_to_view_class(category: str):
    """Map a category label to the corresponding CompareView* class."""
    mapping = {
        "Rarity": CompareViewRarity,
        "Level": CompareViewLevel,
        "Evolution": CompareViewEvolution,
        "Ascension": CompareViewAscension,
        "Familiarity": CompareViewFamiliarity,
        "Clan Stats": CompareViewClan,
    }
    return mapping[category]


def _make_edit_back_view(ctx, message, old_embed, card_data_db, edit_mode, selected_index):
    """Return the appropriate 'back' view depending on whether we're in all/one mode."""
    if edit_mode == "all":
        return CompareViewEditAll(ctx, message, old_embed, card_data_db)
    return CompareViewEditOne(ctx, message, old_embed, card_data_db, selected_index=selected_index)


def _apply_stat(card_data_db, field, value, edit_mode, selected_index):
    """Write `value` into card_state[field] for one or all cards in the compare.

    Args:
        card_data_db: The shared mutable list of card dicts.
        field: Key inside card_state to update (e.g. "card_level").
        value: The new value to set.
        edit_mode: "all" to update every card, "one" to update only selected_index.
        selected_index: Index of the card to update when edit_mode is "one".
    """
    if edit_mode == "all":
        for entry in card_data_db:
            entry["card_state"][field] = value
    else:
        card_data_db[selected_index]["card_state"][field] = value


async def compare_embed_builder(ctx_interaction, card_data_db):
    """Build and return the compare embed from the current card_data_db state.

    Each card gets its own embed field showing computed stats. The best value for
    each stat across all compared cards is marked with ★.

    Args:
        ctx_interaction: commands.Context or discord.Interaction (for author attribution).
        card_data_db: List of {"card_data": ..., "card_state": ...} dicts.

    Returns:
        discord.Embed ready to send or edit into the compare message.
    """
    embed = discord.Embed(title="Caeser's compare", color=0x71368A)
    embed.set_thumbnail(url="https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif")

    if isinstance(ctx_interaction, discord.Interaction):
        avatar_url = ctx_interaction.user.avatar.url if ctx_interaction.user.avatar else None
        embed.set_author(name=ctx_interaction.user.name, icon_url=avatar_url)
    else:
        avatar_url = ctx_interaction.author.avatar.url if ctx_interaction.author.avatar else None
        embed.set_author(name=ctx_interaction.author.name, icon_url=avatar_url)

    # Short display labels for rarity, familiarity, and clan level
    rarity_map = {"Base": "Base", "Common": "C", "Uncommon": "UC", "Rare": "R", "Super Rare": "SR", "Ultra Rare": "UR"}
    fam_holo_map = {0: "F0", 1: "F1", 2: "F2", 3: "F3", 12: "H1"}
    # Clan level N+5 → display "N" (inverse of the level+5 formula applied on save)
    clan_map = {0: "0", **{lvl + 5: str(lvl) for lvl in range(1, 16)}}

    # Compute stats for every card first so we can find per-stat maxima
    calc_stats = []
    for card_entry in card_data_db:
        cd = card_entry["card_data"]
        cs = card_entry["card_state"]
        clan = cs["card_clan"]
        hp, atk, def_, spd = await definitions.calc_card_stats_compare(
            cd["card_hp"], cd["card_atk"], cd["card_def"], cd["card_spd"],
            cs["card_rarity"], cs["card_level"], cs["card_evo"], cs["card_asc"], cs["card_fam"],
            clan["clan_hp"], clan["clan_atk"], clan["clan_def"], clan["clan_spd"],
        )
        calc_stats.append({
            "hp": int(hp), "atk": int(atk), "def": int(def_), "spd": int(spd),
            "total": int(hp) + int(atk) + int(def_) + int(spd),
            "clan_hp": clan["clan_hp"], "clan_atk": clan["clan_atk"],
            "clan_def": clan["clan_def"], "clan_spd": clan["clan_spd"],
        })

    max_hp    = max(s["hp"]    for s in calc_stats)
    max_atk   = max(s["atk"]   for s in calc_stats)
    max_def   = max(s["def"]   for s in calc_stats)
    max_spd   = max(s["spd"]   for s in calc_stats)
    max_total = max(s["total"] for s in calc_stats)

    for idx, (card_entry, stats) in enumerate(zip(card_data_db, calc_stats)):
        cd = card_entry["card_data"]
        cs = card_entry["card_state"]
        card_element = await definitions.element_converter_from_database(cd["card_element"])
        card_talent = await definitions.skill_converter_from_database(cd["card_talent"])

        rarity_short   = rarity_map.get(cs["card_rarity"], cs["card_rarity"])
        fam_short      = fam_holo_map.get(cs["card_fam"], cs["card_fam"])
        cl_hp_short    = clan_map.get(stats["clan_hp"], stats["clan_hp"])
        cl_atk_short   = clan_map.get(stats["clan_atk"], stats["clan_atk"])
        cl_def_short   = clan_map.get(stats["clan_def"], stats["clan_def"])
        cl_spd_short   = clan_map.get(stats["clan_spd"], stats["clan_spd"])

        stat_str = (
            f"{rarity_short} L{cs['card_level']} E{cs['card_evo']} A{cs['card_asc']} {fam_short} "
            f"({cl_hp_short}, {cl_atk_short}, {cl_def_short}, {cl_spd_short})"
        )

        def fmt(label, val, is_max):
            return f"**{label}:** {val} ★" if is_max else f"**{label}:** {val}"

        value_lines = "\n".join([
            fmt("HP",    stats["hp"],    stats["hp"]    == max_hp),
            fmt("ATK",   stats["atk"],   stats["atk"]   == max_atk),
            fmt("DEF",   stats["def"],   stats["def"]   == max_def),
            fmt("SPD",   stats["spd"],   stats["spd"]   == max_spd),
            fmt("Total", stats["total"], stats["total"] == max_total),
        ])
        embed.add_field(
            name=f"{idx + 1}) __{cd['card_name']}__ {card_element} {card_talent}",
            value=f"**{stat_str}**:\n{value_lines}",
            inline=True,
        )

    return embed
