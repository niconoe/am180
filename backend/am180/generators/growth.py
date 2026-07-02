"""Differential growth generator.

A small closed loop of points grows like a living organism: neighbor
attraction keeps the curve smooth, short-range repulsion makes it
buckle and fold to avoid itself, and edges that stretch too far split
to add material. The same mechanics shape corals, brain folds and
lichen colonies.

Snapshots of the curve taken while it grows are rendered as stacked
translucent ink rings, colored along the palette by age. Ink from
overlapping rings accumulates like watercolor (Beer-Lambert
absorption), over the same aged-paper, grain and vignette finish used
by the chaos game generator.

1. Start from a slightly noisy circle of points in [0, 1] space.
2. Each iteration: attract points toward their curve neighbors, repel
   points that come within the fold radius (numpy spatial hash), and
   split edges that grew too long.
3. Record the curve at regular intervals.
4. Rasterize the recorded rings oldest to newest, accumulating optical
   depth, then composite the pooled ink over the paper color.
"""
import numpy as np
from PIL import Image, ImageDraw
from pydantic import BaseModel, Field

from am180.rendering import apply_vignette_and_grain, hex_to_rgb, palette_gradient
from am180.schemas import ParamSpec


class GrowthParams(BaseModel):
    """Parameters for the differential growth generator.

    Attributes
    ----------
    iterations : int
        Number of growth steps. More steps let the form grow larger
        and more convoluted.
    rings : int
        Number of curve snapshots drawn as ink rings.
    fold_scale : float
        Repulsion radius in normalized canvas units. Small values give
        tight, wrinkled folds; large values give smooth lobes.
    smoothing : float
        Strength of the neighbor attraction that irons out the curve.
        High smoothing resists buckling.
    push : float
        Strength of the short-range repulsion driving expansion and
        self-avoidance. High push grows faster and wilder.
    start_radius : float
        Radius of the initial circle, in normalized canvas units.
    line_width : float
        Ring stroke width as a fraction of canvas size.
    ghost_opacity : float
        Ink opacity of a single ring. Low values need many overlapping
        rings to darken, giving the ghostly layered look.
    grain : float
        Monochrome film grain amplitude. Zero disables grain.
    vignette : float
        Strength of the darkened corners. Zero disables the vignette.
    background : str
        Paper color as hex string.
    colors : str
        Comma-separated hex colors; rings sweep through them from the
        newest (outermost) ring to the oldest, so the first color
        inks the silhouette. The frontend owns palette definitions
        and sends the values.
    """

    iterations: int = Field(350, ge=50, le=800)
    rings: int = Field(60, ge=5, le=200)
    fold_scale: float = Field(0.03, ge=0.012, le=0.08)
    smoothing: float = Field(0.4, ge=0.1, le=0.9)
    push: float = Field(0.6, ge=0.1, le=1.0)
    start_radius: float = Field(0.08, ge=0.02, le=0.2)
    line_width: float = Field(0.0018, ge=0.0005, le=0.005)
    ghost_opacity: float = Field(0.5, ge=0.05, le=1.0)
    grain: float = Field(0.05, ge=0.0, le=0.15)
    vignette: float = Field(0.3, ge=0.0, le=1.0)
    background: str = Field("#f2e8d5")
    colors: str = Field("#4a3728,#7a5a3d,#a4885e,#c9b183,#e3d3ab")


PARAM_SCHEMA: list[ParamSpec] = [
    ParamSpec(
        id="iterations", label="Iterations", type="int",
        min=50, max=800, step=10, default=350, group="growth",
    ),
    ParamSpec(
        id="rings", label="Rings", type="int",
        min=5, max=200, step=1, default=60, group="growth",
    ),
    ParamSpec(
        id="fold_scale", label="Fold scale", type="float",
        min=0.012, max=0.08, step=0.001, default=0.03, group="growth",
    ),
    ParamSpec(
        id="smoothing", label="Smoothing", type="float",
        min=0.1, max=0.9, step=0.05, default=0.4, group="growth",
    ),
    ParamSpec(
        id="push", label="Push", type="float",
        min=0.1, max=1.0, step=0.05, default=0.6, group="growth",
    ),
    ParamSpec(
        id="start_radius", label="Start radius", type="float",
        min=0.02, max=0.2, step=0.005, default=0.08, group="growth",
    ),
    ParamSpec(
        id="line_width", label="Line width", type="float",
        min=0.0005, max=0.005, step=0.0001, default=0.0018, group="render",
    ),
    ParamSpec(
        id="ghost_opacity", label="Ghost opacity", type="float",
        min=0.05, max=1.0, step=0.05, default=0.5, group="render",
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
        size=5, default_preset="sepia", group="render",
    ),
]


# Number of points on the initial circle.
_START_POINTS = 40

# Hard cap on curve points. When reached, edges stop splitting and
# growth stalls; keeps preview latency and memory bounded.
_MAX_POINTS = 6000

# Edges longer than this fraction of fold_scale split in two.
_SPLIT_FACTOR = 0.75

# Per-iteration displacement cap, as a fraction of fold_scale. Keeps
# the integration stable at high push values.
_MAX_STEP_FACTOR = 0.25

