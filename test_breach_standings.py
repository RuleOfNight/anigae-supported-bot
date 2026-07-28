import sys
import unittest

try:
    import Commands
except ModuleNotFoundError:
    # This Windows checkout exposes the tracked ``Commands`` folder as lowercase.
    import commands as Commands
    sys.modules["Commands"] = Commands

from Commands.v2.breach_standings import (
    BREACH_DAMAGE_WAIVER_THRESHOLD,
    parse_breach_standings,
)


class BreachStandingsParserTest(unittest.TestCase):
    def test_parses_v2_markdown_and_preserves_username_underscores(self):
        text = """## Breach Clan Standings
**Clan:** *WindyHill*
**#13 | alta_nguyen**
**Damage:** 730,764 (3.85%) | **Attacks:** 98 | **Avg:** 7,456
**#14 | davidingo0614_25375**
**Damage:** 627,034 (3.30%) | **Attacks:** 60 | **Avg:** 10,450
**Page 3 / 4**
"""

        entries, page, total_pages, clan_name = parse_breach_standings(text)

        self.assertEqual(
            entries,
            [
                {"player_name": "alta_nguyen", "damage": 730_764},
                {"player_name": "davidingo0614_25375", "damage": 627_034},
            ],
        )
        self.assertEqual((page, total_pages, clan_name), (3, 4, "WindyHill"))

    def test_waiver_threshold_includes_exactly_400k(self):
        text = """#1 | exact_boundary
Damage: 400,000
#2 | below_boundary
Damage: 399,999
Page 1 / 1
"""
        entries, *_ = parse_breach_standings(text)
        qualified = [
            entry["player_name"]
            for entry in entries
            if entry["damage"] >= BREACH_DAMAGE_WAIVER_THRESHOLD
        ]

        self.assertEqual(qualified, ["exact_boundary"])


if __name__ == "__main__":
    unittest.main()
