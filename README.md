# GUL — Governed Uncertainty Logic v2.1

A formal logic system for policy evaluation under uncertainty. GUL provides a 4-valued decision algebra (`permit`, `deny`, `defer`, `abstain`) with bounded confidence values, jurisdiction scoping, and full audit trails.

This repository contains:
- **Python package** — pure-Python implementation of the GUL type system, inference engine, and policy evaluation
- **C++ CLI** (`gul.exe`) — high-performance dataset streamer for generating ML training data from the GUL formal system

---

## Core Concepts

### Decisions (4-valued logic)

GUL extends boolean allow/deny with two additional outcomes:

| Decision | Meaning |
|----------|---------|
| `PERMIT` | Action allowed |
| `DENY` | Action blocked |
| `DEFER` | Insufficient confidence; escalate to higher authority |
| `ABSTAIN` | Outside jurisdiction scope; policy does not apply |

### Confidence

A bounded value in `[0, 1]` representing certainty in a decision. Four combination modes:

| Mode | Formula | Use when |
|------|---------|---------|
| Union | `max(c1, c2)` | Either source is sufficient (OR) |
| Intersection | `min(c1, c2)` | Both sources required (AND) |
| Sequential | `c1 × c2` | Dependent reasoning; uncertainty compounds |
| Parallel | `c1 + c2 − c1·c2` | Independent sources reinforce each other |

### Jurisdiction

Hierarchical authority scopes (`GLOBAL → REGIONAL → LOCAL → INSTANCE`). Policies declare a jurisdiction; requests outside that scope produce `ABSTAIN` rather than `DENY`.

---

## Python Package

### Installation

```bash
pip install -e .
```

Requires Python 3.10+. No hard dependencies — the optional `geodesic_ai` integration is lazy-imported only when legacy adapters are used.

### Quick start

```python
from gulcli import (
    Confidence, Decision, EvaluatedDecision,
    GULInferenceEngine, GULGovernancePolicy,
)

# 1. Direct inference
engine = GULInferenceEngine()
d1 = EvaluatedDecision(Decision.PERMIT, Confidence(0.9))
d2 = EvaluatedDecision(Decision.PERMIT, Confidence(0.7))

result = engine.evaluate_and(d1, d2)
print(result.decision)          # Decision.PERMIT
print(result.confidence.value)  # 0.7  (min of 0.9, 0.7)

# 2. Policy evaluation
policy = GULGovernancePolicy(max_risk=0.5, min_coherence=0.3, min_confidence=0.6)
decision = policy.evaluate(risk_score=0.2, coherence=0.9)
print(decision.ok)              # True
print(decision.decision)        # Decision.PERMIT
```

### Inference rules

`GULInferenceEngine` provides:

```python
engine.evaluate_and(d1, d2)             # AND: deny dominates; permit requires both
engine.evaluate_or(d1, d2)              # OR: permit if either permits
engine.evaluate_not(d)                  # NOT: PERMIT ↔ DENY; DEFER/ABSTAIN unchanged
engine.evaluate_sequential(d1, d2)      # Dependent chain; confidence multiplies
engine.evaluate_parallel(d1, d2)        # Independent sources; confidence reinforces
engine.evaluate_conditional(cond, t, f) # If-then-else with confidence propagation
engine.evaluate_threshold(d, 0.7)       # Require minimum confidence or DEFER
engine.evaluate_all(decisions, "and")   # Fold over a list

# Retrieve full audit trace
engine.get_trace_summary()
```

### Policy expressions (DSL)

```python
from gulcli import Entity, and_, has_role, has_attribute

user = Entity("agent", "user:alice")
doc  = Entity("resource", "doc:report")

expr = and_(
    has_role(user, "editor"),
    has_attribute(doc, "classification", "internal"),
)
print(expr.to_dict())
```

Available constructors: `atom`, `and_`, `or_`, `not_`, `implies`, `with_confidence`, `always`, `eventually`, `until`, `belongs_to`, `has_role`, `has_attribute`, `in_context`, `time_before`, `time_after`, `custom`.

### Jurisdiction hierarchy

