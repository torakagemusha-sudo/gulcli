from __future__ import annotations

from pathlib import Path

from gulcli.runtime_io import infer_file, validate_file


SPEC = Path("examples/specs/basic_infer.gul.json")


def main() -> None:
    validation = validate_file(SPEC)
    print("validation ok:", validation["ok"])
    print("input hash:", validation["input_hash"])

    result = infer_file(SPEC, include_trace=True)
    print("decision:", result["decision"])
    print("confidence:", f"{result['confidence']:.4f}")
    print("trace steps:", len(result["trace"]))


if __name__ == "__main__":
    main()
