import asyncio
from copy import deepcopy
from types import SimpleNamespace

import discord

from Commands import definitions
from Commands.v2.compare import (
    ComparePreviewView, _extract_talent_emote, _parse_base_stats,
    is_compare_message,
)


def _message(*items):
    return SimpleNamespace(components=[SimpleNamespace(children=list(items))])


def test_compare_detection_requires_full_control_signature():
    buttons = [
        SimpleNamespace(label=label)
        for label in ["Rarity", "Level", "Evo", "Ascension", "Familiarity"]
    ]
    assert is_compare_message(_message(*buttons))
    assert not is_compare_message(_message(*buttons[:-1]))
    description = (
        "**HP:** 85\n**ATK:** 78\n**DEF:** 85\n**SPD:** 78\n"
        "**TALENT:** <:Final_Verdict:123>"
    )
    assert _parse_base_stats(description) == {
        "hp": 85, "atk": 78, "def": 85, "spd": 78,
    }
    assert _extract_talent_emote(description) == "<:Final_Verdict:123>"


def test_classic_preview_contains_expected_controls():
    async def check():
        card = {
            "base": {"hp": 85, "atk": 78, "def": 85, "spd": 78},
            "embed": discord.Embed(
                title="Ryomen Sukuna",
                description=(
                    "**ELEMENT:** Fire 🔥\n**HP:** 85\n**ATK:** 78\n**DEF:** 85\n"
                    "**SPD:** 78\n**TOTAL:** 326\n**TALENT:** <:Final_Verdict:1>\n"
                    "**FAMILIARITY:** Level 0"
                ),
            ).to_dict(),
            "talent_emote": "<:Final_Verdict:1503405518105088010>",
            "state": {
                "rarity": "Base", "level": 0, "evo": 1,
                "ascension": 0, "familiarity": "0",
            },
        }
        view = ComparePreviewView(owner_id=1, cards=[card, deepcopy(card)])
        custom_ids = {item.custom_id for item in view.children}

        assert "compare:mode" in custom_ids
        assert "compare:adjust" in custom_ids
        assert "compare:max" in custom_ids
        assert "compare:delete" in custom_ids
        assert len(view.children) == 9

        view.selected_index = 1
        view.apply_option("max", "Max UR")
        assert view.cards[0]["state"]["rarity"] == "Base"
        assert view.cards[1]["state"] == {
            "rarity": "Ultra Rare", "level": 60, "evo": 3,
            "ascension": 5, "familiarity": "0",
        }
        embeds = await view.build_embeds()
        assert "**HP:** 359" in embeds[1].description
        assert "**TOTAL:** 1378" in embeds[1].description
        assert "<:Final_Verdict:1503405518105088010>" in embeds[1].description

        view.selected_index = 0
        view.apply_option("rarity", "Super Rare")
        view.apply_option("level", "50")
        view.apply_option("evo", "3")
        view.apply_option("ascension", "4")
        assert view.cards[0]["state"] == {
            "rarity": "Super Rare", "level": 50, "evo": 3,
            "ascension": 4, "familiarity": "0",
        }

    asyncio.run(check())


def test_compare_formula_and_talent_emote_mapping():
    async def check():
        rarity_expected = {
            "Base": 100, "Common": 120, "Uncommon": 140, "Rare": 160,
            "Super Rare": 180, "Ultra Rare": 200,
        }
        for rarity, expected in rarity_expected.items():
            stats = await definitions.calc_card_stats_compare(
                100, 100, 100, 100, rarity, 0, 1, 0,
                0, 0, 0, 0, 0,
            )
            assert stats == (expected,) * 4

        for level, evo, ascension, expected in (
            (60, 1, 0, 130),
            (0, 3, 0, 130),
            (0, 1, 5, 125),
        ):
            stats = await definitions.calc_card_stats_compare(
                100, 100, 100, 100, "Base", level, evo, ascension,
                0, 0, 0, 0, 0,
            )
            assert stats == (expected,) * 4

        for familiarity, expected in (
            (0, 100), (1, 102), (2, 104), (3, 106), (12, 112),
            ("Holorized", 112),
        ):
            stats = await definitions.calc_card_stats_compare(
                100, 100, 100, 100, "Base", 0, 1, 0,
                familiarity, 0, 0, 0, 0,
            )
            assert stats == (expected,) * 4

        stats = await definitions.calc_card_stats_compare(
            85, 78, 85, 78, "Ultra Rare", 60, 3, 5,
            12, 20, 20, 20, 20,
        )
        assert stats == (402, 369, 402, 369)
        assert await definitions.skill_converter_from_emote(
            "<:Final_Verdict:123>"
        ) == "<:Final_Verdict:1503405518105088010>"

    asyncio.run(check())
