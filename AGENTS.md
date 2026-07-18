# Caeser — AniGame Discord Bot

Bot Discord hỗ trợ game AniGame, viết bằng Python (discord.py). Bot hoạt động song song với bot gốc AniGame (`target_bot_id = 571027211407196161`) bằng cách lắng nghe embed và component message của nó.

## Chạy bot

```bash
python main.py
```

Yêu cầu file `.env` với:
- `MONGODB_URI` — connection string MongoDB Atlas
- `DISCORD_TOKEN` — token bot Discord

## Cấu trúc project

```
main.py                          # Entry point, on_message router, scheduler
runtime.py                       # Global state (bot, db_ready, active_raid_guilds)
Commands/
  user_commands_slash.py         # Slash commands (app_commands) — Cog: UserCommandsSlash
  user_commands_prefix.py        # Prefix commands cũ
  user_commands_prefix_v2.py     # Prefix commands mới
  user_commands_on_message.py    # Xử lý embed từ AniGame bot (clan donation, raid lobby, profile...)
  user_commands_on_message_v2.py # Xử lý component V2 (Container) từ AniGame bot
  admin_commands.py              # Admin-only commands
  definitions.py                 # Constants dùng chung
  v2/
    dispatcher.py                # Router chính cho discord component V2
    card_info.py                 # Xử lý .info card (base info)
    card_info_instance.py        # Xử lý .info card instance (card cụ thể của player)
    clan_shop.py                 # Clan shop
    pack_opening.py              # Pack opening
    market.py                    # Global market
    card_select.py               # Battle card selection
    utils.py                     # Helper: find_text_in_components, get_all_component_text
db_methods/
  general.py                     # DB connect, collection getters, misc utils
  cards.py                       # CRUD cards collection
  players.py                     # CRUD players collection
  guilds.py                      # CRUD guilds collection (donation tracking, guild reset)
  weekly_donations.py            # Weekly donation tracker collection
data/
  prefixes.json                  # Guild prefix map {guild_id: prefix}
  event_cards.json               # Event card list
  locations.json                 # Location/floor data
  raid_comps.json                # Raid composition data
gif_converter/convert.py         # Convert mp4 → gif cho card art
misc/
  time_calculations.py
  skills.py
```

## Database

MongoDB (`discordbot` database), các collection:
- `cards` — dữ liệu card game
- `players` — dữ liệu player
- `guilds` — dữ liệu clan/guild (donation, member list, threshold)
- `misc` — misc config (energy timer, daily watch counter)
- `weekly_donation_tracker` — tracking donate weekly của player

## Cách on_message hoạt động

`main.py::on_message` chỉ xử lý message từ `target_bot_id`. Luồng:

1. **Component V2 (Container)** → `user_commands_on_message_v2.discord_components_v2()` → `Commands/v2/dispatcher.py`
2. **Embed message** → kiểm tra keyword trong title/description/footer:
   - `"Raid Challenge Timer"` → `in_raid_lobby()`
   - `"Raid Lobby Timer"` → `raid_lobby_waiting_room()`
   - `"to your clan, and received"` → `clan_donation_tracker()`
   - `"Summoner ID:"` (footer) → `profile_tracker()`

## Scheduler (APScheduler)

- **Monthly** (ngày 1, 1:00 UTC): reset guild monthly donation
- **Weekly** (thứ 2, 1:00 UTC): reset guild weekly donation
- **Daily** (1:00 UTC): decrement premium days cho tất cả player
- **Every 10 min**: `check_raid_afk()` — ping người chưa đánh raid sau 30 phút

## Prefix mặc định

`"5"` — lưu per-guild trong `data/prefixes.json`, đổi bằng `5setprefix <new>`

## Emote quan trọng

Emote rarity và ascension được định nghĩa trong `user_commands_on_message.py` và import vào các module khác:
- `ultra_rare_1`, `ultra_rare_2` — Ultra Rare
- `super_rare_1`, `super_rare_2` — Super Rare
- `rare_emote`, `uncommon_emote_1/2`, `common_emote_1` — các rarity còn lại
- `ascension_emote` — emote ascend (sao)

## Convention

- Slash commands định nghĩa trong `UserCommandsSlash` Cog (`Commands/user_commands_slash.py`)
- UI dùng discord.py Components V2: `Container`, `LayoutView`, `TextDisplay`, `MediaGallery`
- Async MongoDB qua `motor`; sync fallback dùng `pymongo` (tránh dùng)
- Không mock DB trong test — dùng DB thật
- Default embed color: `0x71368A`
