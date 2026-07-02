"""Tests for the differential growth generator."""
import io

import numpy as np
from PIL import Image

from am180.generators.growth import GrowthParams, _grow, render


def _fast_params(**overrides) -> GrowthParams:
    """Small, quick parameter set for tests."""
    defaults = dict(iterations=80, rings=15)
    defaults.update(overrides)
    return GrowthParams(**defaults)


def test_render_returns_correct_size() -> None:
    img = render(_fast_params(), seed=42, size=64)
    assert img.size == (64, 64)
    assert img.mode == "RGB"


def test_render_background_color() -> None:
    """Pixels never touched by a ring must stay exactly the paper color.

    Grain and vignette are disabled so untouched pixels are unmodified.
    The form grows from the center, so the corners stay paper-colored.
    """
    params = _fast_params(background="#ff0000", grain=0.0, vignette=0.0)
    img = render(params, seed=1, size=64)
    pixels = np.array(img)
    red_pixels = np.all(pixels == [255, 0, 0], axis=-1)
    assert red_pixels.mean() > 0.2


def test_determinism() -> None:
    """Same (params, seed, size) must produce byte-identical PNG output."""
    params = _fast_params()
    buf1 = io.BytesIO()
    buf2 = io.BytesIO()
    render(params, seed=42, size=64).save(buf1, format="PNG")
    render(params, seed=42, size=64).save(buf2, format="PNG")
    assert buf1.getvalue() == buf2.getvalue()


def test_different_seeds_different_images() -> None:
    params = _fast_params()
    buf1 = io.BytesIO()
    buf2 = io.BytesIO()
    render(params, seed=1, size=64).save(buf1, format="PNG")
    render(params, seed=2, size=64).save(buf2, format="PNG")
    assert buf1.getvalue() != buf2.getvalue()


def test_resolution_invariance() -> None:
    """Rendering at different sizes with the same (params, seed) must
    produce visually similar compositions.

    Grain is disabled (per-pixel texture). The simulation runs in
    normalized space, so only line rasterization differs with size.
    """
    params = _fast_params(grain=0.0)
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


def test_curve_grows() -> None:
    """The curve must gain points over the simulation."""
    rng = np.random.default_rng(0)
    snapshots = _grow(_fast_params(), rng)
    assert len(snapshots) > 1
    assert len(snapshots[-1]) > len(snapshots[0])


def test_curve_stays_in_bounds() -> None:
    """All snapshot points must stay inside the unit square."""
    rng = np.random.default_rng(0)
    snapshots = _grow(_fast_params(iterations=200, push=1.0), rng)
    for snap in snapshots:
        assert np.all(snap >= 0.0) and np.all(snap <= 1.0)


def test_rings_count_respected() -> None:
    """No more snapshots than requested rings."""
    rng = np.random.default_rng(0)
    snapshots = _grow(_fast_params(iterations=80, rings=10), rng)
    assert 1 <= len(snapshots) <= 10


def test_various_color_palettes_render() -> None:
    """Different color strings must produce valid images without errors."""
    palettes = (
        "#4a3728,#7a5a3d,#a4885e,#c9b183,#e3d3ab",  # sepia
        "#4cc9f0,#4361ee,#3a0ca3",                    # fewer colors
        "#ff0000",                                     # single color
    )
    for colors in palettes:
        params = _fast_params(colors=colors)
        img = render(params, seed=1, size=32)
        assert img.size == (32, 32)


def test_param_schema_colors_is_palette() -> None:
    """Growth's `colors` param should be exposed as a palette."""
    from am180.generators.growth import PARAM_SCHEMA
    spec = next(p for p in PARAM_SCHEMA if p.id == "colors")
    assert spec.type == "palette"
    assert spec.size == 5
    assert spec.default_preset == "sepia"
    assert spec.options is None
