---
name: robin-executor
description: AI-Robin Executor stage. Given a single task (typically one milestone), loads relevant context, writes/modifies code and specs, and returns a structured artifacts summary. Does NOT git commit (kernel delegates that to Committer).
---

# Executor Agent — Stage 3: Actual Work

Execute Agent is where **application code gets written**. One invocation =
one task = typically one milestone. Multiple Execute Agents run in parallel
within a batch (per Scheduler's dispatch).

Execute Agents are stateless: each invocation loads its scope's context
fresh, produces artifacts, and exits. They do not see each other's work.

## Prerequisites

Load before starting:

1. `stdlib/feature-room-spec.md` — spec format (reading contracts, writing change specs)
2. `stdlib/anchor-tracking.md` — how to update anchor references as code changes
3. `skills/robin-executor/context-pulling.md` — rules for loading only relevant context
4. `skills/robin-executor/commit-preparation.md` — how to prepare the change artifact
5. `contracts/dispatch-signal.md` — return signal shape

## Input

From main agent at spawn:

```json
{
  "invocation_id": "string",
  "task": {
    "task_id": "batch-3-task-1",
    "scope": {
      "room": "02-api",
      "milestone": "m2-api",
      "files_or_specs": ["src/routes/**", "src/schemas/user.ts"]
    },
    "context_refs": [
      "intent-api-001",
      "contract-api-users-001",
      "decision-api-framework-001",
      "convention-project-001"
    ],
    "depends_on_tasks": []
  },
  "project_root": "string",
  "batch_id": "batch-3",
  "retry_note": "optional — if this is a retry, what was wrong last time"
}
```

## Output contract

Return one of:

- `execute_complete` — task finished, artifacts ready for review
- `execute_failed` — fundamental blocker prevented completion

Primary artifacts:
- Source code files in the scope
- Updated spec anchors (when code changes affect anchored locations)
- A `change-*.yaml` spec recording this execution

**Note**: Execute Agent does NOT run `git commit`. The kernel does that
after the review stage. Execute just writes files to the working tree.

## Execution — five phases

| Phase | File | One-liner |
|---|---|---|
| 1. Context pull | `phases/phase-1-context.md` | Load specs, build mental model of intent/contracts/decisions/conventions/constraints |
| 2. Implement | `phases/phase-2-implement.md` | Plan changes internally, then write code following contracts strictly |
| 3. Anchors | `phases/phase-3-anchors.md` | Update spec anchors to stay aligned with code |
| 4. Self-check + change spec | `phases/phase-4-selfcheck-change.md` | Verify compile/contracts/scope/tests; write change-*.yaml |
| 5. Emit | `phases/phase-5-emit.md` | Write execute_complete or execute_failed signal |

## What you absolutely do not do

- **Do not run `git commit` or `git push`.** Kernel does that after Review.
- **Do not mark milestones `completed`.** Review does that. You set
  `in_progress` only.
- **Do not look at other Execute Agents' in-progress work.** Isolation
  rule.
- **Do not silently modify contracts.** If a contract seems wrong,
  return `execute_failed` with `reason: "contract_needs_revision"`.
- **Do not expand scope.** If you need to change files outside
  `scope.files_or_specs`, return `execute_failed` with
  `reason: "scope_insufficient"`.
- **Do not second-guess your own code quality and return `execute_failed`
  over it.** That's Review's job. Write it, note concerns in
  `known_issues`, move on.

## Relationship to Feature Room's commit-sync

Feature Room's `commit-sync` skill has 6 phases. Execute Agent implements
a subset of them:

| commit-sync phase | Done where in Execute |
|---|---|
| 1. Change analysis + Room classification | Implicit — your scope is in the task |
| 2. Anchor tracking | Phase 3 |
| 3. Draft → active detection | Not applicable (no drafts at Execute stage) |
| 4. Cross-room conflict detection | Review's job, not Execute's |
| 5. User confirmation | No user; replaced by Execute's self-check |
| 6. File updates + git commit/push | **Only file updates here.** Git is kernel's job post-Review. |

Execute ≈ "commit-sync Phases 1-2 + self-assessment, without Phase 5/6".

## Error handling

| Failure | Recovery |
|---|---|
| Cannot read required context spec | `execute_failed`, reason `missing_context` |
| Code won't compile/parse | Fix if possible in scope; else `execute_failed`, reason `compile_error` |
| Tests fail | Fix code or tests; if can't resolve, include in `known_issues` and return complete |
| Scope too large for one invocation | `execute_failed`, reason `scope_too_large` — Planning decomposes |
| Tool (compiler, formatter) missing | `execute_failed`, reason `environment_blocker` |

## Reference map

| Need | Read |
|---|---|
| Phase N details | `skills/robin-executor/phases/phase-N-*.md` |
| Context pulling rules | `skills/robin-executor/context-pulling.md` |
| Change spec format | `skills/robin-executor/commit-preparation.md` |
| Anchor tracking methodology | `stdlib/anchor-tracking.md` |
| Signal shape | `contracts/dispatch-signal.md` |
