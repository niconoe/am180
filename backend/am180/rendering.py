"""Shared rendering utilities.

Palette definitions, color helpers and finishing effects (vignette,
film grain) used across generators.
"""
import numpy as np

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


def palette_gradient(palette: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Interpolate colors along the palette treated as a gradient.

    Parameters
    ----------
    palette : ndarray
        Shape (k, 3), palette colors as floats 0-255.
    t : ndarray
        Values in [0, 1], any shape.

    Returns
    -------
    ndarray
        Interpolated colors, shape t.shape + (3,).
    """
    stops = np.linspace(0, 1, len(palette))
    return np.stack(
        [np.interp(t, stops, palette[:, c]) for c in range(3)], axis=-1
    )


def apply_vignette_and_grain(
    arr: np.ndarray,
    vignette: float,
    grain: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Darken corners and add monochrome film grain.

    Parameters
    ----------
    arr : ndarray
        Shape (size, size, 3) float32 RGB image, modified and returned.
    vignette : float
        Vignette strength in [0, 1]; zero disables it.
    grain : float
        Grain amplitude; zero disables it.
    rng : Generator
        Seeded numpy RNG (consumed only when grain > 0).

    Returns
    -------
    ndarray
        The adjusted image, same shape and dtype as arr.
    """
    size = arr.shape[0]
    if vignette > 0:
        # Radial falloff: 0 at center, 1 at the corners.
        coords = np.linspace(-1.0, 1.0, size, dtype=np.float32)
        r2 = (coords[None, :] ** 2 + coords[:, None] ** 2) / 2.0
        fade = 1.0 - vignette * 0.7 * r2 ** 1.5
        arr *= fade[:, :, None]

    if grain > 0:
        noise = rng.standard_normal((size, size), dtype=np.float32)
        arr += (noise * grain * 80.0)[:, :, None]

    return arr
