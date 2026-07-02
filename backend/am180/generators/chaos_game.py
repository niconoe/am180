"""Chaos game generator.

Ghostly generalized Sierpinski fractals rendered as ink-density fields.
The classic chaos game (jump a fixed fraction toward a randomly chosen
polygon vertex) is generalized with a per-jump rotation ("twist") and
vertex-restriction rules, which together produce a large family of
fractal forms - the Sierpinski triangle is the n=3, ratio=0.5 case.

Instead of plotting individual points, the algorithm accumulates
millions of them into a 2D histogram and tone-maps density to a
translucent ink layer composited over a paper-colored background.
Film grain and a vignette give the output a vintage, nostalgic feel.

1. Place n vertices on a circle, tint each with a palette color.
2. Run many walkers in parallel: each step, pick a vertex (subject to
   the restriction rule) and jump jump_ratio of the way toward it,
   rotating the jump vector by the twist angle.
3. Bin all visited points into a density histogram (per color channel).
4. Tone-map density to alpha (log scale), composite inks over paper.
5. Apply vignette and grain at the final resolution.
"""
from typing import Literal

import numpy as np
from PIL import Image
from pydantic import BaseModel, Field

from am180.rendering import apply_vignette_and_grain, hex_to_rgb, palette_gradient
from am180.schemas import ParamSpec


class ChaosGameParams(BaseModel):
    """Parameters for the chaos game generator.

    Attributes
    ----------
    vertices : int
        Number of polygon vertices (attractors).
    jump_ratio : float
        Fraction of the distance to the chosen vertex covered by each
        jump. 0.5 with 3 vertices gives the Sierpinski triangle.
    ratio_spread : float
        Random per-jump variation of jump_ratio (uniform, plus or minus
        half this value). Superimposes many slightly different fractals,
        softening the self-similar structure into washes of density.
    jitter : float
        Gaussian positional noise added after every jump, in normalized
        canvas units. Blurs fine fractal detail into mist; zero keeps
        the pattern crisp.
    twist : float
        Rotation in degrees applied to every jump vector. Zero gives
        classic straight-line chaos game fractals; nonzero values bend
        the arms into spirals.
    rule : str
        Vertex selection restriction. "none" allows any vertex,
        "no_repeat" forbids picking the same vertex twice in a row,
        "no_neighbor" additionally forbids vertices adjacent to the
        previous choice. Restrictions carve structure into the fractal.
    points_millions : float
        Total number of accumulated points, in millions. More points
        give smoother, deeper density fields but render slower.
    color_mode : str
        "vertex" tints each point by its attracting vertex so fractal
        arms carry different inks; "density" maps local point density
        through the palette as a gradient.
    exposure : float
        Brightness multiplier for the density-to-alpha tone mapping.
    ghost_opacity : float
        Maximum ink opacity (0.1 = barely-there ghost, 1.0 = full ink).
    grain : float
        Monochrome film grain amplitude. Zero disables grain.
    vignette : float
        Strength of the darkened corners. Zero disables the vignette.
    background : str
        Paper color as hex string.
    colors : str
        Comma-separated hex colors for the inks (e.g. "#aa4444,#3344aa").
        The frontend owns palette definitions and sends the values.
    """

    vertices: int = Field(5, ge=3, le=9)
    jump_ratio: float = Field(0.5, ge=0.3, le=0.9)
    ratio_spread: float = Field(0.08, ge=0.0, le=0.4)
    jitter: float = Field(0.0015, ge=0.0, le=0.02)
    twist: float = Field(0.0, ge=-45.0, le=45.0)
    rule: Literal["none", "no_repeat", "no_neighbor"] = "no_repeat"
    points_millions: float = Field(2.0, ge=0.2, le=8.0)
    color_mode: Literal["vertex", "density"] = "vertex"
    exposure: float = Field(1.0, ge=0.3, le=3.0)
    ghost_opacity: float = Field(0.85, ge=0.1, le=1.0)
    grain: float = Field(0.05, ge=0.0, le=0.15)
    vignette: float = Field(0.3, ge=0.0, le=1.0)
    background: str = Field("#f2e8d5")
    colors: str = Field("#ff6b35,#f7931e,#fcbf49,#f77f00,#d62828")