# Curve stays inside a circle of this radius around the canvas center,
# so a fully grown form ends organically instead of against a square
# canvas edge.
_BOUNDARY_RADIUS = 0.47

# Rings are rasterized in this many color batches (one PIL mask each)
# to bound draw calls and array passes, like flow_field's fade levels.
_COLOR_BATCHES = 16

# Maximum rasterization resolution. Drawing happens at up to 2x the
# output size for antialiasing, bounded by this cap so large exports
# stay within reasonable time and memory (they draw at native or
# upscaled resolution instead of supersampled).
_MAX_RASTER = 4096


def _neighbor_pairs(
    pts: np.ndarray, radius: float
) -> tuple[np.ndarray, np.ndarray]:
    """Find all directed point pairs closer than radius.

    Uses a uniform grid (cell size = radius) as a spatial hash: each
    point only checks the 3x3 block of cells around its own, which is
    exact for distances below radius. Pure numpy, no scipy needed.

    Parameters
    ----------
    pts : ndarray
        Shape (n, 2), positions in [0, 1].
    radius : float
        Search radius.

    Returns
    -------
    tuple of ndarray
        (i, j) index arrays of equal length; each entry means point i
        has neighbor j with 0 < dist(i, j) < radius. Both directions
        of every pair are present.
    """
    n = len(pts)
    n_cells = int(1.0 / radius) + 3
    cells = np.floor(pts / radius).astype(np.int64) + 1
    key = cells[:, 0] * n_cells + cells[:, 1]

    order = np.argsort(key, kind="stable")
    sorted_key = key[order]

    all_i: list[np.ndarray] = []
    all_j: list[np.ndarray] = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            probe = key + dx * n_cells + dy
            left = np.searchsorted(sorted_key, probe, side="left")
            right = np.searchsorted(sorted_key, probe, side="right")
            counts = right - left
            total = int(counts.sum())
            if total == 0:
                continue
            i_idx = np.repeat(np.arange(n), counts)
            # Concatenated ranges left[i] .. right[i] for every i.
            seg = np.arange(total) - np.repeat(
                np.cumsum(counts) - counts, counts
            )
            j_idx = order[np.repeat(left, counts) + seg]
            all_i.append(i_idx)
            all_j.append(j_idx)

    i_arr = np.concatenate(all_i)
    j_arr = np.concatenate(all_j)

    d = pts[i_arr] - pts[j_arr]
    d2 = d[:, 0] ** 2 + d[:, 1] ** 2
    ok = (d2 > 0) & (d2 < radius * radius)
    return i_arr[ok], j_arr[ok]


def _grow(
    params: GrowthParams, rng: np.random.Generator
) -> list[np.ndarray]:
    """Run the differential growth simulation.

    Parameters
    ----------
    params : GrowthParams
        Generator parameters.
    rng : Generator
        Seeded numpy RNG.

    Returns
    -------
    list of ndarray
        Recorded curve snapshots, oldest first; each has shape (n_i, 2)
        with points ordered along the closed curve.
    """
    radius = params.fold_scale
    split_len = radius * _SPLIT_FACTOR
    max_step = radius * _MAX_STEP_FACTOR

    theta = np.linspace(0, 2 * np.pi, _START_POINTS, endpoint=False)
    pts = np.stack(
        [
            0.5 + params.start_radius * np.cos(theta),
            0.5 + params.start_radius * np.sin(theta),
        ],
        axis=1,
    )
    pts += rng.normal(0.0, 0.002, pts.shape)

    # Evenly spread snapshot iterations, always including the last one.
    snapshot_iters = set(
        np.linspace(0, params.iterations - 1, params.rings).astype(int)
    )
    snapshots: list[np.ndarray] = []

    for it in range(params.iterations):
        n = len(pts)

        # Attraction: pull each point toward the midpoint of its curve
        # neighbors (irons the curve smooth).
        mid = (np.roll(pts, 1, axis=0) + np.roll(pts, -1, axis=0)) / 2.0
        disp = params.smoothing * 0.5 * (mid - pts)

        # Repulsion: push apart all points closer than the fold radius,
        # except immediate curve neighbors (attraction handles those).
        i_arr, j_arr = _neighbor_pairs(pts, radius)
        gap = (i_arr - j_arr) % n
        nonadjacent = (gap > 1) & (gap < n - 1)
        i_arr, j_arr = i_arr[nonadjacent], j_arr[nonadjacent]
        if len(i_arr):
            d = pts[i_arr] - pts[j_arr]
            dist = np.sqrt(d[:, 0] ** 2 + d[:, 1] ** 2)
            # Linear falloff: strongest at contact, zero at the radius.
            w = (1.0 - dist / radius) / np.maximum(dist, 1e-9)
            force = np.zeros_like(pts)
            np.add.at(force[:, 0], i_arr, d[:, 0] * w)
            np.add.at(force[:, 1], i_arr, d[:, 1] * w)
            disp += params.push * 0.02 * force

        # Clamp displacement for stability, then apply.
        step_len = np.sqrt(disp[:, 0] ** 2 + disp[:, 1] ** 2)
        too_fast = step_len > max_step
        if too_fast.any():
            disp[too_fast] *= (max_step / step_len[too_fast])[:, None]
        pts = pts + disp

        # Project points that left the boundary circle back onto it.
        rel = pts - 0.5
        r = np.sqrt(rel[:, 0] ** 2 + rel[:, 1] ** 2)
        outside = r > _BOUNDARY_RADIUS
        if outside.any():
            pts[outside] = 0.5 + rel[outside] * (
                _BOUNDARY_RADIUS / r[outside]
            )[:, None]

        # Growth: split edges that stretched beyond the threshold, and
        # a few random ones to keep the form growing and asymmetric.
        if n < _MAX_POINTS:
            edge = np.roll(pts, -1, axis=0) - pts
            long_edges = (
                np.sqrt(edge[:, 0] ** 2 + edge[:, 1] ** 2) > split_len
            )
            extra = rng.random(n) < 0.01
            split = np.flatnonzero(long_edges | extra)
            # Insert at most up to the cap, keeping curve order intact.
            split = split[: _MAX_POINTS - n]
            if len(split):
                mids = (pts[split] + pts[(split + 1) % n]) / 2.0
                mids += rng.normal(0.0, 0.0005, mids.shape)
                pts = np.insert(pts, split + 1, mids, axis=0)

        if it in snapshot_iters:
            snapshots.append(pts.copy())

    return snapshots


