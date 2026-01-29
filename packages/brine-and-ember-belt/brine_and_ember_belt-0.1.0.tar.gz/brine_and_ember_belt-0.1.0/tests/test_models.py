import pytest
from pydantic import ValidationError

from belt.models import Scenario
from tests.helpers.mock_data import _base_scenario_dict


def test_scenario_valid():
    data = _base_scenario_dict()
    scenario = Scenario(**data)
    assert scenario.name == "smoke-test"
    assert len(scenario.transformations) == 3


def test_unknown_material_in_process_inputs_raises():
    data = _base_scenario_dict()
    data["transformations"][0]["processes"][0]["materials_input"]["unknown_mat"] = 1.0
    with pytest.raises(ValidationError):
        Scenario(**data)


def test_unknown_energy_source_raises():
    data = _base_scenario_dict()
    data["transformations"][0]["processes"][0]["energy_input"]["type"] = "missing_energy"
    with pytest.raises(ValidationError):
        Scenario(**data)


def test_transfer_exceeds_production_raises():
    data = _base_scenario_dict()
    data["transfers"][0]["quantities"]["wet_biomass_t"] = 2.0  # exceeds harvest output of 1.0
    with pytest.raises(ValidationError):
        Scenario(**data)


def test_transformation_not_in_boundaries_raises():
    data = _base_scenario_dict()
    data["boundaries"] = ["harvest", "dashi"]  # missing pyrolysis
    with pytest.raises(ValidationError):
        Scenario(**data)
