import yaml
from yaml import YAMLError

from belt.parser import parse_scenario_dict


def load_scenario_yaml(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except YAMLError as e:
        raise RuntimeError(f"YAML parse error in {path}: {e}") from e
    except OSError as e:
        raise RuntimeError(f"Unable to read {path}: {e}") from e
    return parse_scenario_dict(raw, path=path)