def _rasterize_rings(
    snapshots: list[np.ndarray],
    params: GrowthParams,
    palette: np.ndarray,
    bg: np.ndarray,
    raster: int,
) -> np.ndarray:
    """Draw the rings and composite pooled ink over the paper color.

    Rings are grouped into _COLOR_BATCHES age bands. Each batch is
    drawn into one grayscale mask, contributing optical depth and
    color weighted by its ink. Total ink converts to opacity with a
    Beer-Lambert curve, so heavily overlapped areas saturate softly
    instead of clipping.

    Parameters
    ----------
    snapshots : list of ndarray
        Curve snapshots, oldest first.
    params : GrowthParams
        Generator parameters.
    palette : ndarray
        Shape (k, 3), ink colors as floats 0-255.
    bg : ndarray
        Shape (3,), paper color as floats 0-255.
    raster : int
        Rasterization resolution in pixels.

    Returns
    -------
    ndarray
        Shape (raster, raster, 3) float32 RGB image, values 0-255.
    """
    n_rings = len(snapshots)
    width = max(1, round(params.line_width * raster))

    depth = np.zeros((raster, raster), dtype=np.float32)
    color_acc = np.zeros((raster, raster, 3), dtype=np.float32)

    n_batches = min(_COLOR_BATCHES, n_rings)
    bounds = np.linspace(0, n_rings, n_batches + 1).astype(int)
    for b in range(n_batches):
        batch = snapshots[bounds[b]:bounds[b + 1]]
        if not batch:
            continue
        mask_img = Image.new("L", (raster, raster), 0)
        draw = ImageDraw.Draw(mask_img)
        for ring in batch:
            px = ring * raster
            points = [(float(x), float(y)) for x, y in px]
            points.append(points[0])
            draw.line(points, fill=255, width=width, joint="curve")

        # Age along the palette: first palette color goes to the
        # newest (outermost) rings so it inks the silhouette.
        t = 1.0 - (bounds[b] + bounds[b + 1]) / 2.0 / n_rings
        ink_rgb = palette_gradient(palette, np.array([t]))[0]

        mask = np.asarray(mask_img, dtype=np.float32) / 255.0
        ink = mask * params.ghost_opacity
        depth += ink
        color_acc += ink[:, :, None] * ink_rgb[None, None, :]

    # Beer-Lambert: opacity saturates smoothly with accumulated ink.
    alpha = 1.0 - np.exp(-1.5 * depth)
    safe_depth = np.maximum(depth, 1e-9)[:, :, None]
    ink_color = color_acc / safe_depth
    return bg[None, None, :] * (1.0 - alpha[:, :, None]) + ink_color * alpha[
        :, :, None
    ]


def render(params: GrowthParams, seed: int, size: int) -> Image.Image:
    """Render a differential growth image.

    Pure function: same (params, seed, size) always produces the same
    image. The simulation runs in normalized [0, 1] space so the
    composition is resolution-independent.

    Parameters
    ----------
    params : GrowthParams
        Generator parameters.
    seed : int
        Random seed for reproducibility.
    size : int
        Output image width and height in pixels.

    Returns
    -------
    Image.Image
        The rendered growth image (RGB).
    """
    rng = np.random.default_rng(seed)

    snapshots = _grow(params, rng)

    palette = np.array(
        [hex_to_rgb(c.strip()) for c in params.colors.split(",")],
        dtype=np.float32,
    )
    bg = np.array(hex_to_rgb(params.background), dtype=np.float32)

    raster = min(size * 2, _MAX_RASTER)
    arr = _rasterize_rings(snapshots, params, palette, bg, raster)

    if raster != size:
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        arr = np.asarray(img, dtype=np.float32)

    arr = apply_vignette_and_grain(arr, params.vignette, params.grain, rng)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
