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
tracetree init
tracetree validate
tracetree link
tracetree aggregate
```

## Expected Structure (Defaults)
- `docs/traceability/requirements.md`
- `docs/traceability/risk_controls.md`
- `docs/traceability/traceability_matrix.csv`
- `docs/traceability/soup_inventory.md`

If you do not already have these files, run:
```bash
tracetree init
```

Generated reports (default):
- `docs/traceability/generated/traceability_report.md`
- `docs/traceability/generated/traceability_report.json`
- `docs/traceability/generated/testid_links.md`
- `docs/traceability/generated/testid_links.json`
- `docs/traceability/generated/aggregate/traceability_rollup.md`
- `docs/traceability/generated/aggregate/traceability_rollup.json`

Test discovery defaults:
- GTest: `tests/`, `test/`
- Pytest: `tests/`, `test/`
- JS/TS (Jest/Mocha/Vitest/Deno): `tests/`, `test/`, `__tests__/`, `spec/`
- Rust (`#[test]`): `tests/`, `test/`, `src/`

TestID matching:
- GTest: `SuiteName.TestName`
- Pytest: `test_function_name`
- JS/TS: string in `test("name", ...)` or `it("name", ...)` (also `Deno.test("name", ...)`)
- Rust: function name following `#[test]`

## Repo Configuration
Create `.traceability/config.json` to override defaults:
```json
{
  "traceability_dir": "docs/traceability",
  "traceability_output_dir": "docs/traceability/generated",
  "requirements_file": "requirements.md",
  "risk_controls_file": "risk_controls.md",
  "matrix_file": "traceability_matrix.csv",
  "gtest_roots": ["tests"],
  "pytest_roots": ["bindings/python/tests"],
  "js_roots": ["packages/web/tests"],
  "rust_roots": ["crates/core/tests", "crates/core/src"]
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
