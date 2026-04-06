# GUL CLI

GUL CLI is a pre-compiled Windows x64 command-line tool (`gul.exe`) for streaming ML-ready dataset samples and running placeholder `validate`/`infer` commands.

## Repository Scope

This is a binary distribution repository:

- No source code.
- No build system.
- No package manifests.
- No automated test suite.

## Platform and Setup

- Binary format: Windows PE x86-64 (`gul.exe`).
- Native support: Windows x64.
- Linux/macOS: run through Wine.

### Prerequisites

- Windows: no extra runtime required.
- Linux/macOS: Wine must be installed and available on `PATH`.

### Invocation Patterns

Windows (PowerShell/CMD):

```bash
gul.exe --help
gul.exe --version
```

Linux/macOS via Wine:

```bash
WINEDEBUG=-all DISPLAY= wine gul.exe --help
WINEDEBUG=-all DISPLAY= wine gul.exe --version
```

## Public CLI Interface

Usage string embedded in the executable:

```text
Usage: gul [options] [command] [args]
```

Options and commands:

| Option / Command | Description |
|---|---|
| `-oneshot` | Single batch mode |
| `-T` | Stream dataset to stdout (JSON Lines training format) |
| `-deepgul` | Enable deep GUL streaming |
| `-L <host/port>` | Stream to TCP (example: `127.0.0.1/1234` or `127.0.0.1:1234`) |
| `-n, --limit <N>` | Limit to `N` samples |
| `-random, --random` | Randomize sample order |
| `-block, --block <N>` | Block size for streaming (default: `64`) |
| `-seed, --seed <N>` | RNG seed (`0` means random) |
| `-config, --config <path>` | Load config file (`key=value` or `key: value`) |
| `validate [file]` | Validate GUL spec file (currently placeholder behavior) |
| `infer [file]` | Run inference from expression file (currently placeholder behavior) |
| `-h, --help` | Show help |
| `-v, --version` | Show version |

## Operational Runbooks

### Stream to stdout (JSONL)

Use this when a trainer or script reads from standard output.

```bash
WINEDEBUG=-all DISPLAY= wine gul.exe -oneshot -T
WINEDEBUG=-all DISPLAY= wine gul.exe -T -n 1000
WINEDEBUG=-all DISPLAY= wine gul.exe -config train.conf -random -block 32 -T
```

### Stream to a TCP consumer

Use this when a remote/local service ingests samples from a socket.

```bash
WINEDEBUG=-all DISPLAY= wine gul.exe -deepgul -L 127.0.0.1/1234
WINEDEBUG=-all DISPLAY= wine gul.exe -oneshot -T -L 127.0.0.1/1234 -n 500
```

### Config-driven runs

Sample config:

```ini
seed = 42
block_size = 64
max_samples = 10000
random_order = true
```

Then run:

```bash
WINEDEBUG=-all DISPLAY= wine gul.exe -config train.conf -T
```

## Dataset Shape and Constraints

Streaming output is JSON Lines. Observed fields include:

- `entity` object with `kind` and `id`
- `predicate` object with `tag` and `args`
- `context_confidence`
- `decision` in `permit | deny | defer | abstain`
- `confidence`
- `evidence`

Constraints:

- Confidence values are expected in `[0, 1]` (the executable includes a `Confidence must be in [0,1]` constraint message).
- Treat each output line as an independent JSON document.

## Troubleshooting and Pitfalls

- `wine: command not found`: install Wine, then re-run using `WINEDEBUG=-all DISPLAY= wine gul.exe ...`.
- `gul.exe: command not found` on Windows: run from the binary directory or add that directory to `PATH`.
- No native execution on Linux/macOS: use Wine or run in Windows.
- No data received on TCP: verify listener is up and `-L` endpoint format is correct.
- Unexpected sample count: check `-n/--limit` and config (`max_samples`) interactions.
- Non-reproducible runs: set explicit `-seed` value (avoid `0` when determinism is required).
- `validate`/`infer` expectations: current help text marks these as placeholder flows.

## Verification Notes

- In this repository, interface details are verified against strings embedded in `gul.exe`.
- Runtime command validation requires a host with Wine (or Windows native execution).
