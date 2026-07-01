# Devlog

## 2026-07-01T14:30:00Z

Implemented Phase 1 production hardening: golden fixtures for `basic_infer` and `jurisdiction_override` specs, `tests/test_golden.py` and `tests/test_schemas.py` with a stdlib-only `tests/schema_validate.py` helper, expanded `runtime-ci.yml` with golden and schema test steps, and added `package-ci.yml` for wheel build plus smoke install (11 tests passing).

## 2026-07-01T12:00:00Z

Consolidated open documentation PRs (#6, #7, #9) into a single branch: merged capability matrix and dataset-generation boundaries into `docs/runtime_usage.md`, hybrid `AGENTS.md` (Python runtime + C++ build + Wine/`gul.exe` paths), PR #9 README/cpp README updates (native placeholder caveats, bounded streaming, removed stale Lean references), and removed all public mentions of external integration frameworks from README, `pyproject.toml`, and package docstring. Wrote roadmap design spec at `docs/superpowers/specs/2026-07-01-gulcli-roadmap-design.md` covering v2.2.0 native closure (A), Python runtime depth (B), and production hardening (C).

## 2026-05-18T16:03:04Z

Refreshed developer-facing runtime documentation after verifying the Python `gulcli` package path with `python3`: documented editable setup, runtime validation/inference commands, schema contracts, bridge fallback behavior, native `gul.exe` constraints, CI coverage, direct-module warning behavior, and troubleshooting notes. Updated `AGENTS.md` so future automation treats the repo as a Python package plus native binary rather than a binary-only distribution.

## 2026-04-12T02:00:17Z

Exported `runtime_io` helpers from the package root (`validate_spec_data`, `evaluate_expr_data`, `validate_file`, `infer_file`), bumped package version to `2.2.0-dev0` (aligned with `pyproject.toml`), updated `cli_bridge.validate` / `cli_infer` to try the native CLI first then fall back to the Python runtime, and documented the executable runtime commands in `README.md`.
