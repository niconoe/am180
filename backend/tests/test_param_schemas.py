"""Test that each generator's PARAM_SCHEMA stays in sync with its Pydantic model."""
from am180.registry import GENERATORS


def test_schema_keys_match_model_fields() -> None:
    """Every PARAM_SCHEMA entry must have a matching field on the params model,
    and every model field must have a matching PARAM_SCHEMA entry."""
    for gen_id, gen in GENERATORS.items():
        schema_ids = {spec.id for spec in gen.param_schema}
        model_fields = set(gen.params_model.model_fields.keys())
        assert schema_ids == model_fields, (
            f"Generator '{gen_id}': PARAM_SCHEMA ids {schema_ids} "
            f"!= model fields {model_fields}"
        )


def test_schema_defaults_match_model_defaults() -> None:
    """PARAM_SCHEMA default values should match the Pydantic model defaults."""
    for gen_id, gen in GENERATORS.items():
        for spec in gen.param_schema:
            field_info = gen.params_model.model_fields[spec.id]
            if spec.default is not None:
                assert spec.default == field_info.default, (
                    f"Generator '{gen_id}', param '{spec.id}': "
                    f"schema default {spec.default!r} != "
                    f"model default {field_info.default!r}"
                )
