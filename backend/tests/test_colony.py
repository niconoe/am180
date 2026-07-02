"""Tests for the colony generator."""
import io

import numpy as np
from PIL import Image

from am180.generators.colony import (
    _MAX_SHAPES,
    ColonyParams,
    _grow_colonies,
    render,
)


def test_render_returns_correct_size() -> None:
    img = render(ColonyParams(), seed=42, size=64)
    assert img.size == (64, 64)
    assert img.mode == "RGB"


def test_render_background_color() -> None:
    """Pixels outside all colonies must stay exactly the paper color.

    Grain and vignette are disabled so untouched pixels are unmodified.
    """
    params = ColonyParams(
        background="#ff0000", clusters=1, root_size=0.06,
        grain=0.0, vignette=0.0,
    )
    img = render(params, seed=1, size=64)
    pixels = np.array(img)
    red_pixels = np.all(pixels == [255, 0, 0], axis=-1)
    assert red_pixels.mean() > 0.2


def test_determinism() -> None:
    """Same (params, seed, size) must produce byte-identical PNG output."""
    params = ColonyParams()
    buf1 = io.BytesIO()
    buf2 = io.BytesIO()
    render(params, seed=42, size=64).save(buf1, format="PNG")
    render(params, seed=42, size=64).save(buf2, format="PNG")
    assert buf1.getvalue() == buf2.getvalue()


def test_different_seeds_different_images() -> None:
    params = ColonyParams()
    buf1 = io.BytesIO()
    buf2 = io.BytesIO()
    render(params, seed=1, size=64).save(buf1, format="PNG")
    render(params, seed=2, size=64).save(buf2, format="PNG")
    assert buf1.getvalue() != buf2.getvalue()


def test_resolution_invariance() -> None:
    """Rendering at different sizes with the same (params, seed) must
    produce visually similar compositions."""
    params = ColonyParams(grain=0.0)
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


def test_shape_cap_respected() -> None:
    """Wildest settings must not exceed the shape budget."""
    rng = np.random.default_rng(0)
    params = ColonyParams(clusters=5, bud_chance=0.9, depth=7)
    shapes = _grow_colonies(params, rng, n_colors=5)
    assert 5 <= len(shapes) <= _MAX_SHAPES


def test_children_shrink() -> None:
    """Every generation must be smaller than the previous one."""
    rng = np.random.default_rng(0)
    params = ColonyParams(clusters=1)
    shapes = _grow_colonies(params, rng, n_colors=5)
    by_gen: dict[int, float] = {}
    for s in shapes:
        by_gen.setdefault(s["generation"], s["radius"])
    gens = sorted(by_gen)
    for a, b in zip(gens, gens[1:]):
        assert by_gen[b] < by_gen[a]


def test_all_shape_modes_and_opacities_render() -> None:
    """Every shapes mode and both fill paths must render."""
    for shapes in ("mixed", "quads", "hexes"):
        for fill_opacity in (1.0, 0.6):
            params = ColonyParams(shapes=shapes, fill_opacity=fill_opacity)
            img = render(params, seed=1, size=32)
            assert img.size == (32, 32)


def test_various_color_palettes_render() -> None:
    """Different color strings must produce valid images without errors."""
    palettes = (
        "#c3d5d3,#8fa8bd,#5b7ea6,#c94a44,#2e3a55",  # porcelain
        "#ffffff,#c0c0c0,#808080",                    # fewer colors
        "#ff0000",                                     # single color
    )
    for colors in palettes:
        params = ColonyParams(colors=colors)
        img = render(params, seed=1, size=32)
        assert img.size == (32, 32)


def test_zero_character_params_render() -> None:
    """The faithful flat look (all character traits off) must render."""
    params = ColonyParams(
        irregularity=0.0, spread=0.0, echoes=0, color_drift=0.0
    )
    img = render(params, seed=1, size=32)
    assert img.size == (32, 32)


def test_color_indices_within_palette() -> None:
    """Lineage drift must never leave the palette bounds."""
    rng = np.random.default_rng(0)
    params = ColonyParams(color_drift=1.0, clusters=3)
    shapes = _grow_colonies(params, rng, n_colors=3)
    assert all(0 <= s["color_idx"] < 3 for s in shapes)


def test_roots_have_no_origin_children_do() -> None:
    """Roots grew from nowhere; every bud records its parent corner."""
    rng = np.random.default_rng(0)
    shapes = _grow_colonies(ColonyParams(), rng, n_colors=5)
    for s in shapes:
        if s["generation"] == 0:
            assert s["origin"] is None
        else:
            assert s["origin"] is not None


def test_param_schema_colors_is_palette() -> None:
    """Colony's `colors` param should be exposed as a palette."""
    from am180.generators.colony import PARAM_SCHEMA
    spec = next(p for p in PARAM_SCHEMA if p.id == "colors")
    assert spec.type == "palette"
    assert spec.size == 5
    assert spec.default_preset == "porcelain"
    assert spec.options is None


def test_param_schema_shapes_select() -> None:
    """The shapes select must ship options containing its default."""
    from am180.generators.colony import PARAM_SCHEMA
    spec = next(p for p in PARAM_SCHEMA if p.id == "shapes")
    assert spec.type == "select"
    assert spec.options
    assert spec.default in {o["value"] for o in spec.options}
