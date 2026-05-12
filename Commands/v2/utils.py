import re

picture_caeser = "https://media1.tenor.com/m/Gjw4udndPjsAAAAd/fight-nikke-goddess-of-victory.gif"


def normalize_picture_url(url: str) -> str:
    """Chuyển Tenor .mp4/.webm thành .gif để Discord embed có thể autoplay."""
    if not url:
        return url
    if "media.tenor.com" in url and "discordapp.net" not in url:
        url = re.sub(r"\.(mp4|webm)$", ".gif", url, flags=re.IGNORECASE)
        if not re.search(r"\.(gif|webp|png|jpg|jpeg)$", url, re.IGNORECASE):
            url = url + ".gif"
    return url


def find_text_in_components(message, pattern: str) -> bool:
    """Tìm kiếm pattern trong toàn bộ text content của các component lồng nhau."""
    for component in message.components:
        if hasattr(component, "children"):
            for child in component.children:
                if hasattr(child, "children"):
                    for subchild in child.children:
                        if hasattr(subchild, "content") and pattern in subchild.content:
                            return True
    return False
