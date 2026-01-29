import typer
from belt.loader import load_scenario_yaml
from belt.viability import assess_viability
from belt.output_writer import write_json

app = typer.Typer()


@app.command()
def analyze_scenario(path: str, out: str = typer.Option(None, help="Optional output JSON file path")):
    scenario = load_scenario_yaml(path)
    result = assess_viability(scenario)
    totals = result["totals"]
    status = "VIABLE" if totals["viable"] else "NOT VIABLE"
    print(f"[{status}] Profit USD: {totals['profit_usd']:.2f} | Net carbon kg: {totals['net_carbon_kg']:.2f} | Reason: {totals['reason']}")
    out_path = write_json(result, getattr(scenario, "name", "scenario"), out)
    print(f"Wrote results to {out_path}")


if __name__ == "__main__":
    app()
