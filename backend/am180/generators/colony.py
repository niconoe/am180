"""Colony generator.

Recursive polygon colonies: a few large polygons seed the canvas, and
every polygon can bud smaller copies of itself from its corners,
shrinking each generation. The aggregates read as coral colonies,
barnacle clusters or specimens from an antique biology plate.

Beyond the classic flat-shape look, several traits make the output
feel hand-made and slightly haunted:

- irregularity deforms every polygon as if cut from paper by hand;
- buds can sit a little off their parent corner (spread), connected
  by a thin stem with a joint dot, like a scientific diagram;
- each shape may leave faded ghost echoes along the direction it grew
  from, like misregistered vintage printing;
- colors follow lineages: a bud inherits its parent's palette slot
  and sometimes drifts one step, so branches develop tonal families.

Every trait has a zero position that restores crisp, flat,
corner-touching colonies.

1. Place cluster seeds spread apart, each with its own polygon family
   (number of sides) and orientation.
2. Grow each colony breadth-first: every vertex of every polygon may
   sprout a child polygon at (or slightly beyond) that corner.
3. Draw stems, then all shapes largest-first, each preceded by its
   ghost echoes.
4. Finish with the house grain and vignette on paper.
"""
import math
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw
from pydantic import BaseModel, Field

from am180.rendering import apply_vignette_and_grain, hex_to_rgb
from am180.schemas import ParamSpec


class ColonyParams(BaseModel):
    """Parameters for the colony generator.

    Attributes
    ----------
    clusters : int
        Number of separate colonies on the canvas.
    shapes : str
        Polygon family: "quads" (rotated squares), "hexes" (hexagons),
        or "mixed" (each colony picks 4, 6 or 7 sides).
    root_size : float
        Radius of each colony's founding polygon, in normalized canvas
        units.
    shrink : float
        Child radius as a fraction of its parent's. Lower values give
        fine, dusty edges; higher values give chunky aggregates.
    bud_chance : float
        Probability that a polygon corner sprouts a child.
    depth : int
        Maximum budding generations.
    wobble : float
        Random rotation of children relative to their parent, in
        degrees. Zero keeps colonies crystalline and aligned.
    irregularity : float
        Hand-cut deformation of every polygon (0 = perfect regular
        shapes, 1 = strongly warped paper cutouts).
    spread : float
        How far buds sit beyond their parent corner, as a fraction of
        their own size. Above zero, a thin stem with a joint dot
        connects parent and bud. Zero restores touching corners and
        draws no stems.
    echoes : int
        Number of faded ghost copies each bud leaves behind along its
        growth direction. Zero disables echoes.
    color_drift : float
        Chance per generation that a bud's color steps to an adjacent
        palette slot instead of keeping its parent's. Zero makes each
        colony monochrome; high values let branches wander across the
        palette.
    fill_opacity : float
        Opacity of shape fills. 1.0 gives flat, paper-cut shapes;
        lower values let older generations show through new buds.
    line_width : float
        Outline and stem width as a fraction of canvas size.
    grain : float
        Monochrome film grain amplitude. Zero disables grain.
    vignette : float
        Strength of the darkened corners. Zero disables the vignette.
    background : str
        Paper color as hex string.
    colors : str
        Comma-separated hex colors. Root shapes favor earlier colors,
        so lead with quiet tones and end with accents. The frontend
        owns palette definitions and sends the values.
    """

    clusters: int = Field(2, ge=1, le=5)
    shapes: Literal["mixed", "quads", "hexes"] = "mixed"
    root_size: float = Field(0.16, ge=0.06, le=0.25)
    shrink: float = Field(0.48, ge=0.35, le=0.6)
    bud_chance: float = Field(0.55, ge=0.2, le=0.9)
    depth: int = Field(5, ge=2, le=7)
    wobble: float = Field(8.0, ge=0.0, le=30.0)
    irregularity: float = Field(0.35, ge=0.0, le=1.0)
    spread: float = Field(0.3, ge=0.0, le=1.0)
    echoes: int = Field(2, ge=0, le=3)
    color_drift: float = Field(0.35, ge=0.0, le=1.0)
    fill_opacity: float = Field(1.0, ge=0.4, le=1.0)
    line_width: float = Field(0.0012, ge=0.0004, le=0.004)
    grain: float = Field(0.03, ge=0.0, le=0.15)
    vignette: float = Field(0.15, ge=0.0, le=1.0)
    background: str = Field("#eef1e4")
    colors: str = Field("#c3d5d3,#8fa8bd,#5b7ea6,#c94a44,#2e3a55")