PARAM_SCHEMA: list[ParamSpec] = [
    ParamSpec(
        id="vertices", label="Vertices", type="int",
        min=3, max=9, step=1, default=5, group="fractal",
    ),
    ParamSpec(
        id="jump_ratio", label="Jump ratio", type="float",
        min=0.3, max=0.9, step=0.01, default=0.5, group="fractal",
    ),
    ParamSpec(
        id="ratio_spread", label="Ratio spread", type="float",
        min=0.0, max=0.4, step=0.01, default=0.08, group="fractal",
    ),
    ParamSpec(
        id="jitter", label="Jitter", type="float",
        min=0.0, max=0.02, step=0.0005, default=0.0015, group="fractal",
    ),
    ParamSpec(
        id="twist", label="Twist (deg)", type="float",
        min=-45.0, max=45.0, step=0.5, default=0.0, group="fractal",
    ),
    ParamSpec(
        id="rule", label="Vertex rule", type="select",
        default="no_repeat", group="fractal",
        options=[
            {"value": "none", "label": "Free"},
            {"value": "no_repeat", "label": "No repeat"},
            {"value": "no_neighbor", "label": "No neighbor"},
        ],
    ),
    ParamSpec(
        id="points_millions", label="Points (millions)", type="float",
        min=0.2, max=8.0, step=0.1, default=2.0, group="points",
    ),
    ParamSpec(
        id="color_mode", label="Color mode", type="select",
        default="vertex", group="render",
        options=[
            {"value": "vertex", "label": "By vertex"},
            {"value": "density", "label": "By density"},
        ],
    ),
    ParamSpec(
        id="exposure", label="Exposure", type="float",
        min=0.3, max=3.0, step=0.05, default=1.0, group="render",
    ),
    ParamSpec(
        id="ghost_opacity", label="Ghost opacity", type="float",
        min=0.1, max=1.0, step=0.05, default=0.85, group="render",
    ),
    ParamSpec(
        id="grain", label="Grain", type="float",
        min=0.0, max=0.15, step=0.005, default=0.05, group="render",
    ),
    ParamSpec(
        id="vignette", label="Vignette", type="float",
        min=0.0, max=1.0, step=0.05, default=0.3, group="render",
    ),
    ParamSpec(
        id="background", label="Paper", type="color",
        default="#f2e8d5", group="render",
    ),
    ParamSpec(
        id="colors", label="Palette", type="palette",
        size=5, default_preset="warm", group="render",
    ),
]


# Number of walkers marched in parallel. Total steps per walker is
# derived from points_millions, so this only affects vectorization
# granularity, not the composition.
_WALKERS = 20_000

# Steps discarded before accumulation starts, so walkers have settled
# onto the attractor.
_BURN_IN = 20

# Maximum histogram grid resolution. Density fields upscale gracefully,
# so exports larger than this render the histogram at the cap and
# resize up - keeping memory bounded at high export sizes.
_MAX_GRID = 4096

# Radius of the vertex circle in normalized [0, 1] coordinates.
_POLY_RADIUS = 0.42


