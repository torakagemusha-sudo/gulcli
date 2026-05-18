# Devlog

## 2026-05-18T16:03:04Z

Refreshed developer-facing runtime documentation after verifying the Python `gulcli` package path with `python3`: documented editable setup, runtime validation/inference commands, schema contracts, bridge fallback behavior, native `gul.exe` constraints, CI coverage, direct-module warning behavior, and troubleshooting notes. Updated `AGENTS.md` so future automation treats the repo as a Python package plus native binary rather than a binary-only distribution.

## 2026-04-12T02:00:17Z

Exported `runtime_io` helpers from the package root (`validate_spec_data`, `evaluate_expr_data`, `validate_file`, `infer_file`), bumped package version to `2.2.0-dev0` (aligned with `pyproject.toml`), updated `cli_bridge.validate` / `cli_infer` to try the native CLI first then fall back to the Python runtime, and documented the executable runtime commands in `README.md`.
