# BELT Packaging Specification

This document specifies how to restructure the BELT project for distribution as a standard Python package on PyPI.

## Current Structure

```
belt/
├── main.py
├── models.py
├── loader.py
├── viability.py
├── output_writer.py
├── pyproject.toml
├── uv.lock
├── README.md
└── tests/
    ├── test_models.py
    └── test_viability.py
```

**Issues with current layout:**
- Modules at root level are not a proper Python package
- No `__init__.py` makes it non-importable as a library
- Cannot be installed via `pip install`
- No CLI entry point defined for distribution

---

## Target Structure (src-layout)

```
belt/
├── src/
│   └── belt/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── models.py
│       ├── loader.py
│       ├── viability.py
│       └── output_writer.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models.py
│   └── test_viability.py
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## File Specifications

### 1. `src/belt/__init__.py`

Purpose: Package initialization and public API exports.

```python
"""BELT - Brine & Ember Life cycle analysis and Techno-economic analysis Tool."""

from belt.models import (
    Scenario,
    Transformation,
    Process,
    Transfer,
    Item,
    Energy,
    EnergySource,
    Finance,
    EnergyType,
    Measurement,
)
from belt.viability import assess_viability
from belt.loader import load_scenario
from belt.output_writer import write_json

__version__ = "0.1.0"

__all__ = [
    "Scenario",
    "Transformation",
    "Process",
    "Transfer",
    "Item",
    "Energy",
    "EnergySource",
    "Finance",
    "EnergyType",
    "Measurement",
    "assess_viability",
    "load_scenario",
    "write_json",
    "__version__",
]
```

### 2. `src/belt/__main__.py`

Purpose: Enable `python -m belt` execution.

```python
"""Entry point for running BELT as a module."""

from belt.cli import app

if __name__ == "__main__":
    app()
```

### 3. `src/belt/cli.py`

Purpose: Typer CLI application (renamed from `main.py`).

**Changes required:**
- Rename file from `main.py` to `cli.py`
- Update imports to use absolute package imports

```python
# Old imports
from models import Scenario
from loader import load_scenario
from viability import assess_viability
from output_writer import write_json

# New imports
from belt.models import Scenario
from belt.loader import load_scenario
from belt.viability import assess_viability
from belt.output_writer import write_json
```

### 4. `src/belt/models.py`

Purpose: Pydantic data models.

**Changes required:**
- No import changes needed (no internal imports)
- Move file to `src/belt/models.py`

### 5. `src/belt/loader.py`

Purpose: YAML scenario loading.

**Changes required:**
- Update imports to absolute package imports

```python
# Old
from models import Scenario

# New
from belt.models import Scenario
```

### 6. `src/belt/viability.py`

Purpose: Core viability calculations.

**Changes required:**
- Update imports to absolute package imports

```python
# Old
from models import Scenario, Transformation

# New
from belt.models import Scenario, Transformation
```

### 7. `src/belt/output_writer.py`

Purpose: JSON output formatting.

**Changes required:**
- No import changes needed (no internal imports)
- Move file to `src/belt/output_writer.py`

### 8. `tests/__init__.py`

Purpose: Make tests a package for proper imports.

```python
"""BELT test suite."""
```

### 9. `tests/conftest.py`

Purpose: Shared pytest fixtures.

```python
"""Shared test fixtures for BELT test suite."""

import pytest


@pytest.fixture
def base_scenario_dict():
    """Base scenario dictionary for testing."""
    return {
        "name": "test_scenario",
        "boundaries": ["harvest", "dashi", "pyrolysis"],
        "energy_sources": {
            "grid_ca": {"carbon_intensity_kg_co2_kwh": 0.23},
            "propane": {"carbon_intensity_kg_co2_kwh": 0.25},
        },
        "materials": ["wet_biomass", "feedstock", "dashi", "biochar"],
        "transformations": [
            {
                "id": "harvest",
                "processes": [
                    {
                        "name": "harvest_process",
                        "inputs": [{"name": "wet_biomass", "measurement": "tonnes", "value": 100}],
                        "outputs": [{"name": "feedstock", "measurement": "tonnes", "value": 80}],
                        "input_energy": [{"kwh": 500, "type": "grid_ca"}],
                        "conserved_energy": [],
                        "emissions": [{"name": "co2", "measurement": "kg", "value": 50}],
                        "carbon_locked": [],
                        "finance": {"capex": 0, "opex": 200, "revenue": 0},
                    }
                ],
            },
            {
                "id": "dashi",
                "processes": [
                    {
                        "name": "dashi_process",
                        "inputs": [{"name": "feedstock", "measurement": "tonnes", "value": 80}],
                        "outputs": [{"name": "dashi", "measurement": "tonnes", "value": 60}],
                        "input_energy": [{"kwh": 1000, "type": "propane"}],
                        "conserved_energy": [],
                        "emissions": [{"name": "co2", "measurement": "kg", "value": 100}],
                        "carbon_locked": [],
                        "finance": {"capex": 0, "opex": 400, "revenue": 500},
                    }
                ],
            },
            {
                "id": "pyrolysis",
                "processes": [
                    {
                        "name": "pyrolysis_process",
                        "inputs": [{"name": "dashi", "measurement": "tonnes", "value": 60}],
                        "outputs": [{"name": "biochar", "measurement": "tonnes", "value": 30}],
                        "input_energy": [{"kwh": 2000, "type": "grid_ca"}],
                        "conserved_energy": [],
                        "emissions": [{"name": "co2", "measurement": "kg", "value": 200}],
                        "carbon_locked": [{"name": "carbon", "measurement": "kg", "value": 1000}],
                        "finance": {"capex": 0, "opex": 1000, "revenue": 2000},
                    }
                ],
            },
        ],
        "transfers": [
            {"material": "feedstock", "from": "harvest", "to": "dashi", "quantity": 80},
            {"material": "dashi", "from": "dashi", "to": "pyrolysis", "quantity": 60},
        ],
    }
