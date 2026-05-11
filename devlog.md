# Devlog

## 2026-05-11T16:07:50Z

Aligned developer and runtime documentation with the current source-backed repository: updated `AGENTS.md` setup/test guidance with copyable `python3` commands for this Linux image, clarified that Python `runtime_io` is the real validation/inference path, and marked native C++ `validate` / `infer` as placeholders while preserving C++ dataset-streaming guidance.

## 2026-04-12T02:00:17Z

Exported `runtime_io` helpers from the package root (`validate_spec_data`, `evaluate_expr_data`, `validate_file`, `infer_file`), bumped package version to `2.2.0-dev0` (aligned with `pyproject.toml`), updated `cli_bridge.validate` / `cli_infer` to try the native CLI first then fall back to the Python runtime, and documented the executable runtime commands in `README.md`.
