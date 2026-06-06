# GUL Runtime Usage

This guide documents the executable Python runtime introduced for the `v2.2.0`
workstream. It covers file-backed validation and inference for canonical GUL
JSON specs, the public Python helper surface, and how that runtime relates to
the native `gul` CLI bridge.

It is the current route to real file-backed validation and inference. The native C++ CLI still owns dataset streaming, but its `validate` and `infer` commands are placeholders until the C++ command surface is upgraded.

---

## Setup

Install the package before using module entry points:

```bash
python3 -m pip install -e .
```

Use the Python 3 executable name for your platform. In CI that may be `python`; on this Linux image it is `python3`.

### Package entry point

```bash
python3 -m gulcli validate examples/specs/basic_infer.gul.json --format json
python3 -m gulcli infer examples/specs/basic_infer.gul.json --format json --trace
```

Prefer the package entry point for smoke tests. `gulcli.runtime_io` also exposes a module `main()` for debugging, but running it with `python3 -m gulcli.runtime_io` can emit a `RuntimeWarning` because the package root imports `runtime_io` during initialization.

---

## Input shape

Runtime files are JSON documents containing either an expression node directly or an envelope with an `expr` key:

```json
{
  "expr": {
    "tag": "threshold",
    "threshold": 0.7,
    "p": {
      "tag": "decision",
      "decision": "permit",
      "confidence": 0.9,
      "evidence": ["role check passed"]
    }
  }
}
```

Validation normalizes the complete input with sorted object keys and includes an `input_hash` derived from that normalized form.

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

`atom` nodes are structurally validated but are not directly executable yet without a fact environment. Inference over an `atom` raises an error.

Binary tags (`and_`, `or_`, `sequential`, `parallel`, `implies`, `until`) use `p1` and `p2` children. Unary tags (`not_`, `always`, `eventually`) use `p`. `threshold` and `with_confidence` also use `p` plus their numeric field.

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

Text mode prints `OK` or `INVALID` and each validation message. JSON mode emits the full envelope. `--strict` currently only promotes warnings to errors; the validator does not emit warnings today.

---

## Inference output

Inference emits a machine-readable envelope shaped as `gul.inference.result/1`.

Important fields:

- `schema`
- `version`
- `input_hash`
- `decision`
- `confidence`
- `evidence`
- `jurisdiction`
- `trace`

Text mode prints the decision, confidence, optional jurisdiction, evidence, and trace summary. JSON mode emits the full envelope.

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
from pathlib import Path
from gulcli import infer_file, validate_file

validation = validate_spec_data(payload)
result = evaluate_expr_data(payload)
```

The same helpers are exported from `gulcli.runtime_io` for callers that prefer importing the implementation module directly.

---

## CLI bridge behavior

`cli_bridge.py` is for workflows that want to call the native `gul` executable when it is available:

```python
from pathlib import Path
from gulcli import cli_infer, cli_validate

ok = cli_validate(Path("examples/specs/basic_infer.gul.json"))
result = cli_infer(Path("examples/specs/basic_infer.gul.json"))
```

The bridge tries the native executable first and only falls back to this Python runtime when the executable is missing or cannot be launched. Because the current C++ `validate` and `infer` commands are placeholders that start successfully, use `validate_file` / `infer_file` when you need guaranteed Python runtime semantics.

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

- the existing C++ `validate` / `infer` commands are placeholders and are separate from this Python runtime
- `atom` execution requires a future fact environment or evaluator backend

- `atom` execution still requires a future fact environment or evaluator backend.
- Temporal tags are structural approximations, not full temporal model checking.
- The Python runtime covers validation and inference; dataset streaming still
  depends on the native CLI.
- `gul.exe` is a Windows binary. On Linux it requires Wine, and Wine may not be
  installed in all automation environments.
