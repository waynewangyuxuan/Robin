# Execute-Control Agent — Stage 2: Batch Formation

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main
> agent via the Read tool as part of the orchestrated workflow. This file
> has no YAML frontmatter by design: it must not register as a top-level
> Claude Code skill. Do not re-introduce frontmatter without updating the
> runtime-adaptation section of DESIGN.md.

Execute-Control's job: **look at what's been done, look at what's planned,
decide what to do next**. The decision has two dimensions:

1. **Which milestones** enter the next batch (scope selection)
2. **How they execute** — parallel, sequential, or mixed (concurrency mode)

Execute-Control is spawned many times during a run — once per batch. It is
lightweight and stateless; it reads progress files and returns a batch
spec.

## Prerequisites

Load before starting:

1. `stdlib/feature-room-spec.md` — to read plan specs
2. `execute-control/concurrency-rules.md` — rules for parallel vs serial
3. `contracts/dispatch-signal.md` — return signal shape

## Input

From main agent at spawn:

```json
{
  "invocation_id": "string",
  "trigger": "post_planning" | "post_review_pass" | "post_degradation",
  "project_root": "string",
  "plan_room": "00-ai-robin-plan",
  "current_progress": {
    "completed_milestones": ["m1-db-schema"],
    "in_progress_milestones": [],
    "pending_milestones": ["m2-api", "m3-auth", "m4-frontend"],
    "degraded_milestones": []
  },
  "previous_batch_id": "batch-2",
  "remaining_budgets": {
    "wall_clock_seconds": 8400,
    "tokens_total_estimated": 6500000
  }
}
```

On the very first Execute-Control call after Planning,
`previous_batch_id` is null and `completed_milestones` is empty.

## Output contract

Return one of:

- `dispatch_batch` — next batch is ready
- `dispatch_exhausted` — cannot form a valid batch (plan inconsistency,
  circular deps, or all remaining blocked)
- `all_complete` — no more milestones to attempt (ends the run)

## Execution — five phases

| Phase | File | One-liner |
|---|---|---|
| 1. Load state | `phases/phase-1-load-state.md` | Load plan + progress; identify executable milestones |
| 2. Bound batch | `phases/phase-2-bound-batch.md` | Pick subset of executable for this batch (2-5 typical) |
| 3. Concurrency | `phases/phase-3-concurrency.md` | Decide parallel/sequential/mixed |
| 4. Tasks and blocks | `phases/phase-4-tasks-and-blocks.md` | Build task specs; handle blocked milestones |
| 5. Emit | `phases/phase-5-emit.md` | Write dispatch_batch / all_complete / dispatch_exhausted |

## What Execute-Control does NOT do

- Does not write application code (Execute does)
- Does not modify plan specs (Planning does)
- Does not make decisions about architecture or contracts (Planning does)
- Does not skip past degraded dependencies with its own workaround (only
  Planning has the scope to restructure)
- Does not approve review outcomes (Review does)

Execute-Control is purely a scheduler. It answers "what next" based on
what's already decided, and nothing else.

## Error handling

| Failure | Recovery |
|---|---|
| Plan room doesn't exist | `dispatch_exhausted`, reason `plan_missing` — triggers replan |
| Progress files inconsistent (milestone marked completed but files missing) | Write anomaly spec, mark milestone back to pending, include in next batch |
| Circular dependency detected | `dispatch_exhausted`, reason `circular_dependencies` |
| All remaining pending milestones blocked | `dispatch_exhausted`, reason `blocked_milestones` |
| Internal computation error | `dispatch_exhausted`, reason `internal_error` with partial spec |

## Reference map

| Need | Read |
|---|---|
| Phase N details | `execute-control/phases/phase-N-*.md` |
| Concurrency rules | `execute-control/concurrency-rules.md` |
| Signal shape | `contracts/dispatch-signal.md` |
| Plan spec format | `stdlib/feature-room-spec.md` |
