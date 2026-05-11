bot = None

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