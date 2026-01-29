# belt

Brine & Ember Life cycle analysis and Techno-economic analysis Tool. Define scenarios as YAML, run viability (profit + carbon), and emit JSON/text via Typer CLI. Uses src-layout packaging and prefers `uv`.

## YAML Structure

One YAML file per scenario. A scenario has multiple transformations; each transformation has processes; processes define materials and energy in/out.

### Example
```yaml
name: vegan dashi to biochar
currency: USD
boundaries: [harvest, dashi, pyrolysis]
energy_sources:
  grid_ca: { carbon_intensity_kg_per_kwh: 0.23 }
  propane: { carbon_intensity_kg_per_kwh: 0.25 }

materials:
  wet_biomass_t:   { name: wet_biomass, measurement: tonnes, value: 0 }
  feedstock_t:     { name: feedstock, measurement: tonnes, value: 0 }
  dashi_liters:    { name: dashi, measurement: liters, value: 0 }
  biochar_t:       { name: biochar, measurement: tonnes, value: 0 }
  emissions_kg:    { name: emissions, measurement: kg, value: 0 }
  carbon_locked_kg:{ name: carbon_locked, measurement: kg, value: 0 }

transformations:
  - id: harvest
    processes:
      - id: cut_collect
        materials_input: { wet_biomass_t: 1.0 }
        energy_input: { amount_kwh: 50, type: grid_ca }
        materials_output: { wet_biomass_t: 1.0 }
        finance: { opex_usd: 500 }

  - id: dashi
    processes:
      - id: boil_extract
        materials_input: { wet_biomass_t: 1.0 }
        energy_input: { amount_kwh: 120, type: propane }
        materials_output: { dashi_liters: 800, feedstock_t: 0.5 }
        finance: { opex_usd: 800, revenue_usd: 2500 }

  - id: pyrolysis
    processes:
      - id: char_burn
        materials_input: { feedstock_t: 0.5 }
        energy_input: { amount_kwh: 60, type: grid_ca }
        materials_output: { biochar_t: 0.1, emissions_kg: 150, carbon_locked_kg: 250 }
        finance: { opex_usd: 300 }

transfers:
  - from: harvest
    to: dashi
    quantities: { wet_biomass_t: 1.0 }
  - from: dashi
    to: pyrolysis
    quantities: { feedstock_t: 0.5 }
```

Key fields:
- `energy_sources`: map energy type → carbon intensity (kg CO2/kWh).
- `materials`: user-defined; referenced in materials_input/materials_output and transfers.
- `materials_input`/`materials_output`: quantities by material key.
- `energy_input`: `{ amount_kwh, type }`, carbon computed via `energy_sources`.
- `finance`: `capex_usd`, `opex_usd`, `revenue_usd` (default 0).
- `transfers`: move materials between transformations; must not exceed produced amounts.
- `boundaries`: list of included transformations; all transformations must be listed.

## Install & Run (uv preferred)
```bash
# install deps in editable mode
uv pip install -e ".[dev]"

# CLI help
uv run python -m belt --help
uv run python -m belt analyze-scenario --help

# Run scenario
uv run python -m belt analyze-scenario path/to/scenario.yaml
```

Behavior:
- Prints viability summary to stdout.
- Writes JSON results to `outputs/<scenario>.json` by default (or `--out` path).

## Tests
```bash
uv run python -m pytest
```

## Packaging / Entry Points
- Src layout under `src/belt/`
- CLI entry: `belt = "belt.cli:app"`
- Module entry: `python -m belt`

## Quick Checks
```bash
uv build
uv run python -c "from belt import Scenario, assess_viability; print('OK')"
belt --help               # after install
python -m belt --help
```
