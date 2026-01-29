import pytest

from belt.parser import parse_scenario_dict, ParseError


def _raw_valid():
    return {
        "name": "valid",
        "currency": "USD",
        "boundaries": ["harvest"],
        "energy_sources": {"grid": {"carbon_intensity_kg_per_kwh": 0.2}},
        "materials": {"foo": {"name": "foo", "measurement": "tonnes", "value": 0}},
        "transformations": [
            {
                "id": "harvest",
                "processes": [
                    {
                        "id": "p1",
                        "materials_input": {"foo": 1.0},
                        "energy_input": {"amount_kwh": 10, "type": "grid"},
                        "materials_output": {"foo": 1.0},
                    }
                ],
            }
        ],
        "transfers": [],
    }


def test_parser_unknown_material_raises():
    raw = _raw_valid()
    raw["transformations"][0]["processes"][0]["materials_input"] = {"bar": 1.0}
    with pytest.raises(ParseError):
        parse_scenario_dict(raw, path="inline")


def test_parser_unknown_energy_source_raises():
    raw = _raw_valid()
    raw["energy_sources"] = {}
    with pytest.raises(ParseError):
        parse_scenario_dict(raw, path="inline")
