# Execute-Control Phase 5: Emit signal

**Autonomy: explicit**

Write the return signal to `.ai-robin/dispatch/inbox/`.

## Three possible signals

### `dispatch_batch`

Normal case — a batch is ready.

Payload:

```json
{
  "batch_id": "batch-3",
  "tasks": [...],
  "concurrency_mode": "parallel" | "sequential" | "mixed",
  "rationale": "string — explain which milestones, why this concurrency"
}
```

Rationale example:

> "Batch 3 contains 3 milestones (m2-api, m3-auth, m4-frontend). m2 and
> m3 are parallel-safe (separate Rooms, no file overlap, no
> dependency). m4 depends on m2 and m3's contracts being committed, so
> it's a later sequential stage. Using mixed mode: parallel group
> {m2-api, m3-auth}, then sequential m4-frontend."

The rationale is recorded in the ledger for audit.

### `all_complete`

Phase 1 determined no more work remains. Every milestone is either
completed or degraded.

Payload:

```json
{
  "summary": {
    "milestones_passed": N,
    "milestones_degraded": N,
    "total_commits": N,
    "wall_clock_total_seconds": N
  },
  "delivery_bundle_path": "string"
}
```

Main agent will finalize delivery and exit the run.

### `dispatch_exhausted`

Can't form a valid batch. Used when:

- All remaining pending milestones are blocked by degraded dependencies
  (reason: `blocked_milestones`)
- Circular dependency detected in plan (reason: `circular_dependencies`)
- Plan room missing or empty (reason: `plan_missing` or `plan_empty`)
- Internal computation error (reason: `internal_error`)

Payload:

```json
{
  "reason": "string",
  "details": "string"
}
```

Main agent will typically trigger a replan. If replan budget is out,
main agent degrades.

## Signal file format

Write to `.ai-robin/dispatch/inbox/{signal_id}.json`.

`signal_id` format: `execute-control-{YYYYMMDDTHHMMSS}-{8-char-hex}`

See `contracts/dispatch-signal.md` for full wrapping schema.

## After emitting

Your work is done. Main agent picks up the signal on its next turn.
Output nothing else; the invocation terminates.
