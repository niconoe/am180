"""Generator registry.

Each generator is a named entry with a Pydantic params model, a UI schema
list, and a render function. Adding a new generator means adding a module
under generators/ and registering it here. api.py does not change.
"""
from collections.abc import Callable
from dataclasses import dataclass

from PIL import Image
from pydantic import BaseModel

from am180.generators import chaos_game, colony, flow_field, growth, hello
from am180.schemas import ParamSpec


@dataclass(frozen=True)
class Generator:
    """A registered generator.

    Attributes
    ----------
    id : str
        URL-safe identifier (e.g. "flow_field").
    name : str
        Human-readable display name.
    description : str
        Short description shown in the generator picker.
    params_model : type of BaseModel
        Pydantic model used for server-side validation.
    param_schema : list of ParamSpec
        UI metadata sent to the frontend.
    render : callable
        Pure function (params, seed, size) -> PIL Image.
    """

    id: str
    name: str
    description: str
    params_model: type[BaseModel]
    param_schema: list[ParamSpec]
    render: Callable[..., Image.Image]


GENERATORS: dict[str, Generator] = {
    "colony": Generator(
        id="colony",
        name="Colony",
        description="Regular polygons budding smaller copies from their corners, like coral colonies",
        params_model=colony.ColonyParams,
        param_schema=colony.PARAM_SCHEMA,
        render=colony.render,
    ),
    "flow_field": Generator(
        id="flow_field",
        name="Flow Field",
        description="Particles drifting through a noise-driven vector field",
        params_model=flow_field.FlowFieldParams,
        param_schema=flow_field.PARAM_SCHEMA,
        render=flow_field.render,
    ),
    "chaos_game": Generator(
        id="chaos_game",
        name="Chaos Game",
        description="Ghostly generalized Sierpinski fractals as vintage ink-density fields",
        params_model=chaos_game.ChaosGameParams,
        param_schema=chaos_game.PARAM_SCHEMA,
        render=chaos_game.render,
    ),
    "growth": Generator(
        id="growth",
        name="Growth",
        description="Differential growth: coral-like rings of a buckling, self-avoiding curve",
        params_model=growth.GrowthParams,
        param_schema=growth.PARAM_SCHEMA,
        render=growth.render,
    ),
    "hello": Generator(
        id="hello",
        name="Hello",
        description="Solid-color test generator for pipeline validation",
        params_model=hello.HelloParams,
        param_schema=hello.PARAM_SCHEMA,
        render=hello.render,
    ),
}
