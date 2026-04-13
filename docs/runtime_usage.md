# GUL Runtime Usage

This runbook covers the executable JSON runtime in `gulcli.runtime_io` and the package CLI entrypoint in `python -m gulcli`.

Use this path when you need deterministic file-backed `validate`/`infer` behavior from Python, including in environments where the native `gul` binary is unavailable.

---

## Setup

Install the package first:

```bash
python -m pip install -e .
```

If your environment does not provide `python`, use `python3` for all commands in this document.

---

## Entry Points

Recommended command surface:

```bash
python -m gulcli validate examples/specs/basic_infer.gul.json --format json
python -m gulcli infer examples/specs/basic_infer.gul.json --format json --trace
```

Direct module entrypoint (equivalent behavior):

```bash
python -m gulcli.runtime_io validate examples/specs/basic_infer.gul.json --format json
python -m gulcli.runtime_io infer examples/specs/basic_infer.gul.json --format json --trace
```

---

## JSON Expression Coverage

### Executable tags

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

### Validation-only tag

- `atom` is structurally validated but is not executable without an external fact environment.

---

## Runtime Semantics Highlights

- `threshold` preserves the input decision only when `confidence >= threshold`; otherwise output is `defer`.
- `jurisdiction` returns the inner result when `request == required` or `request` is a dotted child of `required`; otherwise output is `abstain` with confidence `1.0`.
- `override` applies `DecisionCombiner.override(base, override)`.
- `override` keeps the base confidence when override decision is `abstain`; otherwise confidence is union-combined (`max(base, override)`).
- `until` is currently evaluated as a sequential approximation.

---

## Output Contracts

Validation output shape:

- schema: `gul.validation.result/1`
- key fields: `source`, `ok`, `errors`, `normalized`, `input_hash`, `version`

Inference output shape:

- schema: `gul.inference.result/1`
- key fields: `decision`, `confidence`, `evidence`, `jurisdiction`, `trace`, `input_hash`, `version`

Example spec used by tests and docs:

```text
examples/specs/basic_infer.gul.json
```

---

## Python API Usage

```python
from pathlib import Path
from gulcli import validate_file, infer_file

spec = Path("examples/specs/basic_infer.gul.json")
validation = validate_file(spec)
result = infer_file(spec, include_trace=True)
```

---

## CLI Bridge Fallback Workflow

`cli_validate` and `cli_infer` in `cli_bridge.py` first attempt the native `gul` executable and then fall back to the Python runtime only when the executable cannot be started (`FileNotFoundError` or `OSError`).

This means:

- missing binary: fallback runs automatically
- binary starts but returns an error code: fallback is not used

---

## Troubleshooting

- `python: command not found`: rerun with `python3`.
- `No module named gulcli`: install in the current environment with `python -m pip install -e .`.
- `atom nodes are structural only`: replace `atom` with executable decision expressions, or evaluate with a fact-aware backend.
- `RuntimeWarning` from `python -m gulcli.runtime_io`: prefer `python -m gulcli` when possible.