```python
from gulcli import create_jurisdiction_hierarchy

root, regional, local = create_jurisdiction_hierarchy(
    ["global", "eu-west", "eu-west.ireland"]
)

print(local.id.is_sub_jurisdiction(root.id))   # True
print(root.id.is_sub_jurisdiction(local.id))   # False
```

### Legacy adapters

```python
from gulcli import legacy_decision_to_gul, legacy_policy_to_gul

gul_decision = legacy_decision_to_gul(old_decision, confidence=0.85)
gul_policy   = legacy_policy_to_gul(old_policy)
```

Requires `geodesic_ai` to be installed; raises `RuntimeError` otherwise.

---

## C++ CLI

The C++ binary streams ML training samples from the GUL formal system as JSON Lines.

### Build

```bash
cd cpp
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
# Output: build/Release/gul.exe (Windows) or build/gul (Unix)
```

### Dataset streaming

```bash
# Stream to stdout
gul -oneshot -T
gul -T -n 1000
gul -config sample.conf -random -block 32 -T

# Stream to a TCP listener
gul -deepgul -L 127.0.0.1/1234
gul -oneshot -T -L 127.0.0.1/1234 -n 500
```

### Options

| Option | Description |
|--------|-------------|
| `-T` | Stream dataset to stdout (JSON Lines) |
| `-oneshot` | Single-batch mode |
| `-deepgul` | Deep GUL streaming |
| `-n, --limit <N>` | Limit output to N samples |
| `-random` | Randomize sample order |
| `-block <N>` | Block size (default: 64) |
| `-seed <N>` | RNG seed (0 = random) |
| `-config <path>` | Load config file |
| `-L <host/port>` | Stream to TCP (e.g. `127.0.0.1/1234`) |
| `validate [file]` | Validate a GUL spec file |
| `infer [file]` | Run inference on an expression file |

### Config file

```ini
seed = 42
block_size = 64
max_samples = 10000
random_order = true
```

### Output format (JSON Lines)

Each line is an independent JSON document:

```json
{
  "entity":             { "kind": "agent", "id": "user:42" },
  "predicate":          { "tag": "has_role", "args": ["editor"] },
  "context_confidence": 0.91,
  "decision":           "permit",
  "confidence":         0.83,
  "evidence":           ["role check passed", "context verified"]
}
```

Fields: `entity`, `predicate`, `context_confidence`, `decision` (`permit | deny | defer | abstain`), `confidence` ∈ [0, 1], `evidence`.

### Python bridge

`cli_bridge.py` wraps the binary for use from Python:

```python
from gulcli import generate_dataset, stream_dataset, cli_validate, cli_infer
from pathlib import Path
import json

# Write 1000 samples to a file
generate_dataset(1000, output_path=Path("data/train.jsonl"), seed=42)

# Stream lazily
for line in stream_dataset(n=500, random_order=True):
    record = json.loads(line)

# Validate / infer
ok = cli_validate(Path("policy.gul"))
result = cli_infer(Path("expr.gul"))
```

The executable is resolved in order: `GUL_EXE_PATH` env var → `gul_exe_path` argument → `cpp/build/Release/gul.exe` → PATH.

---

## Module Overview

| Module | Description |
|--------|-------------|
| `confidence.py` | `Confidence` value type + `ConfidenceOps` (union, intersection, sequential, parallel) |
| `decision.py` | `Decision` enum + `EvaluatedDecision` + `DecisionCombiner` |
| `jurisdiction.py` | `JurisdictionLevel`, `JurisdictionId`, `Jurisdiction`, `JType` |
| `inference.py` | `GULInferenceEngine` — all inference rules with audit trace |
| `policy.py` | `GULGovernanceDecision` + `GULGovernancePolicy` |
| `expr.py` | Policy expression DSL (`Entity`, `Predicate`, `PolicyExpr`) |
| `compiler.py` | Compiles `PolicyExpr` / `Predicate` to constraint lattice |
| `integration.py` | Legacy `geodesic_ai` adapters |
| `cli_bridge.py` | Python wrapper around `gul.exe` |

---

## Invariants

- Confidence values are always in `[0, 1]`; construction outside this range raises `ValueError`
- `DENY` dominates in AND combination
- `PERMIT` dominates in OR combination
- Jurisdiction checks produce `ABSTAIN`, never `DENY`
- Decision history is append-only; `reset_history()` is explicit
