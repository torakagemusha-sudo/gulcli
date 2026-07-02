# Devlog

## 2026-07-02T06:40:00Z

Rebuilt checked-in `gul.exe` via mingw-w64 cross-compile (static libgcc/libstdc++), added `cpp/scripts/build-gul-exe.sh`, Windows `build-and-smoke-windows` job in `cpp-runtime-ci.yml`, updated `cli_bridge` to resolve root `gul.exe`. Merged v2.2.0 work and tagged release `2.2.0`.

## 2026-07-02T05:20:00Z

Fixed CI failures: bundled `schema_validate` as installable top-level module (`py-modules` in `pyproject.toml`), corrected `package-ci.yml` to use `python -m build`, consolidated `runtime-ci` to `unittest discover`. Implemented native `--spec` for spec-linked dataset provenance, bumped version to `2.2.0`, added release notes and marked RELEASE_SPEC §8 criteria complete.

## 2026-07-01T18:00:00Z

Completed roadmap phases 2B, 3B, and native atom port: scenario-driven dataset generation with `--scenario`/`--stats` and provenance extensions in C++; temporal trace enrichment (`ALWAYS`/`EVENTUALLY`/`UNTIL` metadata) in Python inference; native `FactEnvironment` with `--facts` on C++ infer and parity tests for atoms and scenarios.

## 2026-07-01T16:00:00Z

Implemented parallel tracks A and B: Python `facts.py` with `FactEnvironment`, `--facts` CLI flag, `examples/facts/basic_facts.json`, `examples/specs/atom_role.gul.json`, and `tests/test_facts.py`; native C++ `json_io` + `runtime_io` for file-backed `validate`/`infer`, parity tests in `tests/test_native_parity.py`, and `cpp-runtime-ci.yml`. Updated docs to reflect native validate/infer and atom fact-environment requirements.

## 2026-07-01T14:30:00Z

Implemented Phase 1 production hardening: golden fixtures for `basic_infer` and `jurisdiction_override` specs, `tests/test_golden.py` and `tests/test_schemas.py` with a stdlib-only `tests/schema_validate.py` helper, expanded `runtime-ci.yml` with golden and schema test steps, and added `package-ci.yml` for wheel build plus smoke install (11 tests passing).

## 2026-07-01T12:00:00Z

Consolidated open documentation PRs (#6, #7, #9) into a single branch: merged capability matrix and dataset-generation boundaries into `docs/runtime_usage.md`, hybrid `AGENTS.md` (Python runtime + C++ build + Wine/`gul.exe` paths), PR #9 README/cpp README updates (native placeholder caveats, bounded streaming, removed stale Lean references), and removed all public mentions of external integration frameworks from README, `pyproject.toml`, and package docstring. Wrote roadmap design spec at `docs/superpowers/specs/2026-07-01-gulcli-roadmap-design.md` covering v2.2.0 native closure (A), Python runtime depth (B), and production hardening (C).

## 2026-05-18T16:03:04Z

Refreshed developer-facing runtime documentation after verifying the Python `gulcli` package path with `python3`: documented editable setup, runtime validation/inference commands, schema contracts, bridge fallback behavior, native `gul.exe` constraints, CI coverage, direct-module warning behavior, and troubleshooting notes. Updated `AGENTS.md` so future automation treats the repo as a Python package plus native binary rather than a binary-only distribution.

## 2026-04-12T02:00:17Z

Exported `runtime_io` helpers from the package root (`validate_spec_data`, `evaluate_expr_data`, `validate_file`, `infer_file`), bumped package version to `2.2.0-dev0` (aligned with `pyproject.toml`), updated `cli_bridge.validate` / `cli_infer` to try the native CLI first then fall back to the Python runtime, and documented the executable runtime commands in `README.md`.
