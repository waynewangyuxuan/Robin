# Session Ledger

An append-only log of every kernel decision during an AI-Robin run. The ledger
is the primary audit trail — at final delivery, the human verifier uses it to
locate any decision point without reading every artifact.

**Written to**: `.ai-robin/ledger.jsonl` (one JSON object per line)
**Written by**: main agent only (sub-agents cannot write to ledger directly)
**Appended at**: every dispatch, every signal routing, every degradation, every
budget decrement, every stage transition

---

## Why append-only matters

A review iteration that fails, then succeeds on retry, must leave both records
visible. A replan that changed course must show the original path. A degraded
scope must show what was attempted. Overwriting or rewriting entries destroys
the audit value.

If you (main agent) find yourself wanting to "fix" a previous ledger entry,
don't. Append a new entry with `entry_type: "correction"` referring to the
previous entry.

---

## Schema

Each line of `ledger.jsonl` is one JSON object:

```json
{
  "entry_id": "integer — monotonically increasing, 1-indexed",
  "timestamp": "ISO 8601",
  "entry_type": "one of the types below",
  "stage": "string — which stage was active when this happened",
  "iteration": "integer — current iteration of that stage",
  "content": {
    "// shape depends on entry_type": null
  },
  "refs": {
    "signal_id": "string — if this entry was triggered by a signal",
    "parent_entry_id": "integer — if this entry relates to an earlier entry",
    "spec_ids": ["string — any spec_ids this entry touches"]
  }
}
```

---

## Entry types

### `run_start`
First entry of a run. Records initial conditions.

```json
{
  "entry_type": "run_start",
  "content": {
    "project_root": "string",
    "initial_budgets": { "...": "..." },
    "user_input_summary": "string — short description of what user asked for",
    "ai_robin_version": "string"
  }
}
```

### `stage_transition`
Kernel moved from one stage to another.

```json
{
  "entry_type": "stage_transition",
  "content": {
    "from_stage": "string",
    "to_stage": "string",
    "reason": "string — which signal triggered this"
  }
}
```

### `dispatch`
Kernel spawned a sub-agent.

```json
{
  "entry_type": "dispatch",
  "content": {
    "sub_agent": "string — e.g. 'consumer', 'planning', 'execute:task-3'",
    "invocation_id": "string",
    "skill_path": "string — path to the SKILL.md loaded",
    "context_refs": ["string — spec_ids or file paths passed in"],
    "purpose": "string — short description in plain language"
  }
}
```

### `signal_received`
Kernel received and is processing a signal from a sub-agent.

```json
{
  "entry_type": "signal_received",
  "content": {
    "signal_type": "string",
    "from_agent": "string",
    "declared_complete": "boolean",
    "artifacts_count": "integer"
  }
}
```

### `routing_decision`
Kernel decided what to do based on a received signal.

```json
{
  "entry_type": "routing_decision",
  "content": {
    "triggered_by_signal": "string — signal_id",
    "decision": "string — plain language description",
    "next_action": "string — e.g. 'spawn_planning', 'spawn_review_merge', 'exit_all_complete'"
  }
}
```

### `budget_decrement`
Kernel consumed part of a budget.

```json
{
  "entry_type": "budget_decrement",
  "content": {
    "budget_name": "string — e.g. 'review_iterations:batch-3', 'replan_iterations'",
    "before": "number | integer",
    "after": "number | integer",
    "reason": "string"
  }
}
```

### `budget_exhausted`
A budget hit zero. This entry is always followed by a `degradation_triggered`
entry (or `run_end` if the exhausted budget is global).

```json
{
  "entry_type": "budget_exhausted",
  "content": {
    "budget_name": "string",
    "scope": "string — what this budget was bounding"
  }
}
```

### `degradation_triggered`
Kernel invoked the degradation protocol for a scope.

```json
{
  "entry_type": "degradation_triggered",
  "content": {
    "scope": "string — what got degraded (milestone_id, spec_id, batch_id, etc.)",
    "reason": "string",
    "known_issue_spec_id": "string — the context-degraded-*.yaml spec written"
  }
}
```

### `commit`
Kernel performed a git commit (always after review).

```json
{
  "entry_type": "commit",
  "content": {
    "batch_id": "string",
    "review_status": "'pass' | 'pass_with_warnings' | 'fail'",
    "review_iteration": "integer",
    "git_hash": "string",
    "commit_message": "string",
    "files_committed": "integer"
  }
}
```

The `commit_message` field is copied verbatim from the source:

