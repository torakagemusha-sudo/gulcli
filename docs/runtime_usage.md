# GUL Runtime Usage

This document describes the executable Python runtime path added during the `v2.2.0` upgrade work.

It is the fastest available route to real file-backed validation and inference while the C++ CLI surface is still being upgraded.

---

## Entry points

### Package entry point

```bash
python -m gulcli validate examples/specs/basic_infer.gul.json --format json
python -m gulcli infer examples/specs/basic_infer.gul.json --format json --trace
```

### Direct module entry point

```bash
python -m gulcli.runtime_io validate examples/specs/basic_infer.gul.json --format json
python -m gulcli.runtime_io infer examples/specs/basic_infer.gul.json --format json --trace
```

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

`atom` nodes are structurally validated but are not directly executable yet without a fact environment.

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
from gulcli.runtime_io import validate_file, infer_file

validation = validate_file(Path("examples/specs/basic_infer.gul.json"))
result = infer_file(Path("examples/specs/basic_infer.gul.json"), include_trace=True)
```

---

## Current limitations

- the existing C++ `validate` / `infer` path is still separate from this Python runtime
- `atom` execution requires a future fact environment or evaluator backend
- the public package `__init__` surface has not yet been rewired to re-export runtime helpers

This document exists so the executable capability is discoverable immediately, even before the remaining surface unification work lands.
