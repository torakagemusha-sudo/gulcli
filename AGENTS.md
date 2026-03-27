# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This repository is a **distribution repo** for **GUL CLI** (Governed Uncertainty Logic), a pre-compiled Windows x86-64 binary (`gul.exe`). There is no source code, no build system, no package manifests, and no test suite.

### Running the binary

`gul.exe` is a Windows PE32+ executable. On this Linux VM it runs via **Wine**:

```bash
WINEDEBUG=-all DISPLAY= wine gul.exe [options]
```

- `WINEDEBUG=-all` suppresses Wine debug noise.
- `DISPLAY=` avoids X11 errors in headless environments.

### Key commands

| Command | Purpose |
|---------|---------|
| `wine gul.exe --help` | Show usage/help |
| `wine gul.exe --version` | Show version (currently 2.1) |
| `wine gul.exe -oneshot -T -n 5` | Generate 5 JSON Lines samples to stdout |
| `wine gul.exe -oneshot -T -n 100 -random -seed 42 -block 8` | Randomized generation with seed and block size |

### Lint / Test / Build

- **No linter** is configured (no source code).
- **No automated tests** exist in the repo.
- **No build step** — the binary is pre-compiled.
- Validation: run `wine gul.exe --help` and `wine gul.exe -oneshot -T -n 1` to confirm the binary works.

### Gotchas

- Wine prefix initialization (`~/.wine`) happens on first run and adds ~7s latency. Subsequent runs are faster (~2.5s).
- The `-deepgul` streaming mode runs indefinitely; always pair with `-n <N>` or Ctrl+C to stop.
- TCP streaming (`-L`) requires a listener on the target host/port before starting.
