# AGENTS.md

## Cursor Cloud Specific Instructions

### Overview

This repository contains the GUL CLI / Python package for Governed Uncertainty
Logic.

The current tree includes:

- a Python package (`gulcli`) with confidence, decision, jurisdiction,
  inference, policy, compiler, integration, runtime I/O, and CLI bridge modules
- JSON schemas under `schemas/`
- executable runtime examples under `examples/`
- runtime unit tests under `tests/`
- a pre-compiled Windows x86-64 dataset streamer (`gul.exe`)

Do not treat this as a binary-only distribution repo. The Python runtime is the
primary verified path for validation and inference in Linux automation.

### Setup

Use `python3` in this environment:

```bash
python3 -m pip install -e .
```

The package requires Python 3.10+ and has no mandatory runtime dependencies.
Optional integrations are declared in `pyproject.toml`.

### Python Runtime Commands

| Command | Purpose |
|---------|---------|
| `python3 -m unittest tests.test_runtime_io` | Run the runtime unit tests |
| `python3 -m gulcli validate examples/specs/basic_infer.gul.json --format json` | Validate a JSON GUL spec |
| `python3 -m gulcli infer examples/specs/basic_infer.gul.json --format json --trace` | Run inference and emit trace output |
| `python3 examples/python_runtime_usage.py` | Exercise the Python helper API |

The package entry point delegates to `runtime_io.main`. The direct module form
also works:

```bash
python3 -m gulcli.runtime_io validate examples/specs/basic_infer.gul.json --format json
python3 -m gulcli.runtime_io infer examples/specs/basic_infer.gul.json --format json --trace
```

### Native Binary

`gul.exe` is a Windows PE32+ executable. On Linux it requires Wine when Wine is
available:

```bash
WINEDEBUG=-all DISPLAY= wine gul.exe [options]
```

- `WINEDEBUG=-all` suppresses Wine debug noise.
- `DISPLAY=` avoids X11 errors in headless environments.
- Wine is not guaranteed to be installed in every Cursor Cloud image. If
  `wine: command not found`, validate and infer through the Python runtime.

### Native Binary Commands

| Command | Purpose |
|---------|---------|
| `WINEDEBUG=-all DISPLAY= wine gul.exe --help` | Show usage/help |
| `WINEDEBUG=-all DISPLAY= wine gul.exe --version` | Show native CLI version |
| `WINEDEBUG=-all DISPLAY= wine gul.exe -oneshot -T -n 5` | Generate 5 JSON Lines samples to stdout |
| `WINEDEBUG=-all DISPLAY= wine gul.exe -oneshot -T -n 100 -random -seed 42 -block 8` | Randomized generation with seed and block size |

### Test / Build

- **Python tests:** `python3 -m unittest tests.test_runtime_io`
- **CI:** `.github/workflows/runtime-ci.yml` tests Python 3.10 through 3.13
- **Python package build backend:** setuptools via `pyproject.toml`
- **Native binary:** the checked-in `gul.exe` is pre-compiled; there is no
  required native build step for ordinary runtime validation

No project-wide linter is configured.

### Gotchas

- `python` may not exist; use `python3`.
- Run `python3 -m pip install -e .` before package-entry commands if
  `No module named gulcli` appears.
- The Python runtime can validate and infer JSON specs. Dataset generation still
  depends on the native CLI.
- `cli_bridge.find_gul_exe` resolution order is `gul_exe_path` argument,
  `GUL_EXE_PATH`, package-local `cpp/build/` artifacts, then `gul` on `PATH`.
- `cli_validate` and `cli_infer` fall back to the Python runtime only when the
  native executable is missing or cannot be launched.
- `-deepgul` streaming mode can run indefinitely; pair it with `-n <N>` or stop
  it manually.
- TCP streaming (`-L`) requires a listener on the target host/port before
  starting.
