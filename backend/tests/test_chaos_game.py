"""Tests for the chaos game generator."""
import io

import numpy as np
from PIL import Image

from am180.generators.chaos_game import ChaosGameParams, render


def test_render_returns_correct_size() -> None:
    params = ChaosGameParams(points_millions=0.2)
    img = render(params, seed=42, size=64)
    assert img.size == (64, 64)
    assert img.mode == "RGB"


def test_render_background_color() -> None:
    """Bins never visited by a point must stay exactly the paper color.

    Grain and vignette are disabled so untouched pixels are unmodified.
    The fractal attractor lives inside the vertex circle, so the image
    corners are guaranteed to stay paper-colored.
    """
    params = ChaosGameParams(
        background="#ff0000", points_millions=0.2, grain=0.0, vignette=0.0
    )
    img = render(params, seed=1, size=64)
    pixels = np.array(img)
    red_pixels = np.all(pixels == [255, 0, 0], axis=-1)
    assert red_pixels.mean() > 0.2


def test_determinism() -> None:
    """Same (params, seed, size) must produce byte-identical PNG output."""
    params = ChaosGameParams(points_millions=0.2)
    buf1 = io.BytesIO()
    buf2 = io.BytesIO()
    render(params, seed=42, size=64).save(buf1, format="PNG")
    render(params, seed=42, size=64).save(buf2, format="PNG")
    assert buf1.getvalue() == buf2.getvalue()


def test_different_seeds_different_images() -> None:
    params = ChaosGameParams(points_millions=0.2)
    buf1 = io.BytesIO()
    buf2 = io.BytesIO()
    render(params, seed=1, size=64).save(buf1, format="PNG")
    render(params, seed=2, size=64).save(buf2, format="PNG")
    assert buf1.getvalue() != buf2.getvalue()


def test_resolution_invariance() -> None:
    """Rendering at different sizes with the same (params, seed) must
    produce visually similar compositions.

    Grain is disabled (it is per-pixel texture, not composition). The
    density tone mapping is normalized per resolution, so downsampling
    the large render should closely match the small one.
    """
    params = ChaosGameParams(points_millions=1.0, grain=0.0)
    seed = 42
    small = render(params, seed, size=128)
    large = render(params, seed, size=256)

    large_down = large.resize((128, 128), Image.Resampling.LANCZOS)

    arr_small = np.array(small, dtype=float)
    arr_large = np.array(large_down, dtype=float)

    mean_diff = np.abs(arr_small - arr_large).mean()
    assert mean_diff < 40, (
        f"Resolution invariance failed: mean pixel diff = {mean_diff:.1f}"
    )


def test_all_rules_and_color_modes_render() -> None:
    """Every rule / color_mode / vertex-count combination must render."""
    for rule in ("none", "no_repeat", "no_neighbor"):
        for color_mode in ("vertex", "density"):
            for vertices in (3, 4, 5):
                params = ChaosGameParams(
                    rule=rule,
                    color_mode=color_mode,
                    vertices=vertices,
                    points_millions=0.2,
                )
                img = render(params, seed=1, size=32)
                assert img.size == (32, 32)


def test_various_color_palettes_render() -> None:
    """Different color strings must produce valid images without errors."""
    palettes = (
        "#ff6b35,#f7931e,#fcbf49,#f77f00,#d62828",  # warm
        "#4cc9f0,#4361ee,#3a0ca3,#7209b7,#560bad",  # cool
        "#ffffff,#c0c0c0,#808080",                    # mono (fewer colors)
        "#ff0000",                                     # single color
    )
    for colors in palettes:
        params = ChaosGameParams(colors=colors, points_millions=0.2)
        img = render(params, seed=1, size=32)
        assert img.size == (32, 32)


def test_sierpinski_triangle_has_empty_center() -> None:
    """The n=3, ratio=0.5 classic must leave the central hole empty.

    The center of the Sierpinski triangle (the midpoint of the three
    vertices) lies in the largest removed triangle, so no points should
    accumulate there and the pixel stays paper-colored.
    """
    params = ChaosGameParams(
        vertices=3,
        jump_ratio=0.5,
        ratio_spread=0.0,
        jitter=0.0,
        twist=0.0,
        rule="none",
        points_millions=1.0,
        grain=0.0,
        vignette=0.0,
        background="#ffffff",
    )
    img = render(params, seed=7, size=256)
    pixels = np.array(img)
    # Center of the canvas is the triangle centroid area - inside the
    # main removed hole.
    cx, cy = 128, 140
    patch = pixels[cy - 4:cy + 4, cx - 4:cx + 4]
    assert np.all(patch == 255), "Sierpinski central hole is not empty"


def test_param_schema_colors_is_palette() -> None:
    """Chaos game's `colors` param should be exposed as a palette."""
    from am180.generators.chaos_game import PARAM_SCHEMA
    spec = next(p for p in PARAM_SCHEMA if p.id == "colors")
    assert spec.type == "palette"
    assert spec.size == 5
    assert spec.default_preset == "warm"
    assert spec.options is None


def test_param_schema_selects_have_options() -> None:
    """Select params must ship their options for the frontend."""
    from am180.generators.chaos_game import PARAM_SCHEMA
    for param_id in ("rule", "color_mode"):
        spec = next(p for p in PARAM_SCHEMA if p.id == param_id)
        assert spec.type == "select"
        assert spec.options
        values = {o["value"] for o in spec.options}
        assert spec.default in values