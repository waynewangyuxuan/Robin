# Stage State

A single JSON file representing "where is this run right now". This is the
kernel's working memory, persisted to disk so the run is resumable.

**Written to**: `.ai-robin/stage-state.json`
**Written by**: main agent only, at every stage transition and every spawn
**Read by**: main agent at the start of every turn

Unlike the ledger (append-only history), stage-state is **mutable** — it's
overwritten on each update. It represents the *current* state; history lives
in the ledger.

---

## Schema

```json
{
  "schema_version": "string — e.g. '1.0'",
  "run_id": "string — unique id for this AI-Robin run",
  "project_root": "string — absolute path to the project being built",

  "current_stage": "'intake' | 'planning' | 'execute-control' | 'execute' | 'review' | 'done'",

  "stage_iterations": {
    "intake": "integer — usually 1",
    "planning": "integer — incremented each time we return to planning",
    "execute_control": "integer — incremented per batch",
    "execute": "integer — incremented per batch",
    "review": "integer — incremented per batch per re-review"
  },

  "active_invocations": [
    {
      "invocation_id": "string",
      "sub_agent": "string",
      "stage": "string",
      "spawned_at": "ISO 8601",
      "expected_return_signal_types": ["string — what signal types would complete this invocation"]
    }
  ],

  "current_batch": {
    "batch_id": "string | null — null if no batch is in flight",
    "milestone_ids": ["string"],
    "tasks": [
      {
        "task_id": "string — matches dispatch_batch payload",
        "status": "'dispatched' | 'complete' | 'failed'",
        "settled_at": "ISO 8601 | null — timestamp when status became complete or failed"
      }
    ],
    "failed_tasks": ["string — denormalized view of failed tasks in tasks[]; equal to {t.task_id : t.status == 'failed'}; see Invariants"],
    "review_iteration": "integer — 1, 2, or 3 — only meaningful when reviewing this batch",
    "status": "'dispatching' | 'executing' | 'reviewing' | 'committed' | null"
  },

  "plan_pointer": {
    "plan_room": "string — where the current plan lives",
    "completed_milestones": ["string"],
    "in_progress_milestones": ["string"],
    "pending_milestones": ["string"],
    "degraded_milestones": ["string — milestones where degradation was triggered"]
  },

  "run_started_at": "ISO 8601",
  "last_updated_at": "ISO 8601",
  "last_ledger_entry_id": "integer — the highest entry_id written; kernel uses this to compute next entry_id"
}
```

---

## Key fields explained

### `current_stage`
The single word that tells the kernel which dispatch branch applies this turn.
The special value `"done"` means the run has ended; the kernel should exit the
loop.

### `stage_iterations`
Counters. Used to check against iteration budgets. For example, if
`stage_iterations.planning == 3` and the replan budget is 3, the next replan
request triggers degradation instead of a 4th planning.

### `active_invocations`
Sub-agents currently running. When a signal comes in, the kernel matches it
against this list by `invocation_id` to verify the signal is expected (defends
against stray signals).

When `active_invocations` is empty AND no signal is in inbox, the run is idle —
this is normal only if `current_stage` is `"done"`. Otherwise it's an anomaly
(see `stdlib/kernel-discipline.md`).

### `current_batch`
Only meaningful during Execute → Review cycles. Tracks which batch of tasks is
currently being executed and its review iteration count.

**`tasks[]`** mirrors the `dispatch_batch` signal: one entry per task the batch
dispatched, identified by `task_id`. Each entry's `status` moves from
`dispatched` → (`complete` | `failed`) exactly once, at which point `settled_at`
is stamped. A task in `dispatched` state always has `settled_at: null`.

**`failed_tasks[]`** is a denormalized lookup view — the list of `task_id`s
whose `tasks[]` entry is `status: "failed"`. The kernel MUST keep it in sync
(see canonical sequence in Invariants). It exists so routing decisions that
only care about the failure set can check one field instead of filtering
`tasks[]`.

A batch is **settled** when every entry in `tasks[]` has `status != "dispatched"`.
Settlement triggers the batch-settled rule (see SKILL.md) exactly once.

When a batch completes review (pass or budget-exhausted fail), `current_batch`
either advances to the next batch (set to a new batch_id, new tasks[],
`failed_tasks: []`) or clears to null (if Execute-Control is about to
determine the next batch).

### `plan_pointer`
A lightweight index into the plan artifacts stored in the project's Feature
Room. The actual plan content lives in spec yaml files in the plan_room; this
field only tells the kernel "where to look" and "what's done".

