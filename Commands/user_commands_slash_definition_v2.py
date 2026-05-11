import discord
from discord import MediaGalleryItem, ui
from discord.ext import commands
from discord.ui import View, Button, MediaGallery, Thumbnail, Select
from db_methods import players, guilds
import json
import os
import asyncio
gold_emote = "<:GOLD:1338511775448043541>"
picture_caeser = "https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg"


async def raid_guide_builder(boss_found, rare_string, sr_string, ur_string,
                             rarity_filter, card_element, card_talent, interaction):

    class RaidGuideAddon(discord.ui.Container):
        text = discord.ui.TextDisplay("-# The information above is shared by community members and reflects their opinions and experiences. "
                                      "Strategies, team compositions, and outcomes may vary based on individual playstyles and circumstances. "
                                      "Any mistakes or issues can be messaged to any of the guide helper on the official anigame server.")

    class RaidGuideRare(discord.ui.Container):
        boss_name = discord.ui.TextDisplay(f"## {card_element} {card_talent} {boss_found}")
        thumbnail_rare = discord.ui.Section(discord.ui.TextDisplay(f"{rare_string}"), accessory=discord.ui.Thumbnail(media=f"{picture_caeser}"))
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="All", style=discord.ButtonStyle.secondary, custom_id="Main"),
                                           discord.ui.Button(label="Rare", style=discord.ButtonStyle.primary, custom_id="R"),
                                           discord.ui.Button(label="Super Rare", style=discord.ButtonStyle.secondary, custom_id="SR"),
                                           discord.ui.Button(label="Ultra Rare", style=discord.ButtonStyle.secondary, custom_id="UR"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="Delete"))

    class RaidGuideSuperRare(discord.ui.Container):
        boss_name = discord.ui.TextDisplay(f"## {card_element} {card_talent} {boss_found}")
        thumbnail_rare = discord.ui.Section(discord.ui.TextDisplay(f"{sr_string}"), accessory=discord.ui.Thumbnail(media=f"{picture_caeser}"))
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="All", style=discord.ButtonStyle.secondary, custom_id="Main"),
                                           discord.ui.Button(label="Rare", style=discord.ButtonStyle.secondary, custom_id="R"),
                                           discord.ui.Button(label="Super Rare", style=discord.ButtonStyle.primary, custom_id="SR"),
                                           discord.ui.Button(label="Ultra Rare", style=discord.ButtonStyle.secondary, custom_id="UR"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="Delete"))

    class RaidGuideUltraRare(discord.ui.Container):
        boss_name = discord.ui.TextDisplay(f"## {card_element} {card_talent} {boss_found}")
        thumbnail_rare = discord.ui.Section(discord.ui.TextDisplay(f"{ur_string}"), accessory=discord.ui.Thumbnail(media=f"{picture_caeser}"))
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="All", style=discord.ButtonStyle.secondary, custom_id="Main"),
                                           discord.ui.Button(label="Rare", style=discord.ButtonStyle.secondary, custom_id="R"),
                                           discord.ui.Button(label="Super Rare", style=discord.ButtonStyle.secondary, custom_id="SR"),
                                           discord.ui.Button(label="Ultra Rare", style=discord.ButtonStyle.primary, custom_id="UR"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="Delete"))

    class RaidGuideContainer(discord.ui.Container):
        boss_name = discord.ui.TextDisplay(f"## {card_element} {card_talent} {boss_found}")
        thumbnail_rare = discord.ui.Section(discord.ui.TextDisplay(f"{rare_string}"), accessory=discord.ui.Thumbnail(media=f"{picture_caeser}"))
        sep2 = discord.ui.Separator()
        text_super_rare = discord.ui.TextDisplay(f"{sr_string}")
        sep3 = discord.ui.Separator()
        text_ultra_rare = discord.ui.TextDisplay(f"{ur_string}")
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="All", style=discord.ButtonStyle.primary, custom_id="Main"),
                                           discord.ui.Button(label="Rare", style=discord.ButtonStyle.secondary, custom_id="R"),
                                           discord.ui.Button(label="Super Rare", style=discord.ButtonStyle.secondary, custom_id="SR"),
                                           discord.ui.Button(label="Ultra Rare", style=discord.ButtonStyle.secondary, custom_id="UR"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="Delete"))

    class RaidGuideView(discord.ui.LayoutView):
        container = RaidGuideContainer(id=1, accent_colour=0x71368A)
        container2 = RaidGuideAddon(id=2, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            button_id = interaction.data.get("custom_id")
            if button_id == "Main":
                await interaction.response.edit_message(view=RaidGuideView())
            elif button_id == "R":
                await interaction.response.edit_message(view=RaidGuideViewRare())
            elif button_id == "SR":
                await interaction.response.edit_message(view=RaidGuideViewSuperRare())
            elif button_id == "UR":
                await interaction.response.edit_message(view=RaidGuideViewUltraRare())
            elif button_id == "Delete":
                await interaction.message.delete()
            return True

    class RaidGuideViewRare(discord.ui.LayoutView):
        container = RaidGuideRare(id=1, accent_colour=0x71368A)
        container2 = RaidGuideAddon(id=2, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            button_id = interaction.data.get("custom_id")
            if button_id == "Main":
                await interaction.response.edit_message(view=RaidGuideView())
            elif button_id == "R":
                await interaction.response.edit_message(view=RaidGuideViewRare())
            elif button_id == "SR":
                await interaction.response.edit_message(view=RaidGuideViewSuperRare())
            elif button_id == "UR":
                await interaction.response.edit_message(view=RaidGuideViewUltraRare())
            elif button_id == "Delete":
                await interaction.message.delete()
            return True

    class RaidGuideViewSuperRare(discord.ui.LayoutView):
        container = RaidGuideSuperRare(id=1, accent_colour=0x71368A)
        container2 = RaidGuideAddon(id=2, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            button_id = interaction.data.get("custom_id")
            if button_id == "Main":
                await interaction.response.edit_message(view=RaidGuideView())
            elif button_id == "R":
                await interaction.response.edit_message(view=RaidGuideViewRare())
            elif button_id == "SR":
                await interaction.response.edit_message(view=RaidGuideViewSuperRare())
            elif button_id == "UR":
                await interaction.response.edit_message(view=RaidGuideViewUltraRare())
            elif button_id == "Delete":
                await interaction.message.delete()
            return True

    class RaidGuideViewUltraRare(discord.ui.LayoutView):
        container = RaidGuideUltraRare(id=1, accent_colour=0x71368A)
        container2 = RaidGuideAddon(id=2, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            button_id = interaction.data.get("custom_id")
            if button_id == "Main":
                await interaction.response.edit_message(view=RaidGuideView())
            elif button_id == "R":
                await interaction.response.edit_message(view=RaidGuideViewRare())
            elif button_id == "SR":
                await interaction.response.edit_message(view=RaidGuideViewSuperRare())
            elif button_id == "UR":
                await interaction.response.edit_message(view=RaidGuideViewUltraRare())
            elif button_id == "Delete":
                await interaction.message.delete()
            return True

    if rarity_filter in ("r", "rare"):
        view = RaidGuideViewRare()
    elif rarity_filter in ("sr", "super rare"):
        view = RaidGuideViewSuperRare()
    elif rarity_filter in ("ur", "ultra rare"):
        view = RaidGuideViewUltraRare()
    else:
        view = RaidGuideView()
    await interaction.response.send_message(view=view)


async def rulesets_builder(interaction):

    class RuleSetButton(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            button_id = interaction.data.get("custom_id")
            if button_id == "000023":
                await interaction.response.send_message("000023")
            elif button_id == "00007i":
                await interaction.response.send_message("00007i")
            elif button_id == "00006q":
                await interaction.response.send_message("00006q")
            elif button_id == "00003l":
                await interaction.response.send_message("00003l")
            elif button_id == "00007o":
                await interaction.response.send_message("00007o")
            elif button_id == "00009d":
                await interaction.response.send_message("00009d")
            elif button_id == "00001q":
                await interaction.response.send_message("00001q")
            elif button_id == "00005j":
                await interaction.response.send_message("00005j")
            return True

    class RuleSetContainer(discord.ui.Container):
        ruleset_header = discord.ui.TextDisplay("## <:da_rules:1414757426535862393> RULESET CODES <:da_rules:1414757426535862393>\n\n"
                                                "__Default Chances__: 15% resist, 5% crit and 1% evasion")
        section1 = discord.ui.Section(
            accessory=RuleSetButton(label='send code', style=discord.ButtonStyle.secondary, custom_id="000023")).add_item(
            discord.ui.TextDisplay("**000023** - 0% crit chance"))
        sep_1 = discord.ui.Separator()
        section2 = discord.ui.Section(
            accessory=RuleSetButton(label='send code', style=discord.ButtonStyle.secondary, custom_id="00007i")).add_item(
            discord.ui.TextDisplay("**00007i** - 0% evade chance"))
        sep_2 = discord.ui.Separator()
        section3 = discord.ui.Section(
            accessory=RuleSetButton(label='send code', style=discord.ButtonStyle.secondary, custom_id="00006q")).add_item(
            discord.ui.TextDisplay("**00006q** - 0% resist chance"))
        sep_3 = discord.ui.Separator()
        section4 = discord.ui.Section(
            accessory=RuleSetButton(label='send code', style=discord.ButtonStyle.secondary, custom_id="00003l")).add_item(
            discord.ui.TextDisplay("**00003l** - 0% crit chance + 0% evade chance"))
        sep_4 = discord.ui.Separator()
        section5 = discord.ui.Section(
            accessory=RuleSetButton(label='send code', style=discord.ButtonStyle.secondary, custom_id="00007o")).add_item(
            discord.ui.TextDisplay("**00007o** - 0% crit chance + 0% resist chance"))
        sep_5 = discord.ui.Separator()
        section6 = discord.ui.Section(
            accessory=RuleSetButton(label='send code', style=discord.ButtonStyle.secondary, custom_id="00009d")).add_item(
            discord.ui.TextDisplay("**00009d** - 0% evade chance + 0% resist chance"))
        sep_6 = discord.ui.Separator()
        section7 = discord.ui.Section(
            accessory=RuleSetButton(label='send code', style=discord.ButtonStyle.secondary, custom_id="00001q")).add_item(
            discord.ui.TextDisplay("**00001q** - 0% crit chance + 0% evade chance + 0% resist chance"))
        sep_7 = discord.ui.Separator()
        section8 = discord.ui.Section(
            accessory=RuleSetButton(label='send code', style=discord.ButtonStyle.secondary, custom_id="00005j")).add_item(
            discord.ui.TextDisplay("**00005j** - 100% resist chance"))
        sep_8 = discord.ui.Separator()
        ruleset_disclaimer = discord.ui.TextDisplay("-# __Disclaimer__: Turning \"off\" the default values will not result "
                                                    "in disabled talents! Therefor talents like Evasion will still be able to evade you. "
                                                    "Rulesets are only usable in ``/dg battles`` !")

    class RuleSetView(discord.ui.LayoutView):
        container = RuleSetContainer(id=1, accent_colour=0x71368A)

    view = RuleSetView()
    await interaction.response.send_message(view=view)


async def update_builder(interaction):
    discord_id = interaction.user.id
    discord_name = interaction.user.name

    class RuleSetContainer(discord.ui.Container):
        update_text = discord.ui.TextDisplay("<a:check:1380797984979030016> **Player has been updated.**\n"
                                             f"Name: ``{discord_name}``\nID: ``{discord_id}``")

    class UpdateView(discord.ui.LayoutView):
        container = RuleSetContainer(id=1, accent_colour=0x71368A)

    view = UpdateView()
    await interaction.response.send_message(view=view)


async def settings_builder(interaction):
    await interaction.response.defer()
    discord_id = interaction.user.id
    discord_name = interaction.user.name
    player_settings = await players.get_settings_from_player_by_discord_id(discord_id)
    if player_settings == "No Player found.":
        await ctx.send("No player found. Please use the ``update`` command to update your profile.")
        return

    async def build_settings():
        if player_settings["raid_lobby_status"] == "long":
            button_style_rl = discord.ButtonStyle.green
            status_rl = "long"
        else:
            button_style_rl = discord.ButtonStyle.danger
            status_rl = "short"
        if player_settings["raid_search_history"] == "yes":
            button_style_rsh = discord.ButtonStyle.green
        else:
            button_style_rsh = discord.ButtonStyle.danger

        class SettingsContainer(discord.ui.Container):
            settings_text = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## Caeser's settings\n**Player Name / ID:**\n{discord_name} / {discord_id}"))
            button_rows_1 = discord.ui.ActionRow(discord.ui.Button(label=f"raid lobby {status_rl}", style=button_style_rl, custom_id="Raid Lobby"),
                                                 discord.ui.Button(label=f"raid search history delete", style=button_style_rsh, custom_id="Raid Search History Delete"))

        class SettingsView(discord.ui.LayoutView):
            container = SettingsContainer(id=1, accent_colour=0x71368A)

            async def interaction_check(self, interaction: discord.Interaction):
                if interaction.user.id != discord_id:
                    await interaction.response.defer(ephemeral=True)
                    return False
                button_id = interaction.data.get("custom_id")
                if button_id == "Raid Lobby":
                    await players.update_player_settings_rl_by_discord_id(discord_id)
                elif button_id == "Raid Search History Delete":
                    await players.update_player_settings_rsh_by_discord_id(discord_id)
                nonlocal player_settings
                new_settings = await players.get_settings_from_player_by_discord_id(discord_id)
                player_settings = new_settings
                await interaction.response.edit_message(view=await build_settings())
                return True
        return SettingsView()
    view = await build_settings()
    await interaction.followup.send(view=view)


async def raid_lobby_search_builder(interaction, text):

    class RaidLobbySearchContainer(discord.ui.Container):
        settings_text = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"{text}"))

    class RaidLobbySearchView(discord.ui.LayoutView):
        container = RaidLobbySearchContainer(id=1, accent_colour=0x71368A)

    view = RaidLobbySearchView()
    await interaction.followup.send(view=view)


# ---------------------------
# Reworked V2
# ---------------------------


class DeleteGuildLayoutView(discord.ui.LayoutView):
    def __init__(self, guild_id, author, *, timeout=180):
        super().__init__(timeout=timeout)
        self.guild_id = guild_id
        self.author = author
        self.container = self.build_container()
        self.add_item(self.container)

    def build_container(self):
        container = ui.Container()
        container.add_item(ui.TextDisplay("## ⚠️ Delete Guild"))
        container.add_item(ui.TextDisplay("Do you really want to delete this guild?"))
        container.add_item(ui.Separator())
        button_yes = ui.Button(label="Yes", style=discord.ButtonStyle.danger)
        button_yes.callback = self.yes_delete_callback
        button_no = ui.Button(label="No", style=discord.ButtonStyle.secondary)
        button_no.callback = self.no_delete_callback
        button_delete = ui.Button(label="🗑️", style=discord.ButtonStyle.danger)
        button_delete.callback = self.delete_button
        container.add_item(ui.ActionRow(button_yes, button_no, button_delete))
        return container

    async def yes_delete_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.defer()
            return
        result = await guilds.delete_guild_by_guild_id_from_guilds(self.guild_id)
        container = ui.Container()
        if result == "no guild found":
            container.add_item(ui.TextDisplay("<a:cross:1380797973373521962> No guild found to delete."))
        elif result == "guild deleted":
            container.add_item(ui.TextDisplay("<a:check:1380797984979030016> Guild deleted successfully."))
        else:
            container.add_item(ui.TextDisplay("<a:cross:1380797973373521962> An unknown error occurred."))
        await interaction.response.edit_message(view=SimpleResultLayoutView(container))

    async def no_delete_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.defer()
            return
        container = ui.Container()
        container.add_item(ui.TextDisplay("<a:cross:1380797973373521962> Guild deletion cancelled."))
        await interaction.response.edit_message( view=SimpleResultLayoutView(container))

    async def delete_button(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.defer()
            return
        await interaction.message.delete()


class SimpleResultLayoutView(discord.ui.LayoutView):
    def __init__(self, container, *, timeout=120):
        super().__init__(timeout=timeout)
        self.add_item(container)


class GuildMemberOverviewLayoutView(discord.ui.LayoutView):
    def __init__(self, msg_owner_id, guild_data, start_unix, end_unix, old_interval=None, page=0, *, timeout=300):
        super().__init__(timeout=timeout)
        self.msg_owner_id = msg_owner_id
        self.guild_data = guild_data
        self.start_unix = start_unix
        self.end_unix = end_unix
        self.old_interval = old_interval
        self.members = guild_data.get("guild_member", [])
        self.per_page = 8
        self.page = page
        self.max_pages = max(1, (len(self.members) - 1) // self.per_page + 1)
        self.guild_container = self.build_container()
        self.add_item(self.guild_container)

    def build_container(self):
        container = ui.Container()
        container.add_item(ui.TextDisplay(f"## {self.guild_data['guild_name']}\n"
                                          f"__Current donation threshold:__ {self.guild_data['guild_reset']} {self.guild_data['guild_threshold']:,} {gold_emote}"))
        container.add_item(ui.TextDisplay(f"**from:** <t:{self.start_unix}:F>"))
        container.add_item(ui.TextDisplay(f"**till:** <t:{self.end_unix}:F>"))
        container.add_item(ui.TextDisplay(f"__adv donations:__ {self.guild_data['guild_advanced_donation']}\n"
                                          f"__guild debt:__ {self.guild_data['guild_debt']}"))
        container.add_item(ui.Separator())
        start = self.page * self.per_page
        end = start + self.per_page
        for member in self.members[start:end]:
            if self.guild_data["guild_debt"] and self.old_interval is None:
                donation = member['guild_member_donation']
            else:
                donation = member['current_period_donation']
            threshold = member.get("threshold_used", self.guild_data['guild_threshold'])
            if donation >= threshold:
                status = "<a:check:1380797984979030016>"
            else:
                status = "<a:cross:1380797973373521962>"
            container.add_item(ui.TextDisplay(f"``{member['guild_member_name']}``"))
            container.add_item(ui.TextDisplay(f"{status} {donation:,} / {threshold:,} {gold_emote}"))
            container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"Page {self.page + 1} / {self.max_pages}"))
        button_prev = ui.Button(label="◀", style=discord.ButtonStyle.secondary)
        button_prev.callback = self.prev_page
        button_next = ui.Button(label="▶", style=discord.ButtonStyle.secondary)
        button_next.callback = self.next_page
        button_delete = ui.Button(label="🗑️", style=discord.ButtonStyle.danger)
        button_delete.callback = self.delete_button
        container.add_item(ui.ActionRow(button_prev, button_next, button_delete))
        return container

    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.msg_owner_id:
            await interaction.response.defer()
            return
        if self.page < self.max_pages - 1:
            new_view = GuildMemberOverviewLayoutView(self.msg_owner_id, self.guild_data, self.start_unix, self.end_unix, self.old_interval, page=self.page + 1)
            await interaction.response.edit_message(view=new_view)
        else:
            await interaction.response.defer()

    async def prev_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.msg_owner_id:
            await interaction.response.defer()
            return
        if self.page > 0:
            new_view = GuildMemberOverviewLayoutView(self.msg_owner_id, self.guild_data, self.start_unix, self.end_unix, self.old_interval, page=self.page - 1)
            await interaction.response.edit_message(view=new_view)
        else:
            await interaction.response.defer()

    async def delete_button(self, interaction: discord.Interaction):
        if interaction.user.id != self.msg_owner_id:
            await interaction.response.defer()
            return
        await interaction.message.delete()


class GuildDonationsLayoutView(discord.ui.LayoutView):
    def __init__(self, msg_owner_id, member, donations, page=0, *, timeout=300):
        super().__init__(timeout=timeout)
        self.msg_owner_id = msg_owner_id
        self.member = member
        self.donations = donations
        self.per_page = 7
        self.page = page
        self.max_pages = max(1, (len(donations) - 1) // self.per_page + 1)
        self.container = self.build_container()
        self.add_item(self.container)

    def build_container(self):
        container = ui.Container()
        container.add_item(ui.TextDisplay(f"## 💰 Donations for {self.member.name}"))
        start = self.page * self.per_page
        end = start + self.per_page
        for donation in self.donations[start:end]:
            donation_id = donation.get("donation_id", "N/A")
            amount = donation.get("donation_amount", 0)
            status = donation.get("donation_status", "auto")
            timestamp = donation.get("timestamp", 0)
            container.add_item(ui.TextDisplay(f":id: ``{donation_id}``"))
            container.add_item(ui.TextDisplay(f"__{status}__ donation amount: **{amount:,}**\n<t:{timestamp}:F>"))
            container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"Page {self.page + 1} / {self.max_pages}"))
        button_prev = ui.Button(label="◀", style=discord.ButtonStyle.secondary)
        button_prev.callback = self.prev_page
        button_next = ui.Button(label="▶", style=discord.ButtonStyle.secondary)
        button_next.callback = self.next_page
        button_delete = ui.Button(label="🗑️", style=discord.ButtonStyle.danger)
        button_delete.callback = self.delete_button
        container.add_item(ui.ActionRow(button_prev, button_next, button_delete))
        return container

    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.msg_owner_id:
            await interaction.response.defer()
            return
        if self.page < self.max_pages - 1:
            new_view = GuildDonationsLayoutView(self.msg_owner_id, self.member, self.donations, page=self.page + 1)
            await interaction.response.edit_message(view=new_view)
        else:
            await interaction.response.defer()

    async def prev_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.msg_owner_id:
            await interaction.response.defer()
            return
        if self.page > 0:
            new_view = GuildDonationsLayoutView(self.msg_owner_id, self.member, self.donations, page=self.page - 1)
            await interaction.response.edit_message(view=new_view)
        else:
            await interaction.response.defer()

    async def delete_button(self, interaction: discord.Interaction):
        if interaction.user.id != self.msg_owner_id:
            await interaction.response.defer()
            return
        await interaction.message.delete()


class GuildDonoForUserLayoutView(discord.ui.LayoutView):
    def __init__(self, member, guild_donations, page=0, *, timeout=300):
        super().__init__(timeout=timeout)
        self.member = member
        self.guild_donations = guild_donations
        self.per_page = 4
        self.page = page
        self.max_pages = max(1, (len(guild_donations) - 1) // self.per_page + 1)
        self.container = self.build_container()
        self.add_item(self.container)

    def build_container(self):
        container = ui.Container()
        container.add_item(ui.TextDisplay(f"## 💰 Donations Overview for {self.member.name}"))
        start = self.page * self.per_page
        end = start + self.per_page
        for guild in self.guild_donations[start:end]:
            if guild["guild_threshold_2"] is not None and self.member.id in guild["threshold_members"]:
                max_donation = guild["guild_threshold_2"]
            else:
                max_donation = guild["guild_threshold"]
            if guild['weekly_donations'] >= max_donation:
                status = "<a:check:1380797984979030016>"
            else:
                status = "<a:cross:1380797973373521962>"
            container.add_item(ui.TextDisplay(f"__{guild['guild_name']}__"))
            container.add_item(ui.TextDisplay(f"Overall Donations: {guild['total_donations']:,} {gold_emote}"))
            container.add_item(ui.TextDisplay(f"This Week: {status} {guild['weekly_donations']:,} {gold_emote} / {max_donation:,} {gold_emote}"))
            container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"Page {self.page + 1} / {self.max_pages}"))
        button_prev = ui.Button(label="◀", style=discord.ButtonStyle.secondary)
        button_prev.callback = self.prev_page
        button_next = ui.Button(label="▶", style=discord.ButtonStyle.secondary)
        button_next.callback = self.next_page
        button_delete = ui.Button(label="🗑️", style=discord.ButtonStyle.danger)
        button_delete.callback = self.delete_button
        container.add_item(ui.ActionRow(button_prev, button_next, button_delete))
        return container

    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.member.id:
            await interaction.response.defer()
            return
        if self.page < self.max_pages - 1:
            new_view = GuildDonoForUserLayoutView(self.member, self.guild_donations, page=self.page + 1)
            await interaction.response.edit_message(view=new_view)
        else:
            await interaction.response.defer()

    async def prev_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.member.id:
            await interaction.response.defer()
            return
        if self.page > 0:
            new_view = GuildDonoForUserLayoutView(self.member, self.guild_donations, page=self.page - 1)
            await interaction.response.edit_message(view=new_view)
        else:
            await interaction.response.defer()

    async def delete_button(self, interaction: discord.Interaction):
        if interaction.user.id != self.member.id:
            await interaction.response.defer()
            return
        await interaction.message.delete()


class DonationResultLayoutView(discord.ui.LayoutView):
    def __init__(self, player_name, amount, guild_names, *, timeout=120):
        super().__init__(timeout=timeout)
        self.player_name = player_name
        self.amount = amount
        self.guild_names = guild_names
        self.container = self.build_container()
        self.add_item(self.container)

    def build_container(self):
        container = ui.Container()
        container.add_item(ui.TextDisplay(f"**Player:** {self.player_name}"))
        container.add_item(ui.TextDisplay(f"**Amount:** {self.amount:,} Gold"))
        container.add_item(ui.Separator())
        if self.guild_names:
            guilds_text = ", ".join(f"``{g}``" for g in self.guild_names) or "None"
            container.add_item(ui.TextDisplay(f"<a:check:1380797984979030016> updated donations for guilds:\n{guilds_text}"))
        else:
            container.add_item(ui.TextDisplay("<a:cross:1380797973373521962> No guilds found for this player. Donation was not added."))
        return container


class RemoveGuildMemberLayoutView(discord.ui.LayoutView):
    def __init__(self, guild_id, guild_member, author, *, timeout=180):
        super().__init__(timeout=timeout)
        self.guild_id = guild_id
        self.guild_member = guild_member
        self.author = author
        self.container = self.build_container()
        self.add_item(self.container)

    def build_container(self):
        container = ui.Container()
        container.add_item(ui.TextDisplay("## ⚠️ Remove Guild Member"))
        container.add_item(ui.TextDisplay(f"Do you really want to remove `{self.guild_member.name}` (ID: {self.guild_member.id})?"))
        container.add_item(ui.Separator())
        button_yes = ui.Button(label="Yes", style=discord.ButtonStyle.danger)
        button_yes.callback = self.yes_callback
        button_no = ui.Button(label="No", style=discord.ButtonStyle.secondary)
        button_no.callback = self.no_callback
        button_delete = ui.Button(label="🗑️", style=discord.ButtonStyle.danger)
        button_delete.callback = self.delete_button
        container.add_item(ui.ActionRow(button_yes, button_no, button_delete))
        return container

    async def yes_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.defer()
            return
        result = await guilds.remove_guild_member(self.guild_id, self.guild_member)
        container = ui.Container()
        if result == "no guild found":
            container.add_item(ui.TextDisplay("<a:cross:1380797973373521962> No guild found. Please create one first."))
        elif result == "member not found":
            container.add_item(ui.TextDisplay("<a:cross:1380797973373521962> Member not found. Please check the name."))
        elif result == "removed":
            container.add_item(ui.TextDisplay(f"<a:check:1380797984979030016> `{self.guild_member.name}` was removed successfully."))
        else:
            container.add_item(ui.TextDisplay("<a:cross:1380797973373521962> An unknown error occurred."))
        await interaction.response.edit_message(view=SimpleResultLayoutView(container))

    async def no_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.defer()
            return
        container = ui.Container()
        container.add_item(ui.TextDisplay("<a:cross:1380797973373521962> Member removal cancelled."))
        await interaction.response.edit_message(view=SimpleResultLayoutView(container))

    async def delete_button(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.defer()
            return
        await interaction.message.delete()


class NoIDCheckLayoutView(discord.ui.LayoutView):
    def __init__(self, guild_members, *, timeout=120):
        super().__init__(timeout=timeout)
        self.guild_members = guild_members
        self.container = self.build_container()
        self.add_item(self.container)

    def build_container(self):
        container = ui.Container()
        container.add_item(ui.TextDisplay("## 🔍 Members without Discord ID"))
        if not self.guild_members:
            container.add_item(ui.TextDisplay("<a:check:1380797984979030016> All members are up to date."))
        else:
            members_text = " ; ".join(f"`{member}`" for member in self.guild_members)
            container.add_item(ui.TextDisplay(members_text))
        return container

