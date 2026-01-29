# Traceability Tooling

Universal traceability validation and rollup for requirements ↔ tests mapping. Designed
to work across monorepos and git submodules.

## Install
```bash
pip install tracetree
```

## Quick Start
From a repo root with `docs/traceability/`:
```bash
tracetree validate
tracetree link
tracetree aggregate
```

## Expected Structure (Defaults)
- `docs/traceability/requirements.md`
- `docs/traceability/risk_controls.md`
- `docs/traceability/traceability_matrix.csv`

Test discovery defaults:
- GTest: `tests/`, `test/`
- Pytest: `tests/`, `test/`

## Repo Configuration
Create `.traceability/config.json` to override defaults:
```json
{
  "traceability_dir": "docs/traceability",
  "requirements_file": "requirements.md",
  "risk_controls_file": "risk_controls.md",
  "matrix_file": "traceability_matrix.csv",
  "gtest_roots": ["tests"],
  "pytest_roots": ["bindings/python/tests"]
}
```

You can also point to a custom config with `TRACEABILITY_CONFIG=/path/to/config.json`.

## Coverage Threshold
Default is 100%. Override with:
```bash
TRACEABILITY_REQ_COVERAGE=0.95 tracetree validate
```

## Submodule Rollup
`tracetree aggregate` reads `.gitmodules` and validates each submodule that contains
traceability files. Results are written to:
`docs/traceability/aggregate/traceability_rollup.md`.
