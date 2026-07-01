# Phase 1 Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gate the Python runtime for release with golden-output tests, JSON schema validation, README smoke coverage in CI, and packaging verification.

**Architecture:** Extend `tests/` with golden fixtures under `tests/golden/` and a small schema-validation helper that loads `schemas/*.json` without external dependencies (stdlib `json` + optional lightweight validator or hand-rolled required-field checks). CI runs the expanded suite across Python 3.10–3.13. Packaging workflow builds sdist/wheel and smoke-installs in an isolated venv.

**Tech Stack:** Python 3.10+, stdlib `unittest`, GitHub Actions, setuptools (`pyproject.toml`)

**Design reference:** `docs/superpowers/specs/2026-07-01-gulcli-roadmap-design.md` §Phase 1

---

## File map

| File | Responsibility |
|------|----------------|
| `tests/golden/basic_infer.validate.json` | Expected validation output for `examples/specs/basic_infer.gul.json` |
| `tests/golden/basic_infer.infer.json` | Expected inference output (no trace) |
| `tests/golden/basic_infer.infer.trace.json` | Expected inference output with trace |
| `tests/golden/jurisdiction_override.infer.json` | Second fixture for jurisdiction/override |
| `tests/test_golden.py` | Compares runtime output to golden files (stable fields only) |
| `tests/test_schemas.py` | Validates public JSON envelopes against schemas |
| `tests/schema_validate.py` | Minimal schema checker (required fields + const checks) |
| `.github/workflows/runtime-ci.yml` | Add golden + schema test steps |
| `.github/workflows/package-ci.yml` | sdist/wheel build + install smoke |

---

## Task 1: Golden fixture capture helper

**Files:**
- Create: `tests/golden/README.md`
- Create: `tests/golden/basic_infer.validate.json`
- Create: `tests/golden/basic_infer.infer.json`
- Create: `tests/golden/basic_infer.infer.trace.json`

- [ ] **Step 1: Create golden directory README**

```markdown
# Golden fixtures

Byte-stable expected outputs for runtime_io validate/infer.

Regenerate after intentional output changes:

```bash
python3 -m gulcli validate examples/specs/basic_infer.gul.json --format json > tests/golden/basic_infer.validate.json
python3 -m gulcli infer examples/specs/basic_infer.gul.json --format json > tests/golden/basic_infer.infer.json
python3 -m gulcli infer examples/specs/basic_infer.gul.json --format json --trace > tests/golden/basic_infer.infer.trace.json
```
```

- [ ] **Step 2: Capture golden files from current runtime**

Run from repo root:

```bash
python3 -m pip install -e .
python3 -m gulcli validate examples/specs/basic_infer.gul.json --format json | python3 -m json.tool > tests/golden/basic_infer.validate.json
python3 -m gulcli infer examples/specs/basic_infer.gul.json --format json | python3 -m json.tool > tests/golden/basic_infer.infer.json
python3 -m gulcli infer examples/specs/basic_infer.gul.json --format json --trace | python3 -m json.tool > tests/golden/basic_infer.infer.trace.json
```

Expected: three JSON files with `schema`, `version`, `input_hash`, and decision fields.

- [ ] **Step 3: Commit**

```bash
git add tests/golden/
git commit -m "test: add golden fixtures for basic_infer spec"
```

---

## Task 2: Golden comparison tests

**Files:**
- Create: `tests/test_golden.py`
- Test: `tests/test_golden.py`

- [ ] **Step 1: Write failing golden test**

```python
import json
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN = Path(__file__).resolve().parent / "golden"
SPEC = REPO_ROOT / "examples/specs/basic_infer.gul.json"


def run_cli(cmd: list[str]) -> dict:
    proc = subprocess.run(
        ["python3", "-m", "gulcli", *cmd, str(SPEC), "--format", "json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


class GoldenOutputTests(unittest.TestCase):
    def test_validate_matches_golden(self):
        expected = json.loads((GOLDEN / "basic_infer.validate.json").read_text())
        actual = run_cli(["validate"])
        self.assertEqual(actual["schema"], expected["schema"])
        self.assertEqual(actual["ok"], expected["ok"])
        self.assertEqual(actual["input_hash"], expected["input_hash"])
        self.assertEqual(actual["errors"], expected["errors"])

    def test_infer_matches_golden(self):
        expected = json.loads((GOLDEN / "basic_infer.infer.json").read_text())
        actual = run_cli(["infer"])
        self.assertEqual(actual["decision"], expected["decision"])
        self.assertAlmostEqual(actual["confidence"], expected["confidence"])
        self.assertEqual(actual["input_hash"], expected["input_hash"])

    def test_infer_trace_matches_golden(self):
        expected = json.loads((GOLDEN / "basic_infer.infer.trace.json").read_text())
        proc = subprocess.run(
            ["python3", "-m", "gulcli", "infer", str(SPEC), "--format", "json", "--trace"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        actual = json.loads(proc.stdout)
        self.assertEqual(len(actual["trace"]), len(expected["trace"]))
        self.assertEqual(actual["decision"], expected["decision"])
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python3 -m unittest tests.test_golden -v`
Expected: PASS (3 tests)

- [ ] **Step 3: Commit**

```bash
git add tests/test_golden.py
git commit -m "test: add golden output comparison tests"
```

---

## Task 3: Minimal schema validator

**Files:**
- Create: `tests/schema_validate.py`
- Create: `tests/test_schemas.py`

- [ ] **Step 1: Write schema helper**

