import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from contracts.models import ALL_MODELS, FlowRecord

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str, kind: str) -> dict:
    return json.loads((FIXTURES / f"{name}_{kind}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", ALL_MODELS)
def test_valid_fixture_loads(name):
    model = ALL_MODELS[name].model_validate(load(name, "valid"))
    # round trip keeps the data
    assert ALL_MODELS[name].model_validate_json(model.model_dump_json()) == model


@pytest.mark.parametrize("name", ALL_MODELS)
def test_invalid_fixture_raises(name):
    with pytest.raises(ValidationError):
        ALL_MODELS[name].model_validate(load(name, "invalid"))


def test_unknown_field_is_rejected():
    data = load("FlowRecord", "valid") | {"surprise": 1}
    with pytest.raises(ValidationError):
        FlowRecord.model_validate(data)


def test_schema_export_matches_models(tmp_path, monkeypatch):
    from contracts import export_schemas

    monkeypatch.setattr(export_schemas, "OUT", tmp_path)
    export_schemas.main()
    for name in ALL_MODELS:
        schema = json.loads((tmp_path / f"{name}.schema.json").read_text(encoding="utf-8"))
        assert schema["title"] == name
