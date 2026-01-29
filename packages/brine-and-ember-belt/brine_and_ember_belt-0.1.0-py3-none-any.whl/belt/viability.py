from typing import Dict, Any

from belt.models import Scenario, Transformation


def summarize_finance(transformation: Transformation) -> Dict[str, float]:
    total_revenue = 0.0
    total_opex = 0.0
    total_capex = 0.0
    for process in transformation.processes:
        total_revenue += process.finance.revenue_usd or 0.0
        total_opex += process.finance.opex_usd or 0.0
        total_capex += process.finance.capex_usd or 0.0
    return {"revenue_usd": total_revenue, "opex_usd": total_opex, "capex_usd": total_capex}


def summarize_carbon(transformation: Transformation, energy_sources: Dict[str, Any]) -> Dict[str, float]:
    emissions = 0.0
    locked = 0.0
    for process in transformation.processes:
        emissions += (process.emissions_kg or 0.0) + (process.materials_output.get("emissions_kg", 0.0) if process.materials_output else 0.0)
        locked += (process.carbon_locked_kg or 0.0) + (process.materials_output.get("carbon_locked_kg", 0.0) if process.materials_output else 0.0)
        if process.energy_input:
            src = energy_sources.get(process.energy_input.type)
            if not src:
                raise ValueError(f"Unknown energy source: {process.energy_input.type}")
            emissions += process.energy_input.amount_kwh * src.carbon_intensity_kg_per_kwh
    return {"emissions_kg": emissions, "carbon_locked_kg": locked}


def assess_viability(scenario: Scenario) -> Dict[str, Any]:
    per_transformation = {}
    totals = {
        "revenue_usd": 0.0,
        "opex_usd": 0.0,
        "capex_usd": 0.0,
        "emissions_kg": 0.0,
        "carbon_locked_kg": 0.0,
    }

    for t in scenario.transformations:
        finance = summarize_finance(t)
        carbon = summarize_carbon(t, scenario.energy_sources)
        profit_usd = finance["revenue_usd"] - (finance["opex_usd"] + finance["capex_usd"])
        net_carbon_kg = carbon["emissions_kg"] - carbon["carbon_locked_kg"]
        per_transformation[t.id] = {
            "revenue_usd": finance["revenue_usd"],
            "opex_usd": finance["opex_usd"],
            "capex_usd": finance["capex_usd"],
            "profit_usd": profit_usd,
            "emissions_kg": carbon["emissions_kg"],
            "carbon_locked_kg": carbon["carbon_locked_kg"],
            "net_carbon_kg": net_carbon_kg,
        }
        totals["revenue_usd"] += finance["revenue_usd"]
        totals["opex_usd"] += finance["opex_usd"]
        totals["capex_usd"] += finance["capex_usd"]
        totals["emissions_kg"] += carbon["emissions_kg"]
        totals["carbon_locked_kg"] += carbon["carbon_locked_kg"]

    profit_total = totals["revenue_usd"] - (totals["opex_usd"] + totals["capex_usd"])
    net_carbon_total = totals["emissions_kg"] - totals["carbon_locked_kg"]
    viable = profit_total > 0 and net_carbon_total < 0

    return {
        "per_transformation": per_transformation,
        "totals": {
            "revenue_usd": totals["revenue_usd"],
            "opex_usd": totals["opex_usd"],
            "capex_usd": totals["capex_usd"],
            "profit_usd": profit_total,
            "emissions_kg": totals["emissions_kg"],
            "carbon_locked_kg": totals["carbon_locked_kg"],
            "net_carbon_kg": net_carbon_total,
            "viable": viable,
            "reason": _viability_reason(profit_total, net_carbon_total),
        },
    }


def _viability_reason(profit_usd: float, net_carbon_kg: float) -> str:
    if profit_usd <= 0 and net_carbon_kg >= 0:
        return "Unprofitable and carbon-positive"
    if profit_usd <= 0:
        return "Unprofitable"
    if net_carbon_kg >= 0:
        return "Carbon-positive"
    return "Profitable and carbon-negative"
