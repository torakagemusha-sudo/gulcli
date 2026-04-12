#!/usr/bin/env python3
"""
Convert GUL training dataset (CSV or JSON Lines) to Apache Arrow IPC format.
Streaming-friendly for large files (e.g. 2GB+).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import pyarrow as pa
    import pyarrow.ipc as ipc
except ImportError:
    print("pyarrow required: pip install pyarrow", file=sys.stderr)
    sys.exit(1)


def detect_format(path: Path) -> str:
    """Return 'jsonlines' or 'csv' based on first line."""
    try:
        with open(path, "rb") as f:
            first = f.readline().decode("utf-8", errors="replace").strip()
    except OSError:
        return "jsonlines"  # default for GUL CLI output if file locked
    if not first:
        return "csv"
    if first.startswith("{"):
        return "jsonlines"
    return "csv"


def jsonlines_to_arrow_stream(
    csv_path: Path,
    arrow_path: Path,
    *,
    batch_size: int = 50_000,
    encoding: str = "utf-8",
) -> None:
    """Stream JSON Lines file to Arrow IPC file (one JSON object per line)."""
    schema = pa.schema([
        ("entity_kind", pa.string()),
        ("entity_id", pa.string()),
        ("predicate_tag", pa.string()),
        ("predicate_args", pa.list_(pa.string())),
        ("context_confidence", pa.float64()),
        ("decision", pa.string()),
        ("confidence", pa.float64()),
        ("evidence", pa.list_(pa.string())),
    ])

    def parse_line(line: bytes) -> dict | None:
        line = line.decode(encoding, errors="replace").strip()
        if not line:
            return None
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return None

    def row_to_arrays(obj: dict) -> tuple:
        entity = obj.get("entity") or {}
        pred = obj.get("predicate") or {}
        args = pred.get("args") or []
        evidence = obj.get("evidence") or []
        return (
            str(entity.get("kind", "")),
            str(entity.get("id", "")),
            str(pred.get("tag", "")),
            [str(a) for a in args],
            float(obj.get("context_confidence", 0.0)),
            str(obj.get("decision", "")),
            float(obj.get("confidence", 0.0)),
            [str(e) for e in evidence],
        )

    with open(csv_path, "rb") as f:
        with open(arrow_path, "wb") as out_stream:
            with ipc.new_file(out_stream, schema) as writer:
                batch_entity_kind: list[str] = []
                batch_entity_id: list[str] = []
                batch_pred_tag: list[str] = []
                batch_pred_args: list[list[str]] = []
                batch_ctx_conf: list[float] = []
                batch_decision: list[str] = []
                batch_confidence: list[float] = []
                batch_evidence: list[list[str]] = []

                for line in f:
                    obj = parse_line(line)
                    if obj is None:
                        continue
                    try:
                        t = row_to_arrays(obj)
                        batch_entity_kind.append(t[0])
                        batch_entity_id.append(t[1])
                        batch_pred_tag.append(t[2])
                        batch_pred_args.append(t[3])
                        batch_ctx_conf.append(t[4])
                        batch_decision.append(t[5])
                        batch_confidence.append(t[6])
                        batch_evidence.append(t[7])
                    except (TypeError, KeyError):
                        continue

                    if len(batch_entity_kind) >= batch_size:
                        table = pa.table({
                            "entity_kind": batch_entity_kind,
                            "entity_id": batch_entity_id,
                            "predicate_tag": batch_pred_tag,
                            "predicate_args": batch_pred_args,
                            "context_confidence": batch_ctx_conf,
                            "decision": batch_decision,
                            "confidence": batch_confidence,
                            "evidence": batch_evidence,
                        })
                        writer.write_table(table)
                        batch_entity_kind.clear()
                        batch_entity_id.clear()
                        batch_pred_tag.clear()
                        batch_pred_args.clear()
                        batch_ctx_conf.clear()
                        batch_decision.clear()
                        batch_confidence.clear()
                        batch_evidence.clear()

                if batch_entity_kind:
                    table = pa.table({
                        "entity_kind": batch_entity_kind,
                        "entity_id": batch_entity_id,
                        "predicate_tag": batch_pred_tag,
                        "predicate_args": batch_pred_args,
                        "context_confidence": batch_ctx_conf,
                        "decision": batch_decision,
                        "confidence": batch_confidence,
                        "evidence": batch_evidence,
                    })
                    writer.write_table(table)


def csv_to_arrow_stream(csv_path: Path, arrow_path: Path) -> None:
    """Stream CSV file to Arrow IPC using PyArrow's CSV reader."""
    with pa.csv.open_csv(csv_path) as reader:
        with open(arrow_path, "wb") as out_stream:
            with ipc.new_file(out_stream, reader.schema) as writer:
                while True:
                    batch = reader.read_next_batch()
                    if batch is None:
                        break
                    writer.write_batch(batch)


def main() -> int:
    p = argparse.ArgumentParser(description="Convert GUL dataset (CSV or JSON Lines) to Arrow IPC")
    p.add_argument("input", type=Path, nargs="?", default=None, help="Input CSV/JSONL path")
    p.add_argument("-o", "--output", type=Path, default=None, help="Output .arrow path")
    p.add_argument("--batch-size", type=int, default=50_000, help="Rows per batch (JSON Lines)")
    p.add_argument("--format", choices=("auto", "csv", "jsonlines"), default="auto")
    args = p.parse_args()

    default_input = Path(r"C:\Users\Thomas\Desktop\script-automation\gul\cpp\build\Release\gul-training-dataset.csv")
    inp = args.input or default_input
    if not inp.exists():
        print(f"Input file not found: {inp}", file=sys.stderr)
        return 1

    out = args.output or inp.with_suffix(".arrow")

    fmt = args.format
    if fmt == "auto":
        fmt = detect_format(inp)
        print(f"Detected format: {fmt}", file=sys.stderr)
    print(f"Converting {inp} -> {out} ...", file=sys.stderr)
    try:
        if fmt == "jsonlines":
            jsonlines_to_arrow_stream(inp, out, batch_size=args.batch_size)
        else:
            csv_to_arrow_stream(inp, out)
    except PermissionError:
        print("Permission denied. Close the CSV file in Excel/other apps and try again.", file=sys.stderr)
        return 1
    print(f"Wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
