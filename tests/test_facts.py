import json
import unittest
from pathlib import Path

from gulcli.facts import FactEnvironment
from gulcli.runtime_io import evaluate_expr_data, infer_file, load_facts

REPO_ROOT = Path(__file__).resolve().parents[1]
FACTS = REPO_ROOT / "examples/facts/basic_facts.json"
SPEC = REPO_ROOT / "examples/specs/atom_role.gul.json"


class FactEnvironmentTests(unittest.TestCase):
    def test_load_facts_file(self):
        facts = load_facts(FACTS)
        self.assertIn("editor", facts.roles["agent:alice"])

    def test_infer_atom_spec_with_facts(self):
        facts = load_facts(FACTS)
        result = infer_file(SPEC, facts=facts)
        self.assertEqual(result["decision"], "permit")
        self.assertGreaterEqual(result["confidence"], 0.9)

    def test_infer_atom_without_facts_raises(self):
        payload = json.loads(SPEC.read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            evaluate_expr_data(payload)

    def test_has_role_missing_entity_defers(self):
        facts = FactEnvironment.from_dict({"roles": {}})
        pred = {
            "tag": "has_role",
            "agent": {"kind": "agent", "id": "bob"},
            "role": "admin",
        }
        result = facts.evaluate_predicate(pred)
        self.assertEqual(result.decision.value, "defer")


if __name__ == "__main__":
    unittest.main()
