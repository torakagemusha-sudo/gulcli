# Devlog

## 2026-06-26T09:17:32Z

Performed scheduled at-rest security review (vulnerability scan). Explored entire Python and C++ codebase, traced input flows, validated subprocess execution paths, and tested recursion depth limits. Identified 2 MEDIUM-severity findings: (1) arbitrary binary execution via unvalidated GUL_EXE_PATH environment variable in cli_bridge.py, and (2) unbounded recursion DoS in runtime_io.py expression tree validation/inference. Both confirmed with proof-of-concept reproduction. Posted findings to Slack and persisted to automation memory.

## 2026-05-18T16:03:04Z

Refreshed developer-facing runtime documentation after verifying the Python `gulcli` package path with `python3`: documented editable setup, runtime validation/inference commands, schema contracts, bridge fallback behavior, native `gul.exe` constraints, CI coverage, direct-module warning behavior, and troubleshooting notes. Updated `AGENTS.md` so future automation treats the repo as a Python package plus native binary rather than a binary-only distribution.

## 2026-04-12T02:00:17Z

Exported `runtime_io` helpers from the package root (`validate_spec_data`, `evaluate_expr_data`, `validate_file`, `infer_file`), bumped package version to `2.2.0-dev0` (aligned with `pyproject.toml`), updated `cli_bridge.validate` / `cli_infer` to try the native CLI first then fall back to the Python runtime, and documented the executable runtime commands in `README.md`.
