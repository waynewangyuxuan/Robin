# Concurrency Rules

The rules Scheduler uses when deciding concurrency mode for a
batch. Used in Phase 3.

These rules operationalize the parallelism annotations Planning wrote
(per `skills/robin-planner/parallelism-identification.md`). Where Planning
identified what CAN parallelize, Scheduler decides what WILL
parallelize in this specific batch.

---

## The rule hierarchy

When deciding how tasks in a batch execute relative to each other, walk
these rules in order. The first rule that applies determines the
concurrency mode for that pair of tasks.

### Rule 1: Explicit `serial_with` annotation

Planning marked two milestones `serial_with` each other → cannot be in
the same batch, or if in the same batch, must be `sequential` mode with
the earlier task completing first.

**Preferred action**: put them in different batches. If they must be in
the same batch (e.g., dependency structure forces it), use `sequential`
mode with explicit `depends_on_tasks`.

### Rule 2: Strict `depends_on` relationship

Task B has `depends_on: [A]` in the plan → A must complete before B
starts.

If both are in the same batch: `sequential` or `mixed` mode with
`depends_on_tasks: [A's task_id]` on B's task.

If A is in a previous (completed) batch: B can run freely in this
batch.

### Rule 3: File-path overlap

Two tasks' `scope.files_or_specs` patterns have any overlapping file
path → cannot run in parallel.

Computing overlap:
- Exact file path in both → overlap
- One task: `src/routes/**`; other task: `src/routes/users/create.ts` →
  overlap (second is within first)
- Task A: `src/routes/users/**`; task B: `src/routes/posts/**` → no
  overlap

**Action**: `sequential` or `mixed` — either split into separate
batches, or serialize within this batch.

### Rule 4: Shared interface layer

Two tasks both touch a shared-interface directory (e.g.,
`packages/shared/src/`) → serialize per single-writer rule, even if
they touch different files within it.

The shared-interface directory is defined by:
- `convention-*.yaml` specs marking directories as shared-interface
- Common conventions: `packages/shared/`, `types/`, `schemas/`,
  `lib/shared/`

If any of the project's `convention-*.yaml` specs calls out a
shared-interface directory and both tasks have paths matching, they
serialize.

### Rule 5: Schema / migration layer

Migrations, schema files, and data-model files have implicit
single-writer rule even if no `convention-*.yaml` spells it out:

- Files matching `**/migrations/**`
- Files matching `**/schema.{sql,prisma,graphql}`
- Files matching `prisma/schema.prisma`

Two tasks touching these → serialize.

### Rule 6: Otherwise, parallel

If none of Rules 1-5 apply, the pair is parallel-safe.

---

## Determining batch-level `concurrency_mode`

After applying the rules above to every pair of tasks in the batch,
you have a pairwise relationship set. Choose batch-level mode:

### `parallel`

All pairs are parallel-safe (no rules triggered).

This is the ideal case. All tasks run simultaneously as separate Execute
Agent invocations.

### `sequential`

Every pair requires serialization, OR the batch is size 1.

Single-size batches are technically "parallel" (no one to parallelize
with) but we use `sequential` for clarity — it means there's a linear
order.

### `mixed`

Some pairs are parallel-safe, some require serialization. This creates
a DAG:

- Independent groups run in parallel
- Serial chains within the DAG

Encode as:
- Each task has `depends_on_tasks: [task_ids]` listing which tasks
  must complete before it starts
- Parallel tasks have empty `depends_on_tasks`
- Serial tasks have the previous task's id

Example mixed batch of 3 tasks:

- Task 1: no dependencies, parallel-safe with Task 2
- Task 2: no dependencies, parallel-safe with Task 1
- Task 3: depends on both Task 1 and Task 2

```json
{
  "concurrency_mode": "mixed",
  "tasks": [
    {"task_id": "batch-3-task-1", "depends_on_tasks": []},
    {"task_id": "batch-3-task-2", "depends_on_tasks": []},
    {"task_id": "batch-3-task-3",
     "depends_on_tasks": ["batch-3-task-1", "batch-3-task-2"]}
  ]
}
```

