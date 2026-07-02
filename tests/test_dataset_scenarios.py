import json
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GUL_BIN = REPO_ROOT / "cpp" / "build" / "gul"
FACTS = REPO_ROOT / "examples/facts/basic_facts.json"
ATOM_SPEC = REPO_ROOT / "examples/specs/atom_role.gul.json"


@unittest.skipUnless(GUL_BIN.exists(), "native gul binary not built")
class NativeDatasetScenarioTests(unittest.TestCase):
    def test_scenario_provenance_emitted(self):
        proc = subprocess.run(
            [str(GUL_BIN), "-oneshot", "-T", "-n", "3", "--scenario", "balanced", "--seed", "42"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        lines = [json.loads(line) for line in proc.stdout.strip().splitlines() if line.strip()]
        self.assertEqual(len(lines), 3)
        for line in lines:
            self.assertIn("extensions", line)
            self.assertEqual(line["extensions"]["schema"], "gul.dataset.sample/1")
            self.assertIn("scenario", line["extensions"])
            self.assertEqual(line["extensions"]["seed"], 42)

    def test_spec_flag_links_source_spec_id(self):
        spec = REPO_ROOT / "examples/specs/basic_infer.gul.json"
        proc = subprocess.run(
            [
                str(GUL_BIN), "-oneshot", "-T", "-n", "1",
                "--scenario", "balanced", "--seed", "1",
                "--spec", str(spec),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        line = json.loads(proc.stdout.strip())
        self.assertEqual(line["extensions"]["source_spec_id"], "spec:basic_infer")

    def test_stats_flag_emits_distribution(self):
        proc = subprocess.run(
            [str(GUL_BIN), "-oneshot", "-T", "-n", "7", "--scenario", "balanced", "--stats", "--seed", "7"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        stats = json.loads(proc.stderr.strip().splitlines()[-1])
        self.assertIn("scenario_distribution", stats)
        self.assertIn("decision_distribution", stats)
        self.assertEqual(sum(stats["scenario_distribution"].values()), 7)


@unittest.skipUnless(GUL_BIN.exists(), "native gul binary not built")
class NativeAtomParityTests(unittest.TestCase):
    def test_native_atom_infer_matches_python(self):
        py = subprocess.run(
            [
                "python3", "-m", "gulcli", "infer", str(ATOM_SPEC),
                "--facts", str(FACTS), "--format", "json",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        native = subprocess.run(
            [
                str(GUL_BIN), "infer", str(ATOM_SPEC),
                "--facts", str(FACTS), "--format", "json",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        py_result = json.loads(py.stdout)
        native_result = json.loads(native.stdout)
        self.assertEqual(native_result["decision"], py_result["decision"])
        self.assertAlmostEqual(native_result["confidence"], py_result["confidence"])


if __name__ == "__main__":
    unittest.main()
