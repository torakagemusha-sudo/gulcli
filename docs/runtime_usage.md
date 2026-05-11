# GUL Runtime Usage

This document describes the executable Python runtime path added during the `v2.2.0` upgrade work.

It is the current route to real file-backed validation and inference. The native C++ CLI still owns dataset streaming, but its `validate` and `infer` commands are placeholders until the C++ command surface is upgraded.

---

## Entry points

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

### Direct module entry point

```bash
python3 -m gulcli.runtime_io validate examples/specs/basic_infer.gul.json --format json
python3 -m gulcli.runtime_io infer examples/specs/basic_infer.gul.json --format json --trace
```

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

## Supported JSON expression tags

The runtime currently supports these executable tags:

- `decision`
- `and_`
- `or_`
- `not_`
- `implies`
- `with_confidence`
- `threshold`
- `jurisdiction`
- `override`
- `sequential`
- `parallel`
- `always`
- `eventually`
- `until`

`atom` nodes are structurally validated but are not directly executable yet without a fact environment. Inference over an `atom` raises an error.

Binary tags (`and_`, `or_`, `sequential`, `parallel`, `implies`, `until`) use `p1` and `p2` children. Unary tags (`not_`, `always`, `eventually`) use `p`. `threshold` and `with_confidence` also use `p` plus their numeric field.

---

## Validation output

Validation emits a machine-readable envelope shaped as `gul.validation.result/1`.

Example fields:

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

Example fields:

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

## Example executable spec

See:

```text
examples/specs/basic_infer.gul.json
```

This example composes two `permit` decisions through `and_` and then applies a confidence threshold.

---

## Python usage

```python
from pathlib import Path
from gulcli import infer_file, validate_file

validation = validate_file(Path("examples/specs/basic_infer.gul.json"))
result = infer_file(Path("examples/specs/basic_infer.gul.json"), include_trace=True)
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

## Current limitations

- the existing C++ `validate` / `infer` commands are placeholders and are separate from this Python runtime
- `atom` execution requires a future fact environment or evaluator backend

This document exists so the executable capability is discoverable immediately, even before the remaining surface unification work lands.
