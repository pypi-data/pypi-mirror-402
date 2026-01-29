from copy import deepcopy
from typing import Any, Dict

from belt.models import Scenario


class ParseError(RuntimeError):
    pass


def _validate_transformation_data(t: Dict[str, Any], path: str | None = None):
    if "processes" not in t or not isinstance(t["processes"], list):
        raise ParseError(f"{path}: transformation '{t.get('id')}' missing processes list")
    for i, proc in enumerate(t["processes"]):
        if not isinstance(proc, dict):
            raise ParseError(f"{path}: process at index {i} in transformation '{t.get('id')}' is not a mapping")


def _validating_scenario_data(raw: Dict[str, Any], path: str) -> Dict[str, Any]:
    data = deepcopy(raw)

    required = ["name", "currency", "boundaries", "energy_sources", "materials", "transformations", "transfers"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ParseError(f"{path}: missing required fields: {', '.join(missing)}")

    for t in data.get("transformations", []):
        _validate_transformation_data(t, path)
    return data


def parse_scenario_dict(raw: Dict[str, Any], path: str | None = None) -> Scenario:
    """
    Normalize raw YAML dict into a Scenario model.
    """
    source = path or "<dict>"
    validated_data = _validating_scenario_data(raw, source)
    try:
        return Scenario(**validated_data)
    except Exception as e:
        raise ParseError(f"{source}: {e}") from e


def parse_scenario_file(path: str) -> Scenario:
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return parse_scenario_dict(raw, path=path)
