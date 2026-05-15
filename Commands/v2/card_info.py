import re
import time
import discord
from discord import MediaGalleryItem
from Commands import definitions
from Commands.v2.utils import picture_caeser, normalize_picture_url
from db_methods import cards, general, players
from math import floor, ceil
import runtime


# ---------------------------------------------------------------------------
# Lookup tables — thay thế các if/elif dài trong callbacks
# ---------------------------------------------------------------------------

# Rarity → (card_rarity_str, evo_ur, asc_ur, evo_sr, asc_sr)
# None = không thay đổi giá trị hiện tại
_RARITY_CONFIG = {
    "UR A5": ("Ultra Rare", 3, 5, None, None),
    "UR A4": ("Ultra Rare", 3, 4, None, None),
    "UR A3": ("Ultra Rare", 3, 3, None, None),
    "UR A2": ("Ultra Rare", 3, 2, None, None),
    "UR A1": ("Ultra Rare", 3, 1, None, None),
    "UR E3": ("Ultra Rare", 3, 0, None, None),
    "UR E2": ("Ultra Rare", 2, 0, None, None),
    "UR E1": ("Ultra Rare", 1, 0, None, None),
    "SR A4": ("Super Rare", None, None, 3, 4),
    "SR A3": ("Super Rare", None, None, 3, 3),
    "SR A2": ("Super Rare", None, None, 3, 2),
    "SR A1": ("Super Rare", None, None, 3, 1),
    "SR E3": ("Super Rare", None, None, 3, 0),
    "SR E2": ("Super Rare", None, None, 2, 0),
    "SR E1": ("Super Rare", None, None, 1, 0),
}

# Clan level → stat bonus (%)
_CLAN_LEVEL_BONUS = {str(i): i + 5 for i in range(1, 16)}
_CLAN_LEVEL_BONUS["0"] = 0

# Familiarity/Holo → (bonus_value, display_name)
_FAM_CONFIG = {
    "fam 1": (2,  "F1"),
    "fam 2": (4,  "F2"),
    "fam 3": (6,  "F3"),
    "holo":  (12, "H1"),
    "fam 0": (0,  "F0"),
}

# Shared SelectOption lists (dùng chung cho Container1 và Container2)
_RARITY_OPTIONS = [
    discord.SelectOption(label="UR A5", value="UR A5"),
    discord.SelectOption(label="UR A4", value="UR A4"),
    discord.SelectOption(label="UR A3", value="UR A3"),
    discord.SelectOption(label="UR A2", value="UR A2"),
    discord.SelectOption(label="UR A1", value="UR A1"),
    discord.SelectOption(label="UR E3", value="UR E3"),
    discord.SelectOption(label="UR E2", value="UR E2"),
    discord.SelectOption(label="UR E1", value="UR E1"),
    discord.SelectOption(label="SR A4", value="SR A4"),
    discord.SelectOption(label="SR A3", value="SR A3"),
    discord.SelectOption(label="SR A2", value="SR A2"),
    discord.SelectOption(label="SR A1", value="SR A1"),
    discord.SelectOption(label="SR E3", value="SR E3"),
    discord.SelectOption(label="SR E2", value="SR E2"),
    discord.SelectOption(label="SR E1", value="SR E1"),
    discord.SelectOption(label="Base",  value="Base"),
]

_CLAN_OPTIONS = [
    discord.SelectOption(label="All Stats",   value="all stats"),
    discord.SelectOption(label="Adjust HP",   value="clan hp"),
    discord.SelectOption(label="Adjust ATK",  value="clan atk"),
    discord.SelectOption(label="Adjust DEF",  value="clan def"),
    discord.SelectOption(label="Adjust SPD",  value="clan spd"),
    discord.SelectOption(label="0 - No Clan", value="0"),
    *[discord.SelectOption(label=str(i), value=str(i)) for i in range(1, 16)],
]

