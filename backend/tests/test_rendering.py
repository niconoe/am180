"""Tests for shared rendering utilities."""
from am180.rendering import PALETTES, hex_to_rgb


def test_palettes_exist() -> None:
    assert "warm" in PALETTES
    assert "cool" in PALETTES
    assert "mono" in PALETTES


def test_palette_has_colors() -> None:
    for name, colors in PALETTES.items():
        assert len(colors) >= 2, f"Palette '{name}' needs at least 2 colors"
        for c in colors:
            assert c.startswith("#"), f"Palette '{name}': '{c}' is not hex"


def test_hex_to_rgb_full() -> None:
    assert hex_to_rgb("#ff6b35") == (255, 107, 53)
    assert hex_to_rgb("#000000") == (0, 0, 0)
    assert hex_to_rgb("#ffffff") == (255, 255, 255)


def test_hex_to_rgb_short() -> None:
    assert hex_to_rgb("#fff") == (255, 255, 255)
    assert hex_to_rgb("#000") == (0, 0, 0)


def test_hex_to_rgb_uppercase() -> None:
    assert hex_to_rgb("#FF6B35") == (255, 107, 53)
