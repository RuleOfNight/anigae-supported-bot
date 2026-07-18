import asyncio
import time

import discord

from db_methods.general import get_config_collection

CURRENT_CHANGELOG_VERSION = "2026-07-18-breach-playbook"
GUILD_CHANGELOG_COOLDOWN_SECONDS = 60 * 60
CHANGELOG_COLOR = 0x71368A
CHANGELOG_THUMBNAIL_URL = "https://cdn.discordapp.com/attachments/1027151586260156516/1337016553954213898/Memory_Diamonds.jpg"

_runtime_cooldowns: dict[tuple[str, int], int] = {}

_CHANGELOG_CONTENT = {
    "en": {
        "title": "Caeser Update Notes",
        "subtitle": "Weekend Breach tools just got a real notebook.",
        "sections": [
            ("Breach Playbook", [
                "New `/breach_comp_add` command lets clan members share Breach plans with comp, RNG notes, setup details, and results.",
                "New `/breach_comp_board` opens a Components V2 board with avatars, paginated plans, Refresh, and per-plan upvotes.",
                "Plans are saved per server in MongoDB, so each clan gets its own little strategy library.",
            ]),
            ("Breach weekly waiver", [
                "Caeser reads AniGame's `Breach Clan Standings` component pages.",
                "Clan members with **400,000+ damage** get next week's weekly donation waived automatically.",
                "Waivers are tracked separately, so the bot does **not** fake a 100,000 gold donation in clan donation history.",
            ]),
            ("Multi-page support", [
                "When you press AniGame's page arrows, Caeser listens to the edited standings page too.",
                "Each Breach page is deduped, so the same page will not grant the same waiver twice.",
            ]),
        ],
        "footer": "You are seeing this once because the bot was updated.",
    },
    "vi": {
        "title": "Caeser v\u1eeba \u0111\u01b0\u1ee3c c\u1eadp nh\u1eadt",
        "subtitle": "Breach cu\u1ed1i tu\u1ea7n gi\u1edd c\u00f3 s\u1ed5 tay chi\u1ebfn thu\u1eadt \u0111\u00e0ng ho\u00e0ng r\u1ed3i.",
        "sections": [
            ("Breach Playbook \u2014 Gi\u00e1o \u00c1n Cu\u1ed1i Tu\u1ea7n", [
                "Th\u00eam `/breach_comp_add` \u0111\u1ec3 member chia s\u1ebb gi\u00e1o \u00e1n Breach g\u1ed3m team comp, RNG note, setup chi ti\u1ebft v\u00e0 k\u1ebft qu\u1ea3.",
                "Th\u00eam `/breach_comp_board` \u0111\u1ec3 m\u1edf b\u1ea3ng Components V2 c\u00f3 avatar ng\u01b0\u1eddi t\u1ea1o, chia trang, Refresh v\u00e0 upvote t\u1eebng gi\u00e1o \u00e1n.",
                "Gi\u00e1o \u00e1n \u0111\u01b0\u1ee3c l\u01b0u ri\u00eang theo server trong MongoDB, n\u00ean m\u1ed7i clan c\u00f3 th\u01b0 vi\u1ec7n comp ri\u00eang.",
            ]),
            ("Mi\u1ec5n donate weekly nh\u1edd Breach", [
                "Caeser c\u00f3 th\u1ec3 \u0111\u1ecdc b\u1ea3ng `Breach Clan Standings` d\u1ea1ng component c\u1ee7a AniGame.",
                "Member \u0111\u1ea1t **400,000+ damage** s\u1ebd \u0111\u01b0\u1ee3c mi\u1ec5n donate weekly cho tu\u1ea7n sau t\u1ef1 \u0111\u1ed9ng.",
                "Waiver \u0111\u01b0\u1ee3c l\u01b0u ri\u00eang, n\u00ean bot **kh\u00f4ng gi\u1ea3 l\u1eadp** donation 100,000 gold trong l\u1ecbch s\u1eed donate clan.",
            ]),
            ("H\u1ed7 tr\u1ee3 b\u1ea3ng nhi\u1ec1u trang", [
                "Khi b\u1ea1n b\u1ea5m m\u0169i t\u00ean \u0111\u1ed5i trang tr\u00ean b\u1ea3ng AniGame, Caeser c\u0169ng \u0111\u1ecdc page m\u1edbi sau khi message edit.",
                "M\u1ed7i page \u0111\u01b0\u1ee3c ch\u1ed1ng c\u1ed9ng tr\u00f9ng, n\u00ean c\u00f9ng m\u1ed9t page kh\u00f4ng c\u1ea5p waiver hai l\u1ea7n.",
            ]),
        ],
        "footer": "B\u1ea1n th\u1ea5y th\u00f4ng b\u00e1o n\u00e0y v\u00ec bot v\u1eeba \u0111\u01b0\u1ee3c update.",
    },
}


