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


class PaginatorRaidHistory(discord.ui.View):
    def __init__(self, ctx_or_interaction, pages, author_id):
        super().__init__()
        self.ctx_or_interaction = ctx_or_interaction
        self.message = None
        self.is_interaction = hasattr(ctx_or_interaction, "response")
        self.pages = pages
        self.current_page = 0
        self.delete_button = discord.ui.Button(label="", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.delete_button.callback = self.delete_callback
        self.add_item(self.delete_button)
        self.author_id = author_id

    async def send_initial_message(self):
        if self.is_interaction:
            await self.ctx_or_interaction.response.send_message(embed=self.pages[self.current_page], view=self)
            self.message = await self.ctx_or_interaction.original_response()
        else:
            self.message = await self.ctx_or_interaction.send(embed=self.pages[self.current_page], view=self)

    async def update_message(self):
        embed = self.pages[self.current_page]
        embed.set_footer(text=f"Page {self.current_page + 1} | {len(embed.fields) + (self.current_page * 5)} / {sum(len(p.fields) for p in self.pages)} Raids found")
        await self.message.edit(embed=embed, view=self)

    async def delete_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return
        await interaction.message.delete()

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
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
    def __init__(self, author, card_data, passcode, wanted_page=0, items_per_page=10):
        super().__init__(timeout=180)
        self.author = author
        self.passcode = passcode
        self.items_per_page = items_per_page
        if passcode == "super rare":
            card_data.sort(key=lambda x: (int(x[1]) if x[1].isdigit() else float('inf')))
        elif passcode == "ultra rare":
            card_data.sort(key=lambda x: (int(x[3]) if x[3].isdigit() else float('inf')))
        else:
            card_data.sort(key=lambda x: x[0])
        self.card_data = card_data
        self.total_cards = len(card_data)
        self.total_pages = (len(card_data) + items_per_page - 1) // items_per_page
        self.current_page = min(max(0, wanted_page), self.total_pages - 1)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.author

    def get_page_embed(self):
        market_embed = discord.Embed(
            title="Anigame Global Market - Caeser's edition",
            description="If you want to update the market price, please use the official market command for the corresponding card/rarity",
            color=0x71368A)
        start_index = self.current_page * self.items_per_page
        end_index = min((self.current_page + 1) * self.items_per_page, len(self.card_data))
        for card_info in self.card_data[start_index:end_index]:
            card, card_price_sr, market_price_sr_timer, card_price_ur, market_price_ur_timer, card_element, card_talent = card_info
            formatted_price_sr = "{:,}".format(int(card_price_sr)) if card_price_sr.isdigit() else card_price_sr
            formatted_price_ur = "{:,}".format(int(card_price_ur)) if card_price_ur.isdigit() else card_price_ur
            if self.passcode == "super rare":
                market_embed.add_field(
                    name=f"__**{card}**__ {card_element} {card_talent}",
                    value=f"SR Evo1: {formatted_price_sr} {gold_emote}** |** last update: {market_price_sr_timer}",
                    inline=False)
            elif self.passcode == "ultra rare":
                market_embed.add_field(
                    name=f"__**{card}**__ {card_element} {card_talent}",
                    value=f"UR Evo1: {formatted_price_ur} {gold_emote}** |** last update: {market_price_ur_timer}",
                    inline=False)
            elif self.passcode == "All":
                market_embed.add_field(
                    name=f"__**{card}**__ {card_element} {card_talent}",
                    value=f"SR Evo1: {formatted_price_sr} {gold_emote}** |** last update: {market_price_sr_timer}\n"
                          f"UR Evo1: {formatted_price_ur} {gold_emote}** |** last update: {market_price_ur_timer}",
                    inline=False)
        market_embed.set_footer(text=f"Page {self.current_page + 1} of {self.total_pages} | {self.total_cards} cards found")
        market_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg")
        author_avatar = self.author.avatar.url if self.author.avatar else None
        market_embed.set_author(name=self.author.name, icon_url=author_avatar)
        return market_embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.get_page_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.get_page_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return
        await interaction.message.delete()


class ButtonsForStatusTeamWarning(View):
    def __init__(self, author, is_slash: bool):
        super().__init__(timeout=180)
        self.author = author
        self.is_slash = is_slash
        self.button1 = Button(label="Yes", style=discord.ButtonStyle.green)
        self.button2 = Button(label="No", style=discord.ButtonStyle.red)
        self.add_item(self.button1)
        self.add_item(self.button2)
        self.button1.callback = self.button1_callback
        self.button2.callback = self.button2_callback
        self.delete_button = discord.ui.Button(label="", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.delete_button.callback = self.delete_callback
        self.add_item(self.delete_button)

    async def delete_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return
        await interaction.message.delete()

    async def button1_callback(self, interaction):
        if interaction.user.id != self.author.id:
            return
        await players.update_status_team_check_by_player_id_in_players(interaction.user.id, interaction.user.name, "yes")
        yes_embed = discord.Embed(title="Update successful", description="Your status was set to \"yes\".")
        yes_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg")
        author_avatar = self.author.avatar.url if self.author.avatar else None
        yes_embed.set_author(name=self.author.name, icon_url=author_avatar)
        view = user_commands_prefix.ViewDeleteButtonPrefix(author_id=self.author.id)
        await interaction.response.edit_message(embed=yes_embed, view=view)

    async def button2_callback(self, interaction):
        if interaction.user.id != self.author.id:
            return
        await players.update_status_team_check_by_player_id_in_players(interaction.user.id, interaction.user.name, "no")
        no_embed = discord.Embed(title="Update successful", description="Your status was set to \"no\".")
        no_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg")
        author_avatar = self.author.avatar.url if self.author.avatar else None
        no_embed.set_author(name=self.author.name, icon_url=author_avatar)
        view = user_commands_prefix.ViewDeleteButtonPrefix(author_id=self.author.id)
        await interaction.response.edit_message(embed=no_embed, view=view)


async def send_daily_watch_embed(ctx_or_interaction_or_channel):
    daily_watch_counter = await general.get_daily_watch_counter()
    if daily_watch_counter is None:
        if isinstance(ctx_or_interaction_or_channel, discord.Interaction):
            await ctx_or_interaction_or_channel.response.send_message("Daily watch chưa được khởi tạo. Admin cần chạy `.set_daily_watch <timer> <counter>`.", ephemeral=True)
        else:
            await ctx_or_interaction_or_channel.send("Daily watch chưa được khởi tạo. Admin cần chạy `.set_daily_watch <timer> <counter>`.")
        return
    daily_watch_counter_last = int(daily_watch_counter) - 1
    daily_watch_counter_next = int(daily_watch_counter) + 1
    card_list = await cards.get_cards_from_daily_watch_counter(daily_watch_counter)
    locations_data = await runtime.retrieve_data("locations")
    location_name = locations_data.get(str(daily_watch_counter), "N/A")
    location_name_last = locations_data.get(str(daily_watch_counter_last), "N/A")
    location_name_next = locations_data.get(str(daily_watch_counter_next), "N/A")
    base_tick = 1746100800
    now = int(time.time())
    while base_tick <= now:
        base_tick += 43200
    daily_watch_embed = discord.Embed(title="Caeser's Daily Watch Overview", description=f"__Current Location__: [{daily_watch_counter}] {location_name}\nEnding in: <t:{base_tick}:d> <t:{base_tick}:T> <t:{base_tick}:R>", color=0x71368A)
    for card in card_list:
        card_name = card["card_name"]
        card_skill = await definitions.skill_converter_from_database(card["card_talent"])
        card_element = await definitions.element_converter_from_database(card["card_element"])
        card_price_sr = card["market_price_sr"]
        if card_price_sr != "N/A":
            card_price_sr = f"{int(card_price_sr):,}"
        card_price_ur = card["market_price_ur"]
        if card_price_ur != "N/A":
            card_price_ur = f"{int(card_price_ur):,}"
        daily_watch_embed.add_field(name=f"{card_name} {card_element} {card_skill}", value=f"SR EVO 1: {card_price_sr} {gold_emote}\nUR EVO 1: {card_price_ur} {gold_emote}", inline=False)
    daily_watch_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg")
    daily_watch_embed.set_footer(text=f"Last Daily: {location_name_last}\nNext Daily: {location_name_next}")
    if isinstance(ctx_or_interaction_or_channel, commands.Context):
        avatar_url = ctx_or_interaction_or_channel.author.avatar.url if ctx_or_interaction_or_channel.author.avatar else None
        daily_watch_embed.set_author(name=ctx_or_interaction_or_channel.author.name, icon_url=avatar_url)
        await ctx_or_interaction_or_channel.send(embed=daily_watch_embed)
    elif isinstance(ctx_or_interaction_or_channel, discord.Interaction):
        avatar_url = ctx_or_interaction_or_channel.user.avatar.url if ctx_or_interaction_or_channel.user.avatar else None
        daily_watch_embed.set_author(name=ctx_or_interaction_or_channel.user.name, icon_url=avatar_url)
        await ctx_or_interaction_or_channel.response.send_message(embed=daily_watch_embed)
    else:
        await ctx_or_interaction_or_channel.send(embed=daily_watch_embed)


class LocationDropdown(discord.ui.Select):
    def __init__(self, page_data, page, max_pages, selected_ids):
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
        await interaction.response.defer(ephemeral=True)
        added = []
        removed = []
        for selected_id in self.values:
            result = await players.toggle_selected_location_for_player(interaction.user.id, selected_id)
            (added if result else removed).append(selected_id)
        db_selected_ids = await players.get_player_selected_locations_by_player_id_in_players(interaction.user.id)
        view = LocationPaginationView(self.view.locations_list, self.view.page_size, self.page, self.view.max_pages, db_selected_ids)
        await interaction.followup.send(content=f"Added: {', '.join(added) if added else '–'}\nRemoved: {', '.join(removed) if removed else '–'}", ephemeral=True)


class LocationPaginationView(discord.ui.View):
    def __init__(self, locations_list, page_size, page, max_pages, selected_ids):
        super().__init__(timeout=180)
        self.locations_list = locations_list
        self.page_size = page_size
        self.page = page
        self.max_pages = max_pages
        self.selected_ids = selected_ids
        self.update_items()

    def update_items(self):
        self.clear_items()
        start = self.page * self.page_size
        end = start + self.page_size
        page_data = self.locations_list[start:end]
        self.add_item(LocationDropdown(page_data, self.page, self.max_pages, self.selected_ids))
        if self.page > 0:
            self.add_item(self.BackButton())
        if self.page < self.max_pages - 1:
            self.add_item(self.NextButton())

    class BackButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="⬅️ Previous", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            view = self.view
            view.page -= 1
            selected_ids = await players.get_player_selected_locations_by_player_id_in_players(interaction.user.id)
            new_view = LocationPaginationView(view.locations_list, view.page_size, view.page, view.max_pages, selected_ids)
            await interaction.response.edit_message(view=new_view)

    class NextButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Next ➡️", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            view = self.view
            view.page += 1
            selected_ids = await players.get_player_selected_locations_by_player_id_in_players(interaction.user.id)
            new_view = LocationPaginationView(view.locations_list, view.page_size, view.page, view.max_pages, selected_ids)
            await interaction.response.edit_message(view=new_view)


class CompareView(View):
    def __init__(self, ctx, old_embed, card_data_db):
        super().__init__(timeout=180)
        self.ctx = ctx
        if isinstance(ctx, discord.Interaction):
            self.author_id = ctx.user.id
        else:
            self.author_id = ctx.author.id
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_all = Button(label="Edit All", style=discord.ButtonStyle.primary)
        self.add_item(self.edit_all)
        self.edit_all.callback = self.edit_all_callback
        self.edit_one = Button(label="Edit One", style=discord.ButtonStyle.primary)
        self.add_item(self.edit_one)
        self.edit_one.callback = self.edit_one_callback
        self.delete_button = Button(label="", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.delete_button.callback = self.delete_callback
        self.add_item(self.delete_button)

    async def delete_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return
        await interaction.message.delete()

    async def edit_all_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return
        await interaction.response.defer(ephemeral=True)
        view = CompareViewEditAll(self.ctx, interaction.message, self.old_embed, self.card_data_db)
        await interaction.followup.send(view=view, ephemeral=True)

    async def edit_one_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return
        await interaction.response.defer(ephemeral=True)
        view = CompareViewEditOne(self.ctx, interaction.message, self.old_embed, self.card_data_db, selected_index=0)
        await interaction.followup.send(view=view, ephemeral=True)


class CompareViewEditAll(View):
    def __init__(self, ctx, old_message, old_embed, card_data_db):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.select_category = Select(placeholder="Choose the stat to change.",
                                      options=[discord.SelectOption(label="Rarity", value="Rarity"),
                                               discord.SelectOption(label="Level", value="Level"),
                                               discord.SelectOption(label="Evolution", value="Evolution"),
                                               discord.SelectOption(label="Ascension", value="Ascension"),
                                               discord.SelectOption(label="Familiarity", value="Familiarity"),
                                               discord.SelectOption(label="Clan Stats", value="Clan Stats")])
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)

    async def select_category_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        selected_value = self.select_category.values[0]
        msg_id = interaction.message.id
        if selected_value == "Rarity":
            view = CompareViewRarity(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="all")
            await interaction.followup.edit_message(view=view, message_id=msg_id)
        elif selected_value == "Level":
            view = CompareViewLevel(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="all")
            await interaction.followup.edit_message(view=view, message_id=msg_id)
        elif selected_value == "Evolution":
            view = CompareViewEvolution(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="all")
            await interaction.followup.edit_message(view=view, message_id=msg_id)
        elif selected_value == "Ascension":
            view = CompareViewAscension(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="all")
            await interaction.followup.edit_message(view=view, message_id=msg_id)
        elif selected_value == "Familiarity":
            view = CompareViewFamiliarity(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="all")
            await interaction.followup.edit_message(view=view, message_id=msg_id)
        elif selected_value == "Clan Stats":
            view = CompareViewClan(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="all")
            await interaction.followup.edit_message(view=view, message_id=msg_id)


class CompareViewEditOne(View):
    def __init__(self, ctx, old_message, old_embed, card_data_db, selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.selected_index = selected_index
        card_options = [discord.SelectOption(label=f"{i+1}) {entry['card_data']['card_name']}", value=str(i), default=(i == self.selected_index)) for i, entry in enumerate(card_data_db)]
        self.card_select = Select(placeholder="Select card to edit", options=card_options)
        self.card_select.callback = self.card_select_callback
        self.add_item(self.card_select)
        self.select_category = Select(placeholder="Choose the stat to change.",
                                      options=[discord.SelectOption(label="Rarity", value="Rarity"),
                                               discord.SelectOption(label="Level", value="Level"),
                                               discord.SelectOption(label="Evolution", value="Evolution"),
                                               discord.SelectOption(label="Ascension", value="Ascension"),
                                               discord.SelectOption(label="Familiarity", value="Familiarity"),
                                               discord.SelectOption(label="Clan Stats", value="Clan Stats")])
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)

    async def card_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        msg_id = interaction.message.id
        new_view = CompareViewEditOne(self.ctx, self.message, self.old_embed, self.card_data_db, selected_index=self.selected_index)
        await interaction.followup.edit_message(view=new_view, message_id=msg_id)

    async def select_category_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        selected_value = self.select_category.values[0]
        msg_id = interaction.message.id
        if selected_value == "Rarity":
            view = CompareViewRarity(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
            await interaction.followup.edit_message(view=view, message_id=msg_id)
        elif selected_value == "Level":
            view = CompareViewLevel(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
            await interaction.followup.edit_message(view=view, message_id=msg_id)
        elif selected_value == "Evolution":
            view = CompareViewEvolution(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
            await interaction.followup.edit_message(view=view, message_id=msg_id)
        elif selected_value == "Ascension":
            view = CompareViewAscension(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
            await interaction.followup.edit_message(view=view, message_id=msg_id)
        elif selected_value == "Familiarity":
            view = CompareViewFamiliarity(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
            await interaction.followup.edit_message(view=view, message_id=msg_id)
        elif selected_value == "Clan Stats":
            view = CompareViewClan(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
            await interaction.followup.edit_message(view=view, message_id=msg_id)


class CompareViewRarity(View):
    def __init__(self, ctx, old_message, old_embed, card_data_db, edit_mode="all", selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_mode = edit_mode
        self.selected_index = selected_index
        if self.edit_mode == "one":
            card_options = [discord.SelectOption(label=f"{i+1}) {entry['card_data']['card_name']}",value=str(i),
                                                 default=(i == self.selected_index)) for i, entry in enumerate(card_data_db)]
            self.card_select = Select(placeholder="Select card", options=card_options)
            self.card_select.callback = self.card_select_callback
            self.add_item(self.card_select)
        self.select_category = Select(placeholder="Choose the desired rarity.",
                                      options=[discord.SelectOption(label="Base", value="Base"),
                                               discord.SelectOption(label="Common", value="Common"),
                                               discord.SelectOption(label="Uncommon", value="Uncommon"),
                                               discord.SelectOption(label="Rare", value="Rare"),
                                               discord.SelectOption(label="Super Rare", value="Super Rare"),
                                               discord.SelectOption(label="Ultra Rare", value="Ultra Rare")])
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)
        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary)
        self.back_button.callback = self.back_button_callback
        self.add_item(self.back_button)

    async def card_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        msg_id = interaction.message.id
        new_view = CompareViewRarity(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
        await interaction.followup.edit_message(view=new_view, message_id=msg_id)

    async def back_button_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        msg_id = interaction.message.id
        if self.edit_mode == "all":
            view = CompareViewEditAll(self.ctx, self.message, self.old_embed, self.card_data_db)
        else:
            view = CompareViewEditOne(self.ctx, self.message, self.old_embed, self.card_data_db, selected_index=self.selected_index)
        await interaction.followup.edit_message(view=view, message_id=msg_id)

    async def select_category_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        selected_value = self.select_category.values[0]
        if self.edit_mode == "all":
            for card_entry in self.card_data_db:
                card_state = card_entry["card_state"]
                card_state["card_rarity"] = selected_value
        else:
            card_state = self.card_data_db[self.selected_index]["card_state"]
            card_state["card_rarity"] = selected_value
        embed = await compare_embed_builder(self.ctx, self.card_data_db)
        await self.message.edit(embed=embed)


class CompareViewLevel(View):
    def __init__(self, ctx, old_message, old_embed, card_data_db, edit_mode="all", selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_mode = edit_mode
        self.selected_index = selected_index
        if self.edit_mode == "one":
            card_options = [discord.SelectOption(label=f"{i+1}) {entry['card_data']['card_name']}", value=str(i),
                                                 default=(i == self.selected_index)) for i, entry in enumerate(card_data_db)]
            self.card_select = Select(placeholder="Select card", options=card_options)
            self.card_select.callback = self.card_select_callback
            self.add_item(self.card_select)
        self.select_category = Select(placeholder="Choose the desired level.",
                                      options=[discord.SelectOption(label="1", value="1"),
                                               discord.SelectOption(label="20", value="20"),
                                               discord.SelectOption(label="30", value="30"),
                                               discord.SelectOption(label="40", value="40"),
                                               discord.SelectOption(label="50", value="50"),
                                               discord.SelectOption(label="60", value="60")])
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)
        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary)
        self.back_button.callback = self.back_button_callback
        self.add_item(self.back_button)

    async def card_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        msg_id = interaction.message.id
        new_view = CompareViewLevel(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
        await interaction.followup.edit_message(view=new_view, message_id=msg_id)

    async def back_button_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        msg_id = interaction.message.id
        if self.edit_mode == "all":
            view = CompareViewEditAll(self.ctx, self.message, self.old_embed, self.card_data_db)
        else:
            view = CompareViewEditOne(self.ctx, self.message, self.old_embed, self.card_data_db, selected_index=self.selected_index)
        await interaction.followup.edit_message(view=view, message_id=msg_id)

    async def select_category_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        selected_value = self.select_category.values[0]
        if self.edit_mode == "all":
            for card_entry in self.card_data_db:
                card_state = card_entry["card_state"]
                if selected_value == "1":
                    card_state["card_level"] = 1
                elif selected_value == "20":
                    card_state["card_level"] = 20
                elif selected_value == "30":
                    card_state["card_level"] = 30
                elif selected_value == "40":
                    card_state["card_level"] = 40
                elif selected_value == "50":
                    card_state["card_level"] = 50
                elif selected_value == "60":
                    card_state["card_level"] = 60
        else:
            card_state = self.card_data_db[self.selected_index]["card_state"]
            if selected_value == "1":
                card_state["card_level"] = 1
            elif selected_value == "20":
                card_state["card_level"] = 20
            elif selected_value == "30":
                card_state["card_level"] = 30
            elif selected_value == "40":
                card_state["card_level"] = 40
            elif selected_value == "50":
                card_state["card_level"] = 50
            elif selected_value == "60":
                card_state["card_level"] = 60
        embed = await compare_embed_builder(self.ctx, self.card_data_db)
        await self.message.edit(embed=embed)


class CompareViewEvolution(View):
    def __init__(self, ctx, old_message, old_embed, card_data_db, edit_mode="all", selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_mode = edit_mode
        self.selected_index = selected_index
        if self.edit_mode == "one":
            card_options = [discord.SelectOption(label=f"{i + 1}) {entry['card_data']['card_name']}", value=str(i),
                                                 default=(i == self.selected_index)) for i, entry in enumerate(card_data_db)]
            self.card_select = Select(placeholder="Select card", options=card_options)
            self.card_select.callback = self.card_select_callback
            self.add_item(self.card_select)
        self.select_category = Select(placeholder="Choose the desired evolution.",
                                      options=[discord.SelectOption(label="1", value="1"),
                                               discord.SelectOption(label="2", value="2"),
                                               discord.SelectOption(label="3", value="3")])
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)
        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary)
        self.back_button.callback = self.back_button_callback
        self.add_item(self.back_button)

    async def card_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        msg_id = interaction.message.id
        new_view = CompareViewEvolution(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
        await interaction.followup.edit_message(view=new_view, message_id=msg_id)

    async def back_button_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        msg_id = interaction.message.id
        if self.edit_mode == "all":
            view = CompareViewEditAll(self.ctx, self.message, self.old_embed, self.card_data_db)
        else:
            view = CompareViewEditOne(self.ctx, self.message, self.old_embed, self.card_data_db, selected_index=self.selected_index)
        await interaction.followup.edit_message(view=view, message_id=msg_id)

    async def select_category_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        selected_value = self.select_category.values[0]
        if self.edit_mode == "all":
            for card_entry in self.card_data_db:
                card_state = card_entry["card_state"]
                if selected_value == "1":
                    card_state["card_evo"] = 1
                elif selected_value == "2":
                    card_state["card_evo"] = 2
                elif selected_value == "3":
                    card_state["card_evo"] = 3
        else:
            card_state = self.card_data_db[self.selected_index]["card_state"]
            if selected_value == "1":
                card_state["card_evo"] = 1
            elif selected_value == "2":
                card_state["card_evo"] = 2
            elif selected_value == "3":
                card_state["card_evo"] = 3
        embed = await compare_embed_builder(self.ctx, self.card_data_db)
        await self.message.edit(embed=embed)


class CompareViewAscension(View):
    def __init__(self, ctx, old_message, old_embed, card_data_db, edit_mode="all", selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_mode = edit_mode
        self.selected_index = selected_index
        if self.edit_mode == "one":
            card_options = [discord.SelectOption(label=f"{i + 1}) {entry['card_data']['card_name']}", value=str(i),
                                                 default=(i == self.selected_index)) for i, entry in enumerate(card_data_db)]
            self.card_select = Select(placeholder="Select card", options=card_options)
            self.card_select.callback = self.card_select_callback
            self.add_item(self.card_select)
        self.select_category = Select(placeholder="Choose the desired ascension.",
                                      options=[discord.SelectOption(label="0", value="0"),
                                               discord.SelectOption(label="1", value="1"),
                                               discord.SelectOption(label="2", value="2"),
                                               discord.SelectOption(label="3", value="3"),
                                               discord.SelectOption(label="4", value="4"),
                                               discord.SelectOption(label="5", value="5")])
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)
        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary)
        self.back_button.callback = self.back_button_callback
        self.add_item(self.back_button)

    async def card_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        msg_id = interaction.message.id
        new_view = CompareViewAscension(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
        await interaction.followup.edit_message(view=new_view, message_id=msg_id)

    async def back_button_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        msg_id = interaction.message.id
        if self.edit_mode == "all":
            view = CompareViewEditAll(self.ctx, self.message, self.old_embed, self.card_data_db)
        else:
            view = CompareViewEditOne(self.ctx, self.message, self.old_embed, self.card_data_db, selected_index=self.selected_index)
        await interaction.followup.edit_message(view=view, message_id=msg_id)

    async def select_category_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        selected_value = self.select_category.values[0]
        if self.edit_mode == "all":
            for card_entry in self.card_data_db:
                card_state = card_entry["card_state"]
                if selected_value == "0":
                    card_state["card_asc"] = 0
                elif selected_value == "1":
                    card_state["card_asc"] = 1
                elif selected_value == "2":
                    card_state["card_asc"] = 2
                elif selected_value == "3":
                    card_state["card_asc"] = 3
                elif selected_value == "4":
                    card_state["card_asc"] = 4
                elif selected_value == "5":
                    card_state["card_asc"] = 5
        else:
            card_state = self.card_data_db[self.selected_index]["card_state"]
            if selected_value == "0":
                card_state["card_asc"] = 0
            elif selected_value == "1":
                card_state["card_asc"] = 1
            elif selected_value == "2":
                card_state["card_asc"] = 2
            elif selected_value == "3":
                card_state["card_asc"] = 3
            elif selected_value == "4":
                card_state["card_asc"] = 4
            elif selected_value == "5":
                card_state["card_asc"] = 5
        embed = await compare_embed_builder(self.ctx, self.card_data_db)
        await self.message.edit(embed=embed)


class CompareViewFamiliarity(View):
    def __init__(self, ctx, old_message, old_embed, card_data_db, edit_mode="all", selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_mode = edit_mode
        self.selected_index = selected_index
        if self.edit_mode == "one":
            card_options = [discord.SelectOption(label=f"{i + 1}) {entry['card_data']['card_name']}", value=str(i),
                                                 default=(i == self.selected_index)) for i, entry in enumerate(card_data_db)]
            self.card_select = Select(placeholder="Select card", options=card_options)
            self.card_select.callback = self.card_select_callback
            self.add_item(self.card_select)
        self.select_category = Select(placeholder="Choose the desired familiarity.",
                                      options=[discord.SelectOption(label="Fam 0", value="Fam 0"),
                                               discord.SelectOption(label="Fam 1", value="Fam 1"),
                                               discord.SelectOption(label="Fam 2", value="Fam 2"),
                                               discord.SelectOption(label="Fam 3", value="Fam 3"),
                                               discord.SelectOption(label="Holo", value="Holo")])
        self.select_category.callback = self.select_category_callback
        self.add_item(self.select_category)
        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary)
        self.back_button.callback = self.back_button_callback
        self.add_item(self.back_button)

    async def card_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.selected_index = int(self.card_select.values[0])
        msg_id = interaction.message.id
        new_view = CompareViewFamiliarity(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
        await interaction.followup.edit_message(view=new_view, message_id=msg_id)

    async def back_button_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        msg_id = interaction.message.id
        if self.edit_mode == "all":
            view = CompareViewEditAll(self.ctx, self.message, self.old_embed, self.card_data_db)
        else:
            view = CompareViewEditOne(self.ctx, self.message, self.old_embed, self.card_data_db, selected_index=self.selected_index)
        await interaction.followup.edit_message(view=view, message_id=msg_id)

    async def select_category_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        selected_value = self.select_category.values[0]
        if self.edit_mode == "all":
            for card_entry in self.card_data_db:
                card_state = card_entry["card_state"]
                if selected_value == "Fam 0":
                    card_state["card_fam"] = 0
                elif selected_value == "Fam 1":
                    card_state["card_fam"] = 2
                elif selected_value == "Fam 2":
                    card_state["card_fam"] = 4
                elif selected_value == "Fam 3":
                    card_state["card_fam"] = 6
                elif selected_value == "Holo":
                    card_state["card_fam"] = 12
        else:
            card_state = self.card_data_db[self.selected_index]["card_state"]
            if selected_value == "Fam 0":
                card_state["card_fam"] = 0
            elif selected_value == "Fam 1":
                card_state["card_fam"] = 2
            elif selected_value == "Fam 2":
                card_state["card_fam"] = 4
            elif selected_value == "Fam 3":
                card_state["card_fam"] = 6
            elif selected_value == "Holo":
                card_state["card_fam"] = 12
        embed = await compare_embed_builder(self.ctx, self.card_data_db)
        await self.message.edit(embed=embed)


class CompareViewClan(View):
    def __init__(self, ctx, old_message, old_embed, card_data_db, edit_mode="all", selected_index=0):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = old_message
        self.old_embed = old_embed
        self.card_data_db = card_data_db
        self.edit_mode = edit_mode
        self.selected_index = selected_index
        self.selected_stat = "all"
        if self.edit_mode == "one":
            card_options = [discord.SelectOption(label=f"{i + 1}) {entry['card_data']['card_name']}", value=str(i), default=(i == self.selected_index)) for i, entry in enumerate(card_data_db)]
            self.card_select = Select(placeholder="Select card", options=card_options)
            self.add_item(self.card_select)

            async def card_callback(interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                self.selected_index = int(self.card_select.values[0])
                msg_id = interaction.message.id
                new_view = CompareViewClan(self.ctx, self.message, self.old_embed, self.card_data_db, edit_mode="one", selected_index=self.selected_index)
                await interaction.followup.edit_message(view=new_view, message_id=msg_id)
            self.card_select.callback = card_callback
            stat_options = [discord.SelectOption(label="All Stats", value="all", default=True),
                            discord.SelectOption(label="HP", value="clan_hp"),
                            discord.SelectOption(label="ATK", value="clan_atk"),
                            discord.SelectOption(label="DEF", value="clan_def"),
                            discord.SelectOption(label="SPD", value="clan_spd")]
            self.stat_select = Select(placeholder="Select stat mode", options=stat_options)
            self.add_item(self.stat_select)

            async def stat_callback(interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                self.selected_stat = self.stat_select.values[0]

        clan_options = [discord.SelectOption(label="No Clan Stats", value="Clan0")] + [discord.SelectOption(label=f"Clan Level {i}", value=f"Clan{i}") for i in range(1, 16)]
        self.select_category = Select(placeholder="Choose the desired clan stats.", options=clan_options)
        self.add_item(self.select_category)

        async def category_callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            selected_value = self.select_category.values[0]
            level = int(selected_value.replace("Clan", ""))
            val = 0 if level == 0 else level + 5
            if self.edit_mode == "all":
                for card_entry in self.card_data_db:
                    card_clan = card_entry["card_state"]["card_clan"]
                    card_clan["clan_hp"] = val
                    card_clan["clan_atk"] = val
                    card_clan["clan_def"] = val
                    card_clan["clan_spd"] = val
            else:
                card_clan = self.card_data_db[self.selected_index]["card_state"]["card_clan"]
                if self.selected_stat == "all":
                    card_clan["clan_hp"] = val
                    card_clan["clan_atk"] = val
                    card_clan["clan_def"] = val
                    card_clan["clan_spd"] = val
                else:
                    card_clan[self.selected_stat] = val
            embed = await compare_embed_builder(self.ctx, self.card_data_db)
            await self.message.edit(embed=embed)

        self.select_category.callback = category_callback
        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary)
        self.add_item(self.back_button)

        async def back_callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            msg_id = interaction.message.id
            if self.edit_mode == "all":
                view = CompareViewEditAll(self.ctx, self.message, self.old_embed, self.card_data_db)
            else:
                view = CompareViewEditOne(self.ctx, self.message, self.old_embed, self.card_data_db, selected_index=self.selected_index)
            await interaction.followup.edit_message(view=view, message_id=msg_id)
        self.back_button.callback = back_callback

async def compare_embed_builder(ctx_interaction, card_data_db):
    compare_embed = discord.Embed(title="Caeser's compare", description=None, color=0x71368A)
    compare_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg")
    if isinstance(ctx_interaction, discord.Interaction):
        avatar_url = ctx_interaction.user.avatar.url if ctx_interaction.user.avatar else None
        compare_embed.set_author(name=ctx_interaction.user.name, icon_url=avatar_url)
    else:
        author_avatar = ctx_interaction.author.avatar.url if ctx_interaction.author.avatar else None
        compare_embed.set_author(name=ctx_interaction.author.name, icon_url=author_avatar)
    rarity_map = {"Base": "Base", "Common": "C", "Uncommon": "UC", "Rare": "R", "Super Rare": "SR", "Ultra Rare": "UR"}
    fam_holo_map = {0: "F0", 2: "F1", 4: "F2", 6: "F3", 12: "H1"}
    clan_map = {0: "0", 6: "1", 7: "2", 8: "3", 9: "4", 10: "5", 11: "6", 12: "7", 13: "8",
                14: "9", 15: "10", 16: "11", 17: "12", 18: "13", 19: "14", 20: "15"}
    calc_stats = []
    for card_entry in card_data_db:
        card_data = card_entry["card_data"]
        card_state = card_entry["card_state"]
        clan_hp = card_state["card_clan"]["clan_hp"]
        clan_atk = card_state["card_clan"]["clan_atk"]
        clan_def = card_state["card_clan"]["clan_def"]
        clan_spd = card_state["card_clan"]["clan_spd"]
        calc_card_hp, calc_card_atk, calc_card_def, calc_card_spd = await definitions.calc_card_stats_compare(card_data["card_hp"], card_data["card_atk"], card_data["card_def"], card_data["card_spd"],
                                                                                                              card_state["card_rarity"], card_state["card_level"], card_state["card_evo"],
                                                                                                              card_state["card_asc"], card_state["card_fam"],
                                                                                                              clan_hp, clan_atk, clan_def, clan_spd)
        calc_stats.append({"hp": int(calc_card_hp), "atk": int(calc_card_atk), "def": int(calc_card_def), "spd": int(calc_card_spd),
                           "total": int(calc_card_hp) + int(calc_card_atk) + int(calc_card_def) + int(calc_card_spd),
                           "clan_hp": clan_hp, "clan_atk": clan_atk, "clan_def": clan_def, "clan_spd": clan_spd})
    max_hp = max(s["hp"] for s in calc_stats)
    max_atk = max(s["atk"] for s in calc_stats)
    max_def = max(s["def"] for s in calc_stats)
    max_spd = max(s["spd"] for s in calc_stats)
    max_total = max(s["total"] for s in calc_stats)
    for idx, (card_entry, stats) in enumerate(zip(card_data_db, calc_stats)):
        card_data = card_entry["card_data"]
        card_state = card_entry["card_state"]
        card_element = await definitions.element_converter_from_database(card_data["card_element"])
        card_talent = await definitions.skill_converter_from_database(card_data["card_talent"])
        rarity_short = rarity_map.get(card_state["card_rarity"], card_state["card_rarity"])
        fam_holo_short = fam_holo_map.get(card_state["card_fam"], card_state["card_fam"])
        cl_hp_short = clan_map.get(stats["clan_hp"], stats["clan_hp"])
        cl_atk_short = clan_map.get(stats["clan_atk"], stats["clan_atk"])
        cl_def_short = clan_map.get(stats["clan_def"], stats["clan_def"])
        cl_spd_short = clan_map.get(stats["clan_spd"], stats["clan_spd"])
        stat_str = (f"{rarity_short} L{card_state['card_level']} E{card_state['card_evo']} A{card_state['card_asc']} {fam_holo_short} "
                    f"({cl_hp_short}, {cl_atk_short}, {cl_def_short}, {cl_spd_short})")
        hp_str = f"**HP:** {stats['hp']} ★" if stats["hp"] == max_hp else f"**HP:** {stats['hp']}"
        atk_str = f"**ATK:** {stats['atk']} ★" if stats["atk"] == max_atk else f"**ATK:** {stats['atk']}"
        def_str = f"**DEF:** {stats['def']} ★" if stats["def"] == max_def else f"**DEF:** {stats['def']}"
        spd_str = f"**SPD:** {stats['spd']} ★" if stats["spd"] == max_spd else f"**SPD:** {stats['spd']}"
        total_str = f"**Total:** {stats['total']} ★" if stats["total"] == max_total else f"**Total:** {stats['total']}"
        compare_embed.add_field(name=f"{idx + 1}) __{card_data['card_name']}__ {card_element} {card_talent}",
                                value=f"**{stat_str}**:\n" + "\n".join([hp_str, atk_str, def_str, spd_str, total_str]),
                                inline=True)
    return compare_embed

