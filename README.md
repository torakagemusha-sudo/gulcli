# GUL CLI

GUL CLI is a Windows x64 command-line tool (`gul.exe`) for streaming ML-ready dataset samples and exposing placeholder `validate`/`infer` commands.

This repository is a distribution repository:

- It ships a precompiled binary (`gul.exe`).
- It does not include source code, build scripts, or automated tests.

## Platform and Setup

- Binary format: Windows PE x86-64 (`gul.exe`).
- Native support: Windows x64.
- Linux/macOS: run with a Windows compatibility layer (for example, Wine), or from a Windows environment.

Use platform-specific invocation:

```bash
# Windows (PowerShell/CMD)
.\gul.exe --help

# Linux/macOS (Wine)
WINEDEBUG=-all DISPLAY= wine ./gul.exe --help
```

## Public CLI Interface

Usage reported by the executable strings:

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
WINEDEBUG=-all DISPLAY= wine ./gul.exe -oneshot -T
WINEDEBUG=-all DISPLAY= wine ./gul.exe -T -n 1000
WINEDEBUG=-all DISPLAY= wine ./gul.exe -config train.conf -random -block 32 -T
```

### Stream to a TCP consumer

Use this when a remote/local service ingests samples from a socket.

```bash
# Example listener first (Linux/macOS):
nc -l 1234

# Then start producer:
WINEDEBUG=-all DISPLAY= wine ./gul.exe -deepgul -L 127.0.0.1/1234
WINEDEBUG=-all DISPLAY= wine ./gul.exe -oneshot -T -L 127.0.0.1/1234 -n 500
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
WINEDEBUG=-all DISPLAY= wine ./gul.exe -config train.conf -T
```

## Binary Update Verification Checklist

Run these checks whenever `gul.exe` is replaced:

```bash
WINEDEBUG=-all DISPLAY= wine ./gul.exe --help
WINEDEBUG=-all DISPLAY= wine ./gul.exe --version
WINEDEBUG=-all DISPLAY= wine ./gul.exe -oneshot -T -n 1
```

Expected outcomes:

- `--help` prints usage and option list.
- `--version` prints a semantic-style version string.
- `-oneshot -T -n 1` emits one JSON line sample.

## Dataset Shape and Constraints

Streaming output is JSON Lines. Runtime samples have included:

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

- `wine: command not found` on Linux/macOS: install Wine or run from Windows.
- `gul: command not found`: invoke `./gul.exe` directly (Windows) or through Wine.
- No native execution on Linux/macOS: use a Windows runtime/compatibility layer.
- No data received on TCP: verify listener is up and `-L` endpoint format is correct.
- Unexpected sample count: check `-n/--limit` and config (`max_samples`) interactions.
- Non-reproducible runs: set explicit `-seed` value (avoid `0` when determinism is required).
- `validate`/`infer` expectations: current help text marks these as placeholder flows.
