

def _base_scenario_dict():
    return {
        "name": "smoke-test",
        "currency": "USD",
        "boundaries": ["harvest", "dashi", "pyrolysis"],
        "energy_sources": {
            "grid_ca": {"carbon_intensity_kg_per_kwh": 0.23},
            "propane": {"carbon_intensity_kg_per_kwh": 0.25},
        },
        "materials": {
            "wet_biomass_t": {"name": "wet_biomass", "measurement": "tonnes", "value": 0},
            "feedstock_t": {"name": "feedstock", "measurement": "tonnes", "value": 0},
            "dashi_liters": {"name": "dashi", "measurement": "liters", "value": 0},
            "biochar_t": {"name": "biochar", "measurement": "tonnes", "value": 0},
            "emissions_kg": {"name": "emissions", "measurement": "kg", "value": 0},
            "carbon_locked_kg": {"name": "carbon_locked", "measurement": "kg", "value": 0},
        },
        "transformations": [
            {
                "id": "harvest",
                "processes": [
                    {
                        "id": "cut_collect",
                        "materials_input": {"wet_biomass_t": 1.0},
                        "energy_input": {"amount_kwh": 50, "type": "grid_ca"},
                        "materials_output": {"wet_biomass_t": 1.0},
                        "finance": {"opex_usd": 500},
                    }
                ],
            },
            {
                "id": "dashi",
                "processes": [
                    {
                        "id": "boil_extract",
                        "materials_input": {"wet_biomass_t": 1.0},
                        "energy_input": {"amount_kwh": 120, "type": "propane"},
                        "materials_output": {"dashi_liters": 800, "feedstock_t": 0.5},
                        "finance": {"opex_usd": 800, "revenue_usd": 2500},
                    }
                ],
            },
            {
                "id": "pyrolysis",
                "processes": [
                    {
                        "id": "char_burn",
                        "materials_input": {"feedstock_t": 0.5},
                        "energy_input": {"amount_kwh": 60, "type": "grid_ca"},
                        "materials_output": {"biochar_t": 0.1, "emissions_kg": 150, "carbon_locked_kg": 250},
                        "finance": {"opex_usd": 300},
                    }
                ],
            },
        ],
        "transfers": [
            {"from": "harvest", "to": "dashi", "quantities": {"wet_biomass_t": 1.0}},
            {"from": "dashi", "to": "pyrolysis", "quantities": {"feedstock_t": 0.5}},
        ],
    }