---

## Invariants

- `stage_iterations[current_stage]` >= 1 (we must have entered the stage to be
  in it)
- If `current_batch.batch_id` is not null, `current_batch.status` must not be
  null
- If `current_batch.batch_id` is not null, `current_batch.tasks[]` must contain
  one entry per task in the latest `dispatch_batch` signal (same task_ids)
- `current_batch.tasks` cannot contain two entries with the same `task_id`
- `current_batch.failed_tasks` cannot contain duplicate `task_id`s
- `current_batch.failed_tasks` = `{t.task_id for t in current_batch.tasks if t.status == "failed"}`
  (equality, not subset — the denormalized view must stay in sync with `tasks[]`)
- For every `t` in `current_batch.tasks`: `t.settled_at` is `null` iff
  `t.status == "dispatched"` (both null or both non-null, never mixed)
- A batch is **settled** iff every entry in `current_batch.tasks[]` has
  `status != "dispatched"`. The batch-settled rule (see SKILL.md) fires exactly
  once per batch, at the first turn after settlement
- `last_ledger_entry_id` must match the actual last entry_id in ledger.jsonl
  (if they diverge, kernel re-reads the ledger's last line to reconcile and
  writes an `anomaly` entry)
- `active_invocations` cannot contain two entries with the same `invocation_id`

### Canonical update sequence

When routing `execute_complete` for task `T`:
1. Find entry `t` in `current_batch.tasks` with `t.task_id == T`
2. Set `t.status = "complete"`, `t.settled_at = now()`
3. No change to `failed_tasks`

When routing `execute_failed` for task `T`:
1. Find entry `t` in `current_batch.tasks` with `t.task_id == T`
2. Set `t.status = "failed"`, `t.settled_at = now()`
3. Append `T` to `current_batch.failed_tasks` (guard against duplicates)

Both sequences are atomic from the kernel's perspective — both `tasks[]` and
`failed_tasks[]` must be updated together, in the same `stage-state.json`
write, so the equality invariant holds at every observable state.

---

## Resumability

If AI-Robin is interrupted (process killed, session ended, machine rebooted),
the next invocation reads `stage-state.json` and resumes:

1. If `active_invocations` is non-empty, those sub-agents were killed mid-flight.
   Kernel marks them as anomalies in ledger, decides whether to re-dispatch or
   degrade based on the specific agent:
   - Consumer / Planning / Execute-Control / Review-Plan / Merge: re-dispatch
     (idempotent roles)
   - Execute / Research / Review sub-agents: re-dispatch with "this is a retry"
     flag; if they already wrote partial artifacts, pick up from there
2. If `active_invocations` is empty but `current_stage != "done"`, something odd
   happened (e.g., kernel was killed right after signal processing but before
   spawning next). Kernel examines the last ledger entry and re-spawns whatever
   the routing_decision said to spawn.

---

## Example

```json
{
  "schema_version": "1.0",
  "run_id": "run-20260416-my-app-7f3a",
  "project_root": "/projects/my-app",
  "current_stage": "review",
  "stage_iterations": {
    "intake": 1,
    "planning": 2,
    "execute_control": 3,
    "execute": 3,
    "review": 4
  },
  "active_invocations": [
    {
      "invocation_id": "inv-review-merge-batch-3",
      "sub_agent": "review-merge",
      "stage": "review",
      "spawned_at": "2026-04-16T14:45:00Z",
      "expected_return_signal_types": ["review_merged"]
    }
  ],
  "current_batch": {
    "batch_id": "batch-3",
    "milestone_ids": ["m2-api-endpoints", "m3-auth-middleware"],
    "tasks": [
      {"task_id": "batch-3-task-1", "status": "complete", "settled_at": "2026-04-16T14:42:00Z"},
      {"task_id": "batch-3-task-2", "status": "failed", "settled_at": "2026-04-16T14:43:00Z"}
    ],
    "failed_tasks": ["batch-3-task-2"],
    "review_iteration": 2,
    "status": "reviewing"
  },
  "plan_pointer": {
    "plan_room": "00-project-plan",
    "completed_milestones": ["m1-db-schema"],
    "in_progress_milestones": ["m2-api-endpoints", "m3-auth-middleware"],
    "pending_milestones": ["m4-frontend-shell", "m5-deploy"],
    "degraded_milestones": []
  },
  "run_started_at": "2026-04-16T10:00:00Z",
  "last_updated_at": "2026-04-16T14:45:00Z",
  "last_ledger_entry_id": 47
}
```
