# GUL — Governed Uncertainty Logic

**Deterministic policy reasoning for systems where “allow or deny” is not enough.**

GUL is an executable policy engine and formal decision framework for AI systems, authorization layers, workflow engines, and governed automation.

Instead of forcing every evaluation into a binary answer, GUL returns one of four explicit outcomes:

- `permit` — the action is authorized;
- `deny` — the action is blocked;
- `defer` — the available evidence is insufficient and the decision must escalate;
- `abstain` — the policy is outside its jurisdiction and has no authority to decide.

Every decision can carry bounded confidence, evidence, jurisdiction context, and an inference trace. This preserves distinctions that binary policy systems often push into application-specific error handling.

GUL v2.2.0 currently provides:

| Surface | Purpose |
|---|---|
| **Python package** | Reference type system, decision algebra, confidence operations, jurisdiction model, inference engine, policy API, and expression DSL |
| **Portable Python CLI** | Validate and evaluate canonical GUL JSON specifications with optional fact environments and traces |
| **Native C++17 CLI** | File-backed validation and inference plus high-throughput JSONL dataset streaming |
| **Python/native bridge** | Native executable discovery, dataset streaming helpers, and Python fallback for validation/inference when the native process cannot launch |
| **Schemas and golden fixtures** | Versioned validation/inference output contracts and cross-runtime regression evidence |

The core Python package requires Python 3.10 or later and has no mandatory runtime dependencies.

---

## Why GUL exists

Many consequential systems cannot honestly answer every question with only `true` or `false`.

A request may be:

- valid but insufficiently supported;
- outside the evaluating policy’s authority;
- supported by conflicting evidence;
- locally authorized but globally constrained;
- conditionally permitted at one confidence threshold and deferred at another.

Collapsing those states into a binary result destroys information precisely where governance needs it most. GUL makes uncertainty, scope, evidence, and escalation part of the decision model itself.

### Design emphasis

| Concern | GUL | Typical binary policy logic |
|---|---|---|
| Decision state | `permit`, `deny`, `defer`, `abstain` | Usually allow/deny |
| Uncertainty | First-class bounded confidence | Commonly handled outside the policy result |
| Out-of-scope evaluation | Explicit `abstain` | Often conflated with denial or missing rules |
| Escalation | Explicit `defer` | Usually application-defined |
| Scope | Hierarchical jurisdiction model | Commonly resource- or role-specific only |
| Evidence | Carried with the evaluated decision | Commonly logged separately |
| Composition | Defined logical and confidence operators | Frequently implementation-specific |
| Auditability | Structured inference trace and versioned output envelopes | Integration-dependent |
| ML support | Native governed-trace dataset generation | Not normally a core policy-engine concern |

GUL is not intended to replace every authorization language. It is most useful when a system must preserve uncertainty, jurisdiction, provenance, or escalation semantics rather than reduce them prematurely.

---

## 60-second start

Clone the repository and install the package in editable mode:

```bash
git clone https://github.com/torakagemusha-sudo/gulcli.git
cd gulcli
python -m pip install -e .
```

Validate an example policy specification:

```bash
python -m gulcli validate examples/specs/basic_infer.gul.json --format json
```

Run inference:

```bash
python -m gulcli infer examples/specs/basic_infer.gul.json --format json
```

The example combines two permitted decisions with confidence values `0.92` and `0.81`, then applies a `0.70` threshold. The stable result is:

```json
{
  "confidence": 0.81,
  "decision": "permit",
  "evidence": [
    "role check passed",
    "context verified"
  ],
  "input_hash": "1033291147243006058ccecc99f19630b18b8a9744a0d465baecb906ba20c363",
  "jurisdiction": null,
  "schema": "gul.inference.result/1",
  "trace": [],
  "version": "2.2.0"
}
```

The result is not just a boolean. It records the decision, confidence, evidence, normalized-input identity, schema version, and optional trace. Add `--trace` to emit the `AND` and `THRESHOLD` inference steps.

---

## Python API

```python
from gulcli import (
    Confidence,
    Decision,
    EvaluatedDecision,
    GULInferenceEngine,
    GULGovernancePolicy,
)

engine = GULInferenceEngine()

role_check = EvaluatedDecision(
    Decision.PERMIT,
    Confidence(0.92),
    evidence=["role check passed"],
)
context_check = EvaluatedDecision(
    Decision.PERMIT,
    Confidence(0.81),
    evidence=["context verified"],
)

result = engine.evaluate_and(role_check, context_check)

print(result.decision)          # Decision.PERMIT
print(result.confidence.value)  # 0.81
print(result.evidence)          # combined evidence
print(engine.get_trace_summary())
```

Threshold policy evaluation is also available directly:

```python
policy = GULGovernancePolicy(
    max_risk=0.40,
    min_coherence=0.50,
    min_confidence=0.65,
    policy_name="deployment_gate",
)

decision = policy.evaluate(
    risk_score=0.25,
    coherence=0.90,
    confidence=Confidence(0.82),
    context={"environment": "production"},
)

print(decision.decision)
print(decision.reason)
print(decision.evidence)
print(decision.to_dict())
```

