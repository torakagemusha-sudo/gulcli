# GUL v2.2.0 — C++ CLI

Governed Uncertainty Logic formal system and constraint engine with a CLI for dataset streaming (ML training).

## Build

### Linux / macOS

```bash
cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build cpp/build
```

Executable: `cpp/build/gul`.

On Linux CI, use `g++-12` if the default compiler cannot link `libstdc++`:

```bash
cmake -S cpp -B cpp/build -DCMAKE_CXX_COMPILER=g++-12
cmake --build cpp/build
```

### Windows

```bash
cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build cpp/build --config Release
```

Executable: `cpp/build/Release/gul.exe` or `cpp/build/gul.exe`.

### Cross-compile `gul.exe` on Linux (mingw-w64)

```bash
bash cpp/scripts/build-gul-exe.sh
```

Writes a portable `gul.exe` to the repository root (static libgcc/libstdc++).

## Usage

Current boundary: dataset streaming and file-backed `validate` / `infer` are
implemented for supported composition tags when built from `cpp/`. Native `atom`
evaluation supports `--facts <path>` on `infer`.

Project updates for runtime and native CLI documentation work are tracked in
`../docs/PROJECT_UPDATES.md`. The current Linear-ready record covers the PR #20
documentation refresh for fact-backed infer, scenario dataset flags, and bridge
limits, plus the PR #21 and PR #22 project-tracking follow-ups.

### Dataset streaming (ML training)

- **Stream to stdout (training format, JSON Lines):**
  ```bash
  gul -oneshot -T -n 64
  gul -T -n 1000
  gul -config sample.conf -T -random -block 32
  ```

- **Stream to TCP listener (e.g. training server):**
  ```bash
  gul -deepgul -L 127.0.0.1/1234 -n 500
  gul -oneshot -T -L 127.0.0.1/1234 -n 500
  ```

### Options

| Option | Description |
|--------|-------------|
| `-config <path>` | Load config file (key=value or key: value) |
| `-oneshot` | Select single-command stdout streaming; pair with `-n` or `max_samples` to exit |
| `-T` | Stream dataset to stdout (training format) |
| `-deepgul` | Enable deep GUL streaming |
| `-L <host/port>` | Stream to TCP (e.g. `127.0.0.1/1234` or `127.0.0.1:1234`) |
| `-n, --limit <N>` | Limit to N samples |
| `-random` | Randomize sample order |
| `-block <N>` | Block size for streaming (default 64) |
| `-seed <N>` | RNG seed (0 = random) |
| `--scenario <mode>` | `balanced` or `adversarial` scenario selection |
| `--spec <path>` | Link samples to a `*.gul.json` spec (`source_spec_id`) |
| `--stats` | Emit scenario/decision distribution JSON to stderr |
| `validate [file]` | Validate a GUL spec file (`--format json` supported) |
| `infer [file]` | Run inference (`--format json`, `--trace`, `--facts` supported) |
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

When neither `-n <N>` nor a config `max_samples` value is provided, native
dataset streaming is unbounded.

### Dataset format (JSON Lines)

Each line is a JSON object with:

- `entity`: `{ "kind", "id" }`
- `predicate`: `{ "tag", "args" }`
- `context_confidence`: number
- `decision`: `"permit"` | `"deny"` | `"defer"` | `"abstain"`
- `confidence`: number in [0, 1]
- `evidence`: array of strings
- `extensions` (optional): provenance (`schema`, `scenario`, `source_spec_id`, `seed`, `generator_version`, `sample_index`)

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
