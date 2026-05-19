import discord
from discord import MediaGalleryItem
from discord.ui import View, Button, MediaGallery, Thumbnail, Select
import json
import os

picture_caeser = "https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif"


async def help_v2(ctx, slash=None):

    class MarketDex(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class MarketDexContainer(discord.ui.Container):
                mdex_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1411467403262693376/image.png?ex=68b4c2f4&is=68b37174&hm=ec4b46a037f34f96c6c3e99e2911216d424ea9b438d0f74f5cdb8edaaa0ec9aa&"
                mdex_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1411467402939600927/image.png?ex=68b4c2f4&is=68b37174&hm=c085e6578f02e4262c65fd7bb2b9006522605616284a64aa0f0fc821c169db6e&"
                mdex_pic_3 = "https://cdn.discordapp.com/attachments/1027151586260156516/1411467402553593856/image.png?ex=68b4c2f4&is=68b37174&hm=66097602729a9ac4628245b2f29797b1c8f2b2b3329643063b3e07c0dba05099&"
                mdex_description = ("__all filter options:__\n"
                                    "- ``-all`` shows all cards\n"
                                    "- ``-name [card name]`` use comma to search for multiple names at once\n"
                                    "- ``-series [series name]`` use comma to search for multiple series at once\n"
                                    "- ``-element [card element]`` use comma to search for multiple elements at once\n"
                                    "- ``-talent [talent name]`` use comma to search for multiple talents at once\n"
                                    "- ``-rarity [sr or ur]`` shows only the price for the corresponding rarity and is sorted from lowest to highest price\n"
                                    "- ``-price [\"<\" or \"=\" or \">\"] [gold value]`` define if you want to search for equal(=), more than(>) or less than (<) the given gold price\n"
                                    "- ``-page [number]`` view the given page number\n\n"
                                    "__aliases for the filter__:\n"
                                    "- ``name / n``\n"
                                    "- ``series / s``\n"
                                    "- ``element / ele / e``\n"
                                    "- ``talent / skill / t``\n"
                                    "- ``rarity / r``\n"
                                    "- ``page / p``\n"
                                    "- ``price`` and ``all`` don't have any alias!\n\n"
                                    "If the new price is higher than the last seen price * price factor then the price __will not be updated__\n"
                                    "- price factor = 10 if the last seen price < 5k\n"
                                    "- price factor = 5 if the last seen price < 10k\n"
                                    "- price factor = 4 if the last seen price < 20k\n"
                                    "- price factor = 3 if the last seen price < 30k\n"
                                    "- price factor = 2 if > 30k\n\n"
                                    "__example commands:__")
                mdex = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## marketdex / mdex\n\n{mdex_description}"))
                mdex_pic_1_text = discord.ui.TextDisplay("Shows only the sr cards with the element NULL that are worth more than 30k")
                gallery = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{mdex_pic_1}"))
                sep1 = discord.ui.Separator()
                mdex_pic_2_text = discord.ui.TextDisplay("Shows page 30 for all available ur prices")
                gallery2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{mdex_pic_2}"))
                sep2 = discord.ui.Separator()
                mdex_pic_3_text = discord.ui.TextDisplay("Shows all cards with the element ground from the series Sword Art Online, One Piece and Dr. Stone")
                gallery3 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{mdex_pic_3}"))

            class MarketDexView(discord.ui.LayoutView):
                container = MarketDexContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=MarketDexView(), ephemeral=True)
            return True

    class MarketDexSlash(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class MarketDexContainer(discord.ui.Container):
                mdex_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420459230351069184/image.png?ex=68d5793f&is=68d427bf&hm=4904ad9090490f4bbb01ecbe4ac16151cb8350a733135d0f18289903f37f62e1&"
                mdex_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420460076740771900/image.png?ex=68d57a09&is=68d42889&hm=cc262c94dbf8dae64db47f9c386edddb7e6bb284a37f91a962c8eeb16605416e&"
                mdex_pic_3 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420460369012461661/image.png?ex=68d57a4e&is=68d428ce&hm=9159a2a607b51d67b43421093f7133bd5e826f65126a434817cde9b7a16aea80&"
                mdex_description = ("__all filter options:__\n"
                                    "- ``name [card name]`` use comma to search for multiple names at once\n"
                                    "- ``series [series name]`` use comma to search for multiple series at once\n"
                                    "- ``element [card element]`` use comma to search for multiple elements at once\n"
                                    "- ``talent [talent name]`` use comma to search for multiple talents at once\n"
                                    "- ``rarity [sr or ur]`` shows only the price for the corresponding rarity and is sorted from lowest to highest price\n"
                                    "- ``price [gold amount]`` does not work with the shortcut \"k\""
                                    "- ``price operator [\"<\" or \"=\" or \">\"]`` define if you want to search for equal(=), more than(>) or less than (<) the given gold price\n"
                                    "- ``page [number]`` view the given page number\n"
                                    "all cards will be shown if no filter is provided\n\n"
                                    "If the new price is higher than the last seen price * price factor then the price __will not be updated__\n"
                                    "- price factor = 10 if the last seen price < 5k\n"
                                    "- price factor = 5 if the last seen price < 10k\n"
                                    "- price factor = 4 if the last seen price < 20k\n"
                                    "- price factor = 3 if the last seen price < 30k\n"
                                    "- price factor = 2 if > 30k\n\n"
                                    "__example commands:__")
                mdex = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## marketdex / mdex\n\n{mdex_description}"))
                mdex_pic_1_text = discord.ui.TextDisplay("Shows all cards worth more than 35k as SR")
                gallery = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{mdex_pic_1}"))
                sep1 = discord.ui.Separator()
                mdex_pic_2_text = discord.ui.TextDisplay("Shows page 30 for all available ur prices")
                gallery2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{mdex_pic_2}"))
                sep2 = discord.ui.Separator()
                mdex_pic_3_text = discord.ui.TextDisplay("Shows all cards with the element ground from the series Sword Art Online, One Piece and Dr. Stone")
                gallery3 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{mdex_pic_3}"))

            class MarketDexView(discord.ui.LayoutView):
                container = MarketDexContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=MarketDexView(), ephemeral=True)
            return True

    class Compare(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class CompareContainer(discord.ui.Container):
                compare_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1423236413490598030/image.png?ex=68df93b3&is=68de4233&hm=81dc9d544f910c71a4c1c1a0a12eea7ea78ed4be4d4cdd15b07288c578da9407&"
                compare_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1423253023630557224/image.png?ex=68dfa32b&is=68de51ab&hm=897bf23729f6487c2369b9e42c1f687d22465e76c042100dc74349b0a3a05472&"
                compare_description = ("Compare up to 18 cards at once!\n\n"
                                       "__filter & alias:__\n"
                                       "- ``-name`` or ``-n`` [card name] use comma to separate multiple\n"
                                       "- ``-series`` or ``-serie`` [series name] use comma to separate multiple\n"
                                       "- ``-element`` or ``-ele`` or ``-e`` [element name] use comma to separate multiple\n"
                                       "- ``-talent`` or ""-skill`` or ``-t`` [talent name] use comma to separate multiple\n"
                                       "__optional:__\n"
                                       "- ``-state`` or ``-stat`` [code for **quick** setup] use comma to separate multiple\n\n"
                                       "__state codes:__\n"
                                       "- ``R[rarity]`` Ultra Rare=UR, Super Rare=SR, Rare=R, Uncommon=UC, Common=C\n"
                                       "- ``L[card level]`` Any number up to 60\n"
                                       "- ``E[card evolution]`` Any number up to 3\n"
                                       "- ``A[card ascension]`` Any number up to 5\n"
                                       "- ``F[card familiarity]`` or ``H[card holo]`` Fam max is 3 and Holo 1\n"
                                       "- ``CL[clan level]`` Clan level and __not__ the bonus, hp/atk/def/spd will be set the same\n"
                                       "Numbers higher than the maximum will the set to the maximum.\n\n"
                                       "**__Main way to edit / change the stats:__**\n"
                                       "The button \"Edit All\" will change __all__ cards and clan stats.\n"
                                       "The button \"Edit One\" will change the selected card and clan stats can be adjusted each on their own.\n\n"
                                       "__example command:__")
                compare = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## compare\n\n{compare_description}"))
                compare_pic_1_text = discord.ui.TextDisplay("Compares 2 Tushan Susu, one as UR L60 E3 A2 H1 and the other as UR L60 E3 A5 F0.")
                gallery1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{compare_pic_1}"))
                compare_pic_2_text = discord.ui.TextDisplay("Stats can be adjusted with the buttons \"Edit All\" or \"Edit One\".")
                gallery2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{compare_pic_2}"))

            class CompareView(discord.ui.LayoutView):
                container = CompareContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=CompareView(), ephemeral=True)
            return True

    class CompareSlash(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class CompareContainer(discord.ui.Container):
                compare_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1423240324129755186/image.png?ex=68df9757&is=68de45d7&hm=d9ec25733eaea12129ebf62d24cc6ceded2ba00c719abdd9c33c4ff30c49899a&"
                compare_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1423253023630557224/image.png?ex=68dfa32b&is=68de51ab&hm=897bf23729f6487c2369b9e42c1f687d22465e76c042100dc74349b0a3a05472&"
                compare_description = ("Compare up to 18 cards at once!\n\n"
                                       "__filter & alias:__\n"
                                       "- ``-name`` [card name] use comma to separate multiple\n"
                                       "- ``-series`` [series name] use comma to separate multiple\n"
                                       "- ``-element`` [element name] use comma to separate multiple\n"
                                       "- ``-talent`` [talent name] use comma to separate multiple\n"
                                       "__optional:__\n"
                                       "- ``-stat`` [code for **quick** setup] use comma to separate multiple\n\n"
                                       "__state codes:__\n"
                                       "- ``R[rarity]`` Ultra Rare=UR, Super Rare=SR, Rare=R, Uncommon=UC, Common=C\n"
                                       "- ``L[card level]`` Any number up to 60\n"
                                       "- ``E[card evolution]`` Any number up to 3\n"
                                       "- ``A[card ascension]`` Any number up to 5\n"
                                       "- ``F[card familiarity]`` or ``H[card holo]`` Fam max is 3 and Holo 1\n"
                                       "- ``CL[clan level]`` Clan level and __not__ the bonus, hp/atk/def/spd will be set the same\n"
                                       "Numbers higher than the maximum will the set to the maximum.\n\n"
                                       "**__Main way to edit / change the stats:__**\n"
                                       "The button \"Edit All\" will change __all__ cards and clan stats.\n"
                                       "The button \"Edit One\" will change the selected card and clan stats can be adjusted each on their own.\n\n"
                                       "__example command:__")
                compare = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## compare\n\n{compare_description}"))
                compare_pic_1_text = discord.ui.TextDisplay("Compares 2 Tushan Susu, one as UR L60 E3 A2 H1 and the other as UR L60 E3 A5 F0.")
                gallery1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{compare_pic_1}"))
                compare_pic_2_text = discord.ui.TextDisplay("Stats can be adjusted with the buttons \"Edit All\" or \"Edit One\".")
                gallery2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{compare_pic_2}"))

            class CompareView(discord.ui.LayoutView):
                container = CompareContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=CompareView(), ephemeral=True)
            return True

    class SetFloor(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class SetFloorContainer(discord.ui.Container):
                sfl_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1411541102804205751/image.png?ex=68b50798&is=68b3b618&hm=6dc6b8813ef894805135055ad888cd25d7b09281ebf98e11c4e898449a162ac5&"
                sfl_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1411541291170271273/image.png?ex=68b507c4&is=68b3b644&hm=9c83544e814b6f76504fa1f46a24df5e59b3ad39bb9f8830da618c26b7f461a8&"
                sfl_description = ("Setup command for ``shardlist / floorlist / soullist``. You can either provide the Location & Floor within the command already or "
                                   "provide them in a follow up message.\n\n"
                                   "__example command:__")
                sfl = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## setfloor / sfl\n\n{sfl_description}"))
                compare_pic_1_text = discord.ui.TextDisplay("Triggered the command and then send the Location & Floor number in a follow up message.")
                gallery1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{sfl_pic_1}"))
                sep = discord.ui.Separator()
                compare_pic_2_text = discord.ui.TextDisplay("Provided the Location & Floor number within the command.")
                gallery2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{sfl_pic_2}"))

            class SetFloorView(discord.ui.LayoutView):
                container = SetFloorContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=SetFloorView(), ephemeral=True)
            return True

    class SetFloorSlash(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class SetFloorContainer(discord.ui.Container):
                sfl_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420421932083576873/image.png?ex=68d55682&is=68d40502&hm=d201413fc4488d0f883e244978b0f3711e670ffa53ce2ca87b5feace1f1023d0&"
                sfl_description = ("Setup command for ``shardlist / floorlist / soullist``.\n\n"
                                   "__example command:__")
                sfl = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## setfloor / sfl\n\n{sfl_description}"))
                gallery1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{sfl_pic_1}"))

            class SetFloorView(discord.ui.LayoutView):
                container = SetFloorContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=SetFloorView(), ephemeral=True)
            return True

    class ShardList(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class ShardListContainer(discord.ui.Container):
                shard_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1416100786064326778/image.png?ex=68c59e21&is=68c44ca1&hm=db90111b73b4d7f96cd021207c1025e3dcb5b62b5be19c3c430ab761b1d284dd&"
                shard_description = ("Shows the best location to farm shards and gold based on the setup of ``setfloor``. "
                                     "If none were provided then the highest possible combination will be shown. \n\n"
                                   "__example command:__")
                shardlist = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## shardlist / soullist / floorlist\n\n{shard_description}"))
                shard_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{shard_pic_1}"))


            class SetFloorView(discord.ui.LayoutView):
                container = ShardListContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=SetFloorView(), ephemeral=True)
            return True

    class ShardListSlash(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class ShardListContainer(discord.ui.Container):
                shard_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420420392442658909/image.png?ex=68d55513&is=68d40393&hm=8bcb48d3744fe3c7f9c45d6f04a206cfde9a7a6ebe887441b31f82b35f523250&"
                shard_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420421505652887583/image.png?ex=68d5561d&is=68d4049d&hm=f3f7c7fd0798fb81477ee9f5622ba2ee42227f7e2c1635d62f9817d607361a47&"
                shard_pic_3 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420421716513128530/image.png?ex=68d5564f&is=68d404cf&hm=4d1ea3f35e1362163e7949e76d330703922b3128053f2908603fb6c663434a54&"
                shard_description = ("Shows the best location to farm shards and gold based on the setup of ``setfloor``. "
                                     "If none were provided then the highest possible combination will be shown. \n\n"
                                   "__example command:__")
                shardlist = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## shardlist / soullist / floorlist\n\n{shard_description}"))
                shard_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{shard_pic_1}"))
                sep = discord.ui.Separator()
                shard_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{shard_pic_2}"))
                sep2 = discord.ui.Separator()
                shard_gallery_3 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{shard_pic_3}"))


            class SetFloorView(discord.ui.LayoutView):
                container = ShardListContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=SetFloorView(), ephemeral=True)
            return True

    class RaidHistory(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RaidHistoryContainer(discord.ui.Container):
                rh_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1416444738806218753/image.png?ex=68c6de76&is=68c58cf6&hm=bf61735dc25bc01de53ae138d9269b99c5263c2c7334cdef6cc258b890c8436c&"
                rh_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1416444986102251550/image.png?ex=68c6deb0&is=68c58d30&hm=030b95c5cce57f455ffe8a510e6d7aa3673a9012c6fa3e0e9d5f082f87b50ab6&"
                rh_description = ("__only 1 optional filter can be applied:__\n"
                                  "- ``-n [boss name]`` works with partial and full names\n"
                                  "- ``-r [boss rarity]``\n"
                                  "- ``-d [boss difficulty]``\n"
                                  "- ``-l [boss level]`` uses the __exact__ level\n\n"
                                  "rarity filter options are: ``uncommon``, ``uc``, ``rare``, ``r``, ``super rare``, ``sr``, ``ultra rare``, ``ur``\n"
                                  "difficulty filter options are: ``easy``, ``e``, ``medium``, ``m``, ``hard``, ``h``, ``impossible``, ``i``\n"
                                  "level can be further filtered with ``<`` & ``>``\n\n"
                                   "__example command:__")
                rh = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## raidhistory / rh\n\n{rh_description}"))
                rh_pic_1_text = discord.ui.TextDisplay("Shows all tracked raids with a __higher__ level than 5000.")
                rh_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{rh_pic_1}"))
                sep = discord.ui.Separator()
                rh_pic_2_text = discord.ui.TextDisplay("Shows all tracked raids of Gowther.")
                rh_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{rh_pic_2}"))

            class RaidHistoryView(discord.ui.LayoutView):
                container = RaidHistoryContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RaidHistoryView(), ephemeral=True)
            return True

    class RaidHistorySlash(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RaidHistoryContainer(discord.ui.Container):
                rh_pic_1     = "https://cdn.discordapp.com/attachments/1027151586260156516/1420448076304482474/image.png?ex=68d56edc&is=68d41d5c&hm=8a4eb9e340973bf6b819eeab61b380fc781f85cdac5aa3b8d5f84e993ac412ce&"
                rh_description = ("all of the following filter can be used together:\n"
                                  "- `` [boss name]`` works with partial and full names\n"
                                  "- `` [rarity]``\n"
                                  "- `` [difficulty]``\n"
                                  "- `` [level]`` uses the __exact__ level\n\n"
                                  "rarity filter options are: ``uncommon``, ``uc``, ``rare``, ``r``, ``super rare``, ``sr``, ``ultra rare``, ``ur``\n"
                                  "difficulty filter options are: ``easy``, ``e``, ``medium``, ``m``, ``hard``, ``h``, ``impossible``, ``i``\n"
                                  "level can be further filtered with ``<`` & ``>``\n\n"
                                  "__example command:__")
                rh = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## raidhistory / rh\n\n{rh_description}"))
                sep = discord.ui.Separator()
                rh_pic_1_text = discord.ui.TextDisplay("Shows all tracked raids of SR Gowther lvl 1600 difficulty impossible.")
                rh_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{rh_pic_1}"))

            class RaidHistoryView(discord.ui.LayoutView):
                container = RaidHistoryContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RaidHistoryView(), ephemeral=True)
            return True

    class RaidLobby(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RaidLobbyContainer(discord.ui.Container):
                rl_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1416471483068321892/image.png?ex=68c6f75e&is=68c5a5de&hm=82fef5b770dd7172056b42ab174d30c2d8338ea5072d25c4bf212581ba906120&"
                rl_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1416472458348859462/image.png?ex=68c6f846&is=68c5a6c6&hm=3cb671f0792d53a65d5e08615fd87be98e98ba00a5b1b68702a617a0fd307585&"
                rl_pic_3 = "https://cdn.discordapp.com/attachments/1027151586260156516/1423798767823491202/image.png?ex=68e19f6f&is=68e04def&hm=1d6ee55d8811eb063a1772204ac2ed9a72214a9a234ca5dbe2a8157d9c77e811&"
                rl_pic_4 = "https://cdn.discordapp.com/attachments/1027151586260156516/1423798767425159238/image.png?ex=68e19f6f&is=68e04def&hm=ea70f52710c2ecd38fc24ed773ad093e199c073be255db8e42cbea7888989465&"
                rl_description = ("The provided gold number works with and without ``k``\n"
                                  "The message length can not exceed 2000 characters/letters due to discords limitations, "
                                  "the message \"To much characters. Please use a different gold number\" will be send instead.\n\n"
                                  "__additional filter option:__\n"
                                  "- ``-exclude [type of event]`` use comma to exclude multiple event types at once\n"
                                  "- ``-sell`` will change **.rd lobbies -r r,sr,ur** to **.inv -r sr -evo 1**\n\n"
                                  "aliases and type of events:\n"
                                  "- ``exclude / ex`` - alias\n"
                                  "- ``cl / clan / cl shop / clan shop`` - event type\n"
                                  "- ``vote / monthly / calendar`` - event type\n"
                                  "- ``event`` - event type\n\n"
                                   "__example command:__")
                rl = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## raidlobbies / rl\n\n{rl_description}"))
                rl_pic_1_text = discord.ui.TextDisplay("Provides an .inv filter with normal & event/mob cards worth at least 50k")
                rl_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{rl_pic_1}"))
                sep = discord.ui.Separator()
                rl_pic_2_text = discord.ui.TextDisplay("Provides .rd lobbies filter without any clan shop, event or vote cards that are worth at least 30k")
                rl_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{rl_pic_2}"))
                sep2 = discord.ui.Separator()
                rl_pic_3_text = discord.ui.TextDisplay(
                    "Fast Copy Paste: open the message options and copy the whole message")
                rl_gallery_3 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{rl_pic_3}"),
                                                       discord.MediaGalleryItem(media=f"{rl_pic_4}"))

            class RaidLobbyView(discord.ui.LayoutView):
                container = RaidLobbyContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RaidLobbyView(), ephemeral=True)
            return True

    class RaidLobbySlash(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RaidLobbyContainer(discord.ui.Container):
                rl_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420462960865972285/image.png?ex=68d57cb8&is=68d42b38&hm=980948b6668ffdaa1a4ee258f4d6daa896cca2784644a2d9771345c5dd202cc7&"
                rl_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420462969728405607/image.png?ex=68d57cba&is=68d42b3a&hm=1c6f41ed4a54bf125b7010807e212a4cdb236ae3309d4907653ec6cecfb94463&"
                rl_pic_3 = "https://cdn.discordapp.com/attachments/1027151586260156516/1423798767823491202/image.png?ex=68e19f6f&is=68e04def&hm=1d6ee55d8811eb063a1772204ac2ed9a72214a9a234ca5dbe2a8157d9c77e811&"
                rl_pic_4 = "https://cdn.discordapp.com/attachments/1027151586260156516/1423798767425159238/image.png?ex=68e19f6f&is=68e04def&hm=ea70f52710c2ecd38fc24ed773ad093e199c073be255db8e42cbea7888989465&"
                rl_description = ("The provided gold number works with and without ``k``\n"
                                  "The message length can not exceed 2000 characters/letters due to discords limitations, "
                                  "the message \"To much characters. Please use a different gold number\" will be send instead.\n\n"
                                  "__additional filter option:__\n"
                                  "- ``-exclude [type of event]`` use comma to exclude multiple event types at once\n"
                                  "- ``-sell`` will change **.rd lobbies -r r,sr,ur** to **.inv -r sr -evo 1**\n\n"
                                   "__example command:__")
                rl = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## raidlobbies / rl\n\n{rl_description}"))
                rl_pic_1_text = discord.ui.TextDisplay("Provides an .inv filter with normal & event/mob cards worth at least 50k")
                rl_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{rl_pic_1}"))
                sep = discord.ui.Separator()
                rl_pic_2_text = discord.ui.TextDisplay("Provides .rd lobbies filter without any clan shop, event or vote cards that are worth at least 30k")
                rl_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{rl_pic_2}"))
                sep2 = discord.ui.Separator()
                rl_pic_3_text = discord.ui.TextDisplay("Fast Copy Paste: open the message options and copy the whole message")
                rl_gallery_3 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{rl_pic_3}"),
                                                       discord.MediaGalleryItem(media=f"{rl_pic_4}"))

            class RaidLobbyView(discord.ui.LayoutView):
                container = RaidLobbyContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RaidLobbyView(), ephemeral=True)
            return True

    class SetPrefix(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class SetPrefixContainer(discord.ui.Container):
                pre_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1416486395450753216/image.png?ex=68c70541&is=68c5b3c1&hm=85a2bdd78e3cc0e838abc746383d09210aec6d232fb0cd566f9eaa8def7fcd3e&"
                pre_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1416486446344310936/image.png?ex=68c7054d&is=68c5b3cd&hm=43b930131bcffce8db458a105bf42fb60dab752decaad326d2347ba369444508&"
                pre_description = ("**This command is only accessible with admin permissions!\n"
                                   "Any letter, number or symbol can be used as prefix.\n\n"
                                   "__example command:__")
                pre = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## setprefix\n\n{pre_description}"))
                pre_pic_1_text = discord.ui.TextDisplay("Set the prefix to 🡆 and changed back to 5.")
                pre_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{pre_pic_1}"))
                pre_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{pre_pic_2}"))

            class SetPrefixView(discord.ui.LayoutView):
                container = SetPrefixContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=SetPrefixView(), ephemeral=True)
            return True

    class DailyWatch(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class DailyWatchContainer(discord.ui.Container):
                dw_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1416498383098478652/image.png?ex=68c7106b&is=68c5beeb&hm=e49dbaa11f9f0e472e7982363d882f67d9d943df5a7dd5b440884ef517689b59&"
                dw_description = ("View all cards Super Rare and Ultra Rare price of the current ongoing daily shop rotation.\n"
                                  "If you want to check other series please use the ``marketdex`` command.\n\n"
                                   "__example command:__")
                dw = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## dailywatch / dw\n\n{dw_description}"))
                dw_pic_1_text = discord.ui.TextDisplay("Shows the current daily shop rotation.")
                dw_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{dw_pic_1}"))

            class DailyWatchView(discord.ui.LayoutView):
                container = DailyWatchContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=DailyWatchView(), ephemeral=True)
            return True

    class DailyWatchSlash(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class DailyWatchContainer(discord.ui.Container):
                dw_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420463968186663056/image.png?ex=68d57da8&is=68d42c28&hm=6c6a2e68552ae748df551454a6602ea868d276ba5f751e6dcec5288c85c5eacc&"
                dw_description = ("View all cards Super Rare and Ultra Rare price of the current ongoing daily shop rotation.\n"
                                  "If you want to check other series please use the ``marketdex`` command.\n\n"
                                   "__example command:__")
                dw = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## dailywatch / dw\n\n{dw_description}"))
                dw_pic_1_text = discord.ui.TextDisplay("Shows the current daily shop rotation.")
                dw_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{dw_pic_1}"))

            class DailyWatchView(discord.ui.LayoutView):
                container = DailyWatchContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=DailyWatchView(), ephemeral=True)
            return True

    class SetLocation(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class SetLocationContainer(discord.ui.Container):
                sl_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1416500758387359896/image.png?ex=68c712a2&is=68c5c122&hm=1ca031c77e87704a7e65b8b541d6bf4695e15b49101ca22dd08628ec1b405090&"
                sl_description = ("__This command is only available for the official Caeser server__\n\n"
                                  "Select all locations you want to receive a ping for when they appear in the daily shop rotation. "
                                  "To disable the pings again, simply select the locations again.\n\n"
                                   "__example command:__")
                sl = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## setlocation / sl\n\n{sl_description}"))
                sl_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{sl_pic_1}"))

            class SetLocationView(discord.ui.LayoutView):
                container = SetLocationContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=SetLocationView(), ephemeral=True)
            return True

    class SetLocationSlash(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class SetLocationContainer(discord.ui.Container):
                sl_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420464911699677194/image.png?ex=68d57e89&is=68d42d09&hm=9b90bdf23d6a30462b78ae3527ddd2ef31bd1c36e7e05ff0c91f053d7ae50dcc&"
                sl_description = ("__This command is only available for the official Caeser server__\n\n"
                                  "Select all locations you want to receive a ping for when they appear in the daily shop rotation. "
                                  "To disable the pings again, simply select the locations again.\n\n"
                                   "__example command:__")
                sl = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## setlocation / sl\n\n{sl_description}"))
                sl_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{sl_pic_1}"))

            class SetLocationView(discord.ui.LayoutView):
                container = SetLocationContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=SetLocationView(), ephemeral=True)
            return True

    class RaidGuide(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RaidGuideContainer(discord.ui.Container):
                raid_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1416771992073404508/image.png?ex=68c80f3d&is=68c6bdbd&hm=4175cd0e74217f9207fc29bf5affd6c4ed72ca67322651309f9092873edcf400&"
                raid_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1416773703428997141/image.png?ex=68c810d5&is=68c6bf55&hm=047ac832995754233cf5331160c8cde525356c595391eaf44ad42d5d6e543a19&"
                raid_description = ("__mandatory filter__:\n"
                                    "- ``-n [boss name]`` works with full and partial names\n\n"
                                    "__optional filter__:\n"
                                    "- ``-r [rarity]``\n\n"
                                    "aliases & rarity options:\n"
                                    "- ``name / n`` - alias\n"
                                    "- ``rarity / r`` - alias\n"
                                    "- ``rare / r`` - rarity option & alias\n"
                                    "- ``sr`` - rarity option\n"
                                    "- ``ur`` - rarity option\n"
                                    "**If no rarity filter is provided then all available rarities will be shown.**\n\n"
                                    "__example command:__")
                raid = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## raidguide\n\n{raid_description}"))
                raid_pic_1_text = discord.ui.TextDisplay("Shows possible team comps for Ultra Rare Anri Sonohara.")
                raid_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{raid_pic_1}"))
                raid_pic_2_text = discord.ui.TextDisplay("Shows all available team comps for Rare & SR & UR Cha Hae In")
                raid_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{raid_pic_2}"))

            class RaidGuideView(discord.ui.LayoutView):
                container = RaidGuideContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RaidGuideView(), ephemeral=True)
            return True

    class RaidGuideSlash(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RaidGuideContainer(discord.ui.Container):
                raid_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420465473006604308/image.png?ex=68d57f0f&is=68d42d8f&hm=d92dd8fe797f1150862356f5c77e7d5328906c4e8bc19d6686405b3cbb51d6f0&"
                raid_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420465711939063839/image.png?ex=68d57f48&is=68d42dc8&hm=f3cc310a634916e85b9ef5f1c08f0c540337a8b90b003d480e0868ca04c9a183&"
                raid_pic_3 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420465857938591924/image.png?ex=68d57f6b&is=68d42deb&hm=e457685d0e81fb541f1a4bc64d95d689665c5cf1a907e7de968013aaedf03f2a&"
                raid_description = ("__mandatory filter__:\n"
                                    "- ``-n [boss name]`` works with full and partial names\n\n"
                                    "__optional filter__:\n"
                                    "- ``-r [rarity]`` rare or r, sr, ur\n"
                                    "**If no rarity filter is provided then all available rarities will be shown.**\n\n"
                                    "__example command:__")
                raid = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## raidguide\n\n{raid_description}"))
                raid_pic_1_text = discord.ui.TextDisplay("Shows possible team comps for Ultra Rare Anri Sonohara.")
                raid_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{raid_pic_1}"))
                raid_pic_2_text = discord.ui.TextDisplay("Shows all available team comps for Rare & SR & UR Cha Hae In")
                raid_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{raid_pic_2}"))
                raid_pic_3_text = discord.ui.TextDisplay("If you enter \"event\" in the name box, it will show all ongoing event cards in the dropdown!")
                raid_gallery_3 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{raid_pic_3}"))

            class RaidGuideView(discord.ui.LayoutView):
                container = RaidGuideContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RaidGuideView(), ephemeral=True)
            return True

    class Rulesets(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RulesetsContainer(discord.ui.Container):
                ruleset_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1416778432557355220/image.png?ex=68c8153c&is=68c6c3bc&hm=e8573f1f8a2c8ddd456ffff6f7dc8b15d0340b2fd8880a646f6b141ac0adea13&"
                ruleset_description = ("Shows the most commonly used Ruleset codes for the anigame command /dg battle .\n"
                                       "Click on the buttons to send the code in a separate message for easier copy & paste.\n\n"
                                       "__example command:__")
                ruleset = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## rulesets\n\n{ruleset_description}"))
                ruleset_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{ruleset_pic_1}"))

            class RulesetsView(discord.ui.LayoutView):
                container = RulesetsContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RulesetsView(), ephemeral=True)
            return True

    class RulesetsSlash(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RulesetsContainer(discord.ui.Container):
                ruleset_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420467188552433735/image.png?ex=68d580a8&is=68d42f28&hm=53047c39e57034b495c5c033c6735052ae9f4b9312f1998994d34e79c18c5887&"
                ruleset_description = ("Shows the most commonly used Ruleset codes for the anigame command /dg battle .\n"
                                       "Click on the buttons to send the code in a separate message for easier copy & paste.\n\n"
                                       "__example command:__")
                ruleset = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## rulesets\n\n{ruleset_description}"))
                ruleset_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{ruleset_pic_1}"))

            class RulesetsView(discord.ui.LayoutView):
                container = RulesetsContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RulesetsView(), ephemeral=True)
            return True

    class UpdatePlayer(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class UpdatePlayerContainer(discord.ui.Container):
                update_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418593367851274431/image.png?ex=68ceaf87&is=68cd5e07&hm=c393dae0d4a2026e2bd30af82bba8dd2e9cfc26235cab8cd5ad17c213d17a1be&"
                update_description = ("If you have issues with any tracking like gold or if you changed your __unique__ discord name then please use this command. "
                                      "The command will update to your new name or add you to the database.\n\n"
                                       "__example command:__")
                update = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## update\n\n{update_description}"))
                update_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{update_pic_1}"))

            class UpdatePlayerView(discord.ui.LayoutView):
                container = UpdatePlayerContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=UpdatePlayerView(), ephemeral=True)
            return True

    class UpdatePlayerSlash(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class UpdatePlayerContainer(discord.ui.Container):
                update_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1420467989198667918/image.png?ex=68d58167&is=68d42fe7&hm=d7c9da0b3bf6ad5028d2b44c5875ed2b27ded6ebc0a76d552b892ce47c70ba4d&"
                update_description = ("If you have issues with any tracking like gold or if you changed your __unique__ discord name then please use this command. "
                                      "The command will update to your new name or add you to the database.\n\n"
                                       "__example command:__")
                update = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## update\n\n{update_description}"))
                update_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{update_pic_1}"))

            class UpdatePlayerView(discord.ui.LayoutView):
                container = UpdatePlayerContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=UpdatePlayerView(), ephemeral=True)
            return True

    class GoldOverview(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class GoldOverviewContainer(discord.ui.Container):
                gold_overview_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418634288458371273/image.png?ex=68ced5a3&is=68cd8423&hm=c6fcb8a23617b99e13801a26f8530286db7de60223314ca639b1bb4ef7f6f174&"
                gold_overview_description = ("The command adds a ``lose / gain`` tracking to your last seen gold value.\n\n"
                                             "__example output:__")
                gold_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## better gold overview\n\n{gold_overview_description}"))
                gold_overview_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{gold_overview_pic_1}"))

            class GoldOverviewView(discord.ui.LayoutView):
                container = GoldOverviewContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=GoldOverviewView(), ephemeral=True)
            return True

    class RubiesOverview(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RubiesOverviewContainer(discord.ui.Container):
                rubies_overview_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418636917129347182/image.png?ex=68ced816&is=68cd8696&hm=6cc454c01307d846ef1c33e7daa31e0df5285e8c75e20834338f61e07408c237&"
                rubies_overview_description = ("The command adds a overview of the max purchasable amount of SR / UR cards as well as how many "
                                               "rubies are missing till the next possible purchase.\n\n"
                                               "__example output:__")
                rubies_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## better rubies overview\n\n{rubies_overview_description}"))
                rubies_overview_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{rubies_overview_pic_1}"))

            class RubiesOverviewView(discord.ui.LayoutView):
                container = RubiesOverviewContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RubiesOverviewView(), ephemeral=True)
            return True

    class StaminaOverview(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class StaminaOverviewContainer(discord.ui.Container):
                stamina_overview_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418654663548469289/image.png?ex=68cee89d&is=68cd971d&hm=90a34e489a94fbbdd6874988cf5969ecff7c557df317dca2638b15dba53ed7e0&"
                stamina_overview_description = ("Shows the time till stamina cap is reached with and without vip as well as the doable amount "
                                                "of battles for normal floors.\n\n"
                                                "__example output:__")
                stamina_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## better stamina overview\n\n{stamina_overview_description}"))
                stamina_overview_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{stamina_overview_pic_1}"))

            class StaminaOverviewView(discord.ui.LayoutView):
                container = StaminaOverviewContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=StaminaOverviewView(), ephemeral=True)
            return True

    class HelperSelling(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class HelperSellingContainer(discord.ui.Container):
                selling_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418657165434163280/image.png?ex=68ceeaf1&is=68cd9971&hm=819644538fd2d333fc927e34ea9f46ee11a9dfac340e1aeeeb5e7c6026b9d633&"
                selling_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418657351107608748/image.png?ex=68ceeb1d&is=68cd999d&hm=3987255381a379db37736719fd2f497c3ca1f2a85572b2219be918991529cc75&"
                selling_pic_3 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418657766234656778/image.png?ex=68ceeb80&is=68cd9a00&hm=4dac60d0b4914b2cec280f109186bcebcd0c0207dec35e76330a2d5b4cde116e&"
                selling_description = ("The bot will add this emote to your inventory view: <a:sell:1378997955507523684> \n"
                                       "React to this emote to trigger the command, select all cards you want to sell in the dropdown menu and copy & paste the given command.\n\n"
                                       "__example output:__")
                selling = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## helper for selling\n\n{selling_description}"))
                selling_pic_1_text = discord.ui.TextDisplay("Message triggered by interacting with the emote <a:sell:1378997955507523684>")
                selling_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{selling_pic_1}"))
                sep = discord.ui.Separator()
                selling_pic_2_text = discord.ui.TextDisplay("Select 1 or more cards from the dropdown menu.")
                selling_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{selling_pic_2}"))
                sep2 = discord.ui.Separator()
                selling_pic_3_text = discord.ui.TextDisplay("Copy & Paste the command to sell the selected card. Since it's a new message you can just copy the whole message!")
                selling_gallery_3 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{selling_pic_3}"))

            class HelperSellingView(discord.ui.LayoutView):
                container = HelperSellingContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=HelperSellingView(), ephemeral=True)
            return True

    class HelperBuying(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class HelperBuyingContainer(discord.ui.Container):
                buying_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418662422012756018/image.png?ex=68ceefd6&is=68cd9e56&hm=f6577d7d4461b2b3e269b6438d089ec6508e5d0356c4542c61d516fd341cc8cf&"
                buying_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418662643513688184/image.png?ex=68cef00b&is=68cd9e8b&hm=e833767d94200091ce02c32f548cbbb95c0b3f0f0f6fa5f766481fb98a1c3d3f&"
                buying_pic_3 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418662698471915563/image.png?ex=68cef018&is=68cd9e98&hm=1cc28697dfb64ab61843a943ce4af6d888cd610eba3b52950816663097b44a3c&"
                buying_description = ("The bot will add this emote to your global market searches: <a:buy:1378997944203612181> \n"
                                       "React to this emote to trigger the command, select all cards you want to buy in the dropdown menu and copy & paste the given command.\n\n"
                                       "__example output:__")
                buying = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## helper for buying\n\n{buying_description}"))
                buying_pic_1_text = discord.ui.TextDisplay("Message triggered by interacting with the emote <a:buy:1378997944203612181>")
                buying_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{buying_pic_1}"))
                sep = discord.ui.Separator()
                buying_pic_2_text = discord.ui.TextDisplay("Select 1 or more cards from the dropdown menu.")
                buying_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{buying_pic_2}"))
                sep2 = discord.ui.Separator()
                buying_pic_3_text = discord.ui.TextDisplay("Copy & Paste the command to buy the selected card(s). Since it's a new message you can just copy the whole message!")
                buying_gallery_3 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{buying_pic_3}"))

            class HelperBuyingView(discord.ui.LayoutView):
                container = HelperBuyingContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=HelperBuyingView(), ephemeral=True)
            return True

    class HelperBuilding(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class HelperBuildingContainer(discord.ui.Container):
                building_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418664020042317854/image.png?ex=68cef153&is=68cd9fd3&hm=cfa9dd13567eed244dd6d75da0a33d5f1cab9f80d09a4e4eb65f96e8df35cbf3&"
                building_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418664154570690701/image.png?ex=68cef173&is=68cd9ff3&hm=119143ccda4e9aa35235d2b3dae5b264efaadfc08d239e2757895484992dea7e&"
                building_pic_3 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418664411496841357/image.png?ex=68cef1b1&is=68cda031&hm=43e4816b5b7d2c052091051ffd3898aa2786022d19a680eb3fab036cbb285121&"
                building_description = ("The bot will add this emote to your inventory view: <:evolution:1395419490434683141> \n"
                                       "React to this emote to trigger the command, select 2 or 4 cards you want to enhance and evolve in the dropdown menu and copy & paste the given command.\n"
                                       "The enhance and evolution command of anigame do not count the input after linebreaks, therefor just paste the whole block and delete the top most line "
                                       "after using it.\n"
                                       "__The command always uses the **lowest card id** of the selected ones.__ If you want a specific card to be the end result then make sure that it has the lowest id.\n\n"
                                       "__example output:__")
                building = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## helper for enhancing and evolution\n\n{building_description}"))
                building_pic_1_text = discord.ui.TextDisplay("Message triggered by interacting with the emote <:evolution:1395419490434683141>")
                building_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{building_pic_1}"))
                sep = discord.ui.Separator()
                building_pic_2_text = discord.ui.TextDisplay("Select 2 or 4 cards from the dropdown menu.")
                building_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{building_pic_2}"))
                sep2 = discord.ui.Separator()
                building_pic_3_text = discord.ui.TextDisplay("Copy & Paste the command to enhance / evolve the selected cards.")
                building_gallery_3 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{building_pic_3}"))

            class HelperBuildingView(discord.ui.LayoutView):
                container = HelperBuildingContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=HelperBuildingView(), ephemeral=True)
            return True

    class ImpCardInfo(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class ImpCardInfoContainer(discord.ui.Container):
                cinfo_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1428994220387074109/image.png?ex=68f48613&is=68f33493&hm=a98c47d5e67191f309f228bd78a3af39bed2b2f742b9ed51408e5014a29d9479&"
                cinfo_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1428994583781707806/image.png?ex=68f4866a&is=68f334ea&hm=c2c40b48f609880c10e04a1a23f0d4be17264e8f01026786f96eebbe76f24a9c&"
                cinfo_description = ("Adds the following features:\n"
                                     "- next available daily\n"
                                     "- market price for SR & UR\n"
                                     "- evolution & ascension stats change via dropdown for SR & UR\n"
                                     "- talent description changes depending on the selected rarity\n"
                                     "- clan & familiarity buff for both SR & UR via dropdown\n\n"
                                     "__customize the layout to your preference!__\n"
                                     "- de/activate the deletion of the original anigame message\n"
                                     "- switch the picture position to original or compact/thumbnail\n"
                                     "- switch the stats display to horizontal or vertical\n\n"
                                     "__example output:__")
                cinfo = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## improved card info\n\n{cinfo_description}"))
                cinfo_pic_text_1 = discord.ui.TextDisplay("Cinfo view of Tushan Susu with ``horizontal stats`` and ``picture as compact/thumbnail``.")
                cinfo_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{cinfo_pic_1}"))
                sep = discord.ui.Separator()
                cinfo_pic_text_2 = discord.ui.TextDisplay("Cinfo view of Raphtalia with ``vertical stats`` and ``picture as original``.")
                cinfo_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{cinfo_pic_2}"))

            class ImpCardInfoView(discord.ui.LayoutView):
                container = ImpCardInfoContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=ImpCardInfoView(), ephemeral=True)
            return True

    class ImpClanShop(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class ImpClanShopContainer(discord.ui.Container):
                clshop_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418672559548792872/image.png?ex=68cef947&is=68cda7c7&hm=fb2d7d95abc3ccdfd8e59f1441ded9aa0476e41c5a0db17e172b2f472e5a13fb&"
                clshop_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1418672728310939838/image.png?ex=68cef970&is=68cda7f0&hm=03adc40dc259e5d9e10c94938cc6d743dc46369c80319502123cd775e8f9bdef&"
                clshop_description = ("Adds the following features:\n"
                                     "- element and talent for each card\n"
                                     "- rubies to gold price comparison\n"
                                     "- next upcoming UR card with start & ending timer\n"
                                     "- overall overview of __all__ cards and their appearance\n"
                                     "To view the overall appearance use the button ``Cycle 1`` or ``Cycle 2``.\n\n"
                                     "__example output:__")
                clshop = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## improved clan shop\n\n{clshop_description}"))
                clshop_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{clshop_pic_1}"))
                sep = discord.ui.Separator()
                clshop_pic_2_text = discord.ui.TextDisplay("__Part__ view of the cl shop first cycle.")
                clshop_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{clshop_pic_2}"))

            class ImpClanShopView(discord.ui.LayoutView):
                container = ImpClanShopContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=ImpClanShopView(), ephemeral=True)
            return True

    class LocationTime(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class LocationTimeContainer(discord.ui.Container):
                channel_to_mention = interaction.client.get_channel(1376249740748128256)
                loc_time_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1419310053667766272/image.png?ex=68d14afe&is=68cff97e&hm=1788c9101b71333fe5a16bb71b80d4610048e1f0119fdfd7f6f3e802d04cbb15&"
                loc_time_description = ("The command / overview is exclusive for the official Caeser's Server.\n"
                                        f"It's accessible in this channel: {channel_to_mention.mention} \n"
                                        "The command always stays up to date on it's own.\n\n"
                                        "__example output:__")
                loc_time = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## location time overview\n\n{loc_time_description}"))
                loc_time_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{loc_time_pic_1}"))

            class LocationTimeView(discord.ui.LayoutView):
                container = LocationTimeContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=LocationTimeView(), ephemeral=True)
            return True

    class PackValue(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class PackValueContainer(discord.ui.Container):
                pack_value_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1419314703233974469/image.png?ex=68d14f52&is=68cffdd2&hm=d33e98a5e7f9dc3f044f5f205b2b0e54c023a16177fabe2c596b28ca9847830d&"
                pack_value_description = ("Automatically gives the last seen global market price of SR & UR cards.\n\n"
                                          "__example output:__")
                pack_value = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## pack opening value\n\n{pack_value_description}"))
                pack_value_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{pack_value_pic_1}"))

            class PackValueView(discord.ui.LayoutView):
                container = PackValueContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=PackValueView(), ephemeral=True)
            return True

    class RaidHistoryTracking(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RaidHistoryTrackingContainer(discord.ui.Container):
                raid_track_description = ("Updates the raid history of the player every time the in raid lobby is shown.\n"
                                          "Opening the raid lobby will update the history for every player within the raid.\n"
                                          "The raid history can be accessed with the ``raid history`` command.")
                raid_track = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## raid history tracking\n\n{raid_track_description}"))

            class RaidHistoryTrackingView(discord.ui.LayoutView):
                container = RaidHistoryTrackingContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RaidHistoryTrackingView(), ephemeral=True)
            return True

    class RaidLobbyInvite(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RaidLobbyInviteContainer(discord.ui.Container):
                raid_inv_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1419318800167338025/image.png?ex=68d15323&is=68d001a3&hm=8357ebf8b228c0b41582df0f738bbc1b4bc99023e5d89fe293ba6ab8dbc66b89&"
                raid_inv_pic_2 = "https://cdn.discordapp.com/attachments/1027151586260156516/1419319892330676244/image.png?ex=68d15428&is=68d002a8&hm=e62042f5b85edb2186d1b57a9e28a1f8fce69725e00964134756a580b588c1db&"
                raid_inv_description = ("Only change is the last part of the message for an easier to copy & paste code.\n\n"
                                        "__example output:__")
                raid_inv = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## raid lobby invite room\n\n{raid_inv_description}"))
                raid_inv_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{raid_inv_pic_1}"))
                sep = discord.ui.Separator()
                raid_inv_text_2 = discord.ui.TextDisplay("Hint: **Android** user can hold tap the marked area for fast copy & paste! The part behind ``|`` will be ignored.")
                raid_inv_gallery_2 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{raid_inv_pic_2}"))

            class RaidLobbyInviteView(discord.ui.LayoutView):
                container = RaidLobbyInviteContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RaidLobbyInviteView(), ephemeral=True)
            return True

    class RaidLobbyInRaid(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RaidLobbyInRaidContainer(discord.ui.Container):
                raid_lobby_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1419324157988044872/image.png?ex=68d15821&is=68d006a1&hm=5746cfbdfd35d37b7a876ae855fad3be55285e1ad2289cf4a2f57d2a57112b26&"
                raid_lobby_description = ("- A finish timer with theoretical ending time, does not include the battle time\n"
                                          "- Damage Per Attack behind the total damage in ()\n"
                                          "- Percentage damage dealt of the boss max hp after Damage per Attack in ()\n"
                                          "- Damage Status: MAX (capping damage), Great (Max till 0,75 of Max), Good (Great till 0,5 of Max), Leeching (below 0,5 of Max)\n"
                                          "- Threshold Status: If the threshold for SR/UR drops is reached\n"
                                          "- Marking players that didn't attack for more than 30min\n"
                                          "- Marking the top 3 damage dealer - they have increased chances for drops (anigame distribution on equal damage is random but Caeser uses the lobby order!)\n\n"
                                          "Estimated end time:\n"
                                          "- excluding afk = afk player are fully removed and timer is calculated without them, the hp reduce isn't accounted!\n"
                                          "- including afk = afk player comes back and starts attacking normally again\n"
                                          "- the calculation does account hp in/decreasing talents & bonus damage of special event raids (duo)\n\n"
                                          "__example output:__")
                raid_lobby = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## raid lobby in raid\n\n{raid_lobby_description}"))
                raid_lobby_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{raid_lobby_pic_1}"))

            class RaidLobbyInRaidView(discord.ui.LayoutView):
                container = RaidLobbyInRaidContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RaidLobbyInRaidView(), ephemeral=True)
            return True

    class RaidSearchSpam(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RaidSearchSpamContainer(discord.ui.Container):
                raid_spam_description = ("Caeser will delete all messages containing ``.rd lobbies -``.\n"
                                         "Has to be activated with the command ``settings``")
                raid_spam = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## raid search spam\n\n{raid_spam_description}"))

            class RaidSearchSpamView(discord.ui.LayoutView):
                container = RaidSearchSpamContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RaidSearchSpamView(), ephemeral=True)
            return True

    class Settings(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class SettingsContainer(discord.ui.Container):
                settings_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1429000271513653398/image.png?ex=68f48bb6&is=68f33a36&hm=eaff1b93299cbc001fef2a11c24b3f44ef98c1cee914ae6bf4489b8d6d11537f&"
                settings_description = ("Setup command for different follow-up commands. Interacting with the buttons will change the setting.\n"
                                        "- ``raid lobby`` Change the length of the output of the command. "
                                        "short = 2k / short = no discord nitro & long = 4k / long = with discord nitro\n"
                                        "- ``raid search history`` Set your status if you want Caeser to delete your raid lobby search spam. "
                                        "The bot will look for ``.rd lobbies -`` inside your message and delete it\n"
                                        "- ``cinfo delete`` Set your status if you want Caeser to delete the original anigame cinfo message.\n"
                                        "- ``cinfo picture`` Change the display position of the picture to either original or compact/thumbnail.\n"
                                        "- ``cinfo stats`` Change the display of the stats to either horizontal or vertical.\n")
                settings = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## settings\n\n{settings_description}"))
                settings_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{settings_pic_1}"))

            class SettingsView(discord.ui.LayoutView):
                container = SettingsContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=SettingsView(), ephemeral=True)
            return True

    class SettingsSlash(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class SettingsContainer(discord.ui.Container):
                settings_pic_1 = "https://cdn.discordapp.com/attachments/1027151586260156516/1429000271513653398/image.png?ex=68f48bb6&is=68f33a36&hm=eaff1b93299cbc001fef2a11c24b3f44ef98c1cee914ae6bf4489b8d6d11537f&"
                settings_description = ("Setup command for different follow-up commands. Interacting with the buttons will change the setting.\n"
                                        "- ``raid lobby`` Change the length of the output of the command. "
                                        "short = 2k / short = no discord nitro & long = 4k / long = with discord nitro\n"
                                        "- ``raid search history`` Set your status if you want Caeser to delete your raid lobby search spam. "
                                        "The bot will look for ``.rd lobbies -`` inside your message and delete it\n"
                                        "- ``cinfo delete`` Set your status if you want Caeser to delete the original anigame cinfo message.\n"
                                        "- ``cinfo picture`` Change the display position of the picture to either original or compact/thumbnail.\n"
                                        "- ``cinfo stats`` Change the display of the stats to either horizontal or vertical.\n")
                settings = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## settings\n\n{settings_description}"))
                settings_gallery_1 = discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{settings_pic_1}"))

            class SettingsView(discord.ui.LayoutView):
                container = SettingsContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=SettingsView(), ephemeral=True)
            return True

    class CreateGuild(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class CreateGuildContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "A Guild needs to be created in order for the other commands to work! Only 1 guild for each server can be created.\n"
                                     "All commands regarding guilds will depend on the server they are used in!\n\n"
                                     "Command example:\n- 5create_guild [any name you want]\n- 5cguild [any name you want]")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## create guild\n\n{guild_description}"))

            class CreateGuildView(discord.ui.LayoutView):
                container = CreateGuildContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=CreateGuildView(), ephemeral=True)
            return True

    class DeleteGuild(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class DeleteGuildContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "Will delete the guild on the server the command is used. You need to confirm your choice via button. "
                                     "You don't need to type your anything else after the command.\n\n"
                                     "Command example:\n- 5delete_guild\n- 5delguild")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## delete guild\n\n{guild_description}"))

            class DeleteGuildView(discord.ui.LayoutView):
                container = DeleteGuildContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=DeleteGuildView(), ephemeral=True)
            return True

    class AddMember(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class AddMemberContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "Adds the mentioned user to the guild with their __unique discord name__."
                                     "Therefor changing that name will result in a loss of the stats!\n"
                                     "Works both with normal text or @ mention.\n\n"
                                     "Command example:\n- 5add_member [example_name]\n- 5add_member @example_name"
                                     "\n- 5addmem [example_name]\n- 5addmem @example_name")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## add member\n\n{guild_description}"))

            class AddMemberView(discord.ui.LayoutView):
                container = AddMemberContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=AddMemberView(), ephemeral=True)
            return True

    class RemoveMember(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RemoveMemberContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                 "Removes the user from the guild __permanently__! You need to confirm your choice via button.\n"
                                 "If you wish to keep the user's stats but want to remove them from the guild then use the archive command.\n"
                                 "- archived members can be activated again\n\n"
                                 "Command example:\n- 5remove_member [example_name]\n- 5remove_member @example_name"
                                 "\n- 5remmem [example_name]\n- 5remmem @example_name")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## remove member\n\n{guild_description}"))

            class RemoveMemberView(discord.ui.LayoutView):
                container = RemoveMemberContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RemoveMemberView(), ephemeral=True)
            return True

    class ArchiveMember(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class ArchiveMemberContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "[same-same, but different](https://www.youtube.com/watch?v=7tTfL-DtpXk&ab_channel=BradGroux) to [remove_member] command\n"
                                     "Will remove the user from the guild but keep the users stats. The user can be activated again.\n\n"
                                     "Command example:\n- 5archive_member [example_name]\n- 5archive_member @example_name"
                                     "\n- 5archmem [example_name]\n- 5archmem @example_name")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## archive member\n\n{guild_description}"))

            class ArchiveMemberView(discord.ui.LayoutView):
                container = ArchiveMemberContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=ArchiveMemberView(), ephemeral=True)
            return True

    class ActivateMember(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class ActivateMemberContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "Activates the archived user and they will appear in the [clandonations] command again.\n\n"
                                     "Command example:\n- 5activate_member [example_name]\n- 5activate_member @example_name"
                                     "\n- 5actmem [example_name]\n- 5actmem @example_name")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## activate member\n\n{guild_description}"))

            class ActivateMemberView(discord.ui.LayoutView):
                container = ActivateMemberContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=ActivateMemberView(), ephemeral=True)
            return True

    class DonationThreshold(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class DonationThresholdContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "Sets the donation limit for the guild. Only numbers can be used and \"k\" as abbreviation does __not__ work currently.\n\n"
                                     "Command example:\n- 5donation_threshold 250000\n- 5dt 250000")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## donation threshold\n\n{guild_description}"))

            class DonationThresholdView(discord.ui.LayoutView):
                container = DonationThresholdContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=DonationThresholdView(), ephemeral=True)
            return True

    class ViewArchive(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class ViewArchiveContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "Shows the list of all users in the archive. If no one is found then \"No Members in archive found.\" will be shown.\n"
                                     "You don't need to type your anything else after the command.\n\n"
                                     "Command example:\n- 5view_archive\n- 5va")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## view archive\n\n{guild_description}"))

            class ViewArchiveView(discord.ui.LayoutView):
                container = ViewArchiveContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=ViewArchiveView(), ephemeral=True)
            return True

    class ClanDonations(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class ClanDonationsContainer(discord.ui.Container):
                guild_description = ("Shows all guild members donation status, the currently needed donation for the guild and \"if\" how much is missing.\n"
                                 "Using \"-old\" will show the last rotation. Works for both weekly and monthly.\n\n"
                                 "Command example:\n- 5clandonations\n- 5cd\n- 5clandonations -old\n- 5cd -old")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## clan donations\n\n{guild_description}"))

            class ClanDonationsView(discord.ui.LayoutView):
                container = ClanDonationsContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=ClanDonationsView(), ephemeral=True)
            return True

    class ClanDonationsTracker(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class ClanDonationsTrackerContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "Shows the own donation overview. Only usable on server where you are in the guild and are not archived!\n\n"
                                     "Command example:\n- 5clandonationstracker\n- 5cdt")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## clan donations tracker\n\n{guild_description}"))

            class ClanDonationsTrackerView(discord.ui.LayoutView):
                container = ClanDonationsTrackerContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=ClanDonationsTrackerView(), ephemeral=True)
            return True

    class GuildReset(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class GuildResetTrackerContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "Choose via buttons if you want the guild reset timing to be weekly or monthly. "
                                     "The command [clandonations] will change accordingly!\n\n"
                                     "Command example:\n- 5guild_reset\n- 5guildreset\n- 5gr")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## guild reset\n\n{guild_description}"))

            class GuildResetTrackerView(discord.ui.LayoutView):
                container = GuildResetTrackerContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=GuildResetTrackerView(), ephemeral=True)
            return True

    class GuildDonationsUser(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class GuildDonationsUserContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "Shows the donation overview of the specific user. The **Title** is the donation id."
                                     "The Donation ID is needed for the command [remove_donation] and [edit_donation].\n"
                                     "__the provided name for the search has to be the unique discord name__\n\n"
                                     "Command example:\n- 5guild_donations_for_user example_name\n- 5guilddonouser example_name\n- 5gdonouser example_name")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## guild donations user\n\n{guild_description}"))

            class GuildDonationsUserView(discord.ui.LayoutView):
                container = GuildDonationsUserContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=GuildDonationsUserView(), ephemeral=True)
            return True

    class AddDonation(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class AddDonationContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "Manually adds a donation to a given username. This command will only update the guild it is used in!\n"
                                     "First the username then the amount. The donation id is created automatically.\n\n"
                                     "Command example:\n- 5add_donation example_name 50k\n- 5add_donation example_name 50000\n- 5adddono example_name 50k\n- 5adddono example_name 50000")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## add donation\n\n{guild_description}"))

            class AddDonationView(discord.ui.LayoutView):
                container = AddDonationContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=AddDonationView(), ephemeral=True)
            return True

    class RemoveDonation(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class RemoveDonationContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "Removes a donation via the donation id. To get the donation id use the command [guild_donations_for_user].\n\n"
                                     "Command example:\n- 5remove_donation example_name1743863286\n- 5remdono example_name1743863286")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## remove donation\n\n{guild_description}"))

            class RemoveDonationView(discord.ui.LayoutView):
                container = RemoveDonationContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=RemoveDonationView(), ephemeral=True)
            return True

    class EditDonation(discord.ui.Button):
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                return False

            class EditDonationContainer(discord.ui.Container):
                guild_description = ("__This command is only accessible with admin permissions__!\n"
                                     "Edite a donation via the donation id. To get the donation id use the command [guild_donations_for_user].\n"
                                     "First the donation id then the new amount you wish to set.\n\n"
                                     "Command example:\n- 5edit_donation example_name1743863286 50k\n- 5edit_donation example_name1743863286 50000\n"
                                     "- 5editdono example_name1743863286 50k\n- 5editdono example_name1743863286 50000")
                guild_overview = discord.ui.Section(accessory=discord.ui.Thumbnail(media=discord.UnfurledMediaItem(url=f"{picture_caeser}"))).add_item(discord.ui.TextDisplay(f"## edit donation\n\n{guild_description}"))

            class EditDonationView(discord.ui.LayoutView):
                container = EditDonationContainer(id=1, accent_colour=0x5865F2)

            await interaction.followup.send(view=EditDonationView(), ephemeral=True)
            return True

    class MainPageContainer(discord.ui.Container):
        official_server = "https://discord.gg/EhdZtDsvtr"
        bot_invite = "https://discord.com/oauth2/authorize?client_id=1301954481851990037"
        dev_profile = "https://discord.com/users/274601299469795328"
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "prefixes.json")
        with open(path, "r") as f:
            prefixes = json.load(f)
        guild_id = str(ctx.guild.id)
        if guild_id in prefixes:
            current_prefix = prefixes[guild_id]
        else:
            current_prefix = "5"
        main_text = discord.ui.TextDisplay("Currently available command variants are:\n"
                                           "- prefix commands\n"
                                           f"-# triggered by a specific sign,letter or number. Current prefix is: ``{current_prefix}``\n"
                                           "- on_message commands\n"
                                           "-# triggered automatically by specific keywords in a message\n"
                                           "- slash commands\n"
                                           "-# triggerd by ``/``\n\n"
                                           "Click the button to see all available commands for the corresponding variant. "
                                           "Prefix & Slash commands are mostly the same.")
        button_rows1 = discord.ui.ActionRow(discord.ui.Button(label="All Prefix", style=discord.ButtonStyle.primary, custom_id="Prefix"),
                                            discord.ui.Button(label="All On_Message", style=discord.ButtonStyle.primary, custom_id="On_Message"),
                                            discord.ui.Button(label="All Slash", style=discord.ButtonStyle.primary, custom_id="Slash"),
                                            discord.ui.Button(label="Custom Guild", style=discord.ButtonStyle.primary, custom_id="Guild"))
        sep = discord.ui.Separator()
        perm_text = discord.ui.TextDisplay("The bot needs these permissions (or at least not being disabled) in the channel:\n"
                                           "- view channel\n"
                                           "- send messages\n"
                                           "- embed links\n"
                                           "- add reactions\n"
                                           "- manage messages\n"
                                           "- read message history")
        button_rows2 = discord.ui.ActionRow(discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="delete"))

    class PrefixContainer(discord.ui.Container):
        header = discord.ui.TextDisplay("# All Prefix Commands\n"
                                        "Click on the buttons to receive a detailed explanation of the command. All commands are in alphabetical order.")
        sep = discord.ui.Separator()
        section1 = discord.ui.Section(accessory=Compare(label='compare', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("1) compare\n-# compare up to 18 cards with each other"))
        section2 = discord.ui.Section(accessory=DailyWatch(label='daily watch', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("2) dailywatch / dw\n-# check the current daily price list"))
        section3 = discord.ui.Section(accessory=MarketDex(label='market dex', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("3) market dex / mdex\n-# overview of the cheapest last tracked card prices"))
        section4 = discord.ui.Section(accessory=RaidGuide(label='raid guide', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("4) raidguide\n-# quick information on raid comps"))
        section5 = discord.ui.Section(accessory=RaidHistory(label='raid history', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("5) raidhistory / rh\n-# view your logged raids"))
        section6 = discord.ui.Section(accessory=RaidLobby(label='raid search lobbies', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("6) raidlobbies / rl\n-# get an raid lobby filter"))
        section7 = discord.ui.Section(accessory=Rulesets(label='rulesets', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("7) rulesets\n-# codes to alter /dg battle"))
        sep2 = discord.ui.Separator()
        page = discord.ui.TextDisplay("-# Current Page: 1 / 2")
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="Main Page", style=discord.ButtonStyle.primary, custom_id="Main"),
                                           discord.ui.Button(label="Next", style=discord.ButtonStyle.primary, custom_id="Page 2"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="delete"))

    class Prefix2Container(discord.ui.Container):
        header = discord.ui.TextDisplay("# All Prefix Commands\n"
                                        "Click on the buttons to receive a detailed explanation of the command. All commands are in alphabetical order.")
        sep = discord.ui.Separator()
        section8 = discord.ui.Section(accessory=Settings(label='settings', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("8) settings\n-# toggle a variety of options on/off"))
        section9 = discord.ui.Section(accessory=SetPrefix(label='set prefix', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("9) setprefix\n-# change the prefix for the bot"))
        section10 = discord.ui.Section(accessory=SetFloor(label='set floor', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("10) setfloor / sfl\n-# setup your location and floor for the shardlist/soullist/floorlist command"))
        section11 = discord.ui.Section(accessory=SetLocation(label='set location ping', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("11) setlocation / sl\n-# enable location pings"))
        section12 = discord.ui.Section(accessory=ShardList(label='shard list', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("12) shardlist / soullist / floorlist\n-# shows the best value floor to farm"))
        section13 = discord.ui.Section(accessory=UpdatePlayer(label='update', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("13) update\n-# update / add yourself to database"))
        sep2 = discord.ui.Separator()
        page = discord.ui.TextDisplay("-# Current Page: 2 / 2")
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="Main Page", style=discord.ButtonStyle.primary, custom_id="Main"),
                                           discord.ui.Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="Page 1"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="delete"))

    class On_MessageContainer(discord.ui.Container):
        header = discord.ui.TextDisplay("# All On_Message Commands\n"
                                        "Click on the buttons to receive a detailed explanation of the command. All commands are in alphabetical order.")
        sep = discord.ui.Separator()
        section1 = discord.ui.Section(accessory=GoldOverview(label='better gold overview', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("1) better gold overview"))
        section2 = discord.ui.Section(accessory=RubiesOverview(label='better rubies overview', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("2) better rubies overview"))
        section3 = discord.ui.Section(accessory=StaminaOverview(label='better stamina overview', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("3) better stamina overview"))
        section4 = discord.ui.Section(accessory=HelperSelling(label='helper for selling', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("4) helper for selling"))
        section5 = discord.ui.Section(accessory=HelperBuying(label='helper for buying', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("5) helper for buying"))
        section6 = discord.ui.Section(accessory=HelperBuilding(label='helper for evolution', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("6) helper for evo"))
        section7 = discord.ui.Section(accessory=ImpCardInfo(label='improved card info', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("7) improved card info"))
        sep2 = discord.ui.Separator()
        page = discord.ui.TextDisplay("-# Current Page: 1 / 2")
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="Main Page", style=discord.ButtonStyle.primary, custom_id="Main"),
                                           discord.ui.Button(label="Next", style=discord.ButtonStyle.primary, custom_id="Page 2"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="delete"))

    class On_Message2Container(discord.ui.Container):
        header = discord.ui.TextDisplay("# All On_Message Commands\n"
                                        "Click on the buttons to receive a detailed explanation of the command. All commands are in alphabetical order.")
        sep = discord.ui.Separator()
        section8 = discord.ui.Section(accessory=ImpClanShop(label='improved clan shop', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("8) improved clan shop"))
        section9 = discord.ui.Section(accessory=LocationTime(label='location time overview', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("9) location time overview"))
        section10 = discord.ui.Section(accessory=PackValue(label='pack opening value', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("10) pack opening value"))
        section11 = discord.ui.Section(accessory=RaidHistoryTracking(label='raid history tracking', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("11) raid history tracking"))
        section12 = discord.ui.Section(accessory=RaidLobbyInvite(label='raid lobby invite room', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("12) raid lobby invite room"))
        section13 = discord.ui.Section(accessory=RaidLobbyInRaid(label='raid lobby in raid', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("13) raid lobby in raid"))
        section14 = discord.ui.Section(accessory=RaidSearchSpam(label='raid search spam', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("14) raid search spam"))
        sep2 = discord.ui.Separator()
        page = discord.ui.TextDisplay("-# Current Page: 2 / 2")
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="Main Page", style=discord.ButtonStyle.primary, custom_id="Main"),
                                           discord.ui.Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="Page 1"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="delete"))

    class SlashContainer(discord.ui.Container):
        header = discord.ui.TextDisplay("# All Slash Commands\n"
                                        "Click on the buttons to receive a detailed explanation of the command. All commands are in alphabetical order.")
        sep = discord.ui.Separator()
        section1 = discord.ui.Section(accessory=CompareSlash(label='compare', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("1) compare\n-# compare up to 18 cards with each other"))
        section2 = discord.ui.Section(accessory=DailyWatchSlash(label='daily watch', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("2) dailywatch / dw\n-# check the current daily price list"))
        section3 = discord.ui.Section(accessory=MarketDexSlash(label='market dex', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("3) market dex / mdex\n-# overview of the cheapest last tracked card prices"))
        section4 = discord.ui.Section(accessory=RaidGuideSlash(label='raid guide', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("4) raidguide\n-# quick information on raid comps"))
        section5 = discord.ui.Section(accessory=RaidHistorySlash(label='raid history', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("5) raidhistory / rh\n-# view your logged raids"))
        section6 = discord.ui.Section(accessory=RaidLobbySlash(label='raid search lobbies', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("6) raidlobbies / rl\n-# get an raid lobby filter"))
        section7 = discord.ui.Section(accessory=RulesetsSlash(label='rulesets', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("7) rulesets\n-# codes to alter /dg battle"))
        sep2 = discord.ui.Separator()
        page = discord.ui.TextDisplay("-# Current Page: 1 / 2")
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="Main Page", style=discord.ButtonStyle.primary, custom_id="Main"),
                                           discord.ui.Button(label="Next", style=discord.ButtonStyle.primary, custom_id="Page 2"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="delete"))

    class Slash2Container(discord.ui.Container):
        header = discord.ui.TextDisplay("# All Slash Commands\n"
                                        "Click on the buttons to receive a detailed explanation of the command. All commands are in alphabetical order.")
        sep = discord.ui.Separator()
        section8 = discord.ui.Section(accessory=SettingsSlash(label='settings', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("8) settings\n-# toggle a variety of options on/off"))
        section9 = discord.ui.Section(accessory=SetFloorSlash(label='set floor', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("9) setfloor / sfl\n-# setup your location and floor for the shardlist/soullist/floorlist command"))
        section10 = discord.ui.Section(accessory=SetLocationSlash(label='set location ping', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("10) setlocation / sl\n-# enable location pings"))
        section11 = discord.ui.Section(accessory=ShardListSlash(label='shard list', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("11) shardlist / soullist / floorlist\n-# shows the best value floor to farm"))
        section12 = discord.ui.Section(accessory=UpdatePlayerSlash(label='update', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("12) update\n-# update / add yourself to database"))
        sep2 = discord.ui.Separator()
        page = discord.ui.TextDisplay("-# Current Page: 2 / 2")
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="Main Page", style=discord.ButtonStyle.primary, custom_id="Main"),
                                           discord.ui.Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="Page 1"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="delete"))

    class CustomGuildContainer(discord.ui.Container):
        header = discord.ui.TextDisplay("# All Custom Guild Commands\n"
                                        "Click on the buttons to receive an explanation of the command. The commands will be reworked soon and therefor not be to detailed.\n"
                                        "Every command has a prefix and a slash version, the slash command is recommended to use.")
        sep = discord.ui.Separator()
        section1 = discord.ui.Section(accessory=CreateGuild(label='create guild', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("1) create guild"))
        section2 = discord.ui.Section(accessory=DeleteGuild(label='delete guild', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("2) delete guild"))
        section3 = discord.ui.Section(accessory=AddMember(label='add member', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("3) add member"))
        section4 = discord.ui.Section(accessory=RemoveMember(label='remove member', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("4) remove member"))
        section5 = discord.ui.Section(accessory=ArchiveMember(label='archive member', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("5) archive member"))
        section6 = discord.ui.Section(accessory=ActivateMember(label='activate member', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("6) activate member"))
        section7 = discord.ui.Section(accessory=DonationThreshold(label='donation threshold', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("7) donation threshold"))
        section8 = discord.ui.Section(accessory=ViewArchive(label='view archive', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("8) view archive"))
        sep2 = discord.ui.Separator()
        page = discord.ui.TextDisplay("-# Current Page: 1 / 2")
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="Main Page", style=discord.ButtonStyle.primary, custom_id="Main"),
                                           discord.ui.Button(label="Next", style=discord.ButtonStyle.primary, custom_id="Page 2"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="delete"))

    class CustomGuild2Container(discord.ui.Container):
        header = discord.ui.TextDisplay("# All Custom Guild Commands\n"
                                        "Click on the buttons to receive an explanation of the command. The commands will be reworked soon and therefor not be to detailed.\n"
                                        "Every command has a prefix and a slash version, the slash command is recommended to use.")
        sep = discord.ui.Separator()
        section9 = discord.ui.Section(accessory=ClanDonations(label='clan donations', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("9) clan donations"))
        section10 = discord.ui.Section(accessory=ClanDonationsTracker(label='clan donations tracker', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("10) clan donations tracker"))
        section11 = discord.ui.Section(accessory=GuildReset(label='guild reset', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("11) guild reset"))
        section12 = discord.ui.Section(accessory=GuildDonationsUser(label='guild donations for user', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("12) guild donations for user"))
        section13 = discord.ui.Section(accessory=AddDonation(label='add donation', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("13) add donation"))
        section14 = discord.ui.Section(accessory=RemoveDonation(label='remove donation', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("14) remove donation"))
        section15 = discord.ui.Section(accessory=EditDonation(label='edit donation', style=discord.ButtonStyle.secondary)).add_item(discord.ui.TextDisplay("15) edit donation"))
        sep2 = discord.ui.Separator()
        page = discord.ui.TextDisplay("-# Current Page: 2 / 2")
        button_rows = discord.ui.ActionRow(discord.ui.Button(label="Main Page", style=discord.ButtonStyle.primary, custom_id="Main"),
                                           discord.ui.Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="Page 1"),
                                           discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="delete"))

    class MainPageView(discord.ui.LayoutView):
        container = MainPageContainer(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction):
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                await interaction.response.defer(ephemeral=True)
                return False
            button_id = interaction.data.get("custom_id")
            if button_id == "Prefix":
                await interaction.response.edit_message(view=PrefixView())
            elif button_id == "On_Message":
                await interaction.response.edit_message(view=On_MessageView())
            elif button_id == "Slash":
                await interaction.response.edit_message(view=SlashView())
            elif button_id == "Guild":
                await interaction.response.edit_message(view=CustomGuildView())
            elif button_id == "delete":
                await interaction.message.delete()
            return True

    class PrefixView(discord.ui.LayoutView):
        container = PrefixContainer(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction):
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                await interaction.response.defer(ephemeral=True)
                return False
            button_id = interaction.data.get("custom_id")
            if button_id == "Main":
                await interaction.response.edit_message(view=MainPageView())
            elif button_id == "Page 2":
                await interaction.response.edit_message(view=PrefixView2())
            elif button_id == "delete":
                await interaction.message.delete()
            return True

    class PrefixView2(discord.ui.LayoutView):
        container = Prefix2Container(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction):
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                await interaction.response.defer(ephemeral=True)
                return False
            button_id = interaction.data.get("custom_id")
            if button_id == "Main":
                await interaction.response.edit_message(view=MainPageView())
            elif button_id == "Page 1":
                await interaction.response.edit_message(view=PrefixView())
            elif button_id == "delete":
                await interaction.message.delete()
            return True

    class On_MessageView(discord.ui.LayoutView):
        container = On_MessageContainer(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction):
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                await interaction.response.defer(ephemeral=True)
                return False
            button_id = interaction.data.get("custom_id")
            if button_id == "Main":
                await interaction.response.edit_message(view=MainPageView())
            elif button_id == "Page 2":
                await interaction.response.edit_message(view=On_MessageView2())
            elif button_id == "delete":
                await interaction.message.delete()
            return True

    class On_MessageView2(discord.ui.LayoutView):
        container = On_Message2Container(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction):
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                await interaction.response.defer(ephemeral=True)
                return False
            button_id = interaction.data.get("custom_id")
            if button_id == "Main":
                await interaction.response.edit_message(view=MainPageView())
            elif button_id == "Page 1":
                await interaction.response.edit_message(view=On_MessageView())
            elif button_id == "delete":
                await interaction.message.delete()
            return True

    class SlashView(discord.ui.LayoutView):
        container = SlashContainer(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction):
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                await interaction.response.defer(ephemeral=True)
                return False
            button_id = interaction.data.get("custom_id")
            if button_id == "Main":
                await interaction.response.edit_message(view=MainPageView())
            elif button_id == "Page 2":
                await interaction.response.edit_message(view=SlashView2())
            elif button_id == "delete":
                await interaction.message.delete()
            return True

    class SlashView2(discord.ui.LayoutView):
        container = Slash2Container(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction):
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                await interaction.response.defer(ephemeral=True)
                return False
            button_id = interaction.data.get("custom_id")
            if button_id == "Main":
                await interaction.response.edit_message(view=MainPageView())
            elif button_id == "Page 1":
                await interaction.response.edit_message(view=SlashView())
            elif button_id == "delete":
                await interaction.message.delete()
            return True

    class CustomGuildView(discord.ui.LayoutView):
        container = CustomGuildContainer(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction):
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                await interaction.response.defer(ephemeral=True)
                return False
            button_id = interaction.data.get("custom_id")
            if button_id == "Main":
                await interaction.response.edit_message(view=MainPageView())
            elif button_id == "Page 2":
                await interaction.response.edit_message(view=CustomGuildView2())
            elif button_id == "delete":
                await interaction.message.delete()
            return True

    class CustomGuildView2(discord.ui.LayoutView):
        container = CustomGuild2Container(id=1, accent_colour=0x71368A)

        async def interaction_check(self, interaction: discord.Interaction):
            if slash:
                user = interaction.user.id
            else:
                user = ctx.author.id
            if interaction.user.id != user:
                await interaction.response.defer(ephemeral=True)
                return False
            button_id = interaction.data.get("custom_id")
            if button_id == "Main":
                await interaction.response.edit_message(view=MainPageView())
            elif button_id == "Page 1":
                await interaction.response.edit_message(view=CustomGuildView())
            elif button_id == "delete":
                await interaction.message.delete()
            return True

    view = MainPageView()
    return view

