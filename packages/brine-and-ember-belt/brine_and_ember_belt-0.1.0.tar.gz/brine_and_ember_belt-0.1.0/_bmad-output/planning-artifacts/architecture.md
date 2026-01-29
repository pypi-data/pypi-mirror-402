---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments: ['_bmad-output/analysis/brainstorming-session-2026-01-15.md']
workflowType: 'architecture'
project_name: 'belt'
user_name: 'Mr Wizard'
date: '2026-01-17'
lastStep: 8
status: 'complete'
completedAt: '2026-01-17'
---

# Architecture Decision Document: BELT

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

**Project:** BELT (Brine & Ember Life cycle analysis and Techno-economic analysis Tool)
**Architect:** Winston
**Date:** 2026-01-17

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
- Define scenarios as YAML configs describing process nodes (seaweed -> dashi -> biochar) with inputs, outputs, and parameters.
- Run dual-ledger calculations (finance + carbon) with simplified hardcoded formulas; state transitions capture energy and carbon intensity separately.
- Produce text console summary and persist JSON results for each scenario; support 2-3 scenarios and basic scenario comparison.
- Validate required fields and fail loudly when missing.

**Non-Functional Requirements:**
- Deliver in 1-2 weeks with minimal dependencies; keep modules clean (data/calculation/output separation).
- Git-friendly artifacts: YAML scenarios and JSON outputs versioned; no UI or API in MVP.
- Architect for growth to Option B (Climatiq, plots, diff views) without rewriting core calculation layer.

**Scale & Complexity:**
- Complexity level: low (single-machine CLI/tooling), primary domain: backend/CLI for LCA/TEA.
- Estimated components: data loader, formula library, calculation engine, output formatter, validation.

### Technical Constraints & Dependencies
- Manual YAML input (no external data fetch in MVP); no UI/API; offline-friendly.
- Keep energy vs carbon intensity decoupled in data model; state-transition structure required.
- Output JSON as a contract for future visualization; maintain dual-ledger data per process node.

### Cross-Cutting Concerns Identified
- Dual accounting (carbon + financial) at every node; boundaries and state transitions must preserve both.
- Energy/carbon decoupling is pervasive across formulas.
- Scenario artifacts as code (YAML/JSON) to enable versioning and comparison.
- Validation and "fail loudly" behavior across modules.

## Starter Template Evaluation

### Primary Technology Domain

Backend/CLI for LCA/TEA calculations (text + JSON output only) aligned to the state-machine model.

### Starter Options Considered

- Python + Typer + Pydantic minimal CLI scaffold; manual module layout for data/calculate/output; fast to ship and strong validation.
- TypeScript/Node CLI (commander + zod) as an alternative; adds toolchain overhead relative to the 3-day goal; not selected for MVP speed.

### Selected Starter: Python + Typer + Pydantic (minimal CLI scaffold)

**Rationale for Selection:**
- Fast to implement with low dependency footprint and good DX for CLI help.
- Pydantic gives typed schemas and validation for YAML scenarios; Typer provides ergonomic CLI entrypoints.
- Keeps the calculation layer UI-free and maps cleanly to data -> calculate -> output modules; easy to extend toward Option B.
- JSON output remains the contract for future visualization; no runtime UI required.

**Initialization Command (uv):**

