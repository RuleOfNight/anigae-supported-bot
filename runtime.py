bot = None
db_ready = False
active_raid_guilds: dict = {}   # {guild_id: timestamp} — set khi detect "Raid Challenge Timer"
raid_battle_tracker: dict = {}  # {user_id: timestamp} — set khi user dùng .rd bt
raid_afk_pinged: dict = {}      # {user_id: timestamp} — lần cuối user bị ping AFK
raid_bt_pending: dict = {}      # {user_id: {"timestamp": float, "channel_id": int}} — chờ confirm sau .rd bt
inv_mset_sent: set = set()      # message_id đã được reply .team mset, tránh gửi lại khi đổi trang

async def retrieve_data(variant):
    if variant == "prefixes":
        prefixes_data = bot.prefixes
        return prefixes_data
    elif variant == "event cards":
        event_cards_data = bot.event_cards
        return event_cards_data
    elif variant == "locations":
        locations_data = bot.locations
        return locations_data
    elif variant == "raid comps":
        raid_comps_data = bot.raid_comps
        return raid_comps_data
    else:
        return "failed"