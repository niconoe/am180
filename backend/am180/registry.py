"""Generator registry.

Each generator is a named entry with a Pydantic params model, a UI schema
list, and a render function. Adding a new generator means adding a module
under generators/ and registering it here. api.py does not change.
"""
from collections.abc import Callable
from dataclasses import dataclass

from PIL import Image
from pydantic import BaseModel

from am180.generators import hello
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
    "hello": Generator(
        id="hello",
        name="Hello",
        description="Solid-color test generator for pipeline validation",
        params_model=hello.HelloParams,
        param_schema=hello.PARAM_SCHEMA,
        render=hello.render,
    ),
}