PARAM_SCHEMA: list[ParamSpec] = [
    ParamSpec(
        id="clusters", label="Clusters", type="int",
        min=1, max=5, step=1, default=2, group="colony",
    ),
    ParamSpec(
        id="shapes", label="Shapes", type="select",
        default="mixed", group="colony",
        options=[
            {"value": "mixed", "label": "Mixed"},
            {"value": "quads", "label": "Squares"},
            {"value": "hexes", "label": "Hexagons"},
        ],
    ),
    ParamSpec(
        id="root_size", label="Root size", type="float",
        min=0.06, max=0.25, step=0.005, default=0.16, group="colony",
    ),
    ParamSpec(
        id="shrink", label="Shrink", type="float",
        min=0.35, max=0.6, step=0.01, default=0.48, group="colony",
    ),
    ParamSpec(
        id="bud_chance", label="Bud chance", type="float",
        min=0.2, max=0.9, step=0.05, default=0.55, group="colony",
    ),
    ParamSpec(
        id="depth", label="Depth", type="int",
        min=2, max=7, step=1, default=5, group="colony",
    ),
    ParamSpec(
        id="wobble", label="Wobble (deg)", type="float",
        min=0.0, max=30.0, step=1.0, default=8.0, group="colony",
    ),
    ParamSpec(
        id="irregularity", label="Irregularity", type="float",
        min=0.0, max=1.0, step=0.05, default=0.35, group="character",
    ),
    ParamSpec(
        id="spread", label="Spread", type="float",
        min=0.0, max=1.0, step=0.05, default=0.3, group="character",
    ),
    ParamSpec(
        id="echoes", label="Ghost echoes", type="int",
        min=0, max=3, step=1, default=2, group="character",
    ),
    ParamSpec(
        id="color_drift", label="Color drift", type="float",
        min=0.0, max=1.0, step=0.05, default=0.35, group="character",
    ),
    ParamSpec(
        id="fill_opacity", label="Fill opacity", type="float",
        min=0.4, max=1.0, step=0.05, default=1.0, group="render",
    ),
    ParamSpec(
        id="line_width", label="Line width", type="float",
        min=0.0004, max=0.004, step=0.0001, default=0.0012, group="render",
    ),
    ParamSpec(
        id="grain", label="Grain", type="float",
        min=0.0, max=0.15, step=0.005, default=0.03, group="render",
    ),
    ParamSpec(
        id="vignette", label="Vignette", type="float",
        min=0.0, max=1.0, step=0.05, default=0.15, group="render",
    ),
    ParamSpec(
        id="background", label="Paper", type="color",
        default="#eef1e4", group="render",
    ),
    ParamSpec(
        id="colors", label="Palette", type="palette",
        size=5, default_preset="porcelain", group="render",
    ),
]


# Hard cap on total shapes across all colonies, bounding render time
# at high bud_chance / depth settings.
_MAX_SHAPES = 3000

# Shapes smaller than this radius (normalized units) stop budding.
_MIN_RADIUS = 0.0025

# Polygon side counts a colony may use in "mixed" mode.
_MIXED_SIDES = (4, 6, 7)

# Supersampling factor for crisp antialiased edges.
_SUPERSAMPLE = 2

# Maximum rasterization resolution (see growth._MAX_RASTER).
_MAX_RASTER = 4096

# Opacity of the strongest (most recent) ghost echo; earlier echoes
# fade toward zero from this value.
_ECHO_OPACITY = 0.30


