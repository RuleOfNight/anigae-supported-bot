import discord
from discord.ui import View, Select


class HelpSelectionView(View):
    def __init__(self, original_message, author_id, author_name, author_avatar):
        super().__init__(timeout=180)
        self.original_message = original_message
        self.author_id = author_id
        self.author_name = author_name
        self.author_avatar = author_avatar
        self.delete_button = discord.ui.Button(label="", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.delete_button.callback = self.delete_callback
        self.add_item(self.delete_button)

        # Dropdown-Menu 1
        self.select_category = Select(placeholder="All commands for prefix usage.", options=[
                discord.SelectOption(label="mdex / marketdex", value="global market", description=None),    # Todo Done
                discord.SelectOption(label="compare", value="compare", description=None),   # Todo Done
                discord.SelectOption(label="invite", value="invite", description=None),
                discord.SelectOption(label="sfl / setfloor", value="setfloor", description=None),   # Todo Done
                discord.SelectOption(label="shards / souls / floors", value="shardlist", description=None),
                discord.SelectOption(label="rsh / raidsearch / raidsearchhistory", value="raidsearchhistory", description=None),
                discord.SelectOption(label="rh / raidhistory", value="raidhistory", description=None),
                discord.SelectOption(label="rl / raidlobbies", value="raidlobbies", description=None),
                discord.SelectOption(label="setprefix", value="prefix", description=None),
                discord.SelectOption(label="stc / setteamwarning", value="setteamwarning", description=None),
                discord.SelectOption(label="ser / setenergyreminder", value="setenergyreminder", description=None),
                discord.SelectOption(label="dw / dailywatch", value="dailywatch", description=None),
                discord.SelectOption(label="sl / setlocation", value="setlocation", description=None)])
        # Dropdown-Menu 2
        self.select_command = Select(placeholder="All commands for on_message usage.", options=[
                discord.SelectOption(label="Raid Lobby / waiting room", value="lobby", description=None),
                discord.SelectOption(label="Raid Party / in raid", value="party", description=None),
                discord.SelectOption(label="Improved card info", value="info", description=None),
                discord.SelectOption(label="Team warning", value="warning", description=None),
                discord.SelectOption(label="Improved clan shop", value="cl_shop", description=None),
                discord.SelectOption(label="Raid Search History delete", value="rsh_delete", description=None),
                discord.SelectOption(label="Raid History", value="rh", description=None),
                discord.SelectOption(label="improved gold / rubies / stamina info", value="go_ru_sta", description=None),
                discord.SelectOption(label="clan donation tracker", value="clan_donation_tracker", description=None),
                discord.SelectOption(label="raid energy reminder", value="raid_energy_reminder", description=None),
                discord.SelectOption(label="set raid energy", value="set_raid_energy", description=None),
                discord.SelectOption(label="daily shop overview", value="daily_shop_overview", description=None),
                discord.SelectOption(label="pack opening value", value="pack_opening", description=None),
                discord.SelectOption(label="buying / selling help", value="sell_buy_help", description=None)])
        # Dropdown-Menu 3
        self.select_guild_commands = Select(placeholder="custom guild and donation tracker", options=[
                discord.SelectOption(label="Create Custom Guild", value="create_guild", description=None),
                discord.SelectOption(label="Delete Custom Guild", value="delete_guild", description=None),
                discord.SelectOption(label="Add Member", value="add_member", description=None),
                discord.SelectOption(label="Remove Member", value="remove_member", description=None),
                discord.SelectOption(label="Archive Member", value="archive_member", description=None),
                discord.SelectOption(label="Activate / Unarchive Member", value="activate_member", description=None),
                discord.SelectOption(label="View Archive Member List", value="view_archive", description=None),
                discord.SelectOption(label="Donation Threshold", value="donation_threshold", description=None),
                discord.SelectOption(label="All Members Clan Donations", value="clandonations", description=None),
                discord.SelectOption(label="Personal Clan Donations", value="clandonationstracker", description=None),
                discord.SelectOption(label="Guild Reset Timing", value="guild_reset", description=None),
                discord.SelectOption(label="Donation History Of Specific Player.", value="guild_donations_for_user", description=None),
                discord.SelectOption(label="Manually Add Donations In Your Guild", value="add_donation", description=None),
                discord.SelectOption(label="Manually Remove Donations In Your Guild", value="remove_donation", description=None),
                discord.SelectOption(label="Manually Edit Donations In Your Guild", value="edit_donation", description=None),])
        self.select_category.callback = self.select_category_callback
        self.select_command.callback = self.select_command_callback
        self.select_guild_commands.callback = self.select_guild_commands_callback
        self.add_item(self.select_category)
        self.add_item(self.select_command)
        self.add_item(self.select_guild_commands)

    async def delete_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return
        await interaction.message.delete()

    async def select_category_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return
        selected_category = self.select_category.values[0]
        embed_description = ""
        title_name = ""
        if selected_category == "global market":
            title_name = "**__Global Market Tracker [mdex / marketdex]__**"
            embed_description = ("possible filter:\n- -all [shows all cards]\n- -name [card name] [use , to search for multiple cards]\n"
                                 "- -series [series name] [use , to search for multiple series]\n- -element [card element] [use , to search for multiple elements]\n"
                                 "- -talent [talent name] [use , to search for multiple talents]\n- -rarity [sr or ur] [shows only the price for the corresponding rarity]\n"
                                 "- -price [\"<\" or \"=\" or \">\"] [gold value] [searches for the gold value of the card, logical order is \"card price > gold value\""
                                 "[shows all cards with the card price above the gold value\n- -page [number] [jump to the set page]\n\n"
                                 "__possible aliases for the filter__:\n[name / n] [series / s] [element / ele / e]\n"
                                 "[talent / skill / t] [rarity / r] [page / p]\n [price] and [all] don't have any alias!\n\nexample command:\n"
                                 "Caeserex -n Todo, Ryusui -r sr [shows aoi todo and ryusui nanami only sr price]\n"
                                 "Caeserex -series piece -ele dark [shows all cards from one piece that have dark element]\n"
                                 "5marketdex -r ur -p 30 [shows the page 30 for all available ur prices]")
        elif selected_category == "compare":
            title_name = "**__Comparing Characters [compare]__**"
            embed_description = ("Compare up to 5 character at once! No need for filter, just write all desired "
                                 "Character names after another and seperate them with a comma.\n "
                                 "as example 5compare Konno, Akeno, Jinx\n"
                                 "You can even select for each character their rarity and ascention!")
        elif selected_category == "invite":
            title_name = "**__Invite links for the Bot and Official Server [invite]__**"
            embed_description = ("Shows the invite link for the Official Server and Bot. That's it.")
        elif selected_category == "setfloor":
            title_name = "**__Set your own Floor [sfl / setfloor]__**"
            embed_description = ("To set your own floor simply write the command and then in a next message your location"
                                 " and floor serperated by a comma. You can write the numbers already within the command!"
                                 "\n__as example__\n- 5setfloor 23,15 **or** 5sfl 40, 20\n- 5setfloor\n 56,15 **or** 87, 23")
        elif selected_category == "shardlist":
            title_name = "**__Best value Floors [shardlist / soullist / floorlist]__**"
            embed_description = ("On standard there will be shown the highest \"value\" location and floor. "
                                 "Basically the best spot for gold and shards.\nvalue = (location * 2) + floor\n"
                                 "If you want to set your own location and floor to use the command to its fullest "
                                 "then simply use the command [sfl / setfloor]. ")
        elif selected_category == "raidsearchhistory":
            title_name = "**__Raid Search History__**"
            embed_description = ("Use that command to update or set your status if you want the raid search spam"
                                 " being deleted. If \"yes\" is selected then the bot will start deleting your spam."
                                 " If \"no\" is selected or you didn't setup then your spam will stay like always.\n"
                                 "- possible commands or alias:\n"
                                 "rsh / raidsearch / raidsearchhistory")
        elif selected_category == "raidhistory":
            title_name = "**__Raid History__**"
            embed_description = ("If you want to see all your tracked raids just the the command as it is as example:\n"
                                 "5raidhistory\n5rh\n\nif you want to filter the output, there are currently 4 possible filter options "
                                 "and you can use multiple filter at once!\n"
                                 "-n [name]\n-d [difficulty]\n-r [rarity]\n-l [level]\n"
                                 "__only for level__:\n if you want to further filter then you can use \" < \" or \" > \" .\n"
                                 "-l< 3000 **|** will show all raids with level of __less__ than 3000!\n\n"
                                 "-n works with full or partial names\n\n-d works for all difficulties, current aliases are\n"
                                 "**[**easy or e**]** **[**medium or m**]** **[**hard or h**]** **[**impossible or i**]**\n\n"
                                 "-r for all rarities, current aliases are\n[uncommon or uc] [rare or r] [super rare or sr] [ultra rare or ur]\n\n"
                                 "example of a command usage:\n5rh -d i -r r -l>2500\nthis will show all raids "
                                 "for difficulty impossible, rarity rare and over level 2500")
        elif selected_category == "raidlobbies":
            title_name = "**__Raid Search Lobbies__**"
            embed_description = ("To get a list of all cards which value is the same or above your used Number. as example\n"
                                 "5rl 50k\n5raidlobbies 50000\nBoth will show all cards with an sr gold value above 50k.\n"
                                 "If the message is longer than 2000 character (which is limited by discord) then it will "
                                 "show the message \"To much characters. Please use a different gold number.\n\n"
                                 "Additional filters are [ex / exclude] and [sell], filter options for exclude:\n"
                                 "- cl / clan / cl shop / clan shop\n"
                                 "- vote / monthly\n"
                                 "- event\n"
                                 "as example:\n5rl 30k -ex vote,event\n"
                                 "[sell] will change \'.rd lobbies -r r,sr,ur\' to \'.inv -r sr -evo 1\'")
        elif selected_category == "prefix":
            title_name = "**__Set Prefix__**"
            embed_description = ("Use the command [setprefix] to change the prefix for your server! \"5\" is the standart prefix.")
        elif selected_category == "setteamwarning":
            title_name = "**__Set Team Warning__**"
            embed_description = ("Use this command to update or set your status if you want to get the warning spam. "
                                 "If \"yes\" is selected then the bot will start scanning your raid battle attempts and warn you."
                                 " If \"no\" is selected or you didn't setup then the bot will ignore every battle attempt.\n"
                                 "For further information check the on_message command [team warning]\n\n"
                                 "- possible commands or alias:\n"
                                 "stw / setteamwarning")
        elif selected_category == "setenergyreminder":
            title_name = "**__Set Energy Reminder__**"
            embed_description = ("Use this command to update or set your status on the energy reminder.\n"
                                 "If \"no\" (default value) is selected then the bot will not remind/ping you.\n"
                                 "If you want to be notified then simply select one of the values of the dropdown menu."
                                 "This value will be used as your desired notification amount.")
        elif selected_category == "dailywatch":
            title_name = "**__Daily Watch__**"
            embed_description = "Shows the current daily shop rotation, all cards of that series with their SR and UR price."
        elif selected_category == "setlocation":
            title_name = "**__Set Location for Daily Watch__**"
            embed_description = ("Enable or Disable the locations you want to be pinged for when they appear in the "
                                 "daily shop rotation.\nThe reminder ping is exclusive on the official Discord!")
        new_embed = discord.Embed(title="Welcome to Caeser's help command", description=f"{title_name}", color=0x71368A)
        new_embed.add_field(name="", value=embed_description, inline=True)
        new_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg")
        new_embed.set_author(name=self.author_name, icon_url=self.author_avatar)
        await interaction.response.edit_message(embed=new_embed, view=self)

    async def select_command_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return
        selected_command = self.select_command.values[0]
        embed_description = ""
        title_name = ""
        if selected_command == "lobby":
            title_name = "**__raid lobby / waiting room__**"
            embed_description = "Within the footer is an easy to copy lobby join code. Everything else is the same."
        elif selected_command == "party":
            title_name = "**__raid party / in raid__**"
            embed_description = ("- A finish timer\n- Damage Per Attack behind the total damage in ()\n"
                                 "- Percentage damage dealt of the boss max hp after Damage per Attack in ()\n"
                                 "- Damage Status: MAX (capping damage), Great (Max till 0,75 of Max), Good (Great till 0,5 of Max), Leeching (below 0,5 of Max)\n"
                                 "- Threshold Status: If the threshold for SR/UR drops is reached\n"
                                 "- Marking players that didn't attack for more than 30min")
        elif selected_command == "info":
            title_name = "**__improved card info__**"
            embed_description = ("- Skill / Talent description for SR and UR\n- Max Evo 3 stats for SR and UR\n"
                                 "- Dropdown menu for ascension stats for both SR and UR (might be off by 1 stat due to roundings)\n"
                                 "- card prices for SR and UR with their last update time")
        elif selected_command == "warning":
            title_name = "**__team warning__**"
            embed_description = ("__You don't get a warning if__:\n- team consists of exactly 2 cards with __less__ than 1100 power level\n"
                                 "- you have an elemental effectiveness of 3 points or more\n- enemy boss is null\n\n"
                                 "__You do get a warning if__:\n- team consists of 1 card only\n - team consists of 2 cards with __more__ than 1100 power level\n"
                                 "- you have an elemental effectiveness of less than 3\n\n"
                                 "__effectiveness overview__:\n- advantage gives 2\n- same element 1\n- disadvantage -1\n"
                                 "- for light and dark same element gives 2\n- neutral always 0\n- null always 1")
        elif selected_command == "cl_shop":
            title_name = "**__improved clan shop__**"
            embed_description = ("The main page shows all 4 avaible cards as always with addon on their element and skill. The required Rubies "
                                 "are shown with the gold value they have. On the bottom is shown the next up UR Card's __ending__ time.\n"
                                 "\"Cycle 1\" and \"Cycle 2\" will show when all cards will have their UR appearance __ending__ time.")
        elif selected_command == "rsh_delete":
            title_name = "**__raid search history__**"
            embed_description = ("If you want the bot to delete your raids search spam then use one of the command/alias"
                                 " [rsh / raidsearch / raidsearchhistory]. Once you selected \"yes\" the bot will start"
                                 " deleting your send messages and keep your chat clean.\n"
                                 "__It does not delete the message of the anigame, only your own__ !")
        elif selected_command == "rh":
            title_name = "**__raid history__**"
            embed_description = ("The bot is automatically tracking __every__ player and their corresponding stats in raid"
                                 " if you open the raid party. To view the history use the command [rh / raidhistory]"
                                 " with the prefix.")
        elif selected_command == "go_ru_sta":
            title_name = "**__improved gold / rubies / stamina info__**"
            embed_description = ("__improved gold info__:\n- added the gain / loss tracker\n\n"
                                 "__improved rubies info__:\n- added how much rubies you need till next SR / UR\n- added how many you could currently purchase\n\n"
                                 "__improved stamina info__:\n- added info till your stamina is full with and without vip\n- added how many battles you could currently do")
        elif selected_command == "clan_donation_tracker":
            title_name = "**__clan donation tracking__**"
            embed_description = ("Tracks all your clan donations and adds them automatically to the guilds you are in."
                                 " If you are in no custom guild from Caeser's then this command will do nothing.")
        elif selected_command == "raid_energy_reminder":
            title_name = "**__raid energy reminder__**"
            embed_description = ("~~Turn on the command [setenergyreminder / ser]. The command can be disabled again if you wish to.\n"
                                 "Once activated the bot will track all your energy usages and ping according to your setup energy status.\n"
                                 "The reminder will ping in the channel of the last seen battle.~~ Currently Disabled")
        elif selected_command == "set_raid_energy":
            title_name = "**__set raid energy__**"
            embed_description = ("Using the AniGame command [rd energy] will set your energy manually. This might be needed if a "
                                 "new raid started but the bot didn't track the first battle or if your energy is not on point.")
        elif selected_command == "daily_shop_overview":
            title_name = "**__daily shop overview__**"
            embed_description = ("Shows __every__ series in the shop rotation and the appearance date and time.\n"
                                 "This feature is exclusive on the official Discord and stays up to date on it's own!")
        elif selected_command == "pack_opening":
            title_name = "**__pack opening value__**"
            embed_description = ("The command automatically sends an answer to the opened pack message. The message "
                                 "contains the card rarity, the card name as well as the market price. Only works for "
                                 "Super Rare and Ultra Rare cards. If none are in the pack then the command will not "
                                 "send any message.")
        elif selected_command == "sell_buy_help":
            title_name = "**__buying & selling help__**"
            embed_description = ("Interacting with the emote <a:buy:1379019047001128970> will trigger the buying help.\n\n"
                                 "Interacting with the emote <a:sell:1379019058758029332> will trigger the selling help.\n\n"
                                 "Then select the cards you want to sell/buy and the bot will post the corresponding command "
                                 "for you to copy paste. Selling has a intern cooldown of ~10s and Buying ~5s between each message.")
        new_embed = discord.Embed(title="Welcome to Caeser's help command", description=f"{title_name}", color=0x71368A)
        new_embed.add_field(name="", value=embed_description, inline=True)
        new_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg")
        new_embed.set_author(name=self.author_name, icon_url=self.author_avatar)
        await interaction.response.edit_message(embed=new_embed, view=self)

    async def select_guild_commands_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return
        selected_category = self.select_guild_commands.values[0]
        embed_description = ""
        title_name = ""
        if selected_category == "create_guild":
            title_name = "**create_guild / cguild**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "A Guild needs to be created in order for the other commands to work! Only 1 guild for each server can be created.\n"
                                 "All commands regarding guilds will depend on the server they are used in!\n\n"
                                 "Command example:\n- 5create_guild [any name you want]\n- 5cguild [any name you want]")
        elif selected_category == "delete_guild":
            title_name = "**delete_guild / delguild**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Will delete the guild on the server the command is used. You need to confirm your choice via button. "
                                 "You don't need to type your anything else after the command.\n\n"
                                 "Command example:\n- 5delete_guild\n- 5delguild")
        elif selected_category == "add_member":
            title_name = "**add_member / addmem**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Adds the mentioned user to the guild with their __unique discord name__."
                                 "Therefor changing that name will result in a loss of the stats!\n"
                                 "Works both with normal text or @ mention.\n\n"
                                 "Command example:\n- 5add_member [example_name]\n- 5add_member @example_name"
                                 "\n- 5addmem [example_name]\n- 5addmem @example_name")
        elif selected_category == "remove_member":
            title_name = "**remove_member / remmem**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Removes the user from the guild __permanently__! You need to confirm your choice via button.\n"
                                 "If you wish to keep the user's stats but want to remove them from the guild then use the archive command.\n"
                                 "- archived members can be activated again\n\n"
                                 "Command example:\n- 5remove_member [example_name]\n- 5remove_member @example_name"
                                 "\n- 5remmem [example_name]\n- 5remmem @example_name")
        elif selected_category == "archive_member":
            title_name = "**archive_member / archmem**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "[same-same, but different](https://www.youtube.com/watch?v=7tTfL-DtpXk&ab_channel=BradGroux) to [remove_member] command\n"
                                 "Will remove the user from the guild but keep the users stats. The user can be activated again.\n\n"
                                 "Command example:\n- 5archive_member [example_name]\n- 5archive_member @example_name"
                                 "\n- 5archmem [example_name]\n- 5archmem @example_name")
        elif selected_category == "activate_member":
            title_name = "**activate_member / actmem**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Activates the archived user and they will appear in the [clandonations] command again.\n\n"
                                 "Command example:\n- 5activate_member [example_name]\n- 5activate_member @example_name"
                                 "\n- 5actmem [example_name]\n- 5actmem @example_name")
        elif selected_category == "view_archive":
            title_name = "**view_archive / va**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Shows the list of all users in the archive. If no one is found then \"No Members in archive found.\" will be shown.\n"
                                 "You don't need to type your anything else after the command.\n\n"
                                 "Command example:\n- 5view_archive\n- 5va")
        elif selected_category == "donation_threshold":
            title_name = "**donation_threshold / dt**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Sets the donation limit for the guild. Only numbers can be used and \"k\" as abbreviation does __not__ work currently.\n\n"
                                 "Command example:\n- 5donation_threshold 250000\n- 5dt 250000")
        elif selected_category == "clandonations":
            title_name = "**clandonations / cd**"
            embed_description = ("Shows all guild members donation status, the currently needed donation for the guild and \"if\" how much is missing.\n"
                                 "Using \"-old\" will show the last rotation. Works for both weekly and monthly.\n\n"
                                 "Command example:\n- 5clandonations\n- 5cd\n- 5clandonations -old\n- 5cd -old")
        elif selected_category == "clandonationstracker":
            title_name = "**clandonationstracker / cdt**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Shows the own donation overview. Only usable on server where you are in the guild and are not archived!\n\n"
                                 "Command example:\n- 5clandonationstracker\n- 5cdt")
        elif selected_category == "guild_reset":
            title_name = "**guild_reset / guildreset / gr**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Choose via buttons if you want the guild reset timing to be weekly or monthly. "
                                 "The command [clandonations] will change accordingly!\n\n"
                                 "Command example:\n- 5guild_reset\n- 5guildreset\n- 5gr")
        elif selected_category == "guild_donations_for_user":
            title_name = "**guild_donations_for_user / guilddonouser / gdonouser**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Shows the donation overview of the specific user. The **Title** is the donation id."
                                 "The Donation ID is needed for the command [remove_donation] and [edit_donation].\n"
                                 "__the provided name for the search has to be the unique discord name__\n\n"
                                 "Command example:\n- 5guild_donations_for_user example_name\n- 5guilddonouser example_name\n- 5gdonouser example_name")
        elif selected_category == "add_donation":
            title_name = "**add_donation / adddono**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Manually adds a donation to a given username. This command will only update the guild it is used in!\n"
                                 "First the username then the amount. The donation id is created automatically.\n\n"
                                 "Command example:\n- 5add_donation example_name 50k\n- 5add_donation example_name 50000\n- 5adddono example_name 50k\n- 5adddono example_name 50000")
        elif selected_category == "remove_donation":
            title_name = "**remove_donation / remdono**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Removes a donation via the donation id. To get the donation id use the command [guild_donations_for_user].\n\n"
                                 "Command example:\n- 5remove_donation example_name1743863286\n- 5remdono example_name1743863286")
        elif selected_category == "edit_donation":
            title_name = "**edit_donation / editdono**"
            embed_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Edite a donation via the donation id. To get the donation id use the command [guild_donations_for_user].\n"
                                 "First the donation id then the new amount you wish to set.\n\n"
                                 "Command example:\n- 5edit_donation example_name1743863286 50k\n- 5edit_donation example_name1743863286 50000\n"
                                 "- 5editdono example_name1743863286 50k\n- 5editdono example_name1743863286 50000")
        new_embed = discord.Embed(title="Welcome to Caeser's help command", description=f"{title_name}", color=0x71368A)
        new_embed.add_field(name="", value=embed_description, inline=True)
        new_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg")
        new_embed.set_author(name=self.author_name, icon_url=self.author_avatar)
        await interaction.response.edit_message(embed=new_embed, view=self)
