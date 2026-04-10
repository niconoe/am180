"""Tests for the flow field generator."""
import io

import numpy as np
from PIL import Image

from am180.generators.flow_field import FlowFieldParams, render


def test_render_returns_correct_size() -> None:
    params = FlowFieldParams()
    img = render(params, seed=42, size=64)
    assert img.size == (64, 64)
    assert img.mode == "RGB"


def test_render_background_color() -> None:
    params = FlowFieldParams(background="#ff0000", particle_density=0.0001)
    img = render(params, seed=1, size=32)
    # With very few particles, most pixels should be the background color.
    pixels = np.array(img)
    red_pixels = np.all(pixels == [255, 0, 0], axis=-1)
    # At least 50% should be background (generous - most will be).
    assert red_pixels.mean() > 0.5


def test_determinism() -> None:
    """Same (params, seed, size) must produce byte-identical PNG output."""
    params = FlowFieldParams()
    buf1 = io.BytesIO()
    buf2 = io.BytesIO()
    render(params, seed=42, size=64).save(buf1, format="PNG")
    render(params, seed=42, size=64).save(buf2, format="PNG")
    assert buf1.getvalue() == buf2.getvalue()


def test_different_seeds_different_images() -> None:
    params = FlowFieldParams()
    buf1 = io.BytesIO()
    buf2 = io.BytesIO()
    render(params, seed=1, size=64).save(buf1, format="PNG")
    render(params, seed=2, size=64).save(buf2, format="PNG")
    assert buf1.getvalue() != buf2.getvalue()


def test_resolution_invariance() -> None:
    """Rendering at different sizes with the same (params, seed) must
    produce visually similar compositions.

    We downsample the larger image and compare pixel values. The mean
    difference must be below a tolerance. This catches coordinate-space
    bugs (e.g. using pixel coords instead of normalized) but tolerates
    rasterization differences (line width rounding, particle count
    scaling with area).
    """
    params = FlowFieldParams(
        particle_density=0.005,
        max_steps=100,
        line_width=0.003,
    )
    seed = 42
    small = render(params, seed, size=128)
    large = render(params, seed, size=256)

    large_down = large.resize((128, 128), Image.Resampling.LANCZOS)

    arr_small = np.array(small, dtype=float)
    arr_large = np.array(large_down, dtype=float)

    mean_diff = np.abs(arr_small - arr_large).mean()
    # Generous tolerance: particle count scales with area so the
    # larger image has 4x more particles. The overall composition
    # (flow directions, color placement) should still be similar.
    assert mean_diff < 40, (
        f"Resolution invariance failed: mean pixel diff = {mean_diff:.1f}"
    )


def test_all_palettes_render() -> None:
    """Every built-in palette must produce a valid image without errors."""
    for palette_name in ("warm", "cool", "mono"):
        params = FlowFieldParams(palette=palette_name)
        img = render(params, seed=1, size=32)
        assert img.size == (32, 32)
