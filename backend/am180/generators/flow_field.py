"""Flow field generator.

Particles drift through a 2D noise-driven vector field, leaving trails
that produce organic, flowing patterns. The algorithm:

1. Build a gradient noise field on an internal grid.
2. Convert noise values to angles.
3. Seed particles at random positions in [0, 1] x [0, 1].
4. March each particle through the angle field (vectorized with numpy).
5. Draw each particle's trail as a colored polyline with Pillow.
"""
import numpy as np
from PIL import Image, ImageDraw
from pydantic import BaseModel, Field

from am180.rendering import PALETTES, hex_to_rgb
from am180.schemas import ParamSpec


class FlowFieldParams(BaseModel):
    """Parameters for the flow field generator.

    Attributes
    ----------
    noise_scale : float
        Controls noise frequency. Higher values produce finer,
        more turbulent textures.
    angle_range : float
        Multiplier for converting noise to angles. Low values give
        smooth parallel flow, high values give swirly chaos.
    particle_density : float
        Particles per pixel-squared. Actual count scales with
        canvas area: n = round(density * size * size).
    step_size : float
        How far each particle moves per step, as a fraction of
        canvas size.
    max_steps : int
        Maximum number of steps per particle trail.
    line_width : float
        Trail thickness as a fraction of canvas size.
    background : str
        Canvas background color as hex string.
    palette : str
        Name of the color palette for particle trails.
    """

    noise_scale: float = Field(3.0, ge=0.5, le=10.0)
    angle_range: float = Field(1.0, ge=0.25, le=4.0)
    particle_density: float = Field(0.001, ge=0.0001, le=0.01)
    step_size: float = Field(0.002, ge=0.0005, le=0.01)
    max_steps: int = Field(200, ge=10, le=1000)
    line_width: float = Field(0.0015, ge=0.0005, le=0.005)
    background: str = Field("#0a0a14")
    palette: str = Field("warm")


PARAM_SCHEMA: list[ParamSpec] = [
    ParamSpec(
        id="noise_scale", label="Noise scale", type="float",
        min=0.5, max=10.0, step=0.1, default=3.0, group="field",
    ),
    ParamSpec(
        id="angle_range", label="Angle range", type="float",
        min=0.25, max=4.0, step=0.05, default=1.0, group="field",
    ),
    ParamSpec(
        id="particle_density", label="Particle density", type="float",
        min=0.0001, max=0.01, step=0.0001, default=0.001,
        group="particles",
    ),
    ParamSpec(
        id="step_size", label="Step size", type="float",
        min=0.0005, max=0.01, step=0.0005, default=0.002,
        group="particles",
    ),
    ParamSpec(
        id="max_steps", label="Max steps", type="int",
        min=10, max=1000, step=10, default=200, group="particles",
    ),
    ParamSpec(
        id="line_width", label="Line width", type="float",
        min=0.0005, max=0.005, step=0.0001, default=0.0015,
        group="render",
    ),
    ParamSpec(
        id="background", label="Background", type="color",
        default="#0a0a14", group="render",
    ),
    ParamSpec(
        id="palette", label="Palette", type="select", default="warm",
        group="render",
        options=[
            {"value": "warm", "label": "Warm"},
            {"value": "cool", "label": "Cool"},
            {"value": "mono", "label": "Mono"},
        ],
    ),
]


# Internal grid resolution for the pre-computed angle field. Independent
# of output image size - chosen to give smooth interpolation.
_NOISE_GRID = 256


