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


def _collect_text_recursive(obj, results: list[str]):
    """Đệ quy thu thập tất cả text content từ component tree."""
    for attr in ("content", "label", "description", "placeholder", "text", "title"):
        value = getattr(obj, attr, None)
        if isinstance(value, str) and value:
            results.append(value)
    for attr in ("children", "items"):
        for child in getattr(obj, attr, []) or []:
            _collect_text_recursive(child, results)


def get_all_component_text(message) -> str:
    """Trả về toàn bộ text trong component tree của message, ghép bằng newline."""
    results: list[str] = []
    for component in message.components:
        _collect_text_recursive(component, results)
    return "\n".join(results)