def _cluster_centers(
    n: int, rng: np.random.Generator
) -> list[tuple[float, float]]:
    """Choose colony seed positions, best-effort spread apart.

    Parameters
    ----------
    n : int
        Number of colonies.
    rng : Generator
        Seeded numpy RNG.

    Returns
    -------
    list of tuple
        (x, y) centers in normalized coordinates.
    """
    centers: list[tuple[float, float]] = []
    min_dist = 0.5 / max(1.4, n ** 0.5)
    for _ in range(n):
        best = None
        best_dist = -1.0
        # Rejection sampling with a fixed budget; keep the candidate
        # farthest from existing centers if none passes the threshold.
        for _attempt in range(30):
            cand = (rng.uniform(0.22, 0.78), rng.uniform(0.22, 0.78))
            dist = min(
                (math.dist(cand, c) for c in centers), default=1.0
            )
            if dist > best_dist:
                best, best_dist = cand, dist
            if dist >= min_dist:
                break
        centers.append(best)
    return centers


def _cutout_offsets(
    sides: int,
    rotation: float,
    irregularity: float,
    rng: np.random.Generator,
) -> list[tuple[float, float]]:
    """Vertex offsets of a hand-cut polygon with circumradius 1.

    Each vertex of the regular polygon is perturbed in angle and
    radius, scaled by irregularity, so the shape looks cut from paper
    rather than computed.

    Parameters
    ----------
    sides : int
        Number of sides.
    rotation : float
        Rotation in radians.
    irregularity : float
        Deformation amount in [0, 1].
    rng : Generator
        Seeded numpy RNG (consumed even at zero irregularity, so the
        parameter does not shift downstream randomness).

    Returns
    -------
    list of tuple
        (dx, dy) offsets from the shape center, for circumradius 1.
    """
    angle_jitter = rng.normal(0.0, 0.35 / sides, sides) * irregularity
    radius_jitter = 1.0 + rng.normal(0.0, 0.13, sides) * irregularity
    return [
        (
            radius_jitter[k]
            * math.cos(rotation + 2 * math.pi * k / sides + angle_jitter[k]),
            radius_jitter[k]
            * math.sin(rotation + 2 * math.pi * k / sides + angle_jitter[k]),
        )
        for k in range(sides)
    ]


def _drift_color(
    parent_idx: int, n_colors: int, drift: float, rng: np.random.Generator
) -> int:
    """Choose a bud's palette slot from its parent's.

    Parameters
    ----------
    parent_idx : int
        Parent's palette index.
    n_colors : int
        Palette size.
    drift : float
        Probability of stepping to an adjacent slot.
    rng : Generator
        Seeded numpy RNG (always consumed, for stable randomness).

    Returns
    -------
    int
        The bud's palette index.
    """
    roll = rng.random()
    step = int(rng.integers(0, 2)) * 2 - 1  # -1 or +1
    if roll >= drift:
        return parent_idx
    return int(np.clip(parent_idx + step, 0, n_colors - 1))


def _grow_colonies(
    params: ColonyParams, rng: np.random.Generator, n_colors: int
) -> list[dict]:
    """Grow all colonies breadth-first.

    Returns
    -------
    list of dict
        Shapes in breadth-first order (parents before children), with
        keys:

        - center: (x, y) shape center
        - radius: circumradius
        - offsets: hand-cut vertex offsets for circumradius 1
        - origin: (x, y) parent corner this shape grew from, or None
          for colony roots
        - color_idx: palette slot
        - generation: budding depth, 0 for roots
    """
    if params.shapes == "quads":
        side_choices = (4,)
    elif params.shapes == "hexes":
        side_choices = (6,)
    else:
        side_choices = _MIXED_SIDES

    weights = np.array(
        [1.0 / (i + 1) ** 1.8 for i in range(n_colors)]
    )
    weights /= weights.sum()

    queue: list[dict] = []
    for cx, cy in _cluster_centers(params.clusters, rng):
        rotation = rng.uniform(0, 2 * math.pi)
        sides = int(rng.choice(side_choices))
        queue.append(
            {
                "center": (cx, cy),
                "radius": params.root_size,
                "rotation": rotation,
                "sides": sides,
                "offsets": _cutout_offsets(
                    sides, rotation, params.irregularity, rng
                ),
                "origin": None,
                "color_idx": int(rng.choice(n_colors, p=weights)),
                "generation": 0,
            }
        )

    shapes: list[dict] = []
    head = 0
    while head < len(queue) and len(queue) < _MAX_SHAPES:
        shape = queue[head]
        head += 1
        shapes.append(shape)

        child_radius = shape["radius"] * params.shrink
        if shape["generation"] >= params.depth or child_radius < _MIN_RADIUS:
            continue

        cx, cy = shape["center"]
        for dx, dy in shape["offsets"]:
            if len(queue) >= _MAX_SHAPES:
                break
            if rng.random() >= params.bud_chance:
                continue
            # Corner position, and outward growth direction from it.
            vx = cx + dx * shape["radius"]
            vy = cy + dy * shape["radius"]
            norm = math.hypot(dx, dy)
            gap = params.spread * child_radius * 2.5
            child_cx = vx + dx / norm * gap
            child_cy = vy + dy / norm * gap

            rotation = shape["rotation"] + rng.normal(
                0.0, math.radians(params.wobble) / 2
            )
            queue.append(
                {
                    "center": (child_cx, child_cy),
                    "radius": child_radius,
                    "rotation": rotation,
                    "sides": shape["sides"],
                    "offsets": _cutout_offsets(
                        shape["sides"], rotation, params.irregularity, rng
                    ),
                    "origin": (vx, vy),
                    "color_idx": _drift_color(
                        shape["color_idx"], n_colors, params.color_drift, rng
                    ),
                    "generation": shape["generation"] + 1,
                }
            )

    # Any shapes still queued past the cap are dropped; queue order is
    # breadth-first so parents always made it in before children.
    shapes.extend(queue[head:_MAX_SHAPES])
    return shapes


