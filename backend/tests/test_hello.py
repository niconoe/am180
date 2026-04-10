"""Tests for the hello (solid-color) test generator."""
import io

from PIL import Image

from am180.generators.hello import HelloParams, render


def test_render_returns_correct_size() -> None:
    params = HelloParams(color="#ff0000")
    img = render(params, seed=42, size=64)
    assert img.size == (64, 64)


def test_render_returns_correct_color() -> None:
    params = HelloParams(color="#ff0000")
    img = render(params, seed=42, size=16)
    # Every pixel should be pure red.
    pixels = list(img.get_flattened_data())
    assert all(p == (255, 0, 0) for p in pixels)


def test_render_deterministic() -> None:
    params = HelloParams(color="#00ff00")
    buf1 = io.BytesIO()
    buf2 = io.BytesIO()
    render(params, seed=99, size=32).save(buf1, format="PNG")
    render(params, seed=99, size=32).save(buf2, format="PNG")
    assert buf1.getvalue() == buf2.getvalue()


def test_render_different_colors() -> None:
    red = render(HelloParams(color="#ff0000"), seed=0, size=8)
    blue = render(HelloParams(color="#0000ff"), seed=0, size=8)
    assert list(red.get_flattened_data())[0] == (255, 0, 0)
    assert list(blue.get_flattened_data())[0] == (0, 0, 255)