```bash
uv venv
source .venv/bin/activate
uv pip install --upgrade pip
uv pip install typer[all] pydantic
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:** Python 3 with Typer CLI and Pydantic models for schemas/validation.

**Styling Solution:** None (CLI only).

**Build Tooling:** uv-managed venv + pip; no bundler or UI build steps.

**Testing Framework:** Not scaffolded; add pytest when tests are introduced.

**Code Organization:** Modules for data loaders (YAML), calculation/formulas (pure functions), output (JSON/text formatting), and CLI commands; scenarios stored as files for git-friendly diffs.

**Development Experience:** Typer-generated help/commands, type hints, simple local setup; no network dependency required beyond Python packages.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** Naming, structure, formats, calculation discipline, validation/error reporting, and CLI behavior for the local CLI POC.

### Naming Patterns

- File names and YAML keys: snake_case.
- Python identifiers: snake_case; Pydantic model classes: CapWords.
- CLI commands/subcommands: kebab-case (e.g., `belt run`, `belt compare`).
- JSON output fields: snake_case.

### Structure Patterns

- Modules by concern: `data`, `calculate`, `output`, `cli`.
- Tests co-located with code as `*_test.py`.
- Scenario inputs under `scenarios/`; run outputs under `outputs/`.

### Format Patterns

- JSON output schema stable: `summary`, `per_node`, `totals` (dual ledger), optional `trace` for calculation details.
- Error shape: `{ "error": { "path": "state[pasteurize].process[dashi_boiling].inputs.energy_kwh", "message": "...", "type": "validation" } }`.
- Timestamps (if any) ISO-8601; numeric types stay numeric.

### Communication/Process Patterns

- Calculation functions are pure and deterministic; no side effects or IO in the calculation layer.
- Energy vs carbon intensity remain separate inputs; dual ledger recorded per node and totals.
- Validation at load with Pydantic; fail fast with contextual paths; non-zero exit on validation failures.

### CLI Behavior

- `belt run <scenario.yml> [--out outputs/run.json]`: human-readable summary to stdout; JSON written to file when `--out` provided.
- `belt compare <a> <b>` may start as a stub; reserve interface now for future diffing.
- Exit codes: 0 on success; non-zero on validation/calculation errors.

### Enforcement Guidelines

- All agents follow naming and structure conventions above; do not invent alternate directory layouts.
- Keep calculation and IO layers separate; no hidden state or globals.
- Preserve JSON schema contract; additive changes only when evolving.

### Pattern Examples

**Good:**
- File: `calculate/ledger.py`; class `ProcessNode(BaseModel)`; field `energy_kwh: float`.
- Error: `{ "error": { "path": "state[drying].inputs.energy_kwh", "message": "field required", "type": "validation" } }`.

**Anti-Patterns:**
- Mixing camelCase keys in YAML/JSON; writing calculation outputs directly to stdout without JSON option; adding side effects (e.g., file writes) inside pure calculation functions.

## Project Structure & Boundaries

### Complete Project Directory Structure (CLI Option A)

```
belt/
├── README.md
├── requirements.txt
├── .gitignore
├── belt/
│   ├── __init__.py
│   ├── cli.py                  # Typer entrypoints (run, compare)
│   ├── data/
│   │   ├── __init__.py
│   │   ├── models.py           # Pydantic schemas for scenario/state/process
+│   │   ├── loader.py           # YAML load + validation + error path mapping
│   │   └── defaults.py         # Shared constants (e.g., default carbon intensities)
│   ├── calculate/
│   │   ├── __init__.py
│   │   ├── formulas.py         # Hardcoded MVP formulas
│   │   └── engine.py           # State-machine traversal + dual-ledger aggregation
│   └── output/
│       ├── __init__.py
│       ├── render_text.py      # Human-readable summary
│       └── render_json.py      # JSON contract writer
├── scenarios/
│   └── sample.yml              # Example scenario
├── outputs/
│   └── .gitkeep                # Collected run outputs
├── tests/
│   ├── __init__.py
│   ├── test_loader.py
│   ├── test_engine.py
│   └── test_output.py
└── pyproject.toml (optional; may use requirements.txt only)
```

### Architectural Boundaries

- CLI orchestrates loader -> calculation -> output; no API/UI layers.
- Data layer (loader/models/defaults) handles YAML parsing, validation, and typed models; no side effects beyond validation errors.
- Calculation layer (formulas/engine) is pure and deterministic; separates energy vs carbon intensity; produces dual-ledger per node and totals.
- Output layer formats only (text/JSON); no business logic.
- Scenarios are file-based; outputs are file-based; no database or network calls in MVP.

### Requirements to Structure Mapping

- YAML scenarios (FR: define scenarios) → `scenarios/*.yml`, validated by `data/models.py` and loaded via `data/loader.py`.
- Dual-ledger calculations (FR: finance + carbon) → `calculate/formulas.py` and `calculate/engine.py` produce per-node and total ledgers.
- Outputs (FR: text + JSON) → `output/render_text.py` (stdout summary) and `output/render_json.py` (persisted JSON).
- CLI commands (FR: run/compare) → `cli.py` exposing `run` and stub `compare` that routes loader → engine → output.

### YAML Scenario Example (Option A happy path)

```yaml
scenario:
  name: base-option-a
  currency: USD
  boundaries: [harvest, dashi, pyrolysis]
  energy_sources:
    grid_ca: { carbon_intensity_kg_per_kwh: 0.23 }
    propane: { carbon_intensity_kg_per_kwh: 0.25 }

states:
  - id: harvest
    processes:
      - id: cut_collect
        inputs:
          biomass_t: 1.0
          energy_kwh: 50
          energy_source: grid_ca
        outputs:
          wet_biomass_t: 1.0
        finance:
          capex_usd: 0
          opex_usd: 500
          revenue_usd: 0

  - id: dashi
    processes:
      - id: boil_extract
        inputs:
          wet_biomass_t: 1.0
          energy_kwh: 120
          energy_source: propane
          water_m3: 2.0
        outputs:
          dashi_liters: 800
          spent_biomass_t: 0.5
        finance:
          capex_usd: 0
          opex_usd: 800
          revenue_usd: 2500

  - id: pyrolysis
    processes:
      - id: char_burn
        inputs:
          feedstock_t: 0.5
          energy_kwh: 60
          energy_source: grid_ca
        outputs:
          biochar_t: 0.1
          emissions_kg: 150
          carbon_locked_kg: 250
        finance:
          capex_usd: 0
          opex_usd: 300
          revenue_usd: 0

transitions:
  - from: harvest
    to: dashi
    transfer:
      wet_biomass_t: 1.0
  - from: dashi
    to: pyrolysis
    transfer:
      feedstock_t: 0.5
```

### JSON Output Contract (example shape)

```json
{
  "summary": {
    "scenario": "base-option-a",
    "profit_usd": 900.0,
    "carbon_net_kg": -100.0
  },
  "per_node": {
    "harvest": {"profit_usd": -500.0, "emissions_kg": 11.5, "carbon_locked_kg": 0},
    "dashi": {"profit_usd": 1700.0, "emissions_kg": 30.0, "carbon_locked_kg": 0},
    "pyrolysis": {"profit_usd": -300.0, "emissions_kg": 150.0, "carbon_locked_kg": 250.0}
  },
  "totals": {
    "profit_usd": 900.0,
    "emissions_kg": 191.5,
    "carbon_locked_kg": 250.0,
    "net_carbon_kg": -58.5
  }
}
```

### Integration Boundaries

- Loader only reads YAML; calculation only consumes typed models; output only formats calculation results. No cross-layer hidden coupling.
- Energy/carbon factors live in `scenario.energy_sources`; formulas consume these, not hardcoded in CLI.
- Transitions define how mass/outputs flow between states; engine enforces conservation according to provided transfers.

## Validations & Boundaries (LCA)

- Material registry: every process input/output and transfer quantity key must exist in `materials`; unknown keys fail fast.
- Energy mapping: every `energy.type` must exist in `energy_sources`; no silent defaults.
- Physical non-negatives: inputs/outputs, energy amounts, emissions, carbon_locked are >= 0 (financials may be negative).
- Transformations (formerly states): each has at least one process and must be declared in `boundaries`; no off-boundary steps.
- Transfers: source/target transformations must be in `boundaries`; quantities are non-negative and cannot exceed what the source produced for that material.
- Boundaries usage: `boundaries` defines the included stages (e.g., cradle-to-gate). Transfers across boundaries are disallowed. Scenario comparisons require matching boundary sets; surface boundaries in reports.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:** Starter (Python + Typer + Pydantic) aligns with CLI-only scope; file-based scenarios/outputs fit Option A; pure-function calculation layer fits dual-ledger/state-machine design.

**Pattern Consistency:** Naming (snake_case YAML/JSON, CapWords models), structure (data/calculate/output/cli), and error/validation rules all reinforce deterministic CLI runs; CLI behavior matches output contracts.

**Structure Alignment:** Project tree supports loader → engine → output flow; boundaries keep IO, calculation, and formatting separate; scenarios/outputs directories enforce file-based contracts.

### Requirements Coverage Validation ✅

**Functional Requirements Coverage:** YAML-defined scenarios; dual-ledger calculations with energy vs carbon separation; text + JSON outputs; 2-3 scenario support; fail-fast validation.

**Non-Functional Requirements Coverage:** Minimal deps, fast setup; git-friendly YAML/JSON artifacts; architecture ready for Option B growth without core rewrites; offline/local CLI.

### Implementation Readiness Validation ✅

**Decision Completeness:** Critical choices captured (data model shape, validation, storage, CLI surface, output contract); no blocking undecideds for MVP.

**Structure Completeness:** Concrete directories/files defined; loader/engine/output separation explicit; scenarios/outputs locations fixed.

**Pattern Completeness:** Naming, error shape, JSON schema, and pure-function rule specified; CLI exit codes defined.

### Gap Analysis Results

- Critical: None.
- Important: Add pytest baseline when time allows to lock regression safety; document JSON schema versioning when evolving beyond MVP.
- Nice-to-Have: Scenario compare implementation after first run; optional CI once code exists.

### Validation Issues Addressed

- Confirmed no contradictions between decisions/patterns/structure; file-based/offline model consistent with MVP scope.

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context analyzed
- [x] Scale/complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Critical decisions documented
- [x] Stack specified (Python + Typer + Pydantic)
- [x] Integration patterns defined (loader → engine → output)
- [x] Performance considerations addressed (pure functions, deterministic runs)

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication/process patterns specified (error/validation, outputs)

**✅ Project Structure**
- [x] Directory structure defined
- [x] Boundaries established (data/calculate/output/cli)
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** high (scope is narrow, dependencies minimal, contracts explicit)

**Key Strengths:** Clean separation of concerns; deterministic, validated inputs; stable JSON contract; state-machine dual-ledger model aligned to domain.

**Areas for Future Enhancement:** Add automated tests; implement compare/diff; formalize schema versioning and Option B integrations (Climatiq, viz) later.

### Implementation Handoff

**AI Agent Guidelines:**
- Follow documented naming/structure; keep calculation pure and side-effect free.
- Respect YAML/JSON contracts and error shapes; use Pydantic validation paths.
- Use CLI surface as defined; route loader → engine → output only.

**First Implementation Priority:** Initialize repo (uv + Typer/Pydantic), implement models/loader, then engine formulas, then outputs, then CLI `run`.

## Architecture Completion Summary

### Workflow Completion

**Architecture Decision Workflow:** COMPLETED ✅
**Total Steps Completed:** 8
**Date Completed:** 2026-01-17
**Document Location:** _bmad-output/planning-artifacts/architecture.md

### Final Architecture Deliverables

**📋 Complete Architecture Document**
- Architectural decisions documented with stack choice (Python + Typer + Pydantic)
- Implementation patterns for agent consistency
- Project structure with files/directories
- Requirements-to-structure mapping and validation confirming coherence

**🏗️ Implementation Ready Foundation**
- ~10 core architectural decisions
- ~8 implementation patterns/rules
- 4 primary components (data, calculate, output, cli)
- MVP requirements (YAML scenarios, dual-ledger calc, text/JSON output, validation) supported

**📚 AI Agent Implementation Guide**
- Technology stack and consistency rules
- Project structure and boundaries
- Integration flow: loader → engine → output

### Implementation Handoff

**First Implementation Priority (uv):**
```bash
uv venv
source .venv/bin/activate
uv pip install --upgrade pip
uv pip install typer[all] pydantic
```
Then implement models/loader → engine formulas → outputs → CLI `run`.

**Development Sequence:**
1. Initialize project and venv (uv)
2. Add Pydantic models + YAML loader with validation
3. Implement formulas/engine (pure functions, dual ledger)
4. Add JSON/text output formatting
5. Wire Typer CLI commands (`run`, stub `compare`)

### Quality Assurance Checklist

**✅ Architecture Coherence**
- [x] Decisions compatible; stack minimal and aligned
- [x] Patterns support decisions
- [x] Structure aligns with choices

**✅ Requirements Coverage**
- [x] Functional requirements supported (YAML scenarios, dual-ledger calc, outputs, validation)
- [x] Non-functional requirements addressed (minimal deps, git-friendly artifacts, offline CLI)
- [x] Cross-cutting concerns handled (naming, error shape, energy/carbon separation)

**✅ Implementation Readiness**
- [x] Decisions actionable
- [x] Patterns prevent agent conflicts
- [x] Structure complete/unambiguous
- [x] Examples provided (YAML + JSON)

### Project Success Factors

**🎯 Clear Decision Framework:** Stack and contracts explicit; dual-ledger/state-machine model defined.

**🔧 Consistency Guarantee:** Naming, structure, validation, and output schemas enforced across agents.

**📋 Complete Coverage:** Option A requirements mapped to files and flows; validation confirms readiness.

**🏗️ Solid Foundation:** Minimal, extensible CLI architecture ready for growth toward Option B.

---

**Architecture Status:** READY FOR IMPLEMENTATION ✅

**Next Phase:** Begin implementation using the documented starter and patterns.

**Document Maintenance:** Update this architecture when major technical decisions change during implementation.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Data shape: YAML schema for the state machine (states, transitions, processes with inputs/outputs, dual-ledger fields) modeled via Pydantic per node/transition.
- Data store: File-based scenarios (YAML) and outputs (JSON); no database.
- Validation: Pydantic validation at load; fail fast on missing/invalid fields.

**Important Decisions (Shape Architecture):**
- Error/reporting: Fail loudly with clear validation errors including context path (state/process/field); deterministic outputs.
- Calculation layer: Pure functions; energy vs carbon intensity separated; dual-ledger results per node and totals.
- Outputs: Persist JSON (full calculation trace) plus concise text summary; stable schema for future visualization.
- CLI surface: Typer commands such as `belt run <scenario.yml>` and `belt compare <a> <b>` (compare may be stub initially).

**Deferred Decisions:**
- None for MVP; auth/security and CI are out-of-scope for this local CLI POC.

### Data Architecture
- YAML-defined state machine with explicit states, transitions, processes, inputs/outputs, and dual-ledger fields; Pydantic models enforce shape.
- File-based storage for scenarios (YAML) and outputs (JSON); no migrations or DB required.
- Validation at load via Pydantic; fail fast with contextual error paths.

### Authentication & Security
- Not applicable for local CLI MVP; no auth/security layer included.

### API & Communication Patterns
- Not applicable (no API/UI in MVP); calculations are in-process pure functions.

### Frontend Architecture
- Not applicable (CLI-only); outputs are text + JSON.

### Infrastructure & Deployment
- Local venv + pip; no hosting/CI requirements for MVP.

### Decision Impact Analysis

**Implementation Sequence:**
1) Define Pydantic models for state machine nodes, transitions, and dual-ledger fields.
2) Implement YAML loader with validation and contextual error reporting.
3) Build calculation layer (pure functions) with energy/carbon separation and dual-ledger outputs.
4) Add output formatting (JSON trace + text summary).
5) Wire Typer CLI commands (`run`, stub `compare`).

**Cross-Component Dependencies:**
- Calculation layer depends on validated Pydantic models from loader.
- Output schemas depend on calculation results; JSON structure is the contract for future visualization.
- CLI commands orchestrate loader → calculation → output; minimal coupling otherwise.
