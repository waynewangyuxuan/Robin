# Merge Phase 4: Write summary and emit

**Autonomy: guided** (summary); **explicit** (emit)

## Write the summary

One-paragraph synthesis. Should answer:

- What was reviewed (batch + scope + playbook count)
- Overall health (pass, warning-level, or fail)
- Biggest concerns if any
- What the next step will be, implied by the status

### Example: fail

> "Batch 3 reviewed by 4 playbooks covering API routes, database,
> code quality, and test coverage. Overall status: FAIL due to 2
> blocking issues — missing uniqueness validation in user creation
> (flagged by both backend-api and db-schema) and unsafe raw SQL
> construction in migration file. 3 quality warnings also present,
> non-blocking. Replan recommended to address the uniqueness issue
> systematically; the raw SQL issue is local to the migration file
> and can be fixed inline during rework."

### Example: pass

> "Batch 5 reviewed by 3 playbooks covering frontend components,
> accessibility, and code quality. All playbooks passed. One
> advisory note about test coverage for the new LoginForm component;
> not blocking. Batch ready for commit and downstream dispatch."

## Set `commit_ready`

Always `true`. The kernel commits every merged verdict regardless of
pass/fail. This field exists for schema symmetry with other signals,
not as a gate.

## Emit `review_merged`

Write the return signal to `.ai-robin/dispatch/inbox/`.

Full payload:

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
      "location": {"file": "apps/api/src/routes/users.ts", "line_start": 78, "line_end": 82, "spec_id": null},
      "description": "User creation inserts row without running email uniqueness check; schema has UNIQUE constraint, so this will throw at runtime.",
      "rationale": "backend-api §4.2: every constraint violation must be surfaced as typed error. db-schema §1.3: application code must validate against schema constraints before insert.",
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

## Signal file format

`signal_id` format: `review-merged-{batch_id}-{YYYYMMDDTHHMMSS}-{8-hex}`

See `contracts/dispatch-signal.md` for full wrapping schema.

## After emitting

Your work is done. Main agent picks up the signal, performs the
hard-rule commit (regardless of pass/fail), then routes:

- `pass` / `pass_with_warnings` → Execute-Control for next batch
- `fail` + budget remaining → Planning for replan
- `fail` + budget exhausted → degrade

Your invocation terminates after writing the signal file.
