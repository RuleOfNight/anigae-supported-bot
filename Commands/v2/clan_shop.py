import discord
from discord import MediaGalleryItem
from Commands import definitions
from Commands.user_commands_on_message import rubies_emote, gold_emote
from Commands.v2.utils import picture_caeser
from db_methods import cards
from misc import time_calculations
from datetime import timezone, datetime


async def v2_improved_clan_shop(message):
    """Parse clan shop message và gửi lại phiên bản cải tiến có thêm emote element/talent và lịch cycle."""
    await time_calculations.update_counter()
    clan_shop_series_data = await cards.get_card_data_by_series_name()
    base_saturday, base_monday = await time_calculations.get_next_saturday_and_monday_unix()
    cl_shop_start = await time_calculations.get_clan_shop_start_time()
    week_seconds = 7 * 24 * 60 * 60
    total_cards = len(clan_shop_series_data)

    # Tính thời gian xuất hiện của từng card trong 2 cycle
    card_data = []
    for index, card in enumerate(clan_shop_series_data):
        offset = index * week_seconds
        c2_offset = (index + total_cards) * week_seconds
        card_element = await definitions.element_converter_from_database(card['card_element'])
        card_talent = await definitions.skill_converter_from_database(card['card_talent'])
        card_data.append({
            "card_name":        card["card_name"],
            "card_element":     card_element,
            "card_talent":      card_talent,
            "cycle_1_saturday": base_saturday + offset,
            "cycle_1_monday":   base_monday + offset,
            "cycle_2_saturday": base_saturday + c2_offset,
            "cycle_2_monday":   base_monday + c2_offset,
        })

    # Parse các text section từ message gốc
    placeholder_header = placeholder_common = placeholder_uncommon = ""
    placeholder_rare = placeholder_superrare = placeholder_ultrarare = ""
    super_rare = ultra_rare = False
    clan_shop_picture = picture_caeser

    for component in message.components:
        if hasattr(component, "children"):
            for child in component.children:
                if hasattr(child, "children"):
                    for subchild in child.children:
                        if not hasattr(subchild, "content"):
                            continue
                        c = subchild.content
                        if "Clan Shop" in c:
                            placeholder_header = c.replace("Clan Shop", "Improved Clan Shop")
                        elif "__Common__" in c:
                            placeholder_common = c.replace("**500** Rubies", f"**500** {rubies_emote} | **2,500** {gold_emote}")
                        elif "__Uncommon__" in c:
                            placeholder_uncommon = c.replace("**1,000** Rubies", f"**1,000** {rubies_emote} | **5,000** {gold_emote}")
                        elif "__Rare__" in c:
                            placeholder_rare = c.replace("**2,000** Rubies", f"**2,000** {rubies_emote} | **10,000** {gold_emote}")
                        elif "__Super Rare__" in c:
                            placeholder_superrare = c.replace("**20,000** Rubies", f"**20,000** {rubies_emote} | **100,000** {gold_emote}")
                            super_rare = True
                            placeholder_ultrarare = ""
                        elif "__Ultra Rare__" in c:
                            placeholder_ultrarare = c.replace("**200,000** Rubies", f"**200,000** {rubies_emote} | **1,000,000** {gold_emote}")
                            ultra_rare = True
                            placeholder_superrare = ""
                if hasattr(child, "items"):
                    for item in child.items:
                        if hasattr(item, "media") and hasattr(item.media, "url"):
                            clan_shop_picture = item.media.url

    # Thêm emote element + talent vào tên card trong từng section
    placeholders = [placeholder_common, placeholder_uncommon, placeholder_rare, placeholder_superrare, placeholder_ultrarare]
    for card in card_data:
        suffix = f"{card['card_name']} {card['card_element']} {card['card_talent']}"
        placeholders = [p.replace(card["card_name"], suffix) if card["card_name"] in p else p for p in placeholders]
    placeholder_common, placeholder_uncommon, placeholder_rare, placeholder_superrare, placeholder_ultrarare = placeholders

    # Tính text "next UR in rotation"
    now = datetime.now(timezone.utc).timestamp()
    next_cl_shop_char = await time_calculations.get_next_cl_shop_character()
    cycle1_end = base_monday + ((total_cards - 2) * week_seconds)
    cycle2_end = cl_shop_start + (2 * total_cards * week_seconds)
    next_card_text = ""
    for card in card_data:
        if card["card_name"] != next_cl_shop_char:
            continue
        if cl_shop_start <= now < cycle1_end:
            next_card_text = (f"**Next UR in Rotation:**\n"
                              f"**{card['card_name']}** {card['card_element']} {card['card_talent']}\n"
                              f"Start **[**<t:{int(card['cycle_1_saturday'])}:R>**]** - End **[**<t:{int(card['cycle_1_monday'])}:R>**]**")
        elif cycle1_end <= now < cycle2_end:
            next_card_text = (f"**Next UR in Rotation:**\n"
                              f"**{card['card_name']}** {card['card_element']} {card['card_talent']}\n"
                              f"Start **[**<t:{int(card['cycle_2_saturday'])}:R>**]** - End **[**<t:{int(card['cycle_2_monday'])}:R>**]**")
        else:
            next_card_text = "Clan Shop finished the 2nd cycle and therefor waiting for the next shop to release."
        break

    # ---- Inner UI classes (dependen vào biến cục bộ đã tính bên trên) ----

    _BANNER = "https://cdn.discordapp.com/attachments/790277741642776598/1376101487553544304/oie_YUqPXdSd03Y4.png"
    _BUTTONS = discord.ui.ActionRow(
        discord.ui.Button(label="Main",    style=discord.ButtonStyle.primary,   custom_id="Main"),
        discord.ui.Button(label="Cycle 1", style=discord.ButtonStyle.secondary, custom_id="Cycle 1"),
        discord.ui.Button(label="Cycle 2", style=discord.ButtonStyle.secondary, custom_id="Cycle 2"),
        discord.ui.Button(label="🗑️",      style=discord.ButtonStyle.danger,    custom_id="Delete"),
    )

    class ClanShopContainer(discord.ui.Container):
        thumbnail    = discord.ui.Section(discord.ui.TextDisplay(placeholder_header), accessory=discord.ui.Thumbnail(media=picture_caeser))
        text_common  = discord.ui.TextDisplay(placeholder_common)
        sep1         = discord.ui.Separator()
        text_uncommon = discord.ui.TextDisplay(placeholder_uncommon)
        sep2         = discord.ui.Separator()
        text_rare    = discord.ui.TextDisplay(placeholder_rare)
        sep3         = discord.ui.Separator()
        if super_rare:
            text_rarity = discord.ui.TextDisplay(placeholder_superrare)
        elif ultra_rare:
            text_rarity = discord.ui.TextDisplay(placeholder_ultrarare)
        sep4         = discord.ui.Separator()
        gallery      = discord.ui.MediaGallery(MediaGalleryItem(media=clan_shop_picture, description="cl shop picture", spoiler=False))
        text_next_ur = discord.ui.TextDisplay(next_card_text)
        button_rows  = discord.ui.ActionRow(
            discord.ui.Button(label="Main",    style=discord.ButtonStyle.primary,   custom_id="Main"),
            discord.ui.Button(label="Cycle 1", style=discord.ButtonStyle.secondary, custom_id="Cycle 1"),
            discord.ui.Button(label="Cycle 2", style=discord.ButtonStyle.secondary, custom_id="Cycle 2"),
            discord.ui.Button(label="🗑️",      style=discord.ButtonStyle.danger,    custom_id="Delete"),
        )

    def _cycle_text(cycle_key):
        return "\n\n".join(
            f"{c['card_name']} {c['card_element']} {c['card_talent']}\n"
            f"Start: <t:{int(c[f'cycle_{cycle_key}_saturday'])}:f> [ <t:{int(c[f'cycle_{cycle_key}_saturday'])}:R> ]\n"
            f"End: <t:{int(c[f'cycle_{cycle_key}_monday'])}:f> [ <t:{int(c[f'cycle_{cycle_key}_monday'])}:R> ]"
            for c in card_data
        )

    class ClanShopContainerCycle1(discord.ui.Container):
        header      = discord.ui.TextDisplay("## Clan Shop Cards Cycle 1")
        text        = discord.ui.TextDisplay(_cycle_text("1"))
        button_rows = discord.ui.ActionRow(
            discord.ui.Button(label="Main",    style=discord.ButtonStyle.primary,   custom_id="Main"),
            discord.ui.Button(label="Cycle 1", style=discord.ButtonStyle.secondary, custom_id="Cycle 1"),
            discord.ui.Button(label="Cycle 2", style=discord.ButtonStyle.secondary, custom_id="Cycle 2"),
            discord.ui.Button(label="🗑️",      style=discord.ButtonStyle.danger,    custom_id="Delete"),
        )

    class ClanShopContainerCycle2(discord.ui.Container):
        header      = discord.ui.TextDisplay("## Clan Shop Cards Cycle 2")
        text        = discord.ui.TextDisplay(_cycle_text("2"))
        button_rows = discord.ui.ActionRow(
            discord.ui.Button(label="Main",    style=discord.ButtonStyle.primary,   custom_id="Main"),
            discord.ui.Button(label="Cycle 1", style=discord.ButtonStyle.secondary, custom_id="Cycle 1"),
            discord.ui.Button(label="Cycle 2", style=discord.ButtonStyle.secondary, custom_id="Cycle 2"),
            discord.ui.Button(label="🗑️",      style=discord.ButtonStyle.danger,    custom_id="Delete"),
        )

    async def _handle_nav(interaction: discord.Interaction, view_class):
        cid = interaction.data.get("custom_id")
        if cid == "Main":
            await interaction.response.edit_message(view=ClanShopView())
        elif cid == "Cycle 1":
            await interaction.response.edit_message(view=ClanShopViewCycle1())
        elif cid == "Cycle 2":
            await interaction.response.edit_message(view=ClanShopViewCycle2())
        elif cid == "Delete":
            await interaction.message.delete()

    class ClanShopView(discord.ui.LayoutView):
        container = ClanShopContainer(id=1, accent_colour=0x71368A)
        async def interaction_check(self, interaction):
            await _handle_nav(interaction, ClanShopView)
            return True

    class ClanShopViewCycle1(discord.ui.LayoutView):
        container = ClanShopContainerCycle1(id=1, accent_colour=0x71368A)
        async def interaction_check(self, interaction):
            await _handle_nav(interaction, ClanShopViewCycle1)
            return True

    class ClanShopViewCycle2(discord.ui.LayoutView):
        container = ClanShopContainerCycle2(id=1, accent_colour=0x71368A)
        async def interaction_check(self, interaction):
            await _handle_nav(interaction, ClanShopViewCycle2)
            return True

    await message.channel.send(view=ClanShopView())
