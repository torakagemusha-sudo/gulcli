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

## Entry Points

### Package Entry Point

```bash
python3 -m gulcli validate examples/specs/basic_infer.gul.json --format json
python3 -m gulcli infer examples/specs/basic_infer.gul.json --format json --trace
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
| `infer <path>` | `--format text|json`, `--trace` | `0` on successful inference, `1` when the input cannot be evaluated |

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

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `python: command not found` | The environment exposes Python as `python3` | Use `python3 -m ...` commands |
| `No module named gulcli` | Package not installed in the active interpreter | Run `python3 -m pip install -e .` from the repo root |
| `RuntimeWarning: 'gulcli.runtime_io' found in sys.modules...` | Direct module execution after package import | Prefer `python3 -m gulcli ...`; the direct module command still completes |
| `atom nodes are structural only...` | The spec contains executable `atom` nodes | Replace atoms with `decision` nodes for current runtime execution |
| `gul` or `wine` is missing | Native Windows streamer is not available in the current environment | Use the Python runtime for validate/infer, or install Wine / provide `GUL_EXE_PATH` for dataset generation |
| Empty `trace` in inference output | `--trace` / `include_trace=True` was not requested | Re-run inference with trace enabled |

---

## Current Limitations

- `atom` execution still requires a future fact environment or evaluator backend.
- Temporal tags are structural approximations, not full temporal model checking.
- The Python runtime covers validation and inference; dataset streaming still
  depends on the native CLI.
- `gul.exe` is a Windows binary. On Linux it requires Wine, and Wine may not be
  installed in all automation environments.
