# GUL Runtime Usage

This guide documents the executable Python runtime introduced for the `v2.2.0`
workstream. It covers file-backed validation and inference for canonical GUL
JSON specs, the public Python helper surface, and how that runtime relates to
the native `gul` CLI bridge.

Use this path when you need a verified local workflow that does not depend on
the Windows `gul.exe` dataset streamer.

---

## Setup

Install the package in editable mode before using the package entry point:

```bash
python3 -m pip install -e .
```

The repository currently uses the standard library test runner:

```bash
python3 -m unittest tests.test_runtime_io
```

CI runs the runtime unit tests and CLI smoke checks on Python `3.10` through
`3.13` in `.github/workflows/runtime-ci.yml`.

---

## Capability Matrix

Use the Python runtime for file-backed validation and inference in Linux
automation. The native C++ CLI supports dataset streaming and file-backed
`validate` / `infer` for composition tags when built from source.

| Surface | Use for | Verified behavior | Constraints |
|---------|---------|-------------------|-------------|
| `python3 -m gulcli validate` | Validate JSON GUL specs | Loads the file, validates supported tags, emits `gul.validation.result/1` | Python `3.10+`; current validator emits errors, not warnings |
| `python3 -m gulcli infer` | Evaluate executable JSON GUL specs | Loads the file, evaluates supported decision/composition tags, optionally emits trace; use `--facts` for `atom` nodes | `atom` nodes require `--facts` or an in-memory `FactEnvironment` |
| `python3 -m gulcli.runtime_io ...` | Direct module access to the same runtime | Same validation and inference logic as the package entry point | Can emit Python's `runpy` warning; prefer `python3 -m gulcli` for automation |
| Native `gul validate` / `gul infer` | C++ file-backed runtime | Load `*.gul.json`, validate or infer supported tags, emit schema JSON with `--format json` | `atom` execution is not implemented natively; use Python `--facts` for atoms |
| Native `gul -T` / `gul -deepgul` | Dataset JSON Lines streaming | Streams samples from the C++ dataset generator | Requires a launchable native binary; no Python fallback; unbounded without `-n <N>` or `max_samples` |
| `cli_bridge.py` helpers | Python subprocess bridge | Dataset helpers call the native CLI; `validate` / `infer` fall back to Python only when the native executable cannot launch | A native command that starts and exits nonzero does not trigger fallback |

This split matters for automation: `cli_validate` and `cli_infer` try the native
executable first when available. Prefer `python3 -m gulcli` when you need `atom`
evaluation via `--facts`.

---

## Entry Points

### Package Entry Point

```bash
python3 -m gulcli validate examples/specs/basic_infer.gul.json --format json
python3 -m gulcli infer examples/specs/basic_infer.gul.json --format json --trace
python3 -m gulcli infer examples/specs/atom_role.gul.json --facts examples/facts/basic_facts.json --format json
```

### Direct Module Entry Point

Prefer the package entry point above for automation. The direct module form
works, but it can emit Python's `runpy` warning because `gulcli.__init__`
imports `runtime_io` before module execution:

```bash
python3 -m gulcli.runtime_io validate examples/specs/basic_infer.gul.json --format json
python3 -m gulcli.runtime_io infer examples/specs/basic_infer.gul.json --format json --trace
```

Both entry points accept:

| Command | Options | Exit behavior |
|---------|---------|---------------|
| `validate <path>` | `--format text|json`, `--strict` | `0` when `ok=true`, `1` when validation errors are present |
| `infer <path>` | `--format text|json`, `--trace`, `--facts <path>` | `0` on successful inference, `1` when the input cannot be evaluated |

`--facts` loads a JSON fact environment for `atom` predicate evaluation. See
`examples/facts/basic_facts.json` with `examples/specs/atom_role.gul.json`.

`--strict` converts warning-severity validation messages to errors. The current
validator primarily emits errors.

---

## Spec Shape

Runtime input can be either an expression node directly or an object with an
`expr` field:

```json
{
  "expr": {
    "tag": "threshold",
    "threshold": 0.7,
    "p": {
      "tag": "and_",
      "p1": {"tag": "decision", "decision": "permit", "confidence": 0.92},
      "p2": {"tag": "decision", "decision": "permit", "confidence": 0.81}
    }
  }
}
```

See `examples/specs/basic_infer.gul.json` for a thresholded `and_` example and
`examples/specs/jurisdiction_override.gul.json` for a jurisdiction plus override
example.

---

## Supported Tags

The runtime validates and evaluates these tags:

| Tag | Behavior |
|-----|----------|
| `decision` | Creates an evaluated decision with optional `confidence`, `evidence`, and `jurisdiction` |
| `and_`, `or_` | Uses the GUL inference engine's logical combiners |
| `not_` | Inverts `permit` and `deny`; preserves `defer` and `abstain` |
| `implies` | Evaluates as `or_(not_(p1), p2)` |
| `with_confidence` | Intersects the child confidence with the annotation |
| `threshold` | Converts low-confidence decisions to `defer` |
| `jurisdiction` | Keeps the child decision when `request == required` or `request` is below `required`; otherwise returns `abstain` |
| `override` | Applies override semantics where an `abstain` override leaves the base decision unchanged |
| `sequential`, `parallel` | Uses dependent and independent confidence composition |
| `always`, `eventually` | Preserves the child decision and adds structural evidence |
| `until` | Composes the two children as a sequential approximation |

