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
        "title": "Caeser' changelogs",
        "subtitle": "A few Breach updates for the weekend.",
        "sections": [
            ("Breach Playbook", [
                "Added `/breach_comp_add` so members can share Breach plans with the clan.",
                "Each plan can include a team comp, RNG notes, extra setup notes, and the result it reached.",
                "Added `/breach_comp_board` to browse shared plans in a prettier board with pages, avatars, and upvotes.",
            ]),
            ("Weekly donation waiver", [
                "When you show the Breach Clan Standings, Caeser can read member damage from the board.",
                "Members who reach **400,000+ damage** will be counted as covered for next week's weekly donation.",
                "This should make the new clan rule easier to run without manually tracking everyone after Breach ends.",
            ]),
        ],
        "footer": "You are seeing this once because the bot was updated.",
    },
    "vi": {
        "title": "Caeser' changelogs",
        "subtitle": "Vài cập nhật hỗ trợ Breach cuối tuần.",
        "sections": [
            ("Breach Playbook", [
                "Thêm lệnh `/breach_comp_add` để các thành viên chia sẻ giáo án Breach với nhau.",
                "Mỗi giáo án có thể ghi team comp, ghi chú RNG, mô tả cách setup và kết quả đạt được.",
                "Thêm lệnh `/breach_comp_board` để mở bảng giáo án của clan, có chia trang, avatar người tạo và nút upvote.",
            ]),
            ("Miễn donate tuần sau", [
                "Khi bạn mở bảng Breach Clan Standings, Caeser có thể đọc damage của từng thành viên.",
                "Ai đạt **400,000+ damage** sẽ được tính là đã hoàn thành donate weekly cho tuần sau.",
                "Như vậy sau khi Breach kết thúc, clan đỡ phải tự ghi nhớ và cộng miễn donate thủ công cho từng người.",
            ]),
        ],
        "footer": "Bạn thấy thông báo này vì bot vừa được cập nhật.",
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
            name=f"? {section_title}",
            value="\n".join(f"? {bullet}" for bullet in bullets),
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

    @discord.ui.button(label="Tiếng Việt", style=discord.ButtonStyle.success)
    async def vietnamese_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=build_changelog_embed("vi"), view=self)

    @discord.ui.button(label="Góp ý", style=discord.ButtonStyle.secondary)
    async def feedback_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Feedback button placeholder: chỗ này sau có thể mở form, gửi link, hoặc log góp ý vào DB.",
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
