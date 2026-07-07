# Golden fixtures

Byte-stable expected outputs for runtime_io validate/infer.

Project-level post-merge updates and Linear fallback records are tracked in
`../../docs/PROJECT_UPDATES.md`; this README stays limited to fixture
regeneration commands.

Regenerate after intentional output changes:

```bash
python3 -m gulcli validate examples/specs/basic_infer.gul.json --format json | python3 -m json.tool > tests/golden/basic_infer.validate.json
python3 -m gulcli infer examples/specs/basic_infer.gul.json --format json | python3 -m json.tool > tests/golden/basic_infer.infer.json
python3 -m gulcli infer examples/specs/basic_infer.gul.json --format json --trace | python3 -m json.tool > tests/golden/basic_infer.infer.trace.json
python3 -m gulcli infer examples/specs/jurisdiction_override.gul.json --format json | python3 -m json.tool > tests/golden/jurisdiction_override.infer.json
```
