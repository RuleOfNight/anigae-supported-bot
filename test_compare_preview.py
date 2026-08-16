import asyncio
from types import SimpleNamespace

import discord

from Commands.v2.compare import ComparePreviewView, is_compare_message


def _message(*items):
    return SimpleNamespace(components=[SimpleNamespace(children=list(items))])


def test_compare_detection_requires_full_control_signature():
    buttons = [
        SimpleNamespace(label=label)
        for label in ["Rarity", "Level", "Evo", "Ascension", "Familiarity"]
    ]
    mode = SimpleNamespace(options=[
        SimpleNamespace(label="Brief"), SimpleNamespace(label="Detailed")
    ])
    adjust = SimpleNamespace(options=[
        SimpleNamespace(label="Adjust All"), SimpleNamespace(label="Adjust Card #1")
    ])

    assert is_compare_message(_message(*buttons, mode, adjust))
    assert not is_compare_message(_message(*buttons, mode))


def test_preview_binds_controls_and_adds_max_before_delete():
    async def check():
        view = ComparePreviewView(owner_id=1)
        mode = discord.ui.Select(options=[
            discord.SelectOption(label="Brief"),
            discord.SelectOption(label="Detailed"),
        ])
        adjust = discord.ui.Select(options=[
            discord.SelectOption(label="Adjust All"),
            discord.SelectOption(label="Adjust Card #1"),
        ])
        editor_row = discord.ui.ActionRow(*[
            discord.ui.Button(label=label)
            for label in ["Rarity", "Level", "Evo", "Ascension", "Familiarity"]
        ])
        delete_row = discord.ui.ActionRow(
            discord.ui.Button(emoji="🗑️", style=discord.ButtonStyle.danger)
        )
        view.add_item(discord.ui.Container(
            discord.ui.ActionRow(mode),
            discord.ui.ActionRow(adjust),
            editor_row,
            delete_row,
        ))

        view._bind_controls()

        assert mode.custom_id == "compare:mode"
        assert adjust.custom_id == "compare:adjust"
        assert [button.label for button in delete_row.children] == ["Max", None]
        assert [button.custom_id for button in delete_row.children] == [
            "compare:max", "compare:delete"
        ]

    asyncio.run(check())
