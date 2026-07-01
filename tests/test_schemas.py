import unittest
from pathlib import Path

from gulcli import infer_file, validate_file

from schema_validate import load_schema, validate_against_schema

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = REPO_ROOT / "examples/specs/basic_infer.gul.json"


class SchemaValidationTests(unittest.TestCase):
    def test_validation_result_matches_schema(self):
        result = validate_file(SPEC)
        schema = load_schema("gul.validation.result-1.json")
        errors = validate_against_schema(result, schema)
        self.assertEqual(errors, [], errors)

    def test_inference_result_matches_schema(self):
        result = infer_file(SPEC, include_trace=True)
        schema = load_schema("gul.inference.result-1.json")
        errors = validate_against_schema(result, schema)
        self.assertEqual(errors, [], errors)


if __name__ == "__main__":
    unittest.main()
