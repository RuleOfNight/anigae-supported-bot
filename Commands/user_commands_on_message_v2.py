# Re-export layer — giữ nguyên để main.py không cần thay đổi import.
# Tất cả logic đã được chuyển vào Commands/v2/.

from Commands.v2.dispatcher import discord_components_v2          # noqa: F401
from Commands.v2.inventory import on_raw_reaction_add             # noqa: F401
from Commands.v2.player_stats import (                            # noqa: F401
    player_stamina_v2,
    raid_pass_v2,
    player_lvl_v2,
)
