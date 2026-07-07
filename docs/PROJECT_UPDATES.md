# Project updates

This file holds Linear-ready project updates for automation runs that cannot
reach Linear directly. The 2026-07-07 runs had no Linear MCP server, no Linear
CLI, and no `LINEAR*` credentials in the environment, so project backfills are
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

### Latest post-merge automation review

| Field | Value |
|-------|-------|
| Related merge | PR #21, `docs: add Linear-ready project update` |
| Merge commit | `0f21318ea025f26fc27e2711483a658a09775fd9` |
| Head commit | `5918a9c542129c78d1b0fbf92273ebf89994e432` |
| Merged at | `2026-07-07T08:36:20Z` |
| Automation follow-up branch | `cursor/linear-project-updates-9e25` |
| Linear action | Add this as the latest update to `GUL v2.2 runtime documentation alignment`; if the project does not exist, create it from the backfill section below first. |

PR #21 added this repo-local Linear backfill record and linked it from every
README entry point. The merge is documentation-only: it changed `README.md`,
`cpp/README.md`, `tests/golden/README.md`, `devlog.md`, and
`docs/PROJECT_UPDATES.md`, with no Python runtime, native C++, schema, fixture,
or packaging changes.

Review result:

- No runtime regression risk was found in the merge itself because the diff is
  limited to documentation and project-tracking text.
- The README links are consistent with the fallback location for Linear-ready
  updates.
- Linear still was not reachable from this automation run, so the update is
  recorded here rather than posted directly to Linear.

### Latest Linear update body

Use this as the latest project update if the Linear project already exists. If
the project does not exist, create it from the project backfill above, then add
both the PR #20 update and this PR #21 follow-up:

```markdown
PR #21 merged the repo-local Linear backfill for the GUL v2.2 runtime documentation alignment project.

What changed:
- Added `docs/PROJECT_UPDATES.md` with project create/update fields, the PR #20 merge review, completed work, suggested Linear issues, and a JSON payload for sync.
- Linked the project update ledger from the root README, C++ README, and golden fixture README.
- Recorded the fallback in `devlog.md` so future automation can see why Linear was not updated directly.

Review:
- Documentation-only merge. No Python runtime, native C++, schema, fixture output, or packaging files changed.
- README entry points now point to the same Linear-ready ledger.
- No regressions were identified from the merge review.

Verification reported by PR #21:
- `python3 -m pip install -e . && python3 -m unittest discover -s tests -v` passed with 24 tests and 6 native-binary skips.
- Every `README.md` linked to `docs/PROJECT_UPDATES.md`.
- The machine-readable JSON payload in `docs/PROJECT_UPDATES.md` parsed successfully.

Follow-up:
- Sync this update into Linear when Linear access is available to automation.
```

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
- Record the Linear backfill ledger for post-merge automation follow-ups.
- Link project update records from every repository README entry point.

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
  "latest_follow_up": {
    "pr_number": 21,
    "title": "docs: add Linear-ready project update",
    "url": "https://github.com/torakagemusha-sudo/gulcli/pull/21",
    "merge_commit": "0f21318ea025f26fc27e2711483a658a09775fd9",
    "head_commit": "5918a9c542129c78d1b0fbf92273ebf89994e432",
    "merged_at": "2026-07-07T08:36:20Z",
    "linear_action": "add_project_update_or_create_project_then_backfill",
    "fallback_reason": "No Linear MCP server, Linear CLI, or LINEAR* credentials were available in automation.",
    "completed_work": [
      "Added docs/PROJECT_UPDATES.md as the Linear-ready backfill ledger",
      "Linked the project update ledger from every README.md",
      "Recorded Linear access limits in devlog.md"
    ],
    "verification_reported": [
      "python3 -m pip install -e . && python3 -m unittest discover -s tests -v",
      "README link coverage check",
      "docs/PROJECT_UPDATES.md JSON payload parse check"
    ]
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
