import json
import shutil
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GUL_BIN = REPO_ROOT / "cpp" / "build" / "gul"
SPEC = REPO_ROOT / "examples/specs/basic_infer.gul.json"


@unittest.skipUnless(GUL_BIN.exists(), "native gul binary not built")
class NativeParityTests(unittest.TestCase):
    def test_native_validate_matches_python(self):
        py = subprocess.run(
            ["python3", "-m", "gulcli", "validate", str(SPEC), "--format", "json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        native = subprocess.run(
            [str(GUL_BIN), "validate", str(SPEC), "--format", "json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        py_result = json.loads(py.stdout)
        native_result = json.loads(native.stdout)
        self.assertEqual(native_result["ok"], py_result["ok"])
        self.assertEqual(native_result["input_hash"], py_result["input_hash"])
        self.assertEqual(native_result["schema"], py_result["schema"])

    def test_native_infer_matches_python(self):
        py = subprocess.run(
            ["python3", "-m", "gulcli", "infer", str(SPEC), "--format", "json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        native = subprocess.run(
            [str(GUL_BIN), "infer", str(SPEC), "--format", "json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        py_result = json.loads(py.stdout)
        native_result = json.loads(native.stdout)
        self.assertEqual(native_result["decision"], py_result["decision"])
        self.assertAlmostEqual(native_result["confidence"], py_result["confidence"])
        self.assertEqual(native_result["input_hash"], py_result["input_hash"])


if __name__ == "__main__":
    unittest.main()