`atom` nodes are structurally validated through `Predicate.from_dict`, but they
cannot be executed without a future fact environment or evaluator backend.

---

## Output Contracts

Validation emits `gul.validation.result/1`, defined in
`schemas/gul.validation.result-1.json`.

Important fields:

- `schema`
- `version`
- `source`
- `ok`
- `errors`
- `normalized`
- `input_hash`

Inference emits `gul.inference.result/1`, defined in
`schemas/gul.inference.result-1.json`.

Important fields:

- `schema`
- `version`
- `input_hash`
- `decision`
- `confidence`
- `evidence`
- `jurisdiction`
- `trace`

`input_hash` is computed from a stable, sorted JSON representation of the
normalized input. Use it to correlate validation and inference records for the
same spec.

---

## Python API

The runtime helpers are exported from both `gulcli.runtime_io` and the package
root:

```python
from pathlib import Path
from gulcli import infer_file, validate_file

spec = Path("examples/specs/basic_infer.gul.json")

validation = validate_file(spec)
result = infer_file(spec, include_trace=True)
```

Lower-level helpers accept already-loaded Python data:

```python
from gulcli import evaluate_expr_data, validate_spec_data

payload = {"tag": "decision", "decision": "permit", "confidence": 0.9}

validation = validate_spec_data(payload)
result = evaluate_expr_data(payload)
```

---

## Native CLI Bridge

`cli_bridge.py` wraps the native `gul` executable for dataset generation and
for `validate` / `infer` compatibility.

Executable resolution order is:

1. `gul_exe_path` argument
2. `GUL_EXE_PATH` environment variable
3. package-local build artifacts under `cpp/build/`
4. `gul` on `PATH`

`cli_validate` and `cli_infer` try the native executable first. If the
executable is missing or cannot be launched, they fall back to the Python
runtime. A native executable that starts and exits nonzero does not trigger the
fallback; the native result is returned.

Dataset generation helpers (`generate_dataset`, `stream_dataset`) require the
native CLI and do not have a Python fallback.

Additional bridge constraints:

- `generate_dataset` uses `-oneshot -T -n <N>`, can pass `-config`, `-random`,
  `-block`, and `-seed`, and uses a `300` second subprocess timeout.
- `stream_dataset` uses `-oneshot -T`, can pass `-n`, `-config`, and `-random`,
  but does not expose `-block` or `-seed`.
- `validate` and `infer` use a `30` second timeout and fall back to
  `runtime_io` only for `FileNotFoundError` or `OSError`.
- `find_gul_exe` checks an explicit argument, `GUL_EXE_PATH`, package-local
  `cpp/build/` artifacts, then `gul` on `PATH`.

---

## Dataset Generation Boundaries

The C++ dataset generator emits JSON Lines records with `entity`, `predicate`,
`context_confidence`, `decision`, `confidence`, and optional `evidence` fields.
Generation uses declared scenario families and optional GUL spec linkage.

Practical constraints:

- Native generation uses scenario families via `--scenario balanced|adversarial`
  with provenance in `extensions`. Pass `--spec <path>` to link samples to a
  `*.gul.json` policy spec (`source_spec_id` like `spec:basic_infer`) and derive
  permit-path baseline decisions from spec inference.
- `--scenario balanced|adversarial`, `--spec <path>`, and `--stats` are available
  on the native CLI.
- No Python `--scenario` or `--spec` flag is implemented today.
- Native dataset streaming can run indefinitely when neither `-n <N>` nor a
  config `max_samples` value is provided. This applies to stdout and TCP paths.
- TCP streaming with `-L <host/port>` requires a listener to be available before
  the CLI starts.
- The checked-in `gul.exe` is a Windows executable; use Wine on Linux when Wine
  is available, or skip dataset generation in environments without a launchable
  native binary.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `python: command not found` | The environment exposes Python as `python3` | Use `python3 -m ...` commands |
| `No module named gulcli` | Package not installed in the active interpreter | Run `python3 -m pip install -e .` from the repo root |
| `RuntimeWarning: 'gulcli.runtime_io' found in sys.modules...` | Direct module execution after package import | Prefer `python3 -m gulcli ...`; the direct module command still completes |
| `atom nodes are structural only...` | The spec contains executable `atom` nodes | Replace atoms with `decision` nodes for current runtime execution |
| Native `gul validate` or `gul infer` errors on atom specs | Native runtime does not evaluate atoms yet | Use `python3 -m gulcli infer --facts ...` for atom-backed specs |
| `gul` or `wine` is missing | Native Windows streamer is not available in the current environment | Use the Python runtime for validate/infer, or install Wine / provide `GUL_EXE_PATH` for dataset generation |
| Empty `trace` in inference output | `--trace` / `include_trace=True` was not requested | Re-run inference with trace enabled |

---

## Current Limitations

- `atom` execution still requires a future fact environment or evaluator backend.
- Temporal tags are structural approximations, not full temporal model checking.
- The Python runtime covers validation and inference; dataset streaming still
  depends on the native CLI.
- Native `gul validate` and `gul infer` are file-backed for composition tags but do not evaluate `atom` nodes without a fact environment.
- Dataset generation currently uses built-in sample pools rather than declared
  scenario families or source specifications.
- `gul.exe` is a Windows binary. On Linux it requires Wine, and Wine may not be
  installed in all automation environments.