def _seen_doc_id(version: str, guild_id: int, user_id: int) -> str:
    return f"changelog_seen:{version}:{guild_id}:{user_id}"


def _cooldown_doc_id(version: str, guild_id: int) -> str:
    return f"changelog_cooldown:{version}:{guild_id}"


def build_changelog_embed(language: str = "en") -> discord.Embed:
    content = _CHANGELOG_CONTENT.get(language, _CHANGELOG_CONTENT["en"])
    embed = discord.Embed(
        title=content["title"],
        description=f"### {content['subtitle']}\n`Version: {CURRENT_CHANGELOG_VERSION}`",
        color=CHANGELOG_COLOR,
    )
    for section_title, bullets in content["sections"]:
        embed.add_field(
            name=f"\u2726 {section_title}",
            value="\n".join(f"\u2022 {bullet}" for bullet in bullets),
            inline=False,
        )
    embed.set_footer(text=content["footer"])
    embed.set_thumbnail(url=CHANGELOG_THUMBNAIL_URL)
    return embed


class ChangelogView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)

    @discord.ui.button(label="English", style=discord.ButtonStyle.primary)
    async def english_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=build_changelog_embed("en"), view=self)

    @discord.ui.button(label="Ti\u1ebfng Vi\u1ec7t", style=discord.ButtonStyle.success)
    async def vietnamese_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=build_changelog_embed("vi"), view=self)

    @discord.ui.button(label="G\u00f3p \u00fd", style=discord.ButtonStyle.secondary)
    async def feedback_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Feedback button placeholder: ch\u1ed7 n\u00e0y sau c\u00f3 th\u1ec3 m\u1edf form, g\u1eedi link, ho\u1eb7c log g\u00f3p \u00fd v\u00e0o DB.",
            ephemeral=True,
        )


async def _should_show_changelog(guild_id: int, user_id: int) -> bool:
    config = get_config_collection()
    if config is None:
        return False

    now = int(time.time())
    runtime_key = (CURRENT_CHANGELOG_VERSION, guild_id)
    previous_runtime_send = _runtime_cooldowns.get(runtime_key, 0)
    if now - previous_runtime_send < GUILD_CHANGELOG_COOLDOWN_SECONDS:
        return False

    # Reserve the guild cooldown before awaiting Mongo calls. This prevents two
    # near-simultaneous commands from both passing the cooldown check.
    _runtime_cooldowns[runtime_key] = now

    seen_id = _seen_doc_id(CURRENT_CHANGELOG_VERSION, guild_id, user_id)
    if await config.find_one({"_id": seen_id}, {"_id": 1}):
        _runtime_cooldowns.pop(runtime_key, None)
        return False

    cooldown_id = _cooldown_doc_id(CURRENT_CHANGELOG_VERSION, guild_id)
    cooldown_doc = await config.find_one({"_id": cooldown_id}, {"last_sent_at": 1})
    if cooldown_doc and now - int(cooldown_doc.get("last_sent_at", 0)) < GUILD_CHANGELOG_COOLDOWN_SECONDS:
        _runtime_cooldowns[runtime_key] = int(cooldown_doc.get("last_sent_at", now))
        return False

    await config.update_one(
        {"_id": cooldown_id},
        {"$set": {
            "type": "changelog_cooldown",
            "version": CURRENT_CHANGELOG_VERSION,
            "guild_id": guild_id,
            "last_sent_at": now,
        }},
        upsert=True,
    )
    await config.update_one(
        {"_id": seen_id},
        {"$setOnInsert": {
            "type": "changelog_seen",
            "version": CURRENT_CHANGELOG_VERSION,
            "guild_id": guild_id,
            "user_id": user_id,
            "seen_at": now,
        }},
        upsert=True,
    )
    return True


async def _send_changelog_to_channel(channel) -> None:
    try:
        await channel.send(embed=build_changelog_embed("vi"), view=ChangelogView())
    except (discord.Forbidden, discord.HTTPException):
        pass


async def maybe_send_changelog_for_message(message) -> None:
    if not getattr(message, "guild", None) or not getattr(message, "channel", None):
        return
    if await _should_show_changelog(message.guild.id, message.author.id):
        await _send_changelog_to_channel(message.channel)


async def maybe_schedule_changelog_for_interaction(bot, interaction: discord.Interaction) -> None:
    if interaction.type != discord.InteractionType.application_command:
        return
    if not interaction.guild or not interaction.channel or not interaction.user:
        return

    async def _delayed_send():
        await asyncio.sleep(2)
        if await _should_show_changelog(interaction.guild.id, interaction.user.id):
            await _send_changelog_to_channel(interaction.channel)

    bot.loop.create_task(_delayed_send())
