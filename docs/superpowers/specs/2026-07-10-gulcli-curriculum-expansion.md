# GULCLI Curriculum Expansion Implementation Spec

Status: Ready for Cursor implementation  
Date: 2026-07-10  
Repository: `torakagemusha-sudo/gulcli`  
Purpose: Convert GULCLI from a compact scenario emitter into a controlled governance-reasoning curriculum for model training and evaluation.

---

## 1. Context

Recent model training showed materially lower best loss on GULCLI-derived data than on a WikiText/C4 mix. This is plausible because the current GULCLI dataset distribution is a constrained formal trace language: seven scenario families, stable JSONL fields, repeated predicate structures, fixed entity/resource/context names, and stereotyped evidence strings.

That is useful, but ambiguous. Low loss may indicate real learning of Governed Uncertainty Logic, or it may indicate compression of a finite generator. This work must separate template memorization from semantic generalization.

The current C++ generator already emits JSONL records with stable top-level fields and provenance extensions. It should remain backward compatible, but gain parameterized diversity, corruption modes, benchmark split generation, and bridge parity.

---

## 2. Goals

1. Add a Python dataset generator fallback so training/eval automation does not require native `gul` or Wine.
2. Expose native dataset flags through `cli_bridge.py`: `--scenario`, `--spec`, and `--stats`.
3. Expand dataset entropy while preserving semantic truth.
4. Add generator-aware benchmark splits to prevent optimistic random-line validation.
5. Add corruption/evaluation tasks for semantic repair, contradiction spotting, and provenance validation.
6. Add diversity tests and benchmark fixture tests.
7. Add a model-card style note explaining what low GULCLI loss does and does not mean.

---

## 3. Non-goals

- Do not replace the C++ generator.
- Do not remove the existing seven scenario families.
- Do not break the existing JSONL sample shape.
- Do not introduce heavyweight runtime dependencies for the core package.
- Do not claim broad language-model capability from low synthetic loss.

---

## 4. Target curriculum tiers

### Tier 0 — Existing deterministic scenario smoke layer

Keep current behavior as a stable compatibility baseline:

- `permit_path`
- `deny_path`
- `defer_escalation`
- `abstain_scope`
- `conflict_resolution`
- `threshold_fail`
- `jurisdiction_override`

Acceptance: existing tests and fixtures continue to pass unchanged.

### Tier 1 — Parameterized diversity layer

Add controlled variation over:

- entity IDs: agents, services, tools, users, operators
- resource IDs: documents, deployments, datasets, robots, policy bundles
- context IDs: workspace, prod, staging, lab, field, offline, restricted
- roles: reviewer, maintainer, operator, admin, contractor, auditor, guest
- classifications: public, internal, confidential, secret, restricted
- confidence bands: low, medium, high, boundary, contradictory
- evidence phrase families with deterministic seed control

Acceptance:

- seed-stable generation
- configurable vocabulary pools
- distribution coverage over predicate tags and decision labels
- no breaking change to existing JSONL schema

### Tier 2 — Compositional policy-expression layer

Generate executable GUL expressions from supported runtime tags:

- `decision`
- `atom`
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

Labels must be derived by the Python reference runtime where practical. If native generation is used, parity tests must compare against Python outputs for a bounded fixture set.

Acceptance:

- generated samples can carry `extensions.expr_hash`, `extensions.depth`, and `extensions.operator_set`
- max expression depth is configurable
- generated labels are runtime-derived, not handwritten when runtime evaluation is available

### Tier 3 — Adversarial corruption/evaluation layer

Add corruption modes that create negative/evaluation examples:

- wrong decision for evidence
- wrong confidence for decision
- confidence outside expected band
- jurisdiction mismatch
- impossible override
- invalid provenance
- source spec mismatch
- evidence string contradicts predicate
- missing required fact
- shuffled predicate arguments

Each corrupted record should preserve the original clean record ID or hash and include an `extensions.corruption` object:

```json
{
  "kind": "wrong_decision",
  "source_clean_hash": "...",
  "expected_decision": "deny",
  "corrupted_decision": "permit"
}
```

Acceptance:

- corruption modes are deterministic under seed
- corrupted examples are separable from clean samples by extension metadata
- tests verify every corruption mode actually mutates the intended invariant

---

## 5. Implementation tasks

### Task A — Python generator fallback

