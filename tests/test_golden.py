import json
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN = Path(__file__).resolve().parent / "golden"
SPEC = REPO_ROOT / "examples/specs/basic_infer.gul.json"


def run_cli(cmd: list[str], spec: Path = SPEC) -> dict:
    proc = subprocess.run(
        ["python3", "-m", "gulcli", *cmd, str(spec), "--format", "json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


class GoldenOutputTests(unittest.TestCase):
    def test_validate_matches_golden(self):
        expected = json.loads((GOLDEN / "basic_infer.validate.json").read_text(encoding="utf-8"))
        actual = run_cli(["validate"])
        self.assertEqual(actual["schema"], expected["schema"])
        self.assertEqual(actual["ok"], expected["ok"])
        self.assertEqual(actual["input_hash"], expected["input_hash"])
        self.assertEqual(actual["errors"], expected["errors"])

    def test_infer_matches_golden(self):
        expected = json.loads((GOLDEN / "basic_infer.infer.json").read_text(encoding="utf-8"))
        actual = run_cli(["infer"])
        self.assertEqual(actual["decision"], expected["decision"])
        self.assertAlmostEqual(actual["confidence"], expected["confidence"])
        self.assertEqual(actual["input_hash"], expected["input_hash"])

    def test_infer_trace_matches_golden(self):
        expected = json.loads((GOLDEN / "basic_infer.infer.trace.json").read_text(encoding="utf-8"))
        proc = subprocess.run(
            ["python3", "-m", "gulcli", "infer", str(SPEC), "--format", "json", "--trace"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        actual = json.loads(proc.stdout)
        self.assertEqual(len(actual["trace"]), len(expected["trace"]))
        self.assertEqual(actual["decision"], expected["decision"])

    def test_jurisdiction_override_infer(self):
        spec = REPO_ROOT / "examples/specs/jurisdiction_override.gul.json"
        expected = json.loads((GOLDEN / "jurisdiction_override.infer.json").read_text(encoding="utf-8"))
        actual = run_cli(["infer"], spec=spec)
        self.assertEqual(actual["decision"], expected["decision"])
        self.assertAlmostEqual(actual["confidence"], expected["confidence"])


if __name__ == "__main__":
    unittest.main()
