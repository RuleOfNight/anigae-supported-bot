import asyncio
from types import SimpleNamespace

from Commands.v2.compare import ComparePreviewView, is_compare_message


def _message(*items):
    return SimpleNamespace(components=[SimpleNamespace(children=list(items))])


def test_compare_detection_requires_full_control_signature():
    buttons = [
        SimpleNamespace(label=label)
        for label in ["Rarity", "Level", "Evo", "Ascension", "Familiarity"]
    ]
    assert is_compare_message(_message(*buttons))
    assert not is_compare_message(_message(*buttons[:-1]))


def test_classic_preview_contains_expected_controls():
    async def check():
        view = ComparePreviewView(owner_id=1, card_count=2)
        custom_ids = {item.custom_id for item in view.children}

        assert "compare:mode" in custom_ids
        assert "compare:adjust" in custom_ids
        assert "compare:max" in custom_ids
        assert "compare:delete" in custom_ids
        assert len(view.children) == 9

    asyncio.run(check())
