"""
GUL v2.1 — CLI bridge: invoke gul.exe from Python for dataset generation and commands.

Provides a single Python surface for:
- generate_dataset: run GUL CLI -T and write JSONL (or stream)
- validate: validate a GUL spec file
- infer: run inference on an expression file

Requires gul/cpp to be built; set GUL_EXE_PATH or ensure gul is on PATH.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterator, Optional


def find_gul_exe(gul_exe_path: Optional[str] = None) -> str:
    """Resolve path to gul executable. Prefer GUL_EXE_PATH env, then argument, then PATH."""
    exe = gul_exe_path or os.environ.get("GUL_EXE_PATH")
    if exe:
        p = Path(exe)
        if p.is_absolute() and p.exists():
            return str(p)
        # Try relative to cwd or PATH
        if p.exists():
            return str(p.resolve())
    # Default relative to this package: gul/cpp/build/Release/gul.exe (Windows) or build/gul (Unix)
    this_dir = Path(__file__).resolve().parent
    for candidate in [
        this_dir / "cpp" / "build" / "Release" / "gul.exe",
        this_dir / "cpp" / "build" / "gul.exe",
        this_dir / "cpp" / "build" / "gul",
    ]:
        if candidate.exists():
            return str(candidate)
    return "gul"  # fallback to PATH


def generate_dataset(
    n: int,
    output_path: Optional[Path] = None,
    config_path: Optional[Path] = None,
    format: str = "jsonl",
    random_order: bool = False,
    block_size: Optional[int] = None,
    seed: Optional[int] = None,
    gul_exe_path: Optional[str] = None,
    cwd: Optional[Path] = None,
) -> Optional[Path]:
    """
    Run GUL CLI to generate a training dataset and optionally write to a file.

    Args:
        n: Number of samples (--limit / -n).
        output_path: If set, write JSONL to this path; otherwise stdout is not captured.
        config_path: Optional -config <path>.
        format: Ignored for now; CLI always outputs JSONL when -T is used.
        random_order: Pass -random.
        block_size: Pass -block N.
        seed: Pass -seed N (0 = random).
        gul_exe_path: Override path to gul.exe.
        cwd: Working directory for subprocess.

    Returns:
        output_path if output was written, else None.
    """
    exe = find_gul_exe(gul_exe_path)
    cmd = [exe, "-oneshot", "-T", "-n", str(n)]
    if config_path and Path(config_path).exists():
        cmd.extend(["-config", str(config_path)])
    if random_order:
        cmd.append("-random")
    if block_size is not None:
        cmd.extend(["-block", str(block_size)])
    if seed is not None:
        cmd.extend(["-seed", str(seed)])

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
                check=True,
                timeout=300,
            )
        return out_file
    subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=True,
        timeout=300,
    )
    return None


def stream_dataset(
    n: Optional[int] = None,
    config_path: Optional[Path] = None,
    random_order: bool = False,
    gul_exe_path: Optional[str] = None,
    cwd: Optional[Path] = None,
) -> Iterator[str]:
    """
    Stream GUL dataset lines from the CLI (generator).

    Yields:
        One JSON line per yield (without trailing newline).
    """
    exe = find_gul_exe(gul_exe_path)
    cmd = [exe, "-oneshot", "-T"]
    if n is not None:
        cmd.extend(["-n", str(n)])
    if config_path and Path(config_path).exists():
        cmd.extend(["-config", str(config_path)])
    if random_order:
        cmd.append("-random")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(cwd) if cwd else None,
        text=True,
        encoding="utf-8",
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip("\n\r")
        if line:
            yield line
    proc.wait()
    if proc.returncode != 0:
        err = proc.stderr.read() if proc.stderr else ""
        raise RuntimeError(f"gul exited {proc.returncode}: {err}")


def validate(spec_path: Path, gul_exe_path: Optional[str] = None, cwd: Optional[Path] = None) -> bool:
    """
    Validate a GUL spec file. Runs: gul validate <spec_path>.

    Returns:
        True if validation succeeded (exit 0), False otherwise.
    """
    exe = find_gul_exe(gul_exe_path)
    cmd = [exe, "validate", str(spec_path)]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        timeout=30,
    )
    return result.returncode == 0


def infer(
    spec_path: Path,
    gul_exe_path: Optional[str] = None,
    cwd: Optional[Path] = None,
) -> subprocess.CompletedProcess:
    """
    Run inference on an expression file. Runs: gul infer <spec_path>.

    Returns:
        CompletedProcess; check .returncode and .stdout / .stderr.
    """
    exe = find_gul_exe(gul_exe_path)
    cmd = [exe, "infer", str(spec_path)]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        timeout=30,
    )