def _gradient_noise(
    xs: np.ndarray, ys: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """Evaluate 2D gradient (Perlin-like) noise at sample points.

    Parameters
    ----------
    xs : ndarray
        X coordinates of sample points (any shape).
    ys : ndarray
        Y coordinates, same shape as xs.
    rng : Generator
        Seeded numpy RNG for reproducible gradient vectors.

    Returns
    -------
    ndarray
        Noise values in approximately [-0.7, 0.7], same shape as xs.
    """
    # Lattice bounds covering all sample points
    x0 = int(np.floor(xs.min()))
    x1 = int(np.ceil(xs.max())) + 1
    y0 = int(np.floor(ys.min()))
    y1 = int(np.ceil(ys.max())) + 1

    # Random unit-length gradient vectors at each lattice point
    angles = rng.uniform(0, 2 * np.pi, (y1 - y0 + 1, x1 - x0 + 1))
    gx = np.cos(angles)
    gy = np.sin(angles)

    # Integer cell coordinates for each sample
    xi = np.floor(xs).astype(int) - x0
    yi = np.floor(ys).astype(int) - y0
    # Fractional position within cell
    xf = xs - np.floor(xs)
    yf = ys - np.floor(ys)

    # Smoothstep (Hermite interpolation weights)
    u = xf * xf * (3 - 2 * xf)
    v = yf * yf * (3 - 2 * yf)

    # Dot product of gradient and offset vector at each of 4 corners
    n00 = gx[yi, xi] * xf + gy[yi, xi] * yf
    n10 = gx[yi, xi + 1] * (xf - 1) + gy[yi, xi + 1] * yf
    n01 = gx[yi + 1, xi] * xf + gy[yi + 1, xi] * (yf - 1)
    n11 = gx[yi + 1, xi + 1] * (xf - 1) + gy[yi + 1, xi + 1] * (yf - 1)

    # Bilinear interpolation with smoothstep weights
    nx0 = n00 + u * (n10 - n00)
    nx1 = n01 + u * (n11 - n01)
    return nx0 + v * (nx1 - nx0)


def _build_angle_field(
    params: FlowFieldParams, rng: np.random.Generator
) -> np.ndarray:
    """Build the 2D angle field on a fixed internal grid.

    Returns
    -------
    ndarray
        Shape (_NOISE_GRID, _NOISE_GRID) of angle values in radians.
    """
    coords = np.linspace(0, params.noise_scale, _NOISE_GRID)
    gx, gy = np.meshgrid(coords, coords)
    noise = _gradient_noise(gx.ravel(), gy.ravel(), rng)
    return noise.reshape(_NOISE_GRID, _NOISE_GRID) * np.pi * params.angle_range


def _march_particles(
    start: np.ndarray,
    angles: np.ndarray,
    step_size: float,
    max_steps: int,
) -> np.ndarray:
    """March particles through the angle field.

    Each particle steps forward by step_size in the direction given by
    the interpolated angle at its current position. Particles that leave
    the [0, 1] canvas are marked dead and stop moving.

    Parameters
    ----------
    start : ndarray
        Shape (n_particles, 2), initial positions in [0, 1].
    angles : ndarray
        Shape (grid, grid), pre-computed angle field.
    step_size : float
        Step length in normalized coordinates.
    max_steps : int
        Maximum number of marching steps.

    Returns
    -------
    ndarray
        Shape (actual_steps + 1, n_particles, 2). Position of every
        particle at every step.
    """
    n = len(start)
    grid = angles.shape[0]
    trail = np.empty((max_steps + 1, n, 2))
    trail[0] = start
    alive = np.ones(n, dtype=bool)
    last_step = 0

    for step in range(max_steps):
        pos = trail[step]

        # Map [0, 1] positions to grid indices for interpolation
        gx = np.clip(pos[:, 0] * (grid - 1), 0, grid - 1.001)
        gy = np.clip(pos[:, 1] * (grid - 1), 0, grid - 1.001)
        xi = np.clip(gx.astype(int), 0, grid - 2)
        yi = np.clip(gy.astype(int), 0, grid - 2)
        fx = gx - xi
        fy = gy - yi

        # Bilinear interpolation of angle
        a = (angles[yi, xi] * (1 - fx) * (1 - fy)
             + angles[yi, xi + 1] * fx * (1 - fy)
             + angles[yi + 1, xi] * (1 - fx) * fy
             + angles[yi + 1, xi + 1] * fx * fy)

        # Step forward (only alive particles move)
        new_pos = pos.copy()
        new_pos[alive, 0] += np.cos(a[alive]) * step_size
        new_pos[alive, 1] += np.sin(a[alive]) * step_size

        # Kill particles that left the canvas
        out = ((new_pos[:, 0] < 0) | (new_pos[:, 0] > 1)
               | (new_pos[:, 1] < 0) | (new_pos[:, 1] > 1))
        alive &= ~out

        trail[step + 1] = new_pos
        last_step = step + 1

        if not alive.any():
            break

    return trail[:last_step + 1]


def _draw_trails(
    img: Image.Image,
    trail: np.ndarray,
    colors: list[tuple[int, int, int]],
    line_width: int,
) -> None:
    """Draw particle trails as polylines onto the image.

    Parameters
    ----------
    img : Image
        Target image (modified in place).
    trail : ndarray
        Shape (steps, n_particles, 2), positions in [0, 1].
    colors : list of (r, g, b)
        One color per particle.
    line_width : int
        Line width in pixels.
    """
    draw = ImageDraw.Draw(img)
    w = img.size[0]
    steps, n_particles, _ = trail.shape

    for i in range(n_particles):
        points: list[tuple[float, float]] = []
        for s in range(steps):
            x, y = trail[s, i]
            if 0 <= x <= 1 and 0 <= y <= 1:
                points.append((x * w, y * w))
            else:
                # Particle left the canvas - draw what we have and reset
                if len(points) >= 2:
                    draw.line(points, fill=colors[i], width=line_width)
                points = []
        if len(points) >= 2:
            draw.line(points, fill=colors[i], width=line_width)


def render(params: FlowFieldParams, seed: int, size: int) -> Image.Image:
    """Render a flow field image.

    Pure function: same (params, seed, size) always produces the same
    image. All coordinates are in normalized [0, 1] space so the
    composition is resolution-independent.

    Parameters
    ----------
    params : FlowFieldParams
        Generator parameters.
    seed : int
        Random seed for reproducibility.
    size : int
        Output image width and height in pixels.

    Returns
    -------
    Image.Image
        The rendered flow field image (RGB).
    """
    rng = np.random.default_rng(seed)

    # 1-2. Build angle field from gradient noise
    angles = _build_angle_field(params, rng)

    # 3. Seed particles in normalized [0, 1] space
    n_particles = max(1, round(params.particle_density * size * size))
    start = rng.uniform(0, 1, (n_particles, 2))

    # 4. March particles through the angle field
    trail = _march_particles(start, angles, params.step_size, params.max_steps)

    # 5-6. Rasterize trails with palette colors
    palette = PALETTES.get(params.palette, PALETTES["warm"])
    palette_rgb = [hex_to_rgb(c) for c in palette]
    colors = [palette_rgb[i % len(palette_rgb)] for i in range(n_particles)]
    line_px = max(1, round(params.line_width * size))

    img = Image.new("RGB", (size, size), params.background)
    _draw_trails(img, trail, colors, line_px)

    return img
