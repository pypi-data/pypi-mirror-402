import pytest

from belt.models import Scenario
from tests.test_models import _base_scenario_dict
from belt.viability import assess_viability, summarize_carbon, summarize_finance


def test_viability_positive_profit_and_negative_carbon_is_viable():
    data = _base_scenario_dict()
    scenario = Scenario(**data)
    result = assess_viability(scenario)
    totals = result["totals"]
    assert totals["viable"] is True
    assert totals["profit_usd"] > 0
    assert totals["net_carbon_kg"] < 0


def test_viability_fails_if_profit_negative():
    data = _base_scenario_dict()
    # remove revenue to force unprofitable
    data["transformations"][1]["processes"][0]["finance"]["revenue_usd"] = 0
    scenario = Scenario(**data)
    totals = assess_viability(scenario)["totals"]
    assert totals["viable"] is False
    assert totals["profit_usd"] < 0 or totals["profit_usd"] == 0


def test_viability_fails_if_carbon_positive():
    data = _base_scenario_dict()
    # zero out carbon_locked to force carbon positive
    data["transformations"][2]["processes"][0]["materials_output"]["carbon_locked_kg"] = 0
    scenario = Scenario(**data)
    totals = assess_viability(scenario)["totals"]
    assert totals["viable"] is False
    assert totals["net_carbon_kg"] >= 0


def test_summarize_carbon_counts_outputs_and_fields():
    data = _base_scenario_dict()
    scenario = Scenario(**data)
    t = scenario.transformations[2]  # pyrolysis
    carbon = summarize_carbon(t, scenario.energy_sources)
    assert carbon["emissions_kg"] == 163.8  # 150 + (60 * 0.23)
    assert carbon["carbon_locked_kg"] == 250


def test_summarize_finance_sums_capex_opex_revenue():
    data = _base_scenario_dict()
    scenario = Scenario(**data)
    t = scenario.transformations[1]  # dashi
    finance = summarize_finance(t)
    assert finance["revenue_usd"] == 2500
    assert finance["opex_usd"] == 800
    assert finance["capex_usd"] == 0
