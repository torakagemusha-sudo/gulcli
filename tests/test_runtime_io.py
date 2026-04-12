import json
import tempfile
import unittest
from pathlib import Path

from gulcli.runtime_io import validate_spec_data, evaluate_expr_data, validate_file, infer_file


class RuntimeIOTests(unittest.TestCase):
    def test_validate_decision_node(self):
        payload = {"tag": "decision", "decision": "permit", "confidence": 0.9, "evidence": ["ok"]}
        result = validate_spec_data(payload)
        self.assertTrue(result["ok"])
        self.assertEqual(result["schema"], "gul.validation.result/1")

    def test_validate_rejects_bad_confidence(self):
        payload = {"tag": "decision", "decision": "permit", "confidence": 1.2}
        result = validate_spec_data(payload)
        self.assertFalse(result["ok"])
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("E_CONF_RANGE", codes)

    def test_infer_and_threshold(self):
        payload = {
            "tag": "threshold",
            "threshold": 0.7,
            "p": {
                "tag": "and_",
                "p1": {"tag": "decision", "decision": "permit", "confidence": 0.9, "evidence": ["role ok"]},
                "p2": {"tag": "decision", "decision": "permit", "confidence": 0.8, "evidence": ["context ok"]},
            },
        }
        result = evaluate_expr_data(payload, include_trace=True)
        self.assertEqual(result["decision"], "permit")
        self.assertAlmostEqual(result["confidence"], 0.8)
        self.assertTrue(result["trace"])

    def test_infer_override(self):
        payload = {
            "tag": "override",
            "base": {"tag": "decision", "decision": "deny", "confidence": 0.6},
            "override": {"tag": "decision", "decision": "permit", "confidence": 0.8},
        }
        result = evaluate_expr_data(payload)
        self.assertEqual(result["decision"], "permit")

    def test_file_roundtrip(self):
        payload = {
            "expr": {
                "tag": "parallel",
                "p1": {"tag": "decision", "decision": "permit", "confidence": 0.4},
                "p2": {"tag": "decision", "decision": "permit", "confidence": 0.5},
            }
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "spec.gul.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            validation = validate_file(path)
            inference = infer_file(path)
        self.assertTrue(validation["ok"])
        self.assertEqual(inference["decision"], "permit")
        self.assertGreater(inference["confidence"], 0.5)


if __name__ == "__main__":
    unittest.main()
