# Finalization Agent — Kernel Relief

> **Internal sub-skill — not user-invocable.** No YAML frontmatter.

Finalization Agent generates the delivery bundle at end-of-run. It computes summary statistics and produces a human-readable summary document for the user.

The kernel cannot do this — it requires reading spec content (to know what was delivered) and ledger archaeology, both of which are domain work.

## Prerequisites

Load before starting:
1. `contracts/session-ledger.md` — for reading ledger history
2. `contracts/dispatch-signal.md` — return signal shape
3. `stdlib/feature-room-spec.md` — to read the plan + change specs

## Input

From main agent at spawn:

```json
{
  "invocation_id": "string",
  "project_root": "string",
  "plan_pointer": {
    "completed_milestones": ["string"],
    "in_progress_milestones": ["string"],
    "pending_milestones": ["string"],
    "degraded_milestones": ["string"]
  },
  "run_started_at": "ISO 8601",
  "ledger_entry_count": "integer"
}
```

## Output contract

Return `delivery_bundle_ready` signal.

Primary artifact: a markdown file at `.ai-robin/DELIVERY.md` summarizing the run.

## Execution — three phases

### Phase 1: Compute summary stats

**Autonomy: explicit**

Scan `.ai-robin/ledger.jsonl` (streamed line-by-line; do NOT load whole file into working memory) to count:
- Total stage transitions
- Total commits (entry_type == 'commit')
- Review iterations per batch (group `commit` entries by `content.batch_id`)
- Degradations triggered (entry_type == 'degradation_triggered')
- Anomalies (entry_type == 'anomaly', group by severity)
- Wall clock elapsed (run_started_at → now)

### Phase 2: Read top-level specs

**Autonomy: guided**

For the delivery bundle narrative, read ONLY:
- Intent specs from the root project Room (one-line summary each)
- Change specs for each completed milestone (to know what was delivered)
- Context-degraded specs for each degraded milestone (for pointer references)

Do NOT read code, do NOT read phase methodology files — keep context minimal.

### Phase 3: Write DELIVERY.md

**Autonomy: guided** (structure); **autonomous** (narrative tone)

Structure:

```markdown
# AI-Robin Delivery: {project name from intent}

## Summary
- Started: {run_started_at}
- Finished: {now}
- Wall clock: {human-readable duration}
- Commits: {count}
- Stages completed: {list}

## What was built
{one paragraph synthesis from intent specs}

## Milestones
### Completed
- {m1}: {one-line description} — commit {short sha}
- ...

### Degraded (if any)
- {mX}: see `META/{room}/specs/{context-degraded-spec-id}.yaml`
- ...

## Where to look next
- Code changes: see `git log`
- Feature Room specs: `META/`
- Audit trail: `.ai-robin/ledger.jsonl`
- Escalations: `.ai-robin/escalation-notice.md` (if any degradations)
```

Write to `{project_root}/.ai-robin/DELIVERY.md`.

Then emit `delivery_bundle_ready` signal to `.ai-robin/dispatch/inbox/{signal_id}.json`. `signal_id` format: `finalize-finalization-{YYYYMMDDTHHMMSS}-{8-char-hex}`.

Payload fields per contracts/dispatch-signal.md `delivery_bundle_ready` schema:
- `bundle_path`: ".ai-robin/DELIVERY.md"
- `summary`: the counts computed in Phase 1

## What you absolutely do not do

- **Do not write code.** You summarize; Execute wrote code.
- **Do not commit.** The delivery bundle is not committed by Finalization; kernel may commit it as the final run_end artifact if desired (outside Finalization's scope).
- **Do not second-guess degradations.** They are reported as recorded in their context-degraded specs.
- **Do not add new stage-state fields or ledger entries.** Read only.

## Reference map

| Need | Read |
|---|---|
| Ledger format | `contracts/session-ledger.md` |
| Spec format | `stdlib/feature-room-spec.md` |
| Signal shape | `contracts/dispatch-signal.md` |