def _shape_pixels(
    shape: dict, center: tuple[float, float], radius: float, raster: int
) -> list[tuple[float, float]]:
    """Pixel coordinates of a shape's outline at a given placement.

    Parameters
    ----------
    shape : dict
        Shape carrying the hand-cut vertex offsets.
    center : tuple of float
        Placement center in normalized coordinates (echoes place the
        same outline at interpolated positions).
    radius : float
        Placement circumradius in normalized coordinates.
    raster : int
        Rasterization resolution.

    Returns
    -------
    list of tuple
        (x, y) pixel coordinates of the outline.
    """
    cx, cy = center
    return [
        ((cx + dx * radius) * raster, (cy + dy * radius) * raster)
        for dx, dy in shape["offsets"]
    ]


def _paste_translucent(
    img: Image.Image,
    px: list[tuple[float, float]],
    fill: tuple[int, ...],
    outline: tuple[int, ...] | None,
    outline_w: int,
) -> None:
    """Alpha-composite one polygon onto the image via a bbox tile.

    Parameters
    ----------
    img : Image
        Target RGB image, modified in place.
    px : list of tuple
        Polygon outline in pixel coordinates.
    fill : tuple
        RGBA fill color.
    outline : tuple or None
        RGBA outline color, or None for no outline.
    outline_w : int
        Outline width in pixels.
    """
    raster = img.size[0]
    xs = [p[0] for p in px]
    ys = [p[1] for p in px]
    x0 = max(0, int(min(xs)) - outline_w - 1)
    y0 = max(0, int(min(ys)) - outline_w - 1)
    x1 = min(raster, int(max(xs)) + outline_w + 2)
    y1 = min(raster, int(max(ys)) + outline_w + 2)
    if x1 <= x0 or y1 <= y0:
        return
    tile = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    tile_draw = ImageDraw.Draw(tile)
    local = [(x - x0, y - y0) for x, y in px]
    tile_draw.polygon(local, fill=fill, outline=outline, width=outline_w)
    region = img.crop((x0, y0, x1, y1)).convert("RGBA")
    img.paste(Image.alpha_composite(region, tile).convert("RGB"), (x0, y0))


