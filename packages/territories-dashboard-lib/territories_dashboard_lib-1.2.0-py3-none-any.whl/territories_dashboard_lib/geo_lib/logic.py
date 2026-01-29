import re


def parse_legend(legend: str | None) -> list[dict] | None:
    """
    Parse a legend text field into a structured JSON format.

    Args:
        legend: The legend text, where each line can optionally start with
                "icone(couleur:#XXXXXX,taille:sm|md)" followed by text.

    Returns:
        None if legend is None or empty.
        A list of dicts with keys: color (str|None), size (str|None), text (str).
    """
    if legend is None or legend.strip() == "":
        return None

    result = []
    icon_pattern = re.compile(
        r"^icone\(couleur:(?P<color>#[0-9a-fA-F]{6}|nulle),taille:(?P<size>sm|md)\)\s*"
    )
    color_pattern = re.compile(r"^couleur\((?P<color>#[0-9a-fA-F]{6})\)\s*")

    for line in legend.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        icon_match = icon_pattern.match(line)
        color_match = color_pattern.match(line)

        color = None
        icon = False
        size = None
        text = line
        if icon_match:
            icon = True
            color = icon_match.group("color")
            color = None if color == "nulle" else color
            size = icon_match.group("size")
            text = line[icon_match.end() :].strip()
        elif color_match:
            color = color_match.group("color")
            text = line[color_match.end() :].strip()
        result.append({"icon": icon, "color": color, "size": size, "text": text})

    return result if result else None
