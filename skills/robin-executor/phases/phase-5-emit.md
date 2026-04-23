# Execute Phase 5: Emit signal

**Autonomy: explicit**

## Record phase start

```bash
echo "$(date -u +%s) phase-5-start" >> .ai-robin/trace/{invocation_id}.log
```

Write the return signal to `.ai-robin/dispatch/inbox/`.

## Signal: `execute_complete`

Task finished, artifacts ready for Review.

Payload:

```json
{
  "task_id": "batch-3-task-1",
  "artifacts_summary": {
    "files_created": ["src/routes/users/create.ts"],
    "files_modified": [],
    "specs_created": ["change-20260416-143000-batch3-task1"],
    "specs_updated": ["contract-api-users-001"],
    "change_spec_id": "change-20260416-143000-batch3-task1"
  },
  "self_assessment": {
    "declared_complete": true,
    "known_issues": [
      "Endpoint does not yet handle rate limiting; deferred per milestone gate"
    ]
  }
}
```

Note: Execute does NOT run `git commit`. The kernel does that after
Review. You just write files to the working tree and report what you
did.

## When to use `execute_complete` vs `execute_failed`

### Use `execute_complete` for

- Work is done, files are written
- You have some concerns (surface them in `known_issues`)
- Minor ambiguities you resolved with a reasonable choice
- Implementation complexity you navigated (even if messy)

Self-doubt about code quality is NOT a reason for `execute_failed`.
That's Review's job to evaluate. Write it, note concerns, let Review
decide.

### Use `execute_failed` for real blockers

- **Contract contradiction**: the contract is logically impossible or
  internally contradictory. Don't silently fix.
- **Missing prerequisite**: a spec you depend on doesn't exist or
  doesn't contain what's expected. Plan bug.
- **Environmental blocker**: required tool/library isn't available and
  no reasonable alternative exists within decision constraints.
- **Scope overlap with in-progress work**: another Execute Agent is
  touching the same files. Should never happen — if it does, fail
  fast.

### `execute_failed` payload

```json
{
  "task_id": "batch-3-task-1",
  "reason": "contract_needs_revision | missing_context | scope_too_large | environment_blocker | scope_overlap | compile_error",
  "details": "string — specific description",
  "partial_artifacts": ["string — anything salvageable on disk"]
}
```

## Signal file format

Write to `.ai-robin/dispatch/inbox/{signal_id}.json`.

`signal_id` format: `execute-{task_id}-{YYYYMMDDTHHMMSS}-{8-char-hex}`

See `contracts/dispatch-signal.md` for full wrapping schema.

## Compute phase timings from the trace log

Before writing the final `budget_consumed` block, read back the trace log and compute real per-phase durations. This is the whole point of the phase-start/phase-end probes — the log is authoritative; do not estimate `wall_clock_seconds`.

Read the log:

```bash
cat .ai-robin/trace/{invocation_id}.log
```

Each line is `<unix-epoch-seconds> <label>`. For each phase `N` in 1..5:

```
phase_N_duration = (phase-N-end epoch) - (phase-N-start epoch)
```

Record `phase-5-end` **immediately before** writing the signal file (so emit time is captured), then re-read the log and compute `phase_5_duration`:

```bash
echo "$(date -u +%s) phase-5-end" >> .ai-robin/trace/{invocation_id}.log
```

Compute total wall-clock from the earliest and latest log entries:

```
wall_clock_seconds = (last epoch in log) - (first epoch in log)
```

Populate `budget_consumed` in the signal wrapper (per `contracts/dispatch-signal.md`):

```json
"budget_consumed": {
  "tokens_estimated": <your estimate>,
  "wall_clock_seconds": <computed from log, NOT estimated>,
  "phase_timings": {
    "context_load_s": <phase_1_duration>,
    "implement_s":    <phase_2_duration>,
    "anchors_s":      <phase_3_duration>,
    "selfcheck_s":    <phase_4_duration>,
    "emit_s":         <phase_5_duration>
  }
}
```

If the trace log is missing or malformed (e.g. you skipped a phase-start probe), report what you have and set the missing phase's value to `null`. Do not fabricate.

The trace log file is ephemeral bookkeeping — leave it on disk for post-hoc analysis; do not stage it for commit.

## After emitting

Your work is done. Main agent picks up the signal, waits for other
Execute Agents in the batch to finish, then spawns Review-Plan. The
invocation terminates after writing the signal file.
