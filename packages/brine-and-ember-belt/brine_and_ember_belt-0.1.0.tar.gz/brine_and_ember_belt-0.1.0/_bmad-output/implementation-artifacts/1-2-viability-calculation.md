# Story 1.2: viability-calculation

Status: ready-for-dev

## Story

As a developer agent,
I want the CLI to compute scenario viability using user-defined materials and energy-driven carbon math,
so that results stay correct and flexible when materials and energy definitions change.

## Acceptance Criteria

1. Viability calculation works with arbitrary user-defined materials (no hardcoded material names); unknown material references raise clear validation errors.
2. Energy input is converted to carbon via `energy_sources` (amount_kwh * carbon_intensity_kg_per_kwh) and included in emissions totals; missing/unknown energy types error clearly.
3. Process fields are renamed and supported (`materials_input`, `materials_output`, `energy_input`, `energy_output`); old names are either mapped or rejected consistently and documented.
4. Viability outputs profit/net carbon/viable flag correctly after refactor; unit tests cover positive/negative viability scenarios with custom materials and energy.
5. Parser module normalizes YAML → models with the new field names, validates materials and energy references, and provides readable errors with field paths.

## Tasks / Subtasks

- [ ] Implement parser module to normalize YAML → Scenario with new field names
  - [ ] Map/migrate old field names or explicitly reject; document behavior
  - [ ] Validate materials/energy references; raise clear errors with paths
- [ ] Refactor models/viability for renamed fields and arbitrary materials
  - [ ] Update models to use materials_input/materials_output/energy_input/energy_output
  - [ ] Ensure viability uses arbitrary materials (no hardcoded keys)
- [ ] Add energy-to-carbon calculation
  - [ ] Include energy_input-derived emissions in totals; error on unknown/missing energy types
- [ ] Testing
  - [ ] Unit tests for parser validations (unknown material/energy, field rename handling)
  - [ ] Unit tests for viability (profit/net carbon and viability flag with custom materials/energy)

## Dev Notes

- Source: _bmad-output/implementation-artifacts/dev-stories.md (Story 2-6 combined for viability refactor)
- Keep deterministic outputs; fail fast with file/field path in errors.
- No hardcoded material assumptions; all materials come from YAML `materials`.
- Energy emissions = energy_input.amount_kwh * energy_sources[type].carbon_intensity_kg_per_kwh.
- Decide and document behavior for legacy field names (map vs reject).

### Project Structure Notes

- Use existing paths: loader/parser/models/viability modules; tests under tests/.
- JSON outputs remain in outputs/ via main CLI.

### References

- Architecture: _bmad-output/planning-artifacts/architecture.md
- Requirements: _bmad-output/implementation-artifacts/dev-stories.md

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
