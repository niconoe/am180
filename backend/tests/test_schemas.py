"""Tests for Pydantic schema models."""
from am180.schemas import (
    GeneratorInfo,
    GeneratorSchema,
    ParamSpec,
    RenderRequest,
)


def test_param_spec_float() -> None:
    spec = ParamSpec(
        id="noise_scale",
        label="Noise scale",
        type="float",
        min=0.5,
        max=10.0,
        step=0.1,
        default=3.0,
        group="field",
    )
    assert spec.id == "noise_scale"
    assert spec.type == "float"
    assert spec.min == 0.5
    assert spec.options is None


def test_param_spec_select() -> None:
    spec = ParamSpec(
        id="palette",
        label="Palette",
        type="select",
        default="warm",
        options=[
            {"value": "warm", "label": "Warm"},
            {"value": "cool", "label": "Cool"},
        ],
    )
    assert spec.type == "select"
    assert len(spec.options) == 2
    assert spec.min is None


def test_param_spec_minimal() -> None:
    spec = ParamSpec(id="x", label="X", type="float")
    assert spec.min is None
    assert spec.max is None
    assert spec.step is None
    assert spec.default is None
    assert spec.group is None
    assert spec.options is None


def test_generator_info() -> None:
    info = GeneratorInfo(id="flow_field", name="Flow Field", description="A test")
    assert info.id == "flow_field"


def test_generator_schema() -> None:
    schema = GeneratorSchema(
        id="hello",
        name="Hello",
        params=[
            ParamSpec(id="color", label="Color", type="color", default="#ff0000"),
        ],
    )
    assert len(schema.params) == 1
    assert schema.params[0].id == "color"


def test_render_request() -> None:
    req = RenderRequest(
        generator="hello",
        params={"color": "#00ff00"},
        seed=42,
    )
    assert req.generator == "hello"
    assert req.seed == 42
    assert req.params["color"] == "#00ff00"
