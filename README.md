# GUL — C++ CLI

Governed Uncertainty Logic formal system and constraint engine with a CLI for dataset streaming (ML training).

Executable: `gul.exe` (Windows) or 

## Usage

### Dataset streaming (ML training)

- **Stream to stdout (training format, JSON Lines):**
  ```bash
  gul -oneshot -T
  gul -T -n 1000
  gul -config sample.conf -T -random -block 32
  ```

- **Stream to TCP listener (e.g. training server):**
  ```bash
  gul -deepgul -L 127.0.0.1/1234
  gul -oneshot -T -L 127.0.0.1/1234 -n 500
  ```

### Options

| Option | Description |
|--------|-------------|
| `-config <path>` | Load config file (key=value or key: value) |
| `-oneshot` | Single-batch mode |
| `-T` | Stream dataset to stdout (training format) |
| `-deepgul` | Enable deep GUL streaming |
| `-L <host/port>` | Stream to TCP (e.g. `127.0.0.1/1234` or `127.0.0.1:1234`) |
| `-n, --limit <N>` | Limit to N samples |
| `-random` | Randomize sample order |
| `-block <N>` | Block size for streaming (default 64) |
| `-seed <N>` | RNG seed (0 = random) |
| `validate [file]` | Validate GUL spec file |
| `infer [file]` | Run inference on expression file |
| `-h, --help` | Show help |
| `-v, --version` | Show version |

### Config file format

Plain text, one key per line:

```
seed = 42
block_size = 64
max_samples = 10000
random_order = true
```

### Dataset format (JSON Lines)

Each line is a JSON object with:

- `entity`: `{ "kind", "id" }`
- `predicate`: `{ "tag", "args" }`
- `context_confidence`: number
- `decision`: `"permit"` | `"deny"` | `"defer"` | `"abstain"`
- `confidence`: number in [0, 1]
- `evidence`: array of strings

Suitable for training models on GUL decision/confidence prediction.

## Core types (C++)

- **Confidence** — bounded [0, 1] lattice; union, intersection, sequential, parallel
- **Decision** — permit, deny, defer, abstain; combiners
- **Entity** — agent, resource, context, policy
- **Predicate** — belongs_to, has_role, has_attribute, in_context, time_before/after, custom
- **PolicyExpr** — atom, and_, or_, not_, implies, with_confidence, always, eventually, until
- **JurisdictionId** — hierarchical scope
- **GULInferenceEngine** — AND, OR, sequential, parallel, NOT, threshold, jurisdiction check
- **DatasetGenerator** — samples for ML; stream to stdout or TCP

## Invariants

- Confidence values remain in [0, 1]
- Deny dominates in decision combination
- Jurisdiction checks use sub-jurisdiction relation

