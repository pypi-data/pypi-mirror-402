import json
import os
from typing import Any, Dict


def write_json(result: Dict[str, Any], scenario_name: str, out_path: str | None = None) -> str:
    path = out_path
    if path is None:
        path = os.path.join("outputs", f"{scenario_name}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return path