---

## Core model

### Four-valued decisions

| Decision | Meaning | Typical next action |
|---|---|---|
| `PERMIT` | The action is authorized | Continue |
| `DENY` | The action is prohibited | Stop |
| `DEFER` | Evidence or confidence is insufficient | Escalate, gather evidence, or invoke a higher-authority policy |
| `ABSTAIN` | The policy has no jurisdiction over the request | Continue evaluation elsewhere |

Key semantics:

- `DENY` dominates conjunction.
- `PERMIT` dominates disjunction.
- `DEFER` preserves unresolved uncertainty.
- `ABSTAIN` acts as “no opinion” rather than a negative judgment.
- inversion swaps `permit` and `deny` while preserving `defer` and `abstain`.

### Confidence algebra

Confidence is an immutable value in `[0, 1]`.

| Operation | Formula | Interpretation |
|---|---|---|
| Union | `max(c1, c2)` | Either source is sufficient |
| Intersection | `min(c1, c2)` | Both are required; weakest evidence dominates |
| Sequential | `c1 × c2` | Dependent uncertainty compounds |
| Parallel | `c1 + c2 − c1·c2` | Independent evidence reinforces |

```python
from gulcli import Confidence, ConfidenceOps

c1 = Confidence(0.90)
c2 = Confidence(0.70)

ConfidenceOps.combine_union(c1, c2)         # Confidence(0.9000)
ConfidenceOps.combine_intersection(c1, c2)  # Confidence(0.7000)
ConfidenceOps.combine_sequential(c1, c2)    # Confidence(0.6300)
ConfidenceOps.combine_parallel(c1, c2)      # Confidence(0.9700)
```

### Jurisdiction

Jurisdictions form a partial order. A policy may evaluate only requests inside its declared scope.

```text
GLOBAL
└── REGIONAL
    └── ORGANIZATIONAL
        └── DEPARTMENTAL
            └── PERSONAL
```

A request outside scope returns `abstain`, not `deny`. This separates lack of authority from an authoritative prohibition.

Supported jurisdiction constraint forms include:

- unrestricted;
- local;
- union;
- intersection;
- delegation.

---

## Runtime architecture

```text
GUL JSON specification or Python DSL
                +
        optional fact environment
                │
                ▼
      validation and normalization
      - supported-tag validation
      - deterministic normalized form
      - input hash
                │
                ▼
          inference engine
      - decision composition
      - confidence propagation
      - jurisdiction checks
      - threshold and override rules
      - evidence accumulation
                │
                ▼
       versioned result envelope
      decision + confidence + evidence
      jurisdiction + trace + input hash
```

The native dataset path is separate but uses the same decision vocabulary:

```text
scenario/configuration/spec
            │
            ▼
      native C++ generator
            │
            ▼
 JSON Lines governed trace records
            │
   stdout or TCP transport
            ▼
 training, evaluation, diagnostics
```

Standard output can be redirected to a file for offline datasets.

---

## Executable policy specifications

Runtime files are JSON documents containing either an expression node or an envelope with an `expr` field.

```json
{
  "expr": {
    "tag": "threshold",
    "threshold": 0.7,
    "p": {
      "tag": "and_",
      "p1": {
        "tag": "decision",
        "decision": "permit",
        "confidence": 0.92,
        "evidence": ["role check passed"]
      },
      "p2": {
        "tag": "decision",
        "decision": "permit",
        "confidence": 0.81,
        "evidence": ["context verified"]
      }
    }
  }
}
```

The current runtime supports:

- `decision`
- `atom`
- `and_`, `or_`, `not_`, `implies`
- `with_confidence`, `threshold`
- `jurisdiction`, `override`
- `sequential`, `parallel`
- `always`, `eventually`, `until`

`atom` predicates can evaluate roles, attributes, membership, context, time, and custom facts supplied through a fact environment.

```bash
python -m gulcli infer examples/specs/atom_role.gul.json \
  --facts examples/facts/basic_facts.json \
  --format json \
  --trace
```

Missing fact bindings defer rather than fabricate certainty. Explicit mismatches deny.

---

## Native C++ CLI

The C++17 executable provides native validation, inference, and high-throughput dataset streaming.

### Build

```bash
cd cpp
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

Expected output:

- Windows: `build/Release/gul.exe`
- Unix-like systems: `build/gul`

### Validate and infer

```bash
gul validate examples/specs/basic_infer.gul.json --format json
gul infer examples/specs/basic_infer.gul.json --format json --trace
gul infer examples/specs/atom_role.gul.json \
  --facts examples/facts/basic_facts.json \
  --format json
```

### Generate governed training data

```bash
# Bounded JSONL stream to stdout
gul -oneshot -T -n 1000

# Reproducible randomized stream
gul -T -n 5000 -random -block 128 -seed 42

# Deep GUL mode
gul -deepgul -T -n 500

# Scenario-driven generation
gul -oneshot -T -n 100 --scenario balanced --seed 42
gul -oneshot -T -n 50 --scenario adversarial \
  --spec examples/specs/basic_infer.gul.json \
  --stats

