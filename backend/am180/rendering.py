"""Shared rendering utilities.

Palette definitions and color helpers used across generators.
"""

PALETTES: dict[str, list[str]] = {
    "warm": ["#ff6b35", "#f7931e", "#fcbf49", "#f77f00", "#d62828"],
    "cool": ["#4cc9f0", "#4361ee", "#3a0ca3", "#7209b7", "#560bad"],
    "mono": ["#ffffff", "#c0c0c0", "#808080", "#d0d0d0", "#e8e8e8"],
}


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string to an (r, g, b) tuple.

    Parameters
    ----------
    hex_color : str
        Color string like "#ff6b35" or "#FFF".

    Returns
    -------
    tuple of int
        (red, green, blue) values 0-255.
    """
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
