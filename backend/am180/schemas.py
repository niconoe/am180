"""Pydantic models for API request/response and parameter schema."""
from pydantic import BaseModel


class ParamSpec(BaseModel):
    """Describes one UI control for a generator parameter.

    Attributes
    ----------
    id : str
        Machine name, matches the corresponding Pydantic model field.
    label : str
        Human-readable label shown in the frontend.
    type : str
        One of "float", "int", "color", "select".
    min : float or None
        Minimum value (for float/int sliders).
    max : float or None
        Maximum value (for float/int sliders).
    step : float or None
        Slider step increment.
    default : float or int or str or None
        Default value for the control.
    group : str or None
        Optional group name for visual grouping in the UI.
    options : list of dict or None
        For type="select": list of {"value": ..., "label": ...} dicts.
    """

    id: str
    label: str
    type: str
    min: float | None = None
    max: float | None = None
    step: float | None = None
    default: float | int | str | None = None
    group: str | None = None
    options: list[dict[str, str]] | None = None


class GeneratorInfo(BaseModel):
    """Summary returned by GET /api/generators.

    Attributes
    ----------
    id : str
        URL-safe identifier for the generator.
    name : str
        Human-readable display name.
    description : str
        Short description shown in the generator picker.
    """

    id: str
    name: str
    description: str


class GeneratorSchema(BaseModel):
    """Full parameter schema returned by GET /api/generators/{id}/schema.

    Attributes
    ----------
    id : str
        Generator identifier.
    name : str
        Display name.
    params : list of ParamSpec
        Parameter definitions for the frontend.
    """

    id: str
    name: str
    params: list[ParamSpec]


class RenderRequest(BaseModel):
    """Request body for POST /api/preview and POST /api/render.

    Attributes
    ----------
    generator : str
        ID of the generator to use.
    params : dict
        Parameter values keyed by param id.
    seed : int
        Random seed owned by the frontend.
    """

    generator: str
    params: dict[str, int | float | str]
    seed: int
