"""Trivial 'hello' generator for testing the render pipeline.

Renders a solid-color square. Exists so Phase 2 can exercise the full
pipeline (endpoints, registry, ParamSpec, seed contract) before the real
flow field algorithm lands in Phase 3.
"""
from PIL import Image
from pydantic import BaseModel, Field

from am180.schemas import ParamSpec


class HelloParams(BaseModel):
    """Parameters for the hello generator.

    Attributes
    ----------
    color : str
        Fill color as a hex string (e.g. "#ff0000").
    """

    color: str = Field("#ff0000", description="Fill color as hex string")


PARAM_SCHEMA: list[ParamSpec] = [
    ParamSpec(
        id="color",
        label="Fill color",
        type="color",
        default="#ff0000",
        group="render",
    ),
]


def render(params: HelloParams, seed: int, size: int) -> Image.Image:
    """Render a solid-color square.

    Parameters
    ----------
    params : HelloParams
        Generator parameters.
    seed : int
        Random seed. Accepted for API contract consistency but does not
        affect output (a solid color is trivially deterministic).
    size : int
        Output image width and height in pixels.

    Returns
    -------
    Image.Image
        A size x size solid-color RGB image.
    """
    return Image.new("RGB", (size, size), params.color)