- For review commits: `review_merged.payload.commit_message` (produced by Merge Agent's Phase 4)
- For degradation commits: kernel-composed from the degradation trigger payload using the deterministic pattern `[degradation] <scope>: <short reason>`, where both `<scope>` and `<short reason>` come from the degradation trigger and require no spec reading (preserving kernel context-minimalism).

Kernel does not otherwise synthesize commit messages.

### `user_message_received`
User sent a message during execution. Per kernel discipline, this is logged but
does not divert the workflow (unless it's STOP/PAUSE — see `kernel-discipline.md`).

```json
{
  "entry_type": "user_message_received",
  "content": {
    "message_summary": "string — brief description",
    "action_taken": "string — almost always 'logged_and_continued'"
  }
}
```

### `anomaly`
Something unexpected happened: malformed signal, sub-agent timeout, inconsistent
state. Recorded for later investigation, then kernel takes its best-guess action.

```json
{
  "entry_type": "anomaly",
  "content": {
    "what": "string",
    "kernel_response": "string — what the kernel did about it",
    "severity": "'low' | 'medium' | 'high'"
  }
}
```

### `correction`
If a previous entry is superseded or corrected, this entry records the
correction. The previous entry is NOT modified.

```json
{
  "entry_type": "correction",
  "content": {
    "corrects_entry_id": "integer",
    "correction_description": "string"
  }
}
```

### `run_end`
Final entry of a run.

```json
{
  "entry_type": "run_end",
  "content": {
    "exit_reason": "'all_complete' | 'intake_blocked' | 'global_budget_exhausted' | 'user_stopped'",
    "summary": {
      "total_entries": "integer",
      "stages_completed": ["string"],
      "milestones_passed": "integer",
      "milestones_degraded": "integer",
      "total_commits": "integer",
      "wall_clock_total_seconds": "integer"
    },
    "delivery_bundle_path": "string"
  }
}
```

---

## Reading the ledger (for human verifier)

At final delivery, the ledger is the map. Common queries a human might want:

- **"What decisions did Consumer Agent make on my behalf?"** → filter
  `stage: "intake"`, look at `dispatch` and linked spec_ids, especially
  agent-proxy decisions.
- **"Why was this milestone degraded?"** → find the `degradation_triggered`
  entry for that milestone's scope, trace `refs.parent_entry_id` back to see
  what led there.
- **"How many review attempts did batch 3 go through?"** → filter for
  `batch_id: "batch-3"` and count `commit` entries.
- **"Was any budget exhausted?"** → filter `entry_type: "budget_exhausted"`.

The ledger is intentionally simple JSONL so it's trivially grep-able and
machine-parseable.

---

## Validation rules

- `entry_id` increases strictly by 1; main agent checks the last entry before
  appending
- Every `dispatch` must eventually have a matching `signal_received` (unless
  the sub-agent was killed/timed out — in which case an `anomaly` entry is
  written)
- Every `signal_received` is followed by a `routing_decision` within the same
  turn
- Every `review_merged` signal must produce both a `routing_decision` and a
  `commit` entry (hard rule from `kernel-discipline.md`)
- `run_start` appears exactly once, at entry_id 1
- `run_end` appears at most once, at the end; its absence means the run was
  interrupted (resumable)

---

## Example excerpt

```jsonl
{"entry_id":1,"timestamp":"2026-04-16T10:00:00Z","entry_type":"run_start","stage":"intake","iteration":0,"content":{"project_root":"/projects/my-app","initial_budgets":{"review_iterations_per_batch":2,"replan_iterations":3},"user_input_summary":"Build an expense-tracking web app with Next.js","ai_robin_version":"0.1.0"},"refs":{}}
{"entry_id":2,"timestamp":"2026-04-16T10:00:05Z","entry_type":"dispatch","stage":"intake","iteration":1,"content":{"sub_agent":"consumer","invocation_id":"inv-consumer-001","skill_path":"consumer/SKILL.md","context_refs":[],"purpose":"Initial intake of user's raw project request"},"refs":{}}
{"entry_id":3,"timestamp":"2026-04-16T10:18:44Z","entry_type":"signal_received","stage":"intake","iteration":1,"content":{"signal_type":"intake_complete","from_agent":"consumer","declared_complete":true,"artifacts_count":12},"refs":{"signal_id":"intake-consumer-20260416T101844-b2e1"}}
{"entry_id":4,"timestamp":"2026-04-16T10:18:44Z","entry_type":"routing_decision","stage":"intake","iteration":1,"content":{"triggered_by_signal":"intake-consumer-20260416T101844-b2e1","decision":"Intake complete, 3 rooms created, 12 specs written. Advance to planning.","next_action":"spawn_planning"},"refs":{"signal_id":"intake-consumer-20260416T101844-b2e1"}}
{"entry_id":5,"timestamp":"2026-04-16T10:18:44Z","entry_type":"stage_transition","stage":"planning","iteration":0,"content":{"from_stage":"intake","to_stage":"planning","reason":"intake_complete signal received"},"refs":{"parent_entry_id":4}}
```