def _polygon_vertices(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Vertex coordinates of a regular n-gon, one vertex pointing up.

    Returns
    -------
    tuple of ndarray
        (x, y) arrays of shape (n,) in normalized [0, 1] coordinates.
    """
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False) - np.pi / 2
    return (
        0.5 + _POLY_RADIUS * np.cos(theta),
        0.5 + _POLY_RADIUS * np.sin(theta),
    )


def _pick_vertices(
    prev: np.ndarray, n: int, rule: str, rng: np.random.Generator
) -> np.ndarray:
    """Choose the next attracting vertex for each walker.

    Restrictions are implemented by sampling an offset from the previous
    choice: "no_repeat" excludes offset 0, "no_neighbor" also excludes
    offsets 1 and n-1 (falling back to "no_repeat" when the polygon is
    too small to have non-neighbors).

    Parameters
    ----------
    prev : ndarray
        Shape (walkers,), previous vertex index per walker.
    n : int
        Number of polygon vertices.
    rule : str
        One of "none", "no_repeat", "no_neighbor".
    rng : Generator
        Seeded numpy RNG.

    Returns
    -------
    ndarray
        Shape (walkers,), chosen vertex indices.
    """
    if rule == "none":
        return rng.integers(0, n, len(prev))
    if rule == "no_neighbor" and n >= 5:
        offset = rng.integers(2, n - 1, len(prev))
    else:
        offset = rng.integers(1, n, len(prev))
    return (prev + offset) % n


def _accumulate_points(
    params: ChaosGameParams, rng: np.random.Generator, grid: int
) -> tuple[np.ndarray, np.ndarray]:
    """Run the chaos game and bin visited points into a grid.

    Parameters
    ----------
    params : ChaosGameParams
        Generator parameters.
    rng : Generator
        Seeded numpy RNG.
    grid : int
        Histogram resolution (grid x grid bins).

    Returns
    -------
    tuple of ndarray
        (flat_bins, vertex_ids): flattened bin index and attracting
        vertex index for every accumulated point. Points that left the
        canvas are already removed.
    """
    n = params.vertices
    vx, vy = _polygon_vertices(n)
    theta = np.radians(params.twist)
    cos_t, sin_t = np.cos(theta), np.sin(theta)

    total = round(params.points_millions * 1_000_000)
    steps = max(1, -(-total // _WALKERS))  # ceil division

    px = rng.uniform(0, 1, _WALKERS)
    py = rng.uniform(0, 1, _WALKERS)
    prev = rng.integers(0, n, _WALKERS)

    flat_chunks: list[np.ndarray] = []
    vid_chunks: list[np.ndarray] = []

    for step in range(_BURN_IN + steps):
        idx = _pick_vertices(prev, n, params.rule, rng)
        prev = idx

        # Jump: rotate the offset vector by the twist angle, then move
        # a (possibly randomized) fraction of the way along it.
        if params.ratio_spread > 0:
            ratio = params.jump_ratio + rng.uniform(
                -params.ratio_spread / 2, params.ratio_spread / 2, _WALKERS
            )
        else:
            ratio = params.jump_ratio
        ox = vx[idx] - px
        oy = vy[idx] - py
        px = px + ratio * (ox * cos_t - oy * sin_t)
        py = py + ratio * (ox * sin_t + oy * cos_t)

        if params.jitter > 0:
            px = px + rng.normal(0.0, params.jitter, _WALKERS)
            py = py + rng.normal(0.0, params.jitter, _WALKERS)

        if step < _BURN_IN:
            continue

        # Bin positions; points outside [0, 1) are dropped.
        ix = np.floor(px * grid).astype(np.int64)
        iy = np.floor(py * grid).astype(np.int64)
        ok = (ix >= 0) & (ix < grid) & (iy >= 0) & (iy < grid)
        flat_chunks.append((iy[ok] * grid + ix[ok]).astype(np.int64))
        vid_chunks.append(idx[ok].astype(np.int8))

    return np.concatenate(flat_chunks), np.concatenate(vid_chunks)


def _compose_ink_layer(
    params: ChaosGameParams,
    flat: np.ndarray,
    vids: np.ndarray,
    grid: int,
    palette: np.ndarray,
    bg: np.ndarray,
) -> np.ndarray:
    """Tone-map point density and composite inks over the paper color.

    Density is normalized against its 99th percentile so the tone
    mapping adapts to point count and grid resolution, keeping preview
    and export visually consistent.

    Parameters
    ----------
    params : ChaosGameParams
        Generator parameters.
    flat : ndarray
        Flattened bin index per point.
    vids : ndarray
        Attracting vertex index per point.
    grid : int
        Histogram resolution.
    palette : ndarray
        Shape (k, 3), ink colors as floats 0-255.
    bg : ndarray
        Shape (3,), paper color as floats 0-255.

    Returns
    -------
    ndarray
        Shape (grid, grid, 3) float32 RGB image, values 0-255.
    """
    n_bins = grid * grid
    count = np.bincount(flat, minlength=n_bins).astype(np.float32)

    # Log tone mapping, normalized so composition survives changes in
    # point count and resolution.
    scale = max(len(flat) / n_bins, 1e-6)
    density = np.log1p(count / scale)
    occupied = density[count > 0]
    norm = np.percentile(occupied, 99.0) if len(occupied) else 1.0
    alpha = np.clip(density / max(norm, 1e-6) * params.exposure, 0.0, 1.0)

    if params.color_mode == "vertex":
        # Mean ink color per bin: accumulate palette-weighted sums.
        point_rgb = palette[vids % len(palette)]
        rgb = np.stack(
            [
                np.bincount(flat, weights=point_rgb[:, c], minlength=n_bins)
                for c in range(3)
            ],
            axis=-1,
        ).astype(np.float32)
        safe_count = np.maximum(count, 1.0)[:, None]
        ink = rgb / safe_count
    else:
        ink = palette_gradient(palette, alpha).astype(np.float32)

    a = (alpha * params.ghost_opacity)[:, None].astype(np.float32)
    out = bg.astype(np.float32) * (1.0 - a) + ink * a
    return out.reshape(grid, grid, 3)


def render(params: ChaosGameParams, seed: int, size: int) -> Image.Image:
    """Render a chaos game image.

    Pure function: same (params, seed, size) always produces the same
    image. Point generation happens in normalized [0, 1] space so the
    composition is resolution-independent.

    Parameters
    ----------
    params : ChaosGameParams
        Generator parameters.
    seed : int
        Random seed for reproducibility.
    size : int
        Output image width and height in pixels.

    Returns
    -------
    Image.Image
        The rendered chaos game image (RGB).
    """
    rng = np.random.default_rng(seed)

    grid = min(size, _MAX_GRID)
    flat, vids = _accumulate_points(params, rng, grid)

    palette = np.array(
        [hex_to_rgb(c.strip()) for c in params.colors.split(",")],
        dtype=np.float32,
    )
    bg = np.array(hex_to_rgb(params.background), dtype=np.float32)

    arr = _compose_ink_layer(params, flat, vids, grid, palette, bg)

    if grid != size:
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        arr = np.asarray(img, dtype=np.float32)

    arr = apply_vignette_and_grain(arr, params.vignette, params.grain, rng)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
