import discord
import re
import asyncio
import json
import os
import time
import runtime
from attr.validators import max_len
from discord import MediaGalleryItem
from discord.ext import commands
from discord.ui import View, Button, MediaGallery, Thumbnail, Select
from db_methods import cards, players
from Commands import definitions, help_def_v2
from Commands.user_commands_on_message import rare_emote, super_rare_1, super_rare_2, ultra_rare_1, ultra_rare_2

picture_caeser = "https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif"


class UserCommandsPrefix_v2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def raidguide(self, ctx, *args):
        boss_query = None
        rarity_filter = None
        args = list(args)
        if "-n" in args:
            idx = args.index("-n")
            if idx + 1 < len(args):
                boss_query = args[idx + 1]
        if "-name" in args:
            idx = args.index("-name")
            if idx + 1 < len(args):
                boss_query = args[idx + 1]
        if "-r" in args:
            idx = args.index("-r")
            if idx + 1 < len(args):
                rarity_filter = args[idx + 1].lower()
        if "-rarity" in args:
            idx = args.index("-rarity")
            if idx + 1 < len(args):
                rarity_filter = args[idx + 1].lower()
        if not boss_query:
            await ctx.send("Please provide a boss name.")
            return
        path = os.path.join("data", "raid_comps.json")
        rare_string = ""
        sr_string = f"{super_rare_1}{super_rare_2} **- Super Rare**\n"
        ur_string = f"{ultra_rare_1}{ultra_rare_2} **- Ultra Rare**\n"
        boss_found = None
        bosses = await runtime.retrieve_data("raid comps")
        for b in bosses.keys():
            if boss_query.lower() in b.lower():
                boss_found = b
                if "R" in bosses[b]:
                    for level, entry in bosses[b]["R"].items():
                        rare_string += f"{rare_emote} **- Rare {level}**\n"
                        for team in entry.get("teams", []):
                            team = re.sub(r"\{([^}]*)\}", r"\n -# (\1)", team).strip()
                            rare_string += f"- {team}\n"
                if "SR" in bosses[b]:
                    for level, entry in bosses[b]["SR"].items():
                        for team in entry.get("teams", []):
                            team = re.sub(r"\{([^}]*)\}", r"\n -# (\1)", team).strip()
                            sr_string += f"- {team}\n"
                if "UR" in bosses[b]:
                    for level, entry in bosses[b]["UR"].items():
                        for team in entry.get("teams", []):
                            team = re.sub(r"\{([^}]*)\}", r"\n -# (\1)", team).strip()
                            ur_string += f"- {team}\n"
                break
        if not boss_found:
            await ctx.send(f"No boss found with this name: **{boss_query}**")
            return
        card_data = await cards.get_card_data_by_name(boss_found)
        card_element = await definitions.element_converter_from_database(card_data[0]["card_element"])
        card_talent = await definitions.skill_converter_from_database(card_data[0]["card_talent"])

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
        await ctx.send(view=view)

    @commands.command(aliases=["ruleset"])
    async def rulesets(self, ctx):

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
        await ctx.send(view=view)

    @commands.command()
    async def help(self, ctx):
        view = await help_def_v2.help_v2(ctx)
        await ctx.send(view=view)

    @commands.command()
    async def update(self, ctx):
        discord_id = ctx.author.id
        discord_name = ctx.author.name
        await players.update_player(discord_id, discord_name)

        class UpdateContainer(discord.ui.Container):
            update_text = discord.ui.TextDisplay("<a:check:1380797984979030016> **Player has been updated.**\n"
                                                 f"Name: ``{discord_name}``\nID: ``{discord_id}``")

        class UpdateView(discord.ui.LayoutView):
            container = UpdateContainer(id=1, accent_colour=0x71368A)

        view = UpdateView()
        await ctx.send(view=view)

    @commands.command()
    async def settings(self, ctx):
        discord_id = ctx.author.id
        discord_name = ctx.author.name
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
            if player_settings["cinfo_delete"] == "yes":
                button_style_cinfo_del = discord.ButtonStyle.green
                status_cinfodel = "on"
            else:
                button_style_cinfo_del = discord.ButtonStyle.danger
                status_cinfodel = "off"
            if player_settings["cinfo_stat_display"] == "original":
                button_style_cinfo_stat = discord.ButtonStyle.green
                status_cinfostat = "original"
            else:
                button_style_cinfo_stat = discord.ButtonStyle.danger
                status_cinfostat = "compact"
            if player_settings["cinfo_picture"] == "original":
                button_style_cinfo_pic = discord.ButtonStyle.green
                status_cinfopic = "original"
            else:
                button_style_cinfo_pic = discord.ButtonStyle.danger
                status_cinfopic = "thumbnail"
            if player_settings["cselect_delete"] == "yes":
                button_style_cselect_del = discord.ButtonStyle.green
                status_cselectdel = "on"
            else:
                button_style_cselect_del = discord.ButtonStyle.danger
                status_cselectdel = "off"
            if player_settings["info_replace"] == "yes":
                button_style_info_replace = discord.ButtonStyle.green
                status_info_replace = "on"
            else:
                button_style_info_replace = discord.ButtonStyle.danger
                status_info_replace = "off"
            if player_settings["raid_afk_ping"] == "yes":
                button_style_raid_afk = discord.ButtonStyle.green
                status_raid_afk = "on"
            else:
                button_style_raid_afk = discord.ButtonStyle.danger
                status_raid_afk = "off"

            class SettingsContainer(discord.ui.Container):
                settings_text = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## Caeser's settings\n**Player Name / ID:**\n{discord_name} / {discord_id}"))
                button_rows_1 = discord.ui.ActionRow(discord.ui.Button(label=f"raid lobby {status_rl}", style=button_style_rl, custom_id="Raid Lobby"),
                                                     discord.ui.Button(label=f"raid search history delete", style=button_style_rsh, custom_id="Raid Search History Delete"),
                                                     discord.ui.Button(label=f"card select delete {status_cselectdel}", style=button_style_cselect_del, custom_id="Cselect Delete"),
                                                     discord.ui.Button(label=f"raid afk ping {status_raid_afk}", style=button_style_raid_afk, custom_id="Raid Afk Ping"))
                sep = discord.ui.Separator()
                button_row_cinfo = discord.ui.ActionRow(discord.ui.Button(label=f"cinfo delete {status_cinfodel}", style=button_style_cinfo_del, custom_id="Cinfo Delete"),
                                                        discord.ui.Button(label=f"cinfo picture {status_cinfopic}", style=button_style_cinfo_pic, custom_id="Cinfo Picture"),
                                                        discord.ui.Button(label=f"cinfo stats {status_cinfostat}", style=button_style_cinfo_stat, custom_id="Cinfo Stats"),
                                                        discord.ui.Button(label=f"info replace {status_info_replace}", style=button_style_info_replace, custom_id="Info Replace"))

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
                    elif button_id == "Cselect Delete":
                        await players.update_player_settings_cselect_delete_by_discord_id(discord_id)
                    elif button_id == "Cinfo Delete":
                        await  players.update_player_settings_cinfo_del_by_discord_id(discord_id)
                    elif button_id == "Cinfo Picture":
                        await  players.update_player_settings_cinfo_pic_by_discord_id(discord_id)
                    elif button_id == "Cinfo Stats":
                        await players.update_player_settings_cinfo_stat_by_discord_id(discord_id)
                    elif button_id == "Info Replace":
                        await players.update_player_settings_info_replace_by_discord_id(discord_id)
                    elif button_id == "Raid Afk Ping":
                        await players.update_player_settings_raid_afk_ping_by_discord_id(discord_id)
                    nonlocal player_settings
                    new_settings = await players.get_settings_from_player_by_discord_id(discord_id)
                    player_settings = new_settings
                    await interaction.response.edit_message(view=await build_settings())
                    return True
            return SettingsView()

        view = await build_settings()
        await ctx.send(view=view)

    @commands.command(aliases=["rl"])
    async def raidlobbies(self, ctx, *, args: str = None):
        if not args:
            await ctx.send("Please enter a gold value.")
            return
        user_sell_formatting = False
        if "-sell" in args:
            user_sell_formatting = True
            args = args.replace("-sell", "").strip()
        alias_map = {"cl": "clan_shop", "clan": "clan_shop", "cl shop": "clan_shop", "clan shop": "clan_shop",
                     "vote": "monthly_vote", "monthly": "monthly_vote", "monthly vote": "monthly_vote",
                     "calendar": "monthly_vote", "event": "event"}
        exclude_pattern = fr"-(ex|exclude)\s([a-zA-Z ,_]+)"
        exclude_match = re.search(exclude_pattern, args)
        exclude_events = []
        if exclude_match:
            raw_input = exclude_match.group(2)
            terms = [term.strip().lower() for term in re.split(r"[,_ ]+", raw_input)]
            for term in terms:
                if term in alias_map:
                    exclude_events.append(alias_map[term])
            args = args.replace(exclude_match.group(0), "").strip()
        user_price = re.findall(r"\s*(\d+)(k?).*", args)
        if not user_price:
            await ctx.send("Please enter a valid gold price.")
            return
        user_gold_price = None
        for price, price_multi in user_price:
            price = int(price)
            if price_multi == "k":
                user_gold_price = price * 1000
            else:
                user_gold_price = price
        if user_gold_price is None:
            await ctx.send("Please enter a valid gold price.")
            return
        card_list = await cards.raid_search_list_from_db(user_gold_price, exclude_events)
        player_setting = await players.get_settings_from_player_by_discord_id(ctx.author.id)
        if player_setting["raid_lobby_status"] == "long":
            max_length = 4000
        else:
            max_length = 2000
        if len(card_list) >= max_length:
            await ctx.send("Too many characters. Please use a different gold number.")
            return
        if user_sell_formatting:
            text = f".inv -r sr -evo 1 -n {card_list}"
        else:
            text = f".rd lobbies -r r,sr,ur -n {card_list}"

        class RaidLobbySearchContainer(discord.ui.Container):
            settings_text = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"{text}"))

        class RaidLobbySearchView(discord.ui.LayoutView):
            container = RaidLobbySearchContainer(id=1, accent_colour=0x71368A)

        view = RaidLobbySearchView()
        await ctx.channel.send(view=view)

