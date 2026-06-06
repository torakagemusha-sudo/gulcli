# AGENTS.md

## Cursor Cloud Specific Instructions

### Overview

This repository contains the GUL CLI / Python package for Governed Uncertainty Logic.

The current tree is not binary-only. It includes:

- a pure-Python `gulcli` package with decision, confidence, jurisdiction, inference, policy-expression, runtime I/O, and CLI-bridge modules
- JSON schemas under `schemas/`
- executable JSON examples under `examples/specs/`
- a C++17 CLI implementation under `cpp/` for dataset streaming
- Python runtime tests under `tests/`

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

- **Python tests:** `python3 -m unittest tests.test_runtime_io`
- **CI:** `.github/workflows/runtime-ci.yml` tests Python 3.10 through 3.13
- **Python package build backend:** setuptools via `pyproject.toml`
- **Native binary:** the checked-in `gul.exe` is pre-compiled; there is no
  required native build step for ordinary runtime validation

- No formatter or linter is configured.
- Python CI runs `python -m unittest tests.test_runtime_io` on Python 3.10 through 3.13.
- The C++ build is manual; there is no C++ test target.
- For documentation-only changes that touch runtime claims, run the Python tests and both Python smoke commands above.

### Gotchas

- `python3 -m gulcli ...` assumes the editable package has been installed; from a raw checkout, imports can fail because the package root is the repository root.
- The real file-backed `validate` / `infer` implementation is the Python runtime in `runtime_io.py`.
- Native C++ `validate` and `infer` currently print placeholders and return success; do not document them as real file-backed validation or inference until `cpp/src/cli.cpp` changes.
- `cli_bridge.validate` and `cli_bridge.infer` try the native `gul` executable first and only fall back to Python when the executable cannot be started.
- Native `-deepgul` TCP streaming can run indefinitely when no `-n <N>` limit is supplied.
- TCP streaming (`-L`) requires a listener on the target host/port before starting.
