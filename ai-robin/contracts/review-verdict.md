# Review Verdict

The structured output of a review sub-agent (a playbook run) and the merged
aggregate output of the Merge Agent. Two related but distinct shapes.

---

## Part 1: Sub-Verdict (one playbook's output)

Written by each review sub-agent when it finishes running its playbook.
Returned to main agent as the payload of a `review_sub_verdict` dispatch-signal.

### Schema

```json
{
  "playbook_name": "string — e.g. 'code-quality', 'frontend-component', 'db-schema'",
  "playbook_version": "string — which version of the playbook was applied",
  "batch_id": "string — the batch being reviewed",
  "scope_reviewed": {
    "files": ["string — file paths actually inspected"],
    "specs": ["string — spec_ids actually inspected"],
    "skipped": [
      {
        "target": "string — file or spec_id",
        "reason": "string — why skipped (out of scope, not readable, etc.)"
      }
    ]
  },

  "status": "'pass' | 'pass_with_warnings' | 'fail'",

  "issues": [
    {
      "issue_id": "string — unique within this verdict",
      "severity": "'blocking' | 'quality' | 'advisory'",
      "category": "string — playbook-defined category (e.g. 'a11y', 'type-safety', 'naming')",
      "location": {
        "file": "string | null",
        "line_start": "integer | null",
        "line_end": "integer | null",
        "spec_id": "string | null"
      },
      "description": "string — what is wrong",
      "rationale": "string — why it matters per this playbook's rules",
      "suggested_action": "string — concrete change to address this"
    }
  ],

  "summary": "string — one-paragraph summary of overall health of reviewed scope",

  "playbook_specific_metrics": {
    "// optional; each playbook may define its own metrics": null,
    "// examples: 'coverage_percent', 'complexity_average', 'anchor_match_rate'": null
  }
}
```

### Severity definitions

These are **normative** — every playbook uses these exact levels.

| Severity | Meaning | Effect on `status` |
|---|---|---|
| `blocking` | The code is broken or violates a hard constraint | Any blocking issue → `status: fail` |
| `quality` | The code works but has problems that should be fixed | → `status: pass_with_warnings` |
| `advisory` | A suggestion or note, not a required fix | Does not change status |

A verdict with zero issues = `pass`. Quality-only issues = `pass_with_warnings`.
Any blocking = `fail`.

### Rules

1. **A playbook must categorize issues, not just describe them.** Every issue
   has a severity. If the playbook can't tell whether something is blocking or
   quality, it defaults to `quality`. Never leave it ambiguous.
2. **Rationale cites the rule, not opinion.** The playbook is a rulebook; every
   issue's rationale must point to a specific rule in that playbook. If the
   rulebook doesn't cover the case, the issue is `advisory`.
3. **Location must be specific when possible.** For code, include file + line.
   For specs, include spec_id. If neither applies (global concern), location
   fields are null but `description` must be explicit about scope.
4. **Suggested_action is concrete.** "Make this better" is not an action. "Split
   `handleCreate` into `handleCreate` + `validateCreatePayload`" is an action.
5. **Skipped targets are recorded, not silently dropped.** If the playbook was
   asked to review something it couldn't (e.g., binary file, absent file,
   out-of-playbook-scope), it goes in `scope_reviewed.skipped`.

---

## Part 2: Merged Verdict (Merge Agent's output)

Written by the Merge Agent after all sub-verdicts for a batch are in. Returned
to main agent as the payload of a `review_merged` dispatch-signal.

### Schema

```json
{
  "batch_id": "string",
  "review_iteration": "integer — 1, 2, or 3",
  "sub_verdicts_count": "integer",
  "sub_verdicts_included": ["string — playbook_names"],

  "overall_status": "'pass' | 'pass_with_warnings' | 'fail'",

  "consolidated_issues": [
    {
      "issue_id": "string — unique within merged verdict, not the sub-verdict's id",
      "severity": "'blocking' | 'quality' | 'advisory'",
      "source_playbooks": ["string — which playbooks raised this"],
      "source_issue_ids": ["string — original issue_ids from sub-verdicts"],
      "merged": "boolean — true if this consolidates multiple similar issues",
      "location": { "// same shape as sub-verdict location": null },
      "description": "string",
      "rationale": "string — if merged, may cite multiple playbook rules",
      "suggested_action": "string"
    }
  ],

  "cross_playbook_observations": [
    {
      "description": "string — an observation only visible across playbook results",
      "example": "Multiple playbooks flagged the same file for unrelated reasons, suggesting architectural issue."
    }
  ],

  "summary": "string — one-paragraph synthesis",

  "commit_ready": "boolean — always true; kernel commits regardless of status"
}
```

