# Devlog

## 2026-04-12T02:00:17Z

Exported `runtime_io` helpers from the package root (`validate_spec_data`, `evaluate_expr_data`, `validate_file`, `infer_file`), bumped package version to `2.2.0-dev0` (aligned with `pyproject.toml`), updated `cli_bridge.validate` / `cli_infer` to try the native CLI first then fall back to the Python runtime, and documented the executable runtime commands in `README.md`.