_FAM_OPTIONS = [
    discord.SelectOption(label="Fam 0", value="fam 0"),
    discord.SelectOption(label="Fam 1", value="fam 1"),
    discord.SelectOption(label="Fam 2", value="fam 2"),
    discord.SelectOption(label="Fam 3", value="fam 3"),
    discord.SelectOption(label="Holo",  value="holo"),
]


# ---------------------------------------------------------------------------
# UI Container classes (module-level để tránh re-define mỗi lần call)
# ---------------------------------------------------------------------------

class CardInfoContainer1(discord.ui.Container):
    """Layout có gallery ảnh lớn phía dưới."""
    thumbnail   = discord.ui.Section(discord.ui.TextDisplay("card data"), accessory=discord.ui.Thumbnail(media=picture_caeser))
    sep         = discord.ui.Separator()
    card_stats  = discord.ui.TextDisplay("card stats")
    card_talent = discord.ui.TextDisplay("card talent")
    sep2        = discord.ui.Separator()
    card_picture = discord.ui.MediaGallery(MediaGalleryItem(media=picture_caeser, spoiler=False))
    sep3        = discord.ui.Separator()
    rarity_row  = discord.ui.ActionRow(discord.ui.Select(placeholder="Select the rarity / ascension level.", min_values=1, max_values=1, options=_RARITY_OPTIONS, custom_id="rarity_row"))
    clan_row    = discord.ui.ActionRow(discord.ui.Select(placeholder="Select clan level & stat to adjust.",  min_values=1, max_values=1, options=_CLAN_OPTIONS,   custom_id="clan_row"))
    fam_row     = discord.ui.ActionRow(discord.ui.Select(placeholder="Select fam / holo level.",            min_values=1, max_values=1, options=_FAM_OPTIONS,    custom_id="holo_row"))
    del_row     = discord.ui.ActionRow(discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="Delete"))


class CardInfoContainer2(discord.ui.Container):
    """Layout có thumbnail nhỏ bên phải."""
    thumbnail   = discord.ui.Section(discord.ui.TextDisplay("card data"), accessory=discord.ui.Thumbnail(media=picture_caeser))
    sep         = discord.ui.Separator()
    card_stats  = discord.ui.TextDisplay("card stats")
    card_talent = discord.ui.TextDisplay("card talent")
    sep2        = discord.ui.Separator()
    rarity_row  = discord.ui.ActionRow(discord.ui.Select(placeholder="Select the rarity / ascension level.", min_values=1, max_values=1, options=_RARITY_OPTIONS, custom_id="rarity_row"))
    clan_row    = discord.ui.ActionRow(discord.ui.Select(placeholder="Select clan level & stat to adjust.",  min_values=1, max_values=1, options=_CLAN_OPTIONS,   custom_id="clan_row"))
    fam_row     = discord.ui.ActionRow(discord.ui.Select(placeholder="Select fam / holo level.",            min_values=1, max_values=1, options=_FAM_OPTIONS,    custom_id="holo_row"))
    del_row     = discord.ui.ActionRow(discord.ui.Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="Delete"))


class CardInfoView(discord.ui.LayoutView):
    async def on_timeout(self):
        for child in self.children:
            for subchild in child.children:
                if isinstance(subchild, discord.ui.ActionRow):
                    for item in subchild.children:
                        item.disabled = True
        try:
            if hasattr(self, "message"):
                await self.message.edit(view=self)
        except Exception:
            pass
        self.stop()


# ---------------------------------------------------------------------------
# Helpers nội bộ
# ---------------------------------------------------------------------------

def _resolve_evo_asc(card_rarity, evolution_ur, ur_asc_lvl, evolution_sr, sr_asc_lvl):
    """Trả về (evolution, ascension) tương ứng với rarity hiện tại."""
    if card_rarity == "Ultra Rare":
        return evolution_ur, ur_asc_lvl
    if card_rarity == "Super Rare":
        return evolution_sr, sr_asc_lvl
    return 1, 0


