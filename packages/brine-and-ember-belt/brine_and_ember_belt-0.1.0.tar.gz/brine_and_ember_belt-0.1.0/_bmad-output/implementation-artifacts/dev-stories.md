# Dev Stories: Viability & Parsing Improvements

## Story 1: User-Defined Materials Only
- Problem: Materials are assumed/validated via predefined registry. Need fully user-defined materials per YAML.
- Requirements:
  - Accept any material keys defined under `materials`. Validation: every `materials_input`/`materials_output`/`transfers` key must exist in `materials`.
  - Remove any hardcoded material assumptions in validations or calculations.
  - Error: Unknown material key → clear validation error with path.
- Acceptance: YAML with arbitrary materials passes if consistent; unknown material key fails with clear error.

## Story 2: Add Parser Module
- Problem: Loader directly constructs models; need a parser to normalize YAML → model-ready dict, enabling field renames/mappings.
- Requirements:
  - Create `parser.py` (or similar) to transform raw YAML dict → normalized dict for `Scenario`.
  - Handle renamed fields (see Stories 5/6) and centralized material/energy mapping.
  - Errors: clear exceptions with file path and field path for malformed shapes or missing required fields.
- Acceptance: Valid YAML → normalized dict → Scenario builds; malformed shapes produce human-readable errors.

## Story 3: Decouple Viability from Hardcoded Materials
- Problem: Viability references fixed material names. Must work with arbitrary materials.
- Requirements:
  - In viability, aggregate finance/emissions/carbon without assuming specific material names (beyond explicit emissions/carbon_locked fields).
  - Support arbitrary material sets; no hardcoded material keys.
- Acceptance: Viability computes with arbitrary materials; removing/renaming materials no longer breaks viability; profit/net carbon/viable remain correct.

## Story 4: Energy to Carbon Impact
- Problem: Energy fields don’t convert to carbon via `energy_sources`.
- Requirements:
  - Compute `energy_emissions_kg = energy_input.amount_kwh * energy_sources[type].carbon_intensity_kg_per_kwh` per process. `energy_output` optional; not used unless explicitly defined later.
  - Add energy-derived emissions into totals; preserve existing emissions/carbon_locked fields additive.
  - Errors: missing/unknown energy type; negative amounts/intensity → clear validation error with path.
- Acceptance: Carbon totals include energy_input-derived emissions; unknown energy type fails clearly; tests cover positive/negative paths.

## Story 5: Rename Process Fields
- Problem: Field names confusing; need clarity.
- Requirements:
  - Rename in models/flow: `input_energy`→`energy_input`; `conserved_energy`→`energy_output`; `inputs`→`materials_input`; `outputs`→`materials_output`.
  - Parser maps old names to new (or fail explicitly—choose and document). Update loader/viability/tests accordingly.
- Acceptance: YAML with new names passes; behavior for old names is defined (mapped or rejected) and documented; tests updated.

## Story 6: Energy Source Legend Enforcement
- Problem: Need explicit mapping from `energy_input.type` to `energy_sources` for carbon computation.
- Requirements:
  - Resolve `energy_input.type` via `energy_sources`; compute carbon; fail if missing.
  - Enforce non-negative amounts/intensities.
- Acceptance: Energy emissions reflected in totals; unknown/missing types fail with clear errors; tests cover.

## Global Error Handling
- Fail fast with clear messages including file path and field path.
- Keep deterministic outputs; no silent defaults for missing mappings.

## Testing
- Unit tests for parser, models, viability after refactor:
  - Unknown material key in inputs/outputs/transfers → error.
  - Unknown energy type → error.
  - Energy-derived carbon included in totals.
  - Field rename handling verified.
  - Viability works with arbitrary material sets.