### Merge rules (how Merge Agent produces the above)

1. **Overall status is determined by worst sub-verdict.** Any sub-verdict with
   `fail` → overall `fail`. Any with `pass_with_warnings` (and none fail) →
   overall `pass_with_warnings`. All `pass` → overall `pass`.

2. **Consolidation.** If two sub-verdicts flag the same file:line with
   substantively similar issues, merge them. The merged issue cites all source
   playbooks. "Substantively similar" is fuzzy and autonomous — guidance in
   `review/merge/SKILL.md`.

3. **No upgrading severity during merge.** If one playbook says `quality` and
   another says `advisory` about the same thing, merged severity is `quality`
   (the higher of the two). Never upgrade beyond what any sub-verdict claimed.

4. **Cross-playbook observations are explicit.** If the merge process reveals
   something no single playbook could see (e.g., "frontend-component and
   a11y both hit `<Button>` for different reasons — suggests `<Button>`
   needs refactor"), this goes in `cross_playbook_observations`, not in
   `consolidated_issues`. Observations don't have a severity; they're guidance
   for the next Planning pass.

5. **`commit_ready` is always true.** Kernel commits verdicts regardless of
   status. This field exists for schema symmetry with other signals, not as
   a gate.

---

## Example sub-verdict

```json
{
  "playbook_name": "code-quality",
  "playbook_version": "1.0",
  "batch_id": "batch-3",
  "scope_reviewed": {
    "files": ["apps/api/src/routes/users.ts", "apps/api/src/routes/auth.ts"],
    "specs": ["contract-api-users-001", "contract-api-auth-001"],
    "skipped": []
  },
  "status": "pass_with_warnings",
  "issues": [
    {
      "issue_id": "cq-1",
      "severity": "quality",
      "category": "function-length",
      "location": {
        "file": "apps/api/src/routes/users.ts",
        "line_start": 45,
        "line_end": 134,
        "spec_id": null
      },
      "description": "handleCreate is 89 lines long.",
      "rationale": "code-quality rule §2.1: functions should be under 80 lines; splits improve testability.",
      "suggested_action": "Extract validation into validateCreatePayload(), DB logic into createUserRecord()."
    }
  ],
  "summary": "Both route files are clean. One function in users.ts is mildly over length limit; non-blocking.",
  "playbook_specific_metrics": {
    "functions_analyzed": 12,
    "average_function_length": 34
  }
}
```

## Example merged verdict

```json
{
  "batch_id": "batch-3",
  "review_iteration": 1,
  "sub_verdicts_count": 4,
  "sub_verdicts_included": ["code-quality", "backend-api", "db-schema", "test-coverage"],
  "overall_status": "fail",
  "consolidated_issues": [
    {
      "issue_id": "m-1",
      "severity": "blocking",
      "source_playbooks": ["backend-api", "db-schema"],
      "source_issue_ids": ["ba-3", "db-1"],
      "merged": true,
      "location": {
        "file": "apps/api/src/routes/users.ts",
        "line_start": 78,
        "line_end": 82,
        "spec_id": null
      },
      "description": "User creation inserts row without running email uniqueness check; schema has UNIQUE constraint, so this will throw at runtime.",
      "rationale": "backend-api rule §4.2: every constraint violation must be surfaced as typed error. db-schema rule §1.3: application code must validate against schema constraints before insert.",
      "suggested_action": "Add uniqueness check before insert, return typed EmailTakenError."
    }
  ],
  "cross_playbook_observations": [
    {
      "description": "code-quality and backend-api both flagged handleCreate for different reasons (length vs error handling). Suggests the function has grown to encompass too many responsibilities.",
      "example": "Consider whether next Planning iteration should split the user creation flow into orchestration + persistence."
    }
  ],
  "summary": "Batch 3 has one blocking issue around uniqueness validation that must be fixed. Other playbooks clean or minor warnings.",
  "commit_ready": true
}
```
