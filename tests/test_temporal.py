import json
import unittest
from pathlib import Path

from gulcli.runtime_io import evaluate_expr_data, infer_file

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = REPO_ROOT / "examples/specs/temporal_always.gul.json"


class TemporalTraceTests(unittest.TestCase):
    def test_always_trace_metadata(self):
        payload = json.loads(SPEC.read_text(encoding="utf-8"))
        result = evaluate_expr_data(payload, include_trace=True)
        self.assertEqual(result["decision"], "permit")
        rules = [step["rule"] for step in result["trace"]]
        self.assertIn("ALWAYS", rules)
        always_step = next(step for step in result["trace"] if step["rule"] == "ALWAYS")
        self.assertEqual(always_step["metadata"]["temporal"], "always")
        self.assertEqual(always_step["metadata"]["approximation"], "structural")

    def test_until_trace_metadata(self):
        payload = {
            "tag": "until",
            "p1": {"tag": "decision", "decision": "permit", "confidence": 0.8},
            "p2": {"tag": "decision", "decision": "deny", "confidence": 0.7},
        }
        result = evaluate_expr_data(payload, include_trace=True)
        rules = [step["rule"] for step in result["trace"]]
        self.assertIn("SEQ", rules)
        self.assertIn("UNTIL", rules)
        until_step = next(step for step in result["trace"] if step["rule"] == "UNTIL")
        self.assertEqual(until_step["metadata"]["temporal"], "until")

    def test_temporal_spec_file(self):
        result = infer_file(SPEC, include_trace=True)
        self.assertTrue(result["trace"])


if __name__ == "__main__":
    unittest.main()