# TCP streaming
gul -deepgul -L 127.0.0.1/1234 -n 500
```

Dataset streaming is unbounded unless `-n <N>` or a configuration `max_samples` value is supplied.

Each output line is an independent JSON document containing a decision, confidence, evidence, entity/predicate context, and optional provenance extensions.

---

## Capability boundaries

The repository intentionally distinguishes implemented behavior from architectural direction.

| Capability | Current state |
|---|---|
| Python decision algebra, confidence operations, jurisdiction model, inference, and policy API | Implemented |
| Portable Python JSON validation and inference | Implemented |
| Fact-backed `atom` evaluation | Implemented |
| Versioned validation and inference result schemas | Implemented |
| Native C++ validation and inference | Implemented when the binary is built |
| Native JSONL dataset streaming | Implemented when the binary is built |
| Python bridge fallback for `validate` and `infer` | Implemented when the native executable cannot launch |
| Python fallback for native dataset generation | Not currently implemented |
| Temporal operators | Structural/approximate semantics in the current runtime |
| Full external proof-assistant equivalence | Not claimed by this repository |
| TFIR and Helmsdeep runtime integration | Ecosystem direction; not a dependency of the standalone package |

For exact operational constraints, use the [runtime usage guide](docs/runtime_usage.md).

---

## ToraFirma ecosystem position

GUL is independently usable. Within the broader ToraFirma architecture, its intended role is policy evaluation rather than ownership of the canonical object model.

```text
TFIR action / policy / state objects
                │
                ▼
       GUL evaluation semantics
 decision + confidence + evidence + trace
                │
                ▼
 TFIR event / receipt representation
                │
                ▼
  Helmsdeep governed runtime admission
```

TFIR remains the canonical semantic object model and ABI. GUL supplies executable decision semantics that can be projected into governed runtime operations. Helmsdeep is the reference consumer direction.

This relationship is architectural context; the core `gulcli` package remains local-first and has no mandatory TFIR or Helmsdeep dependency.

---

## Package map

| Path/module | Responsibility |
|---|---|
| `decision.py` | Four-valued decisions, evaluated decisions, combination and inversion |
| `confidence.py` | Bounded confidence type and composition operations |
| `jurisdiction.py` | Hierarchical scopes, delegation, validity, and constraints |
| `inference.py` | Logical and confidence-aware inference with traces |
| `policy.py` | Threshold-driven governance policy evaluation and history |
| `expr.py` | Immutable JSON-serializable policy expression DSL |
| `facts.py` | Fact-environment bindings for runtime predicates |
| `runtime_io.py` | JSON validation, normalization, hashing, inference, and CLI entry logic |
| `cli_bridge.py` | Native process discovery and Python/native boundary |
| `schemas/` | Versioned validation and inference output contracts |
| `examples/` | Executable specifications, fact environments, and usage examples |
| `cpp/` | Native C++17 implementation and dataset streamer |
| `tests/` | Unit, schema, golden, dataset, and native parity tests |

---

## Development and verification

Install the package and run the full Python test suite:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

Smoke-test the executable Python boundary:

```bash
python -m gulcli validate examples/specs/basic_infer.gul.json --format json
python -m gulcli infer examples/specs/basic_infer.gul.json --format json --trace
```

The GitHub runtime workflow exercises Python 3.10, 3.11, 3.12, and 3.13.

Formal invariants enforced by the implementation include:

- confidence is always bounded to `[0, 1]`;
- conjunction is deny-dominant;
- disjunction is permit-dominant;
- `abstain` is the no-opinion identity;
- out-of-jurisdiction evaluation returns `abstain`;
- low-confidence threshold evaluation returns `defer`;
- inversion preserves `defer` and `abstain`;
- sequential confidence cannot exceed either input confidence;
- policy decision history is append-only until explicitly reset.

---

## Documentation

- [Runtime usage and capability matrix](docs/runtime_usage.md)
- [v2.2.0 release specification](docs/release_notes/RELEASE_SPEC_v2_2_0.md)
- [Project update records](docs/PROJECT_UPDATES.md)
- [Curriculum expansion implementation specification](docs/superpowers/specs/2026-07-10-gulcli-curriculum-expansion.md)
- [Previous full v2.2 README reference](https://github.com/torakagemusha-sudo/gulcli/blob/2c2ed05e11a1a7f3b23f1ce55cdf2068f3f50904/README.md)

---

## Project status

GUL v2.2.0 is a beta-stage formal-policy and governed-data toolkit. The primary interfaces are executable and tested, but users should treat runtime boundaries and documented capability constraints as authoritative rather than inferring unimplemented integrations from the broader architecture.

Contributions should preserve:

- deterministic and inspectable semantics;
- explicit uncertainty rather than fabricated certainty;
- fail-closed validation at command boundaries;
- stable result schemas and golden fixtures;
- truthful implementation-status claims;
- compatibility between the Python reference runtime and native surfaces.

---

## License

MIT License. See [LICENSE](LICENSE).
