# GUL Runtime Usage

This guide documents the executable runtime paths for canonical GUL JSON specs.
It covers Python validation and inference, native `gul validate` / `gul infer`,
fact-backed `atom` evaluation, dataset generation boundaries, and the Python CLI
bridge.

Use `python3 -m gulcli` for portable automation. Use native `gul` commands when
you have built `cpp/build/gul` or provided another launchable binary.

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

## Capability Matrix

Use the Python runtime for portable validation and inference in Linux
automation. The native C++ CLI supports dataset streaming and file-backed
`validate` / `infer` when built from source.

| Surface | Use for | Verified behavior | Constraints |
|---------|---------|-------------------|-------------|
| `python3 -m gulcli validate` | Validate JSON GUL specs | Loads the file, validates supported tags, emits `gul.validation.result/1` | Python `3.10+`; current validator emits errors, not warnings |
| `python3 -m gulcli infer` | Evaluate executable JSON GUL specs | Loads the file, evaluates supported tags, optionally emits trace; use `--facts` for `atom` nodes | `atom` nodes require `--facts` or an in-memory `FactEnvironment` |
| `python3 -m gulcli.runtime_io ...` | Direct module access to the same runtime | Same validation and inference logic as the package entry point | Can emit Python's `runpy` warning; prefer `python3 -m gulcli` for automation |
| Native `gul validate` / `gul infer` | C++ file-backed runtime | Load `*.gul.json`, validate or infer supported tags, emit schema JSON with `--format json`; `infer` accepts `--facts` | Requires a launchable native binary |
| Native `gul -T` / `gul -deepgul` | Dataset JSON Lines streaming | Streams samples from the C++ dataset generator | Requires a launchable native binary; no Python fallback; unbounded without `-n <N>` or `max_samples` |
| `cli_bridge.py` helpers | Python subprocess bridge | Dataset helpers call the native CLI; `validate` / `infer` fall back to Python only when the native executable cannot launch | A native command that starts and exits nonzero does not trigger fallback |

This split matters for automation: `cli_validate` and `cli_infer` try the native
executable first when available. Prefer `python3 -m gulcli` when you need
consistent Python runtime semantics across machines.

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

## Fact environment

`atom` nodes evaluate predicates against a fact environment. Without facts,
inference fails with an error that asks for `--facts` or `facts=`.

```bash
python3 -m gulcli infer examples/specs/atom_role.gul.json \
  --facts examples/facts/basic_facts.json --format json --trace

cpp/build/gul infer examples/specs/atom_role.gul.json \
  --facts examples/facts/basic_facts.json --format json
```

The fact JSON shape matches `FactEnvironment.from_dict`:

| Key | Shape | Used by |
|-----|-------|---------|
| `roles` | Object keyed by `kind:id`, values are role arrays | `has_role` |
| `attributes` | Object keyed by `kind:id`, values are string attribute maps | `has_attribute` |
| `belongs_to` | Array of `{ "entity": ..., "resource": ... }` objects | `belongs_to` |
| `in_context` | Array of `{ "entity": ..., "context": ... }` objects | `in_context` |
| `custom` | Object of boolean named checks | `custom` |
| `now` | Optional Unix timestamp | `time_before`, `time_after` |

Missing role or attribute bindings return `defer`, not `deny`; explicit
mismatches return `deny`.

Programmatic use:

```python
from pathlib import Path
from gulcli.runtime_io import infer_file, load_facts

facts = load_facts(Path("examples/facts/basic_facts.json"))
result = infer_file(Path("examples/specs/atom_role.gul.json"), facts=facts)
```

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
| `atom` | Evaluates a predicate when `--facts` or `facts=` is supplied; raises an error without a fact environment |
| `and_`, `or_` | Uses the GUL inference engine's logical combiners |
| `not_` | Inverts `permit` and `deny`; preserves `defer` and `abstain` |
| `implies` | Evaluates as `or_(not_(p1), p2)` |
| `with_confidence` | Intersects the child confidence with the annotation |
| `threshold` | Converts low-confidence decisions to `defer` |
| `jurisdiction` | Keeps the child decision when `request == required` or `request` is below `required`; otherwise returns `abstain` |
| `override` | Applies override semantics where an `abstain` override leaves the base decision unchanged |
| `sequential`, `parallel` | Uses dependent and independent confidence composition |
| `always`, `eventually` | Preserves the child decision and records structural temporal trace metadata |
| `until` | Composes the two children as a sequential approximation with temporal trace metadata |

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

Temporal tags are structural approximations, not full temporal model checking.
When trace output is enabled, Python temporal evaluation includes metadata:

```json
{
  "rule": "ALWAYS",
  "metadata": {
    "temporal": "always",
    "approximation": "structural"
  }
}
```

See `examples/specs/temporal_always.gul.json` for a runnable temporal spec.

---

## Python API

The runtime helpers are exported from both `gulcli.runtime_io` and the package
root:

```python
from pathlib import Path
from gulcli import infer_file, validate_file
from gulcli.runtime_io import load_facts

spec = Path("examples/specs/basic_infer.gul.json")
atom_spec = Path("examples/specs/atom_role.gul.json")

validation = validate_file(spec)
result = infer_file(spec, include_trace=True)
atom_result = infer_file(atom_spec, facts=load_facts("examples/facts/basic_facts.json"))
```

Lower-level helpers accept already-loaded Python data:

```python
from gulcli import evaluate_expr_data, validate_spec_data

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

The bridge tries the native executable first and only falls back to this Python runtime when the executable is missing or cannot be launched. A native `gul validate` or `gul infer` process that starts and exits nonzero returns its subprocess result. Use `validate_file` / `infer_file` when you need guaranteed Python runtime semantics.

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
| `atom nodes are structural only...` | The spec contains executable `atom` nodes but no facts were supplied | Re-run with `--facts <path>` or call `infer_file(..., facts=load_facts(path))` |
| Native `gul infer` errors on atom specs | No fact environment was supplied, or the binary is older than v2.2.0 | Rebuild the native CLI and pass `--facts <path>` |
| `gul` or `wine` is missing | Native Windows streamer is not available in the current environment | Use the Python runtime for validate/infer, or install Wine / provide `GUL_EXE_PATH` for dataset generation |
| Empty `trace` in inference output | `--trace` / `include_trace=True` was not requested | Re-run inference with trace enabled |

---

## Known limitations

- Temporal tags are structural approximations, not full temporal model checking.
- Dataset generation depends on the native CLI. There is no Python dataset
  generator fallback.
- Native `gul infer` evaluates `atom` nodes only when a fact environment is
  supplied with `--facts`.
- `cli_bridge.generate_dataset` and `cli_bridge.stream_dataset` do not expose
  native `--scenario`, `--spec`, or `--stats` flags today.
- `gul.exe` is a Windows binary. On Linux it requires Wine, and Wine may not be
  installed in all automation environments.
