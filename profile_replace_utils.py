import re
from urllib.parse import urlparse


def profile_discord_id(embed_footer: str) -> int | None:
    match = re.search(r"Summoner ID:\s*(\d+)", embed_footer)
    return int(match.group(1)) if match else None


def normalise_image_url(image_url: str) -> str | None:
    image_url = image_url.strip().strip("<>")
    parsed = urlparse(image_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or len(image_url) > 2048:
        return None
    return image_url