def _draw_stems(
    img: Image.Image,
    shapes: list[dict],
    colors: list[tuple[int, int, int]],
    params: ColonyParams,
    raster: int,
) -> None:
    """Draw parent-to-bud stems with joint dots, under the shapes.

    Parameters
    ----------
    img : Image
        Target RGB image, modified in place.
    shapes : list of dict
        Shapes from _grow_colonies.
    colors : list of (r, g, b)
        Fill color per shape (stems use the darkened bud color).
    params : ColonyParams
        Generator parameters.
    raster : int
        Rasterization resolution.
    """
    draw = ImageDraw.Draw(img)
    stem_w = max(1, round(params.line_width * raster))
    for i, shape in enumerate(shapes):
        if shape["origin"] is None:
            continue
        ox, oy = shape["origin"]
        cx, cy = shape["center"]
        ink = tuple(int(c * 0.55) for c in colors[i])
        draw.line(
            [(ox * raster, oy * raster), (cx * raster, cy * raster)],
            fill=ink,
            width=stem_w,
        )
        # Joint dot at the middle of the stem.
        mx, my = (ox + cx) / 2 * raster, (oy + cy) / 2 * raster
        r_dot = stem_w * 1.6
        draw.ellipse(
            [mx - r_dot, my - r_dot, mx + r_dot, my + r_dot], fill=ink
        )


def _draw_shapes(
    shapes: list[dict],
    colors: list[tuple[int, int, int]],
    params: ColonyParams,
    raster: int,
) -> Image.Image:
    """Draw stems, echoes and shapes largest-first onto the paper.

    Parameters
    ----------
    shapes : list of dict
        Shapes from _grow_colonies, with parallel colors list.
    colors : list of (r, g, b)
        Fill color per shape.
    params : ColonyParams
        Generator parameters.
    raster : int
        Rasterization resolution in pixels.

    Returns
    -------
    Image.Image
        RGB image of the drawn colonies.
    """
    img = Image.new("RGB", (raster, raster), params.background)
    draw = ImageDraw.Draw(img)
    outline_w = max(1, round(params.line_width * raster))
    alpha = int(round(params.fill_opacity * 255))

    if params.spread > 0:
        _draw_stems(img, shapes, colors, params, raster)

    # Largest first so buds land on top of their parents. Sorting is
    # stable, so equal radii keep breadth-first (parent-first) order.
    order = sorted(
        range(len(shapes)), key=lambda i: -shapes[i]["radius"]
    )
    for i in order:
        shape = shapes[i]
        fill = colors[i]
        outline = tuple(int(c * 0.55) for c in fill)

        # Ghost echoes: faded copies along the growth path, oldest
        # (closest to the parent corner, smallest) first.
        if params.echoes > 0 and shape["origin"] is not None:
            ox, oy = shape["origin"]
            cx, cy = shape["center"]
            for k in range(params.echoes):
                t = (k + 1) / (params.echoes + 1)
                e_center = (ox + (cx - ox) * t, oy + (cy - oy) * t)
                e_radius = shape["radius"] * (0.55 + 0.45 * t)
                e_alpha = int(round(_ECHO_OPACITY * t * 255))
                px = _shape_pixels(shape, e_center, e_radius, raster)
                _paste_translucent(img, px, fill + (e_alpha,), None, 0)

        px = _shape_pixels(shape, shape["center"], shape["radius"], raster)
        if alpha >= 255:
            draw.polygon(px, fill=fill, outline=outline, width=outline_w)
        else:
            _paste_translucent(
                img, px, fill + (alpha,), outline + (255,), outline_w
            )

    return img


def render(params: ColonyParams, seed: int, size: int) -> Image.Image:
    """Render a colony image.

    Pure function: same (params, seed, size) always produces the same
    image. Colony growth happens in normalized [0, 1] space so the
    composition is resolution-independent.

    Parameters
    ----------
    params : ColonyParams
        Generator parameters.
    seed : int
        Random seed for reproducibility.
    size : int
        Output image width and height in pixels.

    Returns
    -------
    Image.Image
        The rendered colony image (RGB).
    """
    rng = np.random.default_rng(seed)

    palette = [hex_to_rgb(c.strip()) for c in params.colors.split(",")]
    shapes = _grow_colonies(params, rng, len(palette))
    colors = [palette[s["color_idx"]] for s in shapes]

    raster = min(size * _SUPERSAMPLE, _MAX_RASTER)
    img = _draw_shapes(shapes, colors, params, raster)

    if raster != size:
        img = img.resize((size, size), Image.Resampling.LANCZOS)

    arr = np.asarray(img, dtype=np.float32)
    arr = apply_vignette_and_grain(arr, params.vignette, params.grain, rng)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
