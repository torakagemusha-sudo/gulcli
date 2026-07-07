# Devlog

## 2026-07-07T08:37:54Z

Reviewed merged PR #21 and extended the Linear-ready project backfill because Linear access was still unavailable in the automation environment. Added the PR #21 project update payload to `docs/PROJECT_UPDATES.md` and refreshed README pointers so the related Linear project can be created or updated from the repo ledger.

## 2026-07-07T07:42:51Z

Reviewed merged PR #20 and recorded a Linear-ready project backfill in `docs/PROJECT_UPDATES.md` because Linear access was unavailable in the automation environment. Linked the project update record from README files so the runtime documentation refresh can be synced into Linear when credentials are available.

## 2026-07-06T16:06:02Z

Ran scheduled engineering documentation automation. Refreshed runtime docs and README to match v2.2.0 shipped behavior for native file-backed `validate`/`infer`, fact-backed `atom` evaluation with `--facts`, scenario-driven dataset provenance, and current CLI bridge limits.

## 2026-07-03T13:21:00Z

Merged PR #19 into `main` (consolidated remaining `cursor/*` documentation branches). All 15 `cursor/*` branches are fully merged into `main`; no open PRs remain. Remote branch deletion is blocked by repository rules (`GH013: Cannot delete this branch`).

## 2026-07-03T12:10:00Z

Merged remaining `cursor/*` documentation branches into `main`, resolving conflicts in favor of the current v2.2.0 implementation (native file-backed `validate`/`infer`, `--facts`, scenario-driven dataset generation). Preserved historical devlog entries from security review and verification branches.

## 2026-07-01T20:00:00Z

Verified "ALL 3" deliverables merged on `main` (PR #15): scenario-driven native datasets (`--scenario`, `--stats`, provenance), Python temporal trace enrichment (`ALWAYS`/`EVENTUALLY`/`UNTIL`), and C++ `FactEnvironment` with `--facts` infer parity. Full test suite passes (23 tests).

## 2026-07-02T07:00:00Z

Added explicit `permissions: contents: read` to all GitHub Actions workflows (`runtime-ci`, `package-ci`, `cpp-runtime-ci`) to satisfy CodeQL least-privilege check.

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

## 2026-06-26T09:17:32Z

Performed scheduled at-rest security review (vulnerability scan). Explored entire Python and C++ codebase, traced input flows, validated subprocess execution paths, and tested recursion depth limits. Identified 2 MEDIUM-severity findings: (1) arbitrary binary execution via unvalidated `GUL_EXE_PATH` environment variable in `cli_bridge.py`, and (2) unbounded recursion DoS in `runtime_io.py` expression tree validation/inference. Both confirmed with proof-of-concept reproduction.

## 2026-07-07T09:28:00Z

Scheduled vulnerability scan (cron). Scanned the full codebase at commit 94f9150. Only documentation files changed since the last scan (a81bab5). Identified one new MEDIUM finding: unescaped exception message in the C++ CLI `cmd_infer` JSON error output path (`cli.cpp:176-177`) enables JSON structure injection when the file path contains double-quote characters. The existing `json_escape()` function is used in validation output but not in the inference error handler. Reported to Slack and updated automation memory.

## 2026-06-06T08:01:31Z

Handled the follow-up reminder to commit and push if appropriate. Verified the working tree contained only devlog updates, added this turn's UTC devlog entry, and prepared the devlog-only change for commit and push on the current branch.

## 2026-06-06T08:00:17Z

Performed security review automation for PR #7. Inspected the documentation-only diff, checked prior GitHub review threads, traced referenced runtime/bridge/CLI paths for attacker-controlled input to security sinks, and posted the resulting assessment without pushing code changes.

## 2026-05-18T16:03:04Z

Refreshed developer-facing runtime documentation after verifying the Python `gulcli` package path with `python3`: documented editable setup, runtime validation/inference commands, schema contracts, bridge fallback behavior, native `gul.exe` constraints, CI coverage, direct-module warning behavior, and troubleshooting notes. Updated `AGENTS.md` so future automation treats the repo as a Python package plus native binary rather than a binary-only distribution.

## 2026-04-13T16:05:45Z

Refreshed `docs/runtime_usage.md` to match current runtime behavior by replacing stale limitations, documenting verified `python -m gulcli` and `python -m gulcli.runtime_io` entrypoints, clarifying executable-vs-structural expression tags, adding concrete runtime semantics (`threshold`, `jurisdiction`, `override`, `until`), describing `cli_bridge` fallback constraints, and adding setup/troubleshooting notes observed in this environment (`python3` usage and editable install requirement).

## 2026-04-12T02:00:17Z

Exported `runtime_io` helpers from the package root (`validate_spec_data`, `evaluate_expr_data`, `validate_file`, `infer_file`), bumped package version to `2.2.0-dev0` (aligned with `pyproject.toml`), updated `cli_bridge.validate` / `cli_infer` to try the native CLI first then fall back to the Python runtime, and documented the executable runtime commands in `README.md`.