def _format_stats_content(rarity_name, fam_name, hp, atk, def_, spd, c_hp, c_atk, c_def, c_spd, compact):
    if compact:
        return (f"**__{rarity_name} {fam_name}__**\n"
                f"**HP:** {hp} (+{c_hp}%) **|** **ATK:** {atk} (+{c_atk}%) **|** "
                f"**DEF:** {def_} (+{c_def}%) **|** **SPD:** {spd} (+{c_spd}%)")
    return (f"**__{rarity_name} {fam_name}__**\n"
            f"**HP:** {hp} (+{c_hp}%)\n**ATK:** {atk} (+{c_atk}%)\n"
            f"**DEF:** {def_} (+{c_def}%)\n**SPD:** {spd} (+{c_spd}%)")


def _format_talent_content(card_rarity, talent_emote, talent_name, talent_sr, talent_ur, talent_base):
    if card_rarity == "Super Rare":
        return f"**__Talent__**\n{talent_emote} **{talent_name}:** {talent_sr}"
    if card_rarity == "Ultra Rare":
        return f"**__Talent__**\n{talent_emote} **{talent_name}:** {talent_ur}"
    return f"**Talent**\n{talent_emote} **{talent_name}:** {talent_base}"


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

async def v2_improved_card_info(message):
    """Parse cinfo message của bot và gửi lại embed tương tác với stat calculator."""

    # --- Parse dữ liệu từ các component ---
    card_name = card_id = card_series = card_loc = card_floor = ""
    card_amount_sr = card_amount_ur = card_element = ""
    card_hp = card_atk = card_def = card_speed = ""
    card_info_picture = picture_caeser
    next_daily = "not available"
    floor_1 = floor_2 = floor_3 = ""

    for component in message.components:
        if not hasattr(component, "children"):
            continue
        for child in component.children:
            if hasattr(child, "children"):
                for subchild in child.children:
                    if not hasattr(subchild, "content"):
                        continue
                    m = re.search(
                        r"## \*\*(.*)\*\*\n\n"
                        r"\*\*Card ID:\*\*\s*(\d+)\n"
                        r"\*\*Card Series:\*\*\s*(.*)\n"
                        r"\*\*Location/Floor:\*\*\s*(None|(\d+)\s*\|\s*(\d+),\s*(\d+),\s*(\d+))\n"
                        r"\*\*Copies In Existence \(SR/UR\):\*\*\s*(\d+)\s*\|\s*(\d+)\n"
                        r"\*\*Type:\*\*\s*(.*?)\n"
                        r"\*\*HP:\*\*\s*(\d+)\n"
                        r"\*\*ATK:\*\*\s*(\d+)\n"
                        r"\*\*DEF:\*\*\s*(\d+)\n"
                        r"\*\*SPEED:\*\*\s*(\d+)", subchild.content)
                    if not m:
                        continue
                    card_name       = m.group(1)
                    card_id         = m.group(2)
                    card_series     = m.group(3)
                    card_amount_sr  = m.group(9)
                    card_amount_ur  = m.group(10)
                    card_element    = re.search(r"(\w+)", m.group(11)).group(1)
                    card_hp         = m.group(12)
                    card_atk        = m.group(13)
                    card_def        = m.group(14)
                    card_speed      = m.group(15)

                    if m.group(4) == "None":
                        card_loc = "None"
                        event_cards = await runtime.retrieve_data("event cards")
                        if card_name in event_cards.get("clan_shop", []):
                            card_floor = "Clan Shop"
                        elif card_name in event_cards.get("monthly_vote", []):
                            card_floor = "Monthly Vote"
                        elif card_name in event_cards.get("event", []):
                            card_floor = "Event"
                        else:
                            card_floor = "None"
                    else:
                        card_loc = m.group(5)
                        floor_1, floor_2, floor_3 = m.group(6), m.group(7), m.group(8)
                        card_floor = ", ".join((floor_1, floor_2, floor_3))
                        locations = await runtime.retrieve_data("locations")
                        total_locations = len(locations)
                        current_counter = await general.get_daily_watch_counter()
                        loc_index = next((int(i) for i, name in locations.items() if name.lower() == card_series.lower()), None)
                        print(f"[CINFO DEBUG] card_series={card_series!r} loc_index={loc_index} current_counter={current_counter}")
                        if loc_index is not None and current_counter is not None:
                            relative_offset = (loc_index - current_counter - 1) % total_locations
                            daily_watch_tick = 43200
                            base_tick = await general.get_global_daily_watch_timer()
                            print(f"[CINFO DEBUG] base_tick={base_tick} relative_offset={relative_offset}")
                            if base_tick is not None:
                                now = int(time.time())
                                while base_tick <= now:
                                    base_tick += daily_watch_tick
                                ts = base_tick + (relative_offset * daily_watch_tick)
                                next_daily = f"<t:{ts}:d> <t:{ts}:R>"

            if hasattr(child, "items"):
                for item in child.items:
                    if hasattr(item, "media") and hasattr(item.media, "url"):
                        card_info_picture = item.media.url

            if hasattr(child, "content") and "**Talent**" in child.content:
                talent_name_m    = re.search(r">\s\*\*(.*)\*\*\s?(?:\[PSV])?:", child.content)
                talent_desc_m    = re.search(r"\*\*\s?(?:\[PSV])?:\s?(.*)\*\*", child.content)
                card_talent_name = talent_name_m
                card_talent_description = talent_desc_m
                card_talent_emote = await definitions.skill_converter_from_database(talent_name_m.group(1))
                card_talent_text_sr = re.sub(r"__(\d+)__", lambda m2: f"__{floor(int(m2.group(1)) * 1.8)}__", talent_desc_m.group(1))
                card_talent_text_ur = re.sub(r"__(\d+)__", lambda m2: f"__{floor(int(m2.group(1)) * 2)}__",   talent_desc_m.group(1))

    ele_emote = await definitions.element_converter_from_database(card_element)

    # --- Lấy / tạo dữ liệu card trong database ---
    db_card = await cards.get_cinfo_card_data_by_name(card_name)
    if not db_card:
        floor_db = "None" if card_loc == "None" else [floor_1, floor_2, floor_3]
        await cards.create_card_in_collection(
            card_id, card_name, card_element, card_loc, floor_db,
            card_hp, card_atk, card_def, card_speed,
            card_talent_name.group(1), card_talent_description.group(1),
            card_series, "N/A", "N/A", card_info_picture)
        db_card = await cards.get_cinfo_card_data_by_name(card_name)

    if db_card[0].get("card_picture"):
        card_info_picture = db_card[0]["card_picture"]

    market_sr = "{:,}".format(int(db_card[0]["card_price_sr"])) if db_card[0]["card_price_sr"] != "N/A" else "N/A"
    market_ur = "{:,}".format(int(db_card[0]["card_price_ur"])) if db_card[0]["card_price_ur"] != "N/A" else "N/A"

    # --- Xác định player ---
    player = player_settings = None
    if message.author.id == 571027211407196161 and message.reference:
        ref    = message.reference
        cached = discord.utils.get(runtime.bot.cached_messages, id=ref.message_id)
        if cached:
            player = cached.author
        else:
            original = await message.channel.fetch_message(ref.message_id)
            player   = original.author
        player_settings = await players.get_settings_from_player_by_discord_id(player.id)

    # --- Khởi tạo trạng thái stat calculator ---
    card_rarity          = "Base"
    card_rarity_name     = "Base"
    evolution_sr         = 1
    evolution_ur         = 1
    sr_asc_lvl           = 0
    ur_asc_lvl           = 0
    familiarity_bonus    = 0
    familiarity_bonus_name = "F0"
    clan_stat_to_change  = "all"
    clan_stat_hp = clan_stat_atk = clan_stat_def = clan_stat_spd = 0

    # --- Chọn container layout theo setting của player ---
    card_info_picture = normalize_picture_url(card_info_picture)
    if player_settings and player_settings["cinfo_picture"] == "original":
        container = CardInfoContainer1(id=1, accent_colour=0x71368A)
        container.card_picture.items[0].media = card_info_picture
    else:
        container = CardInfoContainer2(id=1, accent_colour=0x71368A)
        container.thumbnail.accessory.media = card_info_picture

    # --- Header text ---
    thumbnail_text = (
        f"## **{card_name}**\n\n"
        f"**Card ID:** {card_id}\n"
        f"**Card Series:** {card_series}\n"
        f"**Location/Floor:** {card_loc} | {card_floor}\n"
        f"**Next Daily:** {next_daily}\n"
        f"**Copies In Existence (SR/UR):** {card_amount_sr} / {card_amount_ur}\n"
        f"**Element:** {card_element} {ele_emote}\n"
        f"**Market Price SR:** {market_sr} <t:{db_card[0]['market_price_sr_timer']}:R>\n"
        f"**Market Price UR:** {market_ur} <t:{db_card[0]['market_price_ur_timer']}:R>\n"
    )
    container.thumbnail.children[0].content = thumbnail_text

    # --- Base stats table ---
    W = 16
    sr_hp  = ceil(int(card_hp)    * 3.5)
    sr_atk = ceil(int(card_atk)   * 3.5)
    sr_def = ceil(int(card_def)   * 3.5)
    sr_spd = ceil(int(card_speed) * 3.5)
    ur_hp  = ceil(int(card_hp)    * 4.2)
    ur_atk = ceil(int(card_atk)   * 4.2)
    ur_def = ceil(int(card_def)   * 4.2)
    ur_spd = ceil(int(card_speed) * 4.2)
    container.card_stats.content = (
        f"```\n"
        f"{'Base Stats':<{W}}{'SR A4':<{W}}UR A5\n"
        f"{'HP: '+card_hp:<{W}}{'HP: '+str(sr_hp):<{W}}HP: {ur_hp}\n"
        f"{'ATK: '+card_atk:<{W}}{'ATK: '+str(sr_atk):<{W}}ATK: {ur_atk}\n"
        f"{'DEF: '+card_def:<{W}}{'DEF: '+str(sr_def):<{W}}DEF: {ur_def}\n"
        f"{'SPEED: '+card_speed:<{W}}{'SPEED: '+str(sr_spd):<{W}}SPEED: {ur_spd}\n"
        f"{'TOTAL: '+str(int(card_hp)+int(card_atk)+int(card_def)+int(card_speed)):<{W}}"
        f"{'TOTAL: '+f'{sr_hp+sr_atk+sr_def+sr_spd:,}':<{W}}"
        f"TOTAL: {ur_hp+ur_atk+ur_def+ur_spd:,}\n```"
    )
    container.card_talent.content = (
        f"**__SR Talent__**\n{card_talent_emote} **{card_talent_name.group(1)}:** {card_talent_text_sr}\n\n"
        f"**__UR Talent__**\n{card_talent_emote} **{card_talent_name.group(1)}:** {card_talent_text_ur}"
    )

    rarity_select = container.rarity_row.children[0]
    clan_select   = container.clan_row.children[0]
    fam_select    = container.fam_row.children[0]
    del_button    = container.del_row.children[0]

    # Helper: tính lại stat và cập nhật container sau mỗi interaction
    async def _update_stats(interaction):
        evo, asc = _resolve_evo_asc(card_rarity, evolution_ur, ur_asc_lvl, evolution_sr, sr_asc_lvl)
        calc_hp, calc_atk, calc_def, calc_spd = await definitions.calc_card_stats(
            card_hp, card_atk, card_def, card_speed, card_rarity, evo, asc,
            familiarity_bonus, clan_stat_hp, clan_stat_atk, clan_stat_def, clan_stat_spd)
        compact = player_settings and player_settings.get("cinfo_stat_display") == "compact"
        container.card_stats.content = _format_stats_content(
            card_rarity_name, familiarity_bonus_name,
            calc_hp, calc_atk, calc_def, calc_spd,
            clan_stat_hp, clan_stat_atk, clan_stat_def, clan_stat_spd, compact)
        container.card_talent.content = _format_talent_content(
            card_rarity, card_talent_emote,
            card_talent_name.group(1), card_talent_text_sr, card_talent_text_ur,
            card_talent_description.group(1))
        await interaction.response.edit_message(view=view)

    # --- Rarity callback ---
    async def rarity_callback(interaction: discord.Interaction):
        if player and interaction.user.id != player.id:
            await interaction.response.defer()
            return
        nonlocal card_rarity, card_rarity_name, evolution_ur, ur_asc_lvl, evolution_sr, sr_asc_lvl
        val = rarity_select.values[0]
        cfg = _RARITY_CONFIG.get(val)
        if cfg:
            rarity, evo_ur, asc_ur, evo_sr, asc_sr = cfg
            card_rarity = rarity
            card_rarity_name = val
            if evo_ur is not None:
                evolution_ur = evo_ur
                ur_asc_lvl   = asc_ur
            if evo_sr is not None:
                evolution_sr = evo_sr
                sr_asc_lvl   = asc_sr
        else:
            card_rarity = "Base"
            card_rarity_name = "Base"
        await _update_stats(interaction)

    # --- Clan callback ---
    async def clan_callback(interaction: discord.Interaction):
        if player and interaction.user.id != player.id:
            await interaction.response.defer()
            return
        nonlocal clan_stat_to_change, clan_stat_hp, clan_stat_atk, clan_stat_def, clan_stat_spd
        val = clan_select.values[0]

        # Chọn stat cần thay đổi (không cập nhật ngay)
        if val in ("all stats", "clan hp", "clan atk", "clan def", "clan spd"):
            clan_stat_to_change = val.replace("clan ", "") if val != "all stats" else "all"
            label = f"``{clan_stat_to_change}``"
            await interaction.response.send_message(
                f"All following clan stat changes will affect: {label}. Select a different value to change.", ephemeral=True)
            return

        # Áp dụng bonus vào stat tương ứng
        bonus = _CLAN_LEVEL_BONUS.get(val, 0)
        if clan_stat_to_change == "hp":
            clan_stat_hp = bonus
        elif clan_stat_to_change == "atk":
            clan_stat_atk = bonus
        elif clan_stat_to_change == "def":
            clan_stat_def = bonus
        elif clan_stat_to_change == "spd":
            clan_stat_spd = bonus
        else:
            clan_stat_hp = clan_stat_atk = clan_stat_def = clan_stat_spd = bonus
        await _update_stats(interaction)

    # --- Familiarity callback ---
    async def fam_callback(interaction: discord.Interaction):
        if player and interaction.user.id != player.id:
            await interaction.response.defer()
            return
        nonlocal familiarity_bonus, familiarity_bonus_name
        val = fam_select.values[0]
        familiarity_bonus, familiarity_bonus_name = _FAM_CONFIG.get(val, (0, "F0"))
        await _update_stats(interaction)

    # --- Delete callback ---
    async def del_button_callback(interaction: discord.Interaction):
        if player and interaction.user.id != player.id:
            await interaction.response.defer()
            return
        await interaction.message.delete()

    rarity_select.callback = rarity_callback
    clan_select.callback   = clan_callback
    fam_select.callback    = fam_callback
    del_button.callback    = del_button_callback

    view = CardInfoView(timeout=120)
    view.container = container
    view.add_item(container)
    msg = await message.channel.send(view=view)
    view.message = msg

    if player_settings and player_settings.get("cinfo_delete") == "yes":
        try:
            await message.delete()
        except (discord.errors.NotFound, discord.errors.Forbidden):
            pass
