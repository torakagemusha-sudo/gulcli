# GUL — Governed Uncertainty Logic v2.2

GUL is a formal logic system for policy evaluation under uncertainty. It extends classical binary allow/deny into a **4-valued decision algebra** — `permit`, `deny`, `defer`, `abstain` — with bounded confidence tracking, hierarchical jurisdiction scoping, and a full inference audit trail.

The current repository ships as:

- **Python package** — pure-Python implementation of the complete GUL type system, inference engine, policy evaluation, and DSL compiler
- **C++ CLI** (`gul.exe`) — high-performance dataset streamer that generates ML training data sampled from the GUL formal system
- **Python bridge** (`cli_bridge.py`) — subprocess wrapper around the CLI for use within Python workflows

---

## Table of Contents

- [Core Concepts](#core-concepts)
  - [4-valued decisions](#4-valued-decisions)
  - [Confidence lattice](#confidence-lattice)
  - [Jurisdiction](#jurisdiction)
- [Python Package](#python-package)
  - [Installation](#installation)
  - [Quick start](#quick-start)
  - [Executable Python runtime](#executable-python-runtime)
  - [Inference engine](#inference-engine)
  - [Policy evaluation](#policy-evaluation)
  - [Policy expression DSL](#policy-expression-dsl)
  - [Jurisdiction system](#jurisdiction-system)
  - [Constraint compiler](#constraint-compiler)
  - [geodesic_ai adapters](#geodesic_ai-adapters)
- [C++ CLI](#c-cli)
  - [Build](#build)
  - [Dataset streaming](#dataset-streaming)
  - [CLI options](#cli-options)
  - [Config file](#config-file)
  - [Output format](#output-format)
  - [Python bridge](#python-bridge)
- [Module reference](#module-reference)
- [Formal invariants](#formal-invariants)

---

## Core Concepts

### 4-valued decisions

GUL replaces the binary allow/deny model with four distinct outcomes:

| Decision | Wire value | Meaning |
|----------|-----------|---------|
| `PERMIT` | `"permit"` | Action is authorized |
| `DENY` | `"deny"` | Action is blocked |
| `DEFER` | `"defer"` | Confidence is too low; escalate to a higher-authority policy |
| `ABSTAIN` | `"abstain"` | This policy has no opinion; outside its jurisdiction scope |

`PERMIT` and `DENY` are **terminal** — they end evaluation. `DEFER` propagates uncertainty upward. `ABSTAIN` is the identity element in combination: `ABSTAIN + x → x`.

Combination priority: **DENY > PERMIT > DEFER > ABSTAIN**

```python
from gulcli import Decision, DecisionCombiner

DecisionCombiner.combine(Decision.PERMIT, Decision.DENY)    # → DENY
DecisionCombiner.combine(Decision.PERMIT, Decision.PERMIT)  # → PERMIT
DecisionCombiner.combine(Decision.PERMIT, Decision.DEFER)   # → DEFER
DecisionCombiner.combine(Decision.ABSTAIN, Decision.PERMIT) # → PERMIT

DecisionCombiner.invert(Decision.PERMIT)  # → DENY
DecisionCombiner.invert(Decision.DEFER)   # → DEFER (unchanged)

# Override semantics: ABSTAIN means "no override, keep base"
DecisionCombiner.override(Decision.DEFER, Decision.PERMIT)  # → PERMIT
DecisionCombiner.override(Decision.PERMIT, Decision.ABSTAIN) # → PERMIT
```

### Confidence lattice

Confidence is a bounded value in **[0, 1]** representing certainty in a decision. It is an immutable value type; construction outside [0, 1] raises `ValueError`.

Four algebraic combination operations cover all common evidence-composition patterns:

| Operation | Formula | Semantics |
|-----------|---------|-----------|
| **Union** | `max(c1, c2)` | OR — either source is sufficient |
| **Intersection** | `min(c1, c2)` | AND — weakest-link; both required |
| **Sequential** | `c1 × c2` | Dependent chain; uncertainty compounds |
| **Parallel** | `c1 + c2 − c1·c2` | Independent sources reinforce each other |

```python
from gulcli import Confidence, ConfidenceOps

c1 = Confidence(0.9)
c2 = Confidence(0.7)

ConfidenceOps.combine_union(c1, c2)        # Confidence(0.9000)
ConfidenceOps.combine_intersection(c1, c2) # Confidence(0.7000)
ConfidenceOps.combine_sequential(c1, c2)   # Confidence(0.6300)
ConfidenceOps.combine_parallel(c1, c2)     # Confidence(0.9700)

# Aggregation over a list
ConfidenceOps.aggregate([c1, c2], method="min")      # Confidence(0.7000)
ConfidenceOps.aggregate([c1, c2], method="product")  # Confidence(0.6300)
ConfidenceOps.aggregate([c1, c2], method="parallel") # Confidence(0.9700)
ConfidenceOps.aggregate([c1, c2], method="average")  # Confidence(0.8000)

# Weighted average
ConfidenceOps.weighted_average([c1, c2], weights=[3.0, 1.0])  # Confidence(0.8500)

Confidence.zero()  # 0.0 — bottom of lattice
Confidence.one()   # 1.0 — top of lattice
Confidence.from_probability(1.3)  # clamps → Confidence(1.0)
Confidence(0.8).complement()      # Confidence(0.2)
```

### Jurisdiction

Jurisdictions form a **partial order** under the sub-jurisdiction relation (⊆ᵥ). A policy declares its jurisdiction; any request that falls outside produces `ABSTAIN` rather than `DENY` — cleanly separating "out of scope" from "actively blocked".

Five levels from broadest to narrowest:

```
GLOBAL > REGIONAL > ORGANIZATIONAL > DEPARTMENTAL > PERSONAL
```

Five jurisdiction types for constraint composition:

| JType | Meaning |
|-------|---------|
| `UNRESTRICTED` | No jurisdiction constraint |
| `LOCAL` | Bound to a specific jurisdiction |
| `UNION` | Any listed jurisdiction is sufficient |
| `INTERSECTION` | All listed jurisdictions must agree |
| `DELEGATION` | Authority delegated from another jurisdiction |

---

## Python Package

### Installation

```bash
pip install -e .
```

Requires Python 3.10+. The package has **no mandatory dependencies**. The `geodesic_ai` integration and `torch`-backed compiler are lazy-imported only when their respective functions are called, and fail with a clear `RuntimeError` if that package is not installed.

### Quick start

```python
from gulcli import (
    Confidence, Decision, EvaluatedDecision,
    GULInferenceEngine, GULGovernancePolicy,
)

# --- Direct inference ---
engine = GULInferenceEngine()

d1 = EvaluatedDecision(Decision.PERMIT, Confidence(0.9), evidence=["role check passed"])
d2 = EvaluatedDecision(Decision.PERMIT, Confidence(0.7), evidence=["context verified"])

result = engine.evaluate_and(d1, d2)
print(result.decision)          # Decision.PERMIT
print(result.confidence.value)  # 0.7  (intersection = min)
print(result.evidence)          # ['role check passed', 'context verified']

# --- Policy evaluation ---
policy = GULGovernancePolicy(
    max_risk=0.5,
    min_coherence=0.3,
    min_confidence=0.6,
    policy_name="my_policy",
)

decision = policy.evaluate(risk_score=0.2, coherence=0.9)
print(decision.ok)              # True  (PERMIT with conf >= 0.5)
print(decision.decision)        # Decision.PERMIT
print(decision.evidence)        # ['all thresholds satisfied']
print(decision.to_dict())       # full serializable record
```

### Executable Python runtime

JSON spec files under `examples/specs/` validate and run inference without the C++ binary. Use the package entrypoint:

```bash
python3 -m gulcli validate examples/specs/basic_infer.gul.json --format json
python3 -m gulcli infer examples/specs/basic_infer.gul.json --format json --trace
```

The same logic is available from Python via `validate_file`, `infer_file`, `validate_spec_data`, and `evaluate_expr_data` (see the module reference). When the native `gul` CLI is installed, `cli_validate` / `cli_infer` try it first and fall back to this runtime if the executable cannot be started.

For source-verified command boundaries, bridge fallback behavior, and dataset
generation caveats, see `docs/runtime_usage.md`.

### Inference engine

`GULInferenceEngine` implements the package's GUL inference rules. Every call appends an `InferenceTrace` entry; the full trace is available via `get_trace_summary()`.

```python
engine = GULInferenceEngine()

# Binary combiners
engine.evaluate_and(d1, d2)       # DENY if either denies; PERMIT if both permit; else DEFER
engine.evaluate_or(d1, d2)        # PERMIT if either permits; DENY if both deny; else DEFER
engine.evaluate_sequential(d1, d2) # Dependent chain; confidence = c1 × c2
engine.evaluate_parallel(d1, d2)   # Independent sources; confidence = c1 + c2 − c1·c2

# Unary
engine.evaluate_not(d)             # PERMIT ↔ DENY; DEFER/ABSTAIN unchanged; confidence preserved

# Branching
engine.evaluate_conditional(condition, then_branch, else_branch)
# If condition=PERMIT → then with sequential confidence
# If condition=DENY   → else with sequential confidence
# If condition=DEFER  → DEFER (condition uncertain)

# Threshold gate
engine.evaluate_threshold(d, threshold=0.7)
# Returns d unchanged if d.confidence >= threshold; else returns DEFER

# Jurisdiction scope check
engine.evaluate_jurisdiction_check(d, request_jurisdiction, policy_jurisdiction)
# Returns d if request ⊆ᵥ policy; else ABSTAIN with confidence=1.0

# Fold over a list
engine.evaluate_all([d1, d2, d3], combiner="and")       # left-fold with AND
engine.evaluate_all([d1, d2, d3], combiner="or")        # left-fold with OR
engine.evaluate_all([d1, d2, d3], combiner="sequential")
engine.evaluate_all([d1, d2, d3], combiner="parallel")

# Audit trace
engine.get_trace_summary()  # list of dicts: rule, inputs, output, metadata
engine.clear_trace()
engine.enable_trace(False)  # disable tracing for hot paths
```

### Policy evaluation

`GULGovernancePolicy` applies threshold checks in order — jurisdiction scope, risk ceiling, coherence floor, confidence floor — and returns a `GULGovernanceDecision` with a full audit record.

```python
from gulcli import GULGovernancePolicy, Confidence, EvaluatedDecision, Decision

policy = GULGovernancePolicy(
    max_risk=0.4,        # DENY if risk_score > 0.4
    min_coherence=0.5,   # DENY if coherence < 0.5
    min_confidence=0.65, # DEFER if confidence < 0.65
    policy_name="risk_gate",
)

# From raw metrics
decision = policy.evaluate(risk_score=0.3, coherence=0.8)
decision = policy.evaluate(risk_score=0.3, coherence=0.8, confidence=Confidence(0.9))
decision = policy.evaluate(risk_score=0.3, coherence=0.8, context={"user": "alice"})

# From a stats dict
decision = policy.evaluate_stats({"risk": 0.3, "coherence": 0.8, "confidence": 0.9})

# From pre-evaluated sub-decisions (uses inference engine internally)
sub_decisions = [
    EvaluatedDecision(Decision.PERMIT, Confidence(0.9)),
    EvaluatedDecision(Decision.PERMIT, Confidence(0.8)),
]
decision = policy.evaluate_with_inference(sub_decisions, combiner="and")

# Decision record
decision.decision        # Decision.PERMIT / DENY / DEFER / ABSTAIN
decision.confidence      # Confidence(...)
decision.ok              # True iff PERMIT and confidence >= 0.5 (legacy compat)
decision.reason          # human-readable string
decision.evidence        # list of strings
decision.risk_score      # float
decision.coherence_score # float
decision.timestamp       # ISO timestamp
decision.to_dict()       # fully serializable

# History and audit
policy.get_decision_history()     # list of all decisions
policy.get_decision_history(n=10) # last n decisions
policy.get_audit_summary()        # counts by decision type + averages
policy.reset_history()
```

**Evaluation order:**

1. **Jurisdiction check** — if `context["jurisdiction"]` is outside `policy.jurisdiction`, return `ABSTAIN`
2. **Risk ceiling** — if `risk_score > max_risk`, return `DENY`
3. **Coherence floor** — if `coherence < min_coherence`, return `DENY`
4. **Confidence floor** — if `confidence < min_confidence`, return `DEFER`
5. All checks pass → return `PERMIT`

Audit events are emitted to `geodesic_ai.data.event_bus.EventBus` if available; otherwise silently skipped.

### Policy expression DSL

The DSL provides `Predicate` and `PolicyExpr` types. All expressions are immutable and JSON-serializable via `to_dict()` / `from_dict()`.

#### Entities

```python
from gulcli import Entity

user    = Entity("agent",    "user:alice")
doc     = Entity("resource", "doc:report-q4")
ctx     = Entity("context",  "workspace:prod")
policy  = Entity("policy",   "gdpr-v2")
```

Kinds: `"agent"`, `"resource"`, `"context"`, `"policy"`.

#### Predicates

```python
from gulcli import belongs_to, has_role, has_attribute, in_context, time_before, time_after, custom

belongs_to(user, doc)                        # user owns/belongs to doc
has_role(user, "editor")                     # user has role "editor"
has_attribute(doc, "classification", "confidential")  # doc.classification == "confidential"
in_context(user, ctx)                        # user is operating in ctx
time_before(1_700_000_000)                   # current time < unix timestamp
time_after(1_600_000_000)                    # current time > unix timestamp
custom("my_check", user, doc)               # extensible custom predicate
```

#### Policy expressions

```python
from gulcli import atom, and_, or_, not_, implies, with_confidence, always, eventually, until

# Propositional
expr = and_(
    atom(has_role(user, "editor")),
    atom(has_attribute(doc, "status", "draft")),
)

expr = or_(
    atom(has_role(user, "admin")),
    atom(has_role(user, "owner")),
)

expr = not_(atom(has_attribute(doc, "classification", "top-secret")))

expr = implies(
    atom(has_role(user, "contractor")),
    atom(in_context(user, ctx)),
)

# Confidence annotation
expr = with_confidence(atom(has_role(user, "reviewer")), 0.85)

# Temporal (structural; evaluated by inference engine)
expr = always(atom(has_attribute(doc, "encrypted", "true")))
expr = eventually(atom(has_role(user, "approver")))
expr = until(atom(has_role(user, "pending")), atom(has_role(user, "active")))

# Serialization round-trip
d = expr.to_dict()
expr2 = PolicyExpr.from_dict(d)
```

### Jurisdiction system

```python
from gulcli import (
    JurisdictionId, JurisdictionLevel, Jurisdiction, JType,
    JurisdictionConstraint, create_jurisdiction_hierarchy,
)

# Build a hierarchy (names listed root-first)
jurisdictions = create_jurisdiction_hierarchy(
    ["global", "eu", "eu.ireland"],
    authority="platform-team",
)
global_j, eu_j, ireland_j = jurisdictions

# Sub-jurisdiction checks
ireland_j.id.is_sub_jurisdiction(global_j.id)   # True
ireland_j.id.is_sub_jurisdiction(eu_j.id)       # True
global_j.id.is_sub_jurisdiction(ireland_j.id)   # False

ireland_j.id.fully_qualified_name()  # "global.eu.eu.ireland"
ireland_j.id.depth()                 # 2
ireland_j.id.root()                  # JurisdictionId(global)

# Validity window
from datetime import datetime
j = Jurisdiction(
    id=JurisdictionId("temp"),
    level=JurisdictionLevel.LOCAL,
    authority="ops",
    valid_since=datetime(2024, 1, 1),
    valid_until=datetime(2026, 12, 31),
)
j.is_valid()  # True/False based on current time

# Delegation
j.can_delegate_to("sub-team")  # checks j.delegates list

# Constraint types
JurisdictionConstraint.unrestricted()              # always matches
JurisdictionConstraint.local(ireland_j.id)         # must be ⊆ ireland
JurisdictionConstraint.union(eu_j.id, ireland_j.id) # either suffices
JurisdictionConstraint.intersection(eu_j.id, ireland_j.id)  # must be in both
```

### Constraint compiler

The compiler translates `PolicyExpr` trees into `geodesic_ai` `Constraint` objects for use in the constraint lattice. Requires `geodesic_ai` and `torch`.

```python
from gulcli import (
    default_registry,
    compile_predicate_to_constraint,
    compile_policy_expr_to_constraints,
    build_lattice_from_gul_spec,
    custom, atom,
)

# Default registry provides: "box", "box_bounds", "sphere", "upper_bound", "lower_bound"
registry = default_registry()

# Compile a single custom predicate
pred = custom("box", ...)
constraint = compile_predicate_to_constraint(pred, name="bounds", weight=2.0, confidence=0.9)

# Compile a full expression tree
expr = and_(
    with_confidence(atom(custom("box")), 0.9),
    atom(custom("sphere")),
)
constraints = compile_policy_expr_to_constraints(expr, name_prefix="my_policy", weight=1.0)

# Load from a checkpoint-style dict
spec = {
    "gul_constraints": [
        {"name": "bounds", "weight": 1.5, "confidence": 0.85,
         "expr": {"tag": "atom", "pred": {"tag": "custom", "name": "box"}}},
    ]
}
lattice = build_lattice_from_gul_spec(spec)
```

Compilation rules for expression tags:

| Tag | Behaviour |
|-----|-----------|
| `atom(custom(name, ...))` | Looked up in registry; skipped if not found |
| `and_`, `or_`, `implies` | Both children compiled; results concatenated |
| `with_confidence` | Child compiled; confidence applied to each result |
| `not_` | Child compiled (structural; no negation of constraint) |
| `always`, `eventually`, `until` | Child compiled (temporal structure preserved) |

### geodesic_ai adapters

`integration.py` provides the bridge between GUL types and the `geodesic_ai` ecosystem. All imports are lazy — no `ImportError` at module load time.

```python
from gulcli import (
    GULAdapter,
    legacy_decision_to_gul,
    legacy_policy_to_gul,
    constraint_with_confidence,
    lattice_with_uniform_confidence,
    evaluate_constraint_with_gul,
    evaluate_lattice_with_gul,
)

# Wrap legacy types
gul_decision = legacy_decision_to_gul(old_decision, confidence=0.85)
gul_policy   = legacy_policy_to_gul(old_policy, min_confidence=0.6)

# Add GUL confidence to a constraint
new_constraint = constraint_with_confidence(constraint, confidence=0.9, jurisdiction=j.id)

# Apply uniform confidence to all constraints in a lattice
new_lattice = lattice_with_uniform_confidence(lattice, confidence=0.8)

# Evaluate with GUL semantics (returns EvaluatedDecision)
result = evaluate_constraint_with_gul(constraint, x_tensor, min_confidence=0.5)
result = evaluate_lattice_with_gul(lattice, x_tensor, min_confidence=0.5, combiner="and")

# Central adapter object
adapter = GULAdapter(min_confidence=0.6, default_jurisdiction=eu_j)
adapter.wrap_policy(old_policy)
adapter.wrap_decision(old_decision, confidence=0.8)
adapter.wrap_constraint(constraint, confidence=0.9)
adapter.evaluate_constraint(constraint, x_tensor)
adapter.evaluate_lattice(lattice, x_tensor, combiner="or")
```

---

## C++ CLI

The C++ binary provides native GUL data structures and streams ML training
samples as JSON Lines. It can write to stdout or push directly to a TCP socket.

Current boundary: native dataset streaming is implemented, but native
`gul validate` and `gul infer` are placeholders that print status text and
return success. Use `python3 -m gulcli validate` and `python3 -m gulcli infer`
for file-backed validation and inference.

### Build

```bash
cd cpp
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

Output: `build/Release/gul.exe` (Windows) or `build/gul` (Unix).

**On Linux/macOS** (no native build): run through Wine:

```bash
WINEDEBUG=-all DISPLAY= wine ./gul.exe --help
```

### Dataset streaming

```bash
# Basic: stream to stdout with an explicit limit
gul -oneshot -T -n 64
gul -T -n 1000
gul -config sample.conf -T

# Randomized, custom block size, fixed seed
gul -T -n 5000 -random -block 128 -seed 42

# Deep GUL streaming to stdout
gul -deepgul -T -n 500

# Stream to a TCP consumer (start listener first)
nc -l 1234                              # listener (Linux/macOS)
gul -deepgul -L 127.0.0.1/1234
gul -oneshot -T -L 127.0.0.1/1234 -n 500

# Native validate/infer placeholders; use python3 -m gulcli for real execution
gul validate policy.gul
gul infer expr.gul
```

### CLI options

| Option | Description |
|--------|-------------|
| `-T` | Stream dataset to stdout in JSON Lines format |
| `-oneshot` | Select single-command stdout streaming; pair with `-n` or `max_samples` to exit |
| `-deepgul` | Enable deep GUL streaming mode |
| `-n <N>`, `--limit <N>` | Limit output to N samples |
| `-random`, `--random` | Randomize sample order |
| `-block <N>`, `--block <N>` | Block size for streaming (default: 64) |
| `-seed <N>`, `--seed <N>` | RNG seed; 0 means random |
| `-config <path>` | Load config file (key=value or key: value format) |
| `-L <host/port>` | Stream to TCP endpoint, e.g. `127.0.0.1/1234` or `127.0.0.1:1234` |
| `validate [file]` | Native placeholder; use `python3 -m gulcli validate` for file-backed validation |
| `infer [file]` | Native placeholder; use `python3 -m gulcli infer` for file-backed inference |
| `-h`, `--help` | Print usage |
| `-v`, `--version` | Print version |

### Config file

Plain text, one key per line. Both `=` and `:` separators are accepted.

```ini
seed = 42
block_size = 64
max_samples = 10000
random_order = true
```

When neither `-n <N>` nor a config `max_samples` value is provided, native
dataset streaming is unbounded.

### Output format

Each line of output is a self-contained JSON object (JSON Lines / NDJSON):

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

| Field | Type | Description |
|-------|------|-------------|
| `entity` | object | `kind` ∈ `{agent, resource, context, policy}`; `id` string |
| `predicate` | object | `tag` string; `args` array |
| `context_confidence` | float [0,1] | Confidence of the evaluation context |
| `decision` | string | `permit` \| `deny` \| `defer` \| `abstain` |
| `confidence` | float [0,1] | Confidence in the decision |
| `evidence` | array of strings | Reasoning chain |

Treat each line as an independent JSON document. Confidence values are guaranteed to be in [0, 1].

### Python bridge

`cli_bridge.py` wraps the binary for use from Python. The executable is resolved in order: `gul_exe_path` argument → `GUL_EXE_PATH` env var → package-local `cpp/build/` artifacts → `gul` on PATH.

```python
from gulcli import generate_dataset, stream_dataset, cli_validate, cli_infer, find_gul_exe
from pathlib import Path
import json

# Resolve the binary path
exe = find_gul_exe()                          # auto-discover
exe = find_gul_exe("/custom/path/gul.exe")    # explicit override

# Write N samples to a JSONL file (blocks until complete)
out = generate_dataset(
    n=10_000,
    output_path=Path("data/train.jsonl"),
    config_path=Path("cpp/sample.conf"),
    random_order=True,
    block_size=128,
    seed=42,
)

# Lazy streaming generator (yields one decoded line at a time)
for line in stream_dataset(n=500, random_order=True):
    record = json.loads(line)
    print(record["decision"], record["confidence"])

# Validate a spec file
ok = cli_validate(Path("policy.gul"))   # returns True/False

# Run inference and inspect result
result = cli_infer(Path("expr.gul"))
print(result.returncode, result.stdout, result.stderr)
```

---

## Module reference

| Module | Exports | Description |
|--------|---------|-------------|
| `confidence.py` | `Confidence`, `ConfidenceOps` | Bounded [0,1] confidence value type; union, intersection, sequential, parallel, weighted average, and aggregate operations |
| `decision.py` | `Decision`, `EvaluatedDecision`, `DecisionCombiner` | 4-valued decision enum; decision + confidence + evidence record; combine, override, invert combiners |
| `jurisdiction.py` | `JurisdictionLevel`, `JurisdictionId`, `Jurisdiction`, `JType`, `JurisdictionConstraint` | Hierarchical authority scopes; sub-jurisdiction partial order; validity windows; delegation; constraint types |
| `inference.py` | `GULInferenceEngine`, `InferenceTrace` | All formal inference rules with full audit trace; AND, OR, NOT, sequential, parallel, conditional, threshold, jurisdiction check |
| `policy.py` | `GULGovernanceDecision`, `GULGovernancePolicy` | Threshold-based policy evaluation; decision history; audit summary; `geodesic_ai` event bus integration |
| `expr.py` | `Entity`, `Predicate`, `PolicyExpr`, DSL constructors | JSON-serializable AST for policy expressions |
| `compiler.py` | `default_registry`, `compile_predicate_to_constraint`, `compile_policy_expr_to_constraints`, `build_lattice_from_gul_spec` | Compiles `PolicyExpr` → `geodesic_ai` `Constraint` objects; checkpoint loading |
| `integration.py` | `GULAdapter`, `legacy_decision_to_gul`, `legacy_policy_to_gul`, `constraint_with_confidence`, `lattice_with_uniform_confidence`, `evaluate_constraint_with_gul`, `evaluate_lattice_with_gul`, `create_jurisdiction_hierarchy` | Full bridge between GUL types and `geodesic_ai` constraint/policy ecosystem |
| `runtime_io.py` | `validate_spec_data`, `evaluate_expr_data`, `validate_file`, `infer_file` | JSON spec validation and inference; powers `python -m gulcli` |
| `cli_bridge.py` | `find_gul_exe`, `generate_dataset`, `stream_dataset`, `cli_validate`, `cli_infer` | Subprocess wrapper around `gul`; validate/infer fall back to `runtime_io` when the CLI is unavailable |

---

## Formal invariants

These invariants hold across the entire system and are enforced at construction or combination time:

- **Confidence bounds**: `Confidence(v)` raises `ValueError` if `v ∉ [0, 1]`. All combination operations preserve this bound.
- **DENY dominance**: In AND combination, `DENY` dominates any other decision.
- **PERMIT dominance**: In OR combination, `PERMIT` dominates any other decision.
- **ABSTAIN identity**: `ABSTAIN` combined with any decision `x` yields `x`.
- **Jurisdiction scope → ABSTAIN**: A request outside a policy's jurisdiction always produces `ABSTAIN`, never `DENY`.
- **DEFER on low confidence**: `evaluate_threshold` converts any decision below the threshold to `DEFER`, never to `DENY`.
- **Inversion**: `NOT(PERMIT) = DENY`, `NOT(DENY) = PERMIT`, `NOT(DEFER) = DEFER`, `NOT(ABSTAIN) = ABSTAIN`.
- **Decision history is append-only**: `reset_history()` must be called explicitly to clear it.
- **Sequential confidence is monotonically non-increasing**: `c1 × c2 ≤ min(c1, c2)` for all `c1, c2 ∈ [0,1]`.