Add a pure-Python generator module, suggested path:

- `dataset_generator.py` or `gulcli/dataset_generator.py` depending current package layout constraints.

Required public helpers:

```python
def generate_samples(n: int, *, scenario: str = "balanced", seed: int | None = None, spec_path: str | None = None, tier: int = 0) -> list[dict]: ...

def stream_samples(n: int | None = None, *, scenario: str = "balanced", seed: int | None = None, spec_path: str | None = None, tier: int = 0) -> Iterator[str]: ...
```

Acceptance:

- mirrors the existing JSONL record shape
- supports Tier 0 and Tier 1 initially
- can be extended for Tier 2/Tier 3 without API break
- has unit tests independent of native CLI

### Task B — Bridge parity for native dataset flags

Extend `cli_bridge.generate_dataset` and `cli_bridge.stream_dataset` to expose:

- `scenario: str | None`
- `spec_path: Path | None`
- `emit_stats: bool = False`

Native invocation mapping:

- `scenario` -> `--scenario <balanced|adversarial>`
- `spec_path` -> `--spec <path>`
- `emit_stats` -> `--stats`

Acceptance:

- existing function calls remain backward compatible
- tests assert generated command arguments without requiring native binary
- docs update removes stale bridge limitation

### Task C — Diversity controls

Add configurable pools, either as Python constants plus optional JSON config, or as C++/Python shared docs-first config.

Suggested file:

- `examples/dataset/curriculum_pools.json`

Acceptance:

- deterministic seed produces stable samples
- different seeds change at least entity/resource/context/evidence selections
- test coverage verifies coverage over multiple categories

### Task D — Benchmark split generation

Add a script:

- `scripts/generate_curriculum_splits.py`

Outputs:

- `data/gulcli/train.jsonl`
- `data/gulcli/valid_random.jsonl`
- `data/gulcli/valid_holdout_scenario.jsonl`
- `data/gulcli/valid_holdout_vocab.jsonl`
- `data/gulcli/valid_corrupted.jsonl`
- `data/gulcli/eval_generalization.jsonl`

Do not commit large generated datasets by default. Commit small golden fixtures only.

Acceptance:

- script can write to a user-specified output directory
- default fixture mode creates small deterministic files suitable for CI
- holdout splits are generator-aware, not random-only

### Task E — Diversity and invariant tests

Add tests for:

- all scenario families covered in balanced generation
- adversarial mode changes scenario distribution
- every decision label appears under a bounded sample run
- provenance fields exist when scenario metadata is emitted
- bridge command construction includes `--scenario`, `--spec`, `--stats`
- corruption modes alter exactly the target invariant
- Python fallback generates schema-compatible records

### Task F — Model card / interpretation note

Add:

- `docs/GULCLI_MODEL_CARD.md`

Must explain:

- low loss on GULCLI is expected because the corpus is lower entropy than WikiText/C4
- low loss is not equivalent to general language competence
- use generator-aware splits
- report transfer matrix, not one scalar
- recommended evals: in-domain, holdout scenario, holdout vocab, corrupted repair, adjacent technical text

---

## 6. Acceptance checklist

- [ ] Python generator fallback implemented and tested.
- [ ] `cli_bridge.py` exposes `scenario`, `spec_path`, and `emit_stats` without breaking existing callers.
- [ ] Curriculum pools or equivalent diversity controls added.
- [ ] Split generation script added with fixture mode.
- [ ] Corruption/evaluation modes implemented or at minimum scaffolded with tests.
- [ ] Documentation updated in README and `docs/runtime_usage.md`.
- [ ] `docs/GULCLI_MODEL_CARD.md` added.
- [ ] Full test suite passes: `python3 -m unittest discover -s tests -v`.
- [ ] Native tests remain skipped when native binary is unavailable; no CI hard failure due to Wine/native absence.

---

## 7. Cursor implementation prompt

Implement the GULCLI curriculum expansion described in this spec. Start with backward-compatible Python fallback generation, bridge flag parity, small deterministic fixtures, and tests. Prefer stdlib-only Python. Do not commit large generated datasets. Preserve existing JSONL sample shape and v2.2.0 semantics. Update docs so the runtime boundary is truthful. Run the full unittest suite and report exact pass/skip counts. If native CLI is unavailable, test command construction and Python fallback behavior rather than blocking.
