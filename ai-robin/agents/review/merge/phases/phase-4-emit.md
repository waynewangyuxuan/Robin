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

## Compose `commit_message`

**Autonomy: guided** (content); **explicit** (format).

The kernel uses `payload.commit_message` verbatim as the git commit
message. You are the authoritative producer — the kernel does NOT
synthesize its own. Write a message that a human reviewer scanning
`git log` can understand without reading the code.

### Format

Conventional-Commits-style header + body, separated by a blank line:

```
<type>(<scope>): <short description> (batch-<N>)

Review: <overall_status> (iteration <N>)
<one-or-two-line summary of key findings>

Milestones: <m1-id>, <m2-id>, ...
Playbooks run: <playbook_1>, <playbook_2>, ...
```

- `<type>`: infer from the batch's change specs. Common values:
  `feat` (new functionality), `fix` (bug fix), `refactor`, `test`,
  `docs`, `chore`. If the batch is heterogeneous, use `feat`.
- `<scope>`: the primary room affected (e.g., `api`, `db`, `frontend`).
  If the batch spans rooms, pick the room with the most milestones.
- `<short description>`: one clause describing what the batch produced.
  Draw from milestone names or from `consolidated_issues`.
- `<N>`: `batch_id` suffix.
- Body: mirror `summary` but formatted for git log readability.

**Header exception for failed/anomaly iterations.** When
`overall_status: fail` or the anomaly-fallback path fires, use this
alternative header shape instead of the `<type>(<scope>): ... (batch-<N>)`
template above:

```
review(failed): batch-<N> iteration <N> — <short description>
review(anomaly): batch-<N> — <short description>
```

The `review(failed)` / `review(anomaly)` types encode batch and iteration
directly in the header, so do NOT append a trailing `(batch-<N>)` suffix
as well. This keeps failed-attempt commits greppable via
`git log --grep='^review('` and visually distinct from the normal
feature-style headers of successful batches.

### Three concrete examples

**Pass**:
```
feat(api): implement user CRUD endpoints (batch-3)

Review: pass (iteration 1)
All 3 playbooks clean. No issues flagged.

Milestones: m2-api-endpoints, m3-auth-middleware
Playbooks run: code-quality, backend-api, test-coverage
```

**Pass with warnings**:
```
feat(api): implement user CRUD endpoints (batch-3)

Review: pass_with_warnings (iteration 1)
1 quality warning on function length, non-blocking.

Milestones: m2-api-endpoints, m3-auth-middleware
Playbooks run: code-quality, backend-api, test-coverage
```

**Fail** (kernel still commits the failed attempt per hard rule):
```
review(failed): batch-3 iteration 1 — uniqueness check missing

Review: fail (iteration 1)
1 blocking issue: user creation inserts without email uniqueness check.
backend-api and db-schema both flagged; replan will follow.

Milestones: m2-api-endpoints, m3-auth-middleware
Playbooks run: code-quality, backend-api, db-schema, test-coverage
```

Note the `review(failed):` type for failed iterations — this distinguishes
failed-attempt commits from successful ones in `git log`.

### When commit_message cannot be composed

If `sub_verdicts` is empty (zero playbooks returned) or all sub-verdicts
were malformed, produce a fallback message:

```
review(anomaly): batch-<N> — merge produced no verdict

Review: fail (iteration <N>)
Merge could not synthesize a verdict from the returned sub-verdicts.
See ledger for the anomaly entry.
```

Emit as `overall_status: fail` with the fallback `commit_message` so the
kernel's hard-commit rule can still execute deterministically.

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
  "commit_message": "review(failed): batch-3 iteration 1 — uniqueness check missing\n\nReview: fail (iteration 1)\n1 blocking issue: user creation inserts without email uniqueness check.\nbackend-api and db-schema both flagged; replan will follow.\n\nMilestones: m2-api-endpoints, m3-auth-middleware\nPlaybooks run: code-quality, backend-api, db-schema, test-coverage",
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
