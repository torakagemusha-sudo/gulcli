# Project updates

This file holds Linear-ready project updates for automation runs that cannot
reach Linear directly. The 2026-07-07 run had no Linear MCP server, no Linear
CLI, and no `LINEAR*` credentials in the environment, so the project backfill is
recorded here for manual sync.

## GUL v2.2 runtime documentation alignment

### Linear project backfill

| Field | Value |
|-------|-------|
| Suggested project name | `GUL v2.2 runtime documentation alignment` |
| Suggested status | Completed, pending Linear sync |
| Repository | `torakagemusha-sudo/gulcli` |
| Related merge | PR #20, `docs: refresh runtime and fact environment guidance` |
| Merge commit | `1471c00653224a5e51e29a8763f361589bf2acf6` |
| Merged at | `2026-07-07T07:41:16Z` |
| Related release track | v2.2.0 documentation closure |
| Release spec mapping | WP-02 `infer`, WP-04 dataset generation, WP-06 documentation and examples |
| Primary docs | `README.md`, `docs/runtime_usage.md` |
| Supporting docs | `devlog.md`, `cpp/README.md`, `docs/release_notes/RELEASE_SPEC_v2_2_0.md` |

### Review of the merged change

PR #20 was a documentation-only merge. It refreshed runtime guidance after the
v2.2.0 implementation work landed, with no Python or C++ runtime code changes.

Completed work:

- Replaced stale native placeholder guidance with the current Python and C++
  file-backed `validate` / `infer` boundary.
- Documented fact-backed `atom` evaluation with `--facts` for Python and native
  infer paths.
- Added fact JSON key guidance for `roles`, `attributes`, `belongs_to`,
  `in_context`, `custom`, and `now`.
- Updated dataset generation docs for `--scenario`, `--spec`, `--stats`, and
  provenance under `extensions`.
- Clarified `cli_bridge.py` fallback behavior and the current lack of Python
  bridge exposure for native scenario/spec/stats dataset flags.

Review result:

- No runtime regression risk was found in the merge itself because the diff is
  limited to documentation and devlog text.
- The update aligns with the v2.2.0 release spec requirement that public docs
  describe only shipped behavior.
- No linked Linear project or issue ID was discoverable from the repository
  contents or PR metadata available in this run.

### Linear update body

Use this as the first project update if the Linear project is created during
backfill, or as the latest update if the project already exists:

```markdown
PR #20 merged the runtime documentation refresh for GUL v2.2.0.

What changed:
- README and runtime docs now describe the shipped Python/native validate and infer paths.
- Fact-backed atom evaluation is documented for both Python and native infer with `--facts`.
- Dataset generation docs now include scenario selection, spec linkage, stats, and provenance fields.
- CLI bridge limits are explicit, including native-first fallback behavior and missing scenario/spec/stats bridge flags.

Review:
- Documentation-only merge. No Python or C++ runtime files changed.
- No regressions were identified from the merge review.
- This closes the docs alignment portion of the v2.2.0 runtime surface after implementation landed.

Verification from PR #20:
- `python3 -m gulcli infer examples/specs/atom_role.gul.json --facts examples/facts/basic_facts.json --format json --trace`
- `cpp/build/gul infer examples/specs/atom_role.gul.json --facts examples/facts/basic_facts.json --format json`
- `cpp/build/gul -oneshot -T -n 3 --scenario balanced --seed 42 --stats`
- `python3 -m unittest discover -s tests -v` passed with 24 tests.

Follow-up:
- Sync this project record into Linear when Linear access is available to automation.
```

### Suggested completed Linear issues

- Document Python and native runtime boundaries for `validate` and `infer`.
- Document fact environment requirements for executable `atom` predicates.
- Document native scenario dataset flags and provenance fields.
- Clarify CLI bridge fallback and flag exposure limits.

### Machine-readable payload

```json
{
  "project": {
    "name": "GUL v2.2 runtime documentation alignment",
    "status": "completed_pending_linear_sync",
    "repository": "torakagemusha-sudo/gulcli",
    "release_track": "v2.2.0 documentation closure",
    "release_spec_mapping": ["WP-02", "WP-04", "WP-06"]
  },
  "merge": {
    "pr_number": 20,
    "title": "docs: refresh runtime and fact environment guidance",
    "url": "https://github.com/torakagemusha-sudo/gulcli/pull/20",
    "merge_commit": "1471c00653224a5e51e29a8763f361589bf2acf6",
    "merged_at": "2026-07-07T07:41:16Z"
  },
  "linear_access": {
    "available_in_automation": false,
    "fallback": "docs/PROJECT_UPDATES.md"
  },
  "completed_work": [
    "Updated runtime documentation for Python and native validate/infer",
    "Documented fact-backed atom inference",
    "Documented scenario dataset flags and provenance",
    "Clarified cli_bridge fallback and dataset flag limits"
  ],
  "verification_from_merge": [
    "python3 -m gulcli infer examples/specs/atom_role.gul.json --facts examples/facts/basic_facts.json --format json --trace",
    "cpp/build/gul infer examples/specs/atom_role.gul.json --facts examples/facts/basic_facts.json --format json",
    "cpp/build/gul -oneshot -T -n 3 --scenario balanced --seed 42 --stats",
    "python3 -m unittest discover -s tests -v"
  ]
}
```