```python
"""Minimal JSON schema checks without external dependencies."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def validate_against_schema(data: dict[str, Any], schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    if schema.get("type") == "object":
        if not isinstance(data, dict):
            return [f"{path}: expected object"]
        for key in schema.get("required", []):
            if key not in data:
                errors.append(f"{path}: missing required field {key!r}")
        props = schema.get("properties", {})
        for key, subschema in props.items():
            if key in data:
                errors.extend(validate_against_schema(data[key], subschema, f"{path}.{key}"))
        const = props.get("schema", {}).get("const")
        if const is not None and data.get("schema") != const:
            errors.append(f"{path}.schema: expected {const!r}")
    elif schema.get("type") == "array":
        if not isinstance(data, list):
            return [f"{path}: expected array"]
        item_schema = schema.get("items", {})
        for i, item in enumerate(data):
            errors.extend(validate_against_schema(item, item_schema, f"{path}[{i}]"))
    elif schema.get("type") == "string":
        if not isinstance(data, str):
            errors.append(f"{path}: expected string")
    elif schema.get("type") == "boolean":
        if not isinstance(data, bool):
            errors.append(f"{path}: expected boolean")
    elif schema.get("type") == "number":
        if not isinstance(data, (int, float)):
            errors.append(f"{path}: expected number")
    return errors
```

- [ ] **Step 2: Write schema tests**

```python
import json
import unittest
from pathlib import Path

from gulcli import infer_file, validate_file
from tests.schema_validate import load_schema, validate_against_schema

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = REPO_ROOT / "examples/specs/basic_infer.gul.json"


class SchemaValidationTests(unittest.TestCase):
    def test_validation_result_matches_schema(self):
        result = validate_file(SPEC)
        schema = load_schema("gul.validation.result-1.json")
        errors = validate_against_schema(result, schema)
        self.assertEqual(errors, [], errors)

    def test_inference_result_matches_schema(self):
        result = infer_file(SPEC, include_trace=True)
        schema = load_schema("gul.inference.result-1.json")
        errors = validate_against_schema(result, schema)
        self.assertEqual(errors, [], errors)
```

- [ ] **Step 3: Run tests**

Run: `python3 -m unittest tests.test_schemas -v`
Expected: PASS (2 tests)

- [ ] **Step 4: Commit**

```bash
git add tests/schema_validate.py tests/test_schemas.py
git commit -m "test: validate runtime JSON against canonical schemas"
```

---

## Task 4: Expand CI workflow

**Files:**
- Modify: `.github/workflows/runtime-ci.yml`

- [ ] **Step 1: Add golden and schema test steps after unit tests**

Insert after the "Run unit tests" step:

```yaml
      - name: Run golden output tests
        run: |
          python -m unittest tests.test_golden

      - name: Run schema validation tests
        run: |
          python -m unittest tests.test_schemas
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/runtime-ci.yml
git commit -m "ci: run golden and schema validation tests"
```

---

## Task 5: Packaging CI workflow

**Files:**
- Create: `.github/workflows/package-ci.yml`

- [ ] **Step 1: Add packaging workflow**

```yaml
name: package-ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build-and-install:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Build sdist and wheel
        run: |
          python -m pip install --upgrade pip build
          python -m pip build

      - name: Smoke install wheel in clean venv
        run: |
          python -m venv /tmp/gulcli-venv
          /tmp/gulcli-venv/bin/pip install dist/*.whl
          /tmp/gulcli-venv/bin/python -m gulcli validate examples/specs/basic_infer.gul.json --format json
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/package-ci.yml
git commit -m "ci: add wheel build and smoke install workflow"
```

---

## Task 6: Jurisdiction override golden fixture

**Files:**
- Create: `tests/golden/jurisdiction_override.infer.json`
- Modify: `tests/test_golden.py`

- [ ] **Step 1: Capture second fixture**

```bash
python3 -m gulcli infer examples/specs/jurisdiction_override.gul.json --format json | python3 -m json.tool > tests/golden/jurisdiction_override.infer.json
```

- [ ] **Step 2: Add test case**

```python
    def test_jurisdiction_override_infer(self):
        spec = REPO_ROOT / "examples/specs/jurisdiction_override.gul.json"
        expected = json.loads((GOLDEN / "jurisdiction_override.infer.json").read_text())
        proc = subprocess.run(
            ["python3", "-m", "gulcli", "infer", str(spec), "--format", "json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        actual = json.loads(proc.stdout)
        self.assertEqual(actual["decision"], expected["decision"])
```

- [ ] **Step 3: Run full suite**

Run: `python3 -m unittest discover -s tests -v`
Expected: all tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/golden/jurisdiction_override.infer.json tests/test_golden.py
git commit -m "test: add jurisdiction_override golden fixture"
```

---

## Phase 1 exit checklist

- [ ] `python3 -m unittest discover -s tests` passes locally
- [ ] CI green on Python 3.10–3.13
- [ ] `package-ci` builds wheel and smoke-installs
- [ ] Golden fixtures cover at least 2 spec files
- [ ] Schema tests validate both validation and inference envelopes

---

## What comes next (Phases 2–3)

After Phase 1 lands, start these tracks in parallel per the design spec:

| Track | Plan to write | First deliverable |
|-------|---------------|-------------------|
| A — Native closure | `2026-07-01-phase2-native-validate-infer.md` | `cpp/src/validate.cpp` file loader |
| B — Atom execution | `2026-07-01-phase3a-fact-environment.md` | `facts.py` + `--facts` CLI flag |
| C — Done | This plan | Release-gated Python runtime |
