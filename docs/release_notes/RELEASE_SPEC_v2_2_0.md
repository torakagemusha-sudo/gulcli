# GUL v2.2.0 Release Specification

Status: Draft for execution  
Repository: `torakagemusha-sudo/gulcli`  
Target version: `2.2.0`

---

## 1. Release thesis

`v2.2.0` should convert GUL from a coherent logic kernel and dataset streamer into an executable governed-logic toolchain with a truthful public command surface.

The release is complete only when the public claims and the actual shipped capability coincide.

In particular:

- `validate` must perform real file-backed validation
- `infer` must perform real file-backed inference
- all machine-readable outputs must conform to explicit versioned schemas
- dataset generation must derive from declared GUL structures and scenario templates rather than a toy canned pool
- deterministic tests must gate the release

---

## 2. Why this release exists

The repository already presents GUL as:

- a Python package
- a C++ CLI
- a Python bridge
- a formal logic system for governed decision-making under uncertainty

The next release should therefore emphasize executable closure, not conceptual expansion.

This release is not about adding breadth. It is about making the public surface mechanically true.

---

## 3. Release objectives

### O1. Command-surface closure
Every documented CLI command must do real work.

### O2. Contract closure
Python, C++, and the bridge must exchange a canonical, versioned JSON IR.

### O3. Generation closure
Streaming output must be generated from declared GUL scenario families and source specifications.

### O4. Proof closure
Tests, golden outputs, and schema validation must act as release gates.

### O5. Documentation closure
README, examples, and release notes must reflect only what is actually shipped.

---

## 4. Scope

### In scope for `2.2.0`

- real `validate`
- real `infer`
- canonical JSON schema registry
- deterministic, spec-driven corpus generation
- unit and golden tests
- packaging and release hygiene
- end-to-end examples

### Explicitly out of scope

- full theorem proving pipeline
- full Lean artifact execution chain
- advanced distributed governance runtime
- rich standalone language frontend beyond minimum viable input
- UI / web console work

---

## 5. Work packages

### WP-01 — Real `validate`

#### Goal
Replace placeholder validation behavior with real structural and semantic validation over canonical input files.

#### Deliverables
- input acceptance for `*.gul.json`
- normalized IR emission
- structural validation
- semantic validation
- machine-readable error reporting

#### CLI shape
```bash
gul validate spec.gul.json
gul validate spec.gul.json --format json
gul validate spec.gul.json --strict
```

#### Acceptance criteria
- valid input returns exit code `0`
- invalid input returns nonzero exit code
- JSON mode emits schema-valid `gul.validation.result/1`
- errors include code, severity, path/line/column when available, message, and violated invariant
- identical input under the same version yields byte-stable normalized output in JSON mode

#### Minimum checks
- decision values constrained to `permit|deny|defer|abstain`
- confidence values constrained to `[0,1]`
- jurisdiction references resolve
- predicate/operator names are known or explicitly namespaced
- recursive expression structure is well-formed

---

### WP-02 — Real `infer`

#### Goal
Replace placeholder inference behavior with deterministic evaluation over canonical IR.

#### Deliverables
- file-backed inference execution
- structured result envelope
- optional audit trace emission

#### CLI shape
```bash
gul infer expr.gul.json
gul infer expr.gul.json --format json
gul infer expr.gul.json --trace
```

#### Output envelope
```json
{
  "schema": "gul.inference.result/1",
  "input_hash": "...",
  "decision": "defer",
  "confidence": 0.74,
  "jurisdiction": "org.root.teamA",
  "evidence": [],
  "trace": [],
  "version": "2.2.0"
}
```

#### Acceptance criteria
- same input + same seed + same version => byte-stable JSON output
- `--trace` emits ordered rule application chain
- conflict resolution follows documented combiner semantics
- threshold and jurisdiction effects are visible in the trace

#### Minimum operator support
- AND
- OR
- NOT
- threshold
- jurisdiction check
- override
- sequential confidence composition
- parallel confidence composition

---

### WP-03 — Canonical schema registry

#### Goal
Create one public contract for machine-readable exchange across Python, C++, and bridge layers.

#### Deliverables
Add `schemas/` with versioned JSON schemas for:

- `gul.decision/1`
- `gul.evaluated_decision/1`
- `gul.predicate/1`
- `gul.policy.expr/1`
- `gul.validation.result/1`
- `gul.inference.result/1`
- `gul.dataset.sample/1`

#### Acceptance criteria
- all public CLI JSON outputs validate against schema
- Python bridge roundtrips schema-valid objects
- schema version is present in every emitted JSON artifact
- no breaking schema changes inside `2.2.x`

#### Design rule
No hidden fields. Free-form payloads are only allowed under a clearly marked `extensions` object.

---

### WP-04 — Spec-driven corpus forge

#### Goal
Replace the visible toy-pool dataset generator with generation from declared GUL structures and scenario templates.

#### Deliverables
Generator consumes:

- policy specs
- predicate registries
- jurisdiction trees
- confidence templates
- conflict templates

Scenario families:

- permit path
- deny path
- defer escalation
- abstain / out-of-scope
- conflict resolution
- low-confidence threshold failure
- cross-jurisdiction override