Main agent spawns 1 and 2 in parallel, waits for both, then spawns 3.

---

## How to check the rules efficiently

For each pair of tasks (A, B) in the selected batch:

```
def analyze_pair(A, B):
  # Rule 1
  if milestone(A) in milestone(B).serial_with:
    return "serial"

  # Rule 2
  if milestone(A) in milestone(B).depends_on:
    return "serial_with_order"  # A before B
  if milestone(B) in milestone(A).depends_on:
    return "serial_with_order"  # B before A

  # Rule 3
  if any_file_overlap(A.scope, B.scope):
    return "serial"

  # Rule 4
  if touches_shared_interface(A) and touches_shared_interface(B):
    return "serial"

  # Rule 5
  if touches_schema_layer(A) and touches_schema_layer(B):
    return "serial"

  # Rule 6
  return "parallel"
```

Collect pairwise results. If all are parallel → `concurrency_mode:
parallel`. If all are serial → `sequential`. Mixed → `mixed` with DAG.

---

## Sanity checks on the result

Before emitting:

### The DAG must be acyclic

If any cycle exists in `depends_on_tasks`, there's a planning bug.
Return `dispatch_exhausted` with reason `circular_dependencies`.

### Serial chains shouldn't be too long within one batch

A batch with 5 sequential tasks is fine. A batch with 20 sequential
tasks is a smell — something's wrong with milestone granularity or
the batch is too large.

If you find a very long serial chain, consider splitting into multiple
batches instead.

### Parallel width shouldn't exceed reasonable limits

A batch of 10 parallel tasks is unusual. Consider whether:
- Scheduler's budget-aware batching (Phase 2) over-sized this
  batch
- The milestones are too finely granular and should be combined

Reasonable parallel width: 2-5. Edge cases can go to 7-8.

---

## Special cases

### Single-task batch

Trivially `sequential` (nothing to parallelize). No
`depends_on_tasks` needed.

### Empty batch

Shouldn't happen — Scheduler Phase 2 picks at least one
milestone or returns `all_complete` / `dispatch_exhausted`. If you're
here with zero tasks, something's wrong.

### All tasks have the same scope

If every task is in the same Room with overlapping scopes, Planning
probably wrote one milestone where multiple belonged. Return
`dispatch_exhausted` with reason `scope_ambiguity` and let Planning
re-examine.

---

## Rationale output

Every `dispatch_batch` signal includes a `rationale` string. It
should explain the concurrency decisions:

Example:

> "Batch 3 selected milestones m2 (api-users), m3 (api-auth), m4
> (frontend-login).
>
> Pairwise analysis:
> - (m2, m3): both touch `src/routes/**` but at non-overlapping paths
>   (users vs auth). No shared-interface overlap. Parallel-safe.
> - (m2, m4): m4 consumes the API contract m2 implements. m4 must
>   wait for m2 commit. Serial with dependency.
> - (m3, m4): similar — m4 consumes m3's auth API. Serial with
>   dependency.
>
> Result: mixed mode. Parallel group {m2, m3}, then sequential m4
> depending on both."

The rationale goes into the ledger for audit and debugging.

---

## Anti-patterns

### Defaulting to sequential "for safety"

This defeats the whole point of multiple Execute Agents. Require a
specific Rule 1-5 match to serialize.

### Letting Planning's `parallel_safe_with` override Rules 3-5

If Planning annotated "parallel-safe" but the tasks have file overlap,
the file overlap wins. Planning's annotation is a hint; the rules are
authoritative.

### Ignoring Planning's `serial_with`

Don't second-guess Planning's explicit serial annotation. If it's
there, honor it.

### Large parallel batches with no thought

A 10-task parallel batch places 10 simultaneous Execute Agents; that's
10x token consumption at once. Consider whether the batch should be
smaller.

---

## Future: platform-specific concurrency limits

The runtime platform may cap max parallel sub-agents. If so, batch size
and mode should respect the cap. For now, AI-Robin assumes no hard
platform cap; Scheduler self-limits via batch-size rules in
Phase 2.

If such a cap exists in your deployment, add it as a constraint to
Phase 2's batch sizing.
