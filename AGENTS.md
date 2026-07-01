# AGENTS.md

## Cursor Cloud Specific Instructions

### Overview

This repository contains the GUL CLI / Python package for Governed Uncertainty Logic.

The current tree is not binary-only. It includes:

- a pure-Python `gulcli` package with decision, confidence, jurisdiction, inference, policy-expression, runtime I/O, and CLI-bridge modules
- JSON schemas under `schemas/`
- executable JSON examples under `examples/specs/`
- a C++17 CLI implementation under `cpp/` for dataset streaming
- a pre-compiled Windows x86-64 dataset streamer (`gul.exe`)
- Python runtime tests under `tests/`

Do not treat this as a binary-only distribution repo. The Python runtime is the
primary verified path for validation and inference in Linux automation.

### Python setup and validation

Install the package in editable mode before running module entry points:

```bash
python3 -m pip install -e .
```

Key Python commands:

| Command | Purpose |
|---------|---------|
| `python3 -m unittest tests.test_runtime_io` | Run runtime validation/inference tests |
| `python3 -m gulcli validate examples/specs/basic_infer.gul.json --format json` | Validate a JSON GUL expression |
| `python3 -m gulcli infer examples/specs/basic_infer.gul.json --format json --trace` | Execute inference and include the trace |
| `python3 examples/python_runtime_usage.py` | Run the documented Python helper example |

The package entry point delegates to `runtime_io.main` and is preferred for
automation. The direct module form also works, but it can emit Python's `runpy`
warning because `gulcli.__init__` imports `runtime_io`:

```bash
python3 -m gulcli.runtime_io validate examples/specs/basic_infer.gul.json --format json
python3 -m gulcli.runtime_io infer examples/specs/basic_infer.gul.json --format json --trace
```

### C++ CLI

Build the native CLI from `cpp/` when working on dataset streaming or C++ core types:

```bash
cd cpp
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

This requires CMake and a C++17 compiler/linker toolchain. If the linker cannot find `libstdc++`, install the system C++ build tools first. C++ build verification is not part of the default documentation-only validation path.

Common streaming commands after a build:

| Command | Purpose |
|---------|---------|
| `cpp/build/gul --help` | Show native CLI usage on Linux |
| `cpp/build/gul -oneshot -T -n 5` | Generate 5 JSON Lines samples to stdout |
| `cpp/build/gul -oneshot -T -n 100 -random -seed 42 -block 8` | Randomized generation with seed and block size |

On Windows, CMake may emit `build/Release/gul.exe` depending on generator.

The checked-in `gul.exe` is a Windows PE32+ executable. On Linux it requires Wine when Wine is available:

```bash
WINEDEBUG=-all DISPLAY= wine gul.exe [options]
```

- `WINEDEBUG=-all` suppresses Wine debug noise.
- `DISPLAY=` avoids X11 errors in headless environments.
- Wine is not guaranteed to be installed in every Cursor Cloud image. If
  `wine: command not found`, validate and infer through the Python runtime.

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
- The real file-backed `validate` / `infer` implementation is the Python runtime in `runtime_io.py`.
- Native C++ `validate` and `gul infer` load `*.gul.json` files when built from `cpp/` (`cpp/build/gul`). Atom evaluation requires the Python runtime with `--facts`.
- `cli_bridge.validate` and `cli_bridge.infer` try the native `gul` executable first and only fall back to Python when the executable cannot be started.
- The Python runtime can validate and infer JSON specs. Dataset generation still
  depends on the native CLI.
- `cli_bridge.find_gul_exe` resolution order is `gul_exe_path` argument,
  `GUL_EXE_PATH`, package-local `cpp/build/` artifacts, then `gul` on `PATH`.
- Native `-deepgul` streaming mode can run indefinitely; pair it with `-n <N>` or stop
  it manually.
- TCP streaming (`-L`) requires a listener on the target host/port before
  starting.