```

### 10. `tests/test_models.py`

**Changes required:**
- Update imports to absolute package imports
- Use shared fixture from conftest.py

```python
# Old
from models import Scenario

# New
from belt.models import Scenario
```

### 11. `tests/test_viability.py`

**Changes required:**
- Update imports to absolute package imports
- Use shared fixture from conftest.py

```python
# Old
from models import Scenario
from viability import assess_viability

# New
from belt.models import Scenario
from belt.viability import assess_viability
```

---

## pyproject.toml Specification

```toml
[project]
name = "belt"
version = "0.1.0"
description = "Brine & Ember Life cycle analysis and Techno-economic analysis Tool for LCA/TEA scenario analysis"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.12"
authors = [
    { name = "Your Name", email = "your.email@example.com" }
]
keywords = ["lca", "tea", "lifecycle-analysis", "techno-economic", "biomass", "carbon"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering",
]

dependencies = [
    "pydantic>=2.12.5",
    "pyyaml>=6.0.3",
    "typer>=0.21.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.2",
    "ruff>=0.4.0",
]

[project.scripts]
belt = "belt.cli:app"

[project.urls]
Homepage = "https://github.com/yourusername/belt"
Repository = "https://github.com/yourusername/belt"
Documentation = "https://github.com/yourusername/belt#readme"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/belt"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
```

---

## Migration Steps

### Step 1: Create directory structure

```bash
mkdir -p src/belt
```

### Step 2: Move and rename files

```bash
# Move source files
mv main.py src/belt/cli.py
mv models.py src/belt/
mv loader.py src/belt/
mv viability.py src/belt/
mv output_writer.py src/belt/

# Create new files
touch src/belt/__init__.py
touch src/belt/__main__.py
touch tests/__init__.py
touch tests/conftest.py
```

### Step 3: Update imports in all files

Update every Python file to use absolute imports (`from belt.module import ...`).

### Step 4: Update pyproject.toml

Replace contents with the specification above.

### Step 5: Install in development mode

```bash
uv pip install -e ".[dev]"
```

### Step 6: Verify installation

```bash
# Test CLI entry point
belt --help

# Test module execution
python -m belt --help

# Run tests
pytest

# Test import
python -c "from belt import Scenario, assess_viability; print('OK')"
```

---

## Building and Publishing

### Build the package

```bash
uv build
```

Output:
```
dist/
├── belt-0.1.0.tar.gz
└── belt-0.1.0-py3-none-any.whl
```

### Test installation from built package

```bash
# Create a fresh virtual environment
uv venv test-env
source test-env/bin/activate

# Install from wheel
uv pip install dist/belt-0.1.0-py3-none-any.whl

# Verify
belt --help
```

### Publish to PyPI

```bash
# Test PyPI (recommended first)
uv publish --repository testpypi

# Production PyPI
uv publish
```

### User installation

Once published, users install with:

```bash
pip install belt
# or
uv pip install belt
```

---

## Post-Migration Verification Checklist

- [ ] `belt --help` displays CLI help
- [ ] `python -m belt --help` displays CLI help
- [ ] `belt analyze scenario.yaml` runs analysis
- [ ] `pytest` passes all tests
- [ ] `from belt import Scenario` works in Python REPL
- [ ] `from belt import __version__` returns "0.1.0"
- [ ] `uv build` creates wheel and sdist without errors
- [ ] Wheel installs correctly in fresh environment

---

## Benefits of This Structure

1. **Installable**: Users can `pip install belt` from PyPI
2. **CLI access**: `belt` command available system-wide after install
3. **Importable**: `from belt import Scenario` works as a library
4. **Isolated**: src-layout prevents accidental local imports during development
5. **Testable**: Pytest configured with proper Python path
6. **Standard**: Follows PyPA recommendations and works with all Python tools
7. **Extensible**: Easy to add subpackages (e.g., `belt.plugins`, `belt.reports`)