#### CLI shape
```bash
gul -T -n 1000 --scenario balanced
gul -T -n 1000 --scenario adversarial --seed 42
gul -T -n 1000 --stats
```

#### Acceptance criteria
- emitted samples derive from declared scenarios rather than hardcoded toy entities
- every sample carries provenance:
  - schema
  - scenario family
  - seed
  - generator version
  - source spec id
- balanced and adversarial modes are both supported
- `--stats` reports decision distribution and scenario distribution

---

### WP-05 — Test and CI release gate

#### Goal
Make the release mechanically self-policing.

#### Deliverables
- unit tests
- golden-output tests
- schema validation tests
- deterministic seed tests
- CLI smoke tests
- packaging tests
- GitHub Actions workflow

#### Minimum matrix
- Python `3.10` to `3.13`
- Linux
- Windows for CLI packaging sanity

#### Mandatory invariants
- confidence never escapes `[0,1]`
- decision combination is total
- `ABSTAIN` acts as identity where documented
- deterministic inference under fixed seed
- deterministic generation under fixed seed
- schema validity for all public JSON artifacts

#### Acceptance criteria
- all tests pass in CI
- wheel builds successfully
- source distribution installs successfully
- packaged CLI smoke tests pass

---

### WP-06 — Documentation and examples

#### Goal
Bring public documentation into exact alignment with shipped behavior.

#### Deliverables
- README revision
- `examples/` directory
- migration notes from `2.1.0`
- explicit input-format documentation
- explicit statement of supported vs future capability

#### Acceptance criteria
- every documented command runs as written
- examples cover validate, infer, generate, and Python bridge usage
- release notes enumerate known limitations

---

## 6. Recommended repository additions

```text
docs/release_notes/RELEASE_SPEC_v2_2_0.md
schemas/
examples/
tests/
.github/workflows/
```

Potential file additions:

```text
cpp/src/validate.cpp
cpp/src/infer.cpp
cpp/src/schema_io.cpp
tests/golden/
examples/specs/
examples/policies/
```

---

## 7. Execution order

### Phase A — Surface closure
Ship real `validate` and `infer` first.

### Phase B — Contract closure
Freeze the canonical JSON schema registry.

### Phase C — Generation closure
Rework dataset generation around declared scenario families.

### Phase D — Proof closure
Add tests, golden outputs, and CI.

### Phase E — Public closure
Rewrite docs, examples, and release notes.

---

## 8. Release cut criteria

Do **not** tag `2.2.0` unless all are true:

- [ ] `validate` is real
- [ ] `infer` is real
- [ ] canonical JSON schemas exist
- [ ] dataset generation is spec-driven
- [ ] deterministic tests pass
- [ ] README matches implementation
- [ ] packaged install works

If only docs and minor cleanup land, tag `2.1.1` instead.

---

## 9. Failure mode catalog

### F-01 — Surface/implementation mismatch
Documented commands do not perform real work.

**Mitigation:** CI smoke-test every README command.

### F-02 — Schema drift
Python and C++ emit different shapes for nominally identical artifacts.

**Mitigation:** shared schema validation in both test suites.

### F-03 — Nondeterministic outputs
Inference or generation cannot support stable golden tests.

**Mitigation:** explicit seed threading, ordered serialization, and golden output checks.

### F-04 — Cosmetic dataset sophistication
Generator still behaves randomly but with more formal labels.

**Mitigation:** require scenario provenance and source spec linkage in every sample.

### F-05 — Over-expansion
Scope expands into theorem proving or rich language design.

**Mitigation:** JSON IR first; richer frontend later.

### F-06 — Audit opacity
Results are technically correct but not inspectable.

**Mitigation:** `infer --trace` must emit an ordered rule application chain.

---

## 10. Suggested milestone issues

1. Implement canonical validation result schema
2. Implement CLI file loader and normalized IR emitter
3. Implement executable `validate`
4. Implement inference result schema
5. Implement executable `infer`
6. Add schema validation tests
7. Replace toy dataset pool with scenario-driven generator
8. Add sample provenance and generator stats
9. Add golden tests for inference and generation
10. Add GitHub Actions release gate
11. Rewrite README around shipped capability
12. Cut `2.2.0` release notes and tag

---

## 11. Draft changelog skeleton

### Added
- executable `validate` command for canonical GUL spec files
- executable `infer` command with structured trace output
- versioned canonical JSON schemas for validation, inference, decisions, and dataset samples
- spec-driven corpus generation with deterministic seeds and scenario provenance
- end-to-end CLI and Python examples
- invariant and golden-output test suite
- CI-based release gating

### Changed
- dataset generation now derives from declared scenario families and source specifications
- public JSON outputs conform to explicit versioned schemas
- documentation reflects only shipped capability

### Fixed
- command/help surface mismatch around `validate` and `infer`
- nondeterministic serialization edge cases
- incomplete machine-readable auditability for inference results

### Known limitations
- `2.2.0` prioritizes canonical JSON IR over a richer standalone language frontend
- full formal proof artifact execution remains future work
- advanced runtime backends remain optional integrations

---

## 12. Final recommendation

Use `2.2.0` to close the execution gap, not to add conceptual breadth.

That is the highest-leverage move available to the repository at its current stage.
