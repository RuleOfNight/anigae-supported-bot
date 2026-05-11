import time
from zoneinfo import ZoneInfo
from db_methods import cards
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from db_methods.general import get_misc_collection


async def load_counter():
    misc_information = get_misc_collection()
    document = await misc_information.find_one({"_id": ObjectId("67ae69c3cf53d633cb1cd358")})
    current_cl_shop_counter = int(document["clan_shop_counter"])
    return current_cl_shop_counter


async def save_counter(counter):
    misc_information = get_misc_collection()
    update_values = {"$set": {"clan_shop_counter": f"{counter}"}}
    await misc_information.update_one({"_id": ObjectId("67ae69c3cf53d633cb1cd358")}, update_values)


async def get_last_update_time():
    misc_information = get_misc_collection()
    document = await misc_information.find_one({"_id": ObjectId("67ae69c3cf53d633cb1cd358")})
    cl_shop_last_update_timer = int(document["clan_shop_last_update_timer"])
    return cl_shop_last_update_timer


async def save_last_update_time():
    misc_information = get_misc_collection()
    current_timer = int(time.time())
    update_values = {"$set": {"clan_shop_last_update_timer": f"{current_timer}"}}
    await misc_information.update_one({"_id": ObjectId("67ae69c3cf53d633cb1cd358")}, update_values)


async def get_clan_shop_start_time():
    misc_information = get_misc_collection()
    document = await misc_information.find_one({"_id": ObjectId("67ae69c3cf53d633cb1cd358")})
    clan_shop_start_time = int(document["clan_shop_start_timer"])
    return clan_shop_start_time


async def get_next_cl_shop_character():
    current_index = await load_counter()
    card_series_list = await cards.get_card_data_by_series_name()
    current_index = current_index % len(card_series_list)
    next_character = card_series_list[current_index]["card_name"]
    return next_character


async def update_counter():
    last_update_time = await get_last_update_time()
    current_index = await load_counter()
    total_cards = len(await cards.get_card_data_by_series_name())
    last_saturday_2am = await get_last_saturday_2am_utc()
    if last_update_time is None or last_saturday_2am > last_update_time:
        next_index = (current_index + 1) % total_cards
        await save_counter(next_index)
        await save_last_update_time()


async def get_last_saturday_2am_utc():
    now = datetime.now(timezone.utc)
    days_since_saturday = (now.weekday() - 5) % 7
    last_saturday = now - timedelta(days=days_since_saturday)
    last_saturday_2am = last_saturday.replace(hour=2, minute=0, second=0, microsecond=0)
    if now < last_saturday_2am:
        last_saturday_2am -= timedelta(days=7)
    return int(last_saturday_2am.timestamp())


async def get_last_monday_berlin_time_from_current_time_in_unix():
    now = datetime.now(timezone.utc)
    days_since_monday = now.weekday()
    last_monday = now - timedelta(days=days_since_monday)
    if days_since_monday == 0:
        last_monday -= timedelta(days=7)
    last_monday_1am = last_monday.replace(hour=1, minute=0, second=0, microsecond=0)
    return int(last_monday_1am.timestamp())


async def get_current_month_start_unix(old_interval=None):
    now = datetime.now(timezone.utc)
    if old_interval is None:
        month_start_dt = now.replace(day=1, hour=1, minute=0, second=0, microsecond=0)
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1, hour=1, minute=0, second=0, microsecond=0)
        else:
            next_month = now.replace(month=now.month + 1, day=1, hour=1, minute=0, second=0, microsecond=0)
        month_end_dt = next_month
    else:
        year = now.year
        month = now.month - old_interval
        while month <= 0:
            month += 12
            year -= 1
        month_start_dt = datetime(year, month, 1, 1, 0, 0, tzinfo=timezone.utc)
        if month == 12:
            next_month = datetime(year + 1, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        else:
            next_month = datetime(year, month + 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        month_end_dt = next_month
    return int(month_start_dt.timestamp()), int(month_end_dt.timestamp())


async def get_next_saturday_and_monday_unix():
    unix_timestamp = await get_clan_shop_start_time()
    timestamp_utc = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    weekday = timestamp_utc.weekday()
    days_until_saturday = (5 - weekday) % 7
    if days_until_saturday == 0 and timestamp_utc.time() > datetime.min.time():
        days_until_saturday = 7
    next_saturday = (timestamp_utc + timedelta(days=days_until_saturday)).replace(hour=0, minute=0, second=0, microsecond=0)
    days_until_monday = (7 - weekday) % 7
    if days_until_monday == 0 and timestamp_utc.time() > datetime.min.time():
        days_until_monday = 7
    next_monday = (timestamp_utc + timedelta(days=days_until_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(next_saturday.timestamp()), int(next_monday.timestamp())
