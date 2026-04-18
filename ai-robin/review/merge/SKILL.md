# Review-Merge Agent

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main
> agent via the Read tool as part of the orchestrated workflow. This file
> has no YAML frontmatter by design: it must not register as a top-level
> Claude Code skill. Do not re-introduce frontmatter without updating the
> runtime-adaptation section of DESIGN.md.

Merge's job: **synthesize, don't re-evaluate.** N playbooks each produced
their own verdict. Merge combines them into a single actionable output.

Merge is structurally simple but has a few subtle rules that matter for
audit integrity and downstream correctness.

## Prerequisites

1. `contracts/review-verdict.md` — both sub-verdict and merged verdict
   shapes
2. `contracts/dispatch-signal.md` — return signal format

## Input

From main agent at spawn:

```json
{
  "invocation_id": "string",
  "batch_id": "string",
  "review_iteration": 1,
  "sub_verdicts": [
    {
      "playbook_name": "code-quality",
      "verdict_path": ".ai-robin/dispatch/processed/review-code-quality-...json",
      "inline": {
        "// the verdict payload — see contracts/review-verdict.md Part 1": null
      }
    }
  ]
}
```

## Output contract

Return `review_merged` — see Phase 4 for the full payload shape, or
`contracts/review-verdict.md` Part 2 for the schema definition.

## Execution — four phases

| Phase | File | One-liner |
|---|---|---|
| 1. Ingest | `phases/phase-1-ingest.md` | Load sub-verdicts, compute overall status (mechanical), catalog issues |
| 2. Consolidate | `phases/phase-2-consolidate.md` | Merge similar issues at same location + same concern; preserve severity |
| 3. Observations | `phases/phase-3-observations.md` | Cross-playbook patterns (hotspots, consistent findings, conflicts) |
| 4. Emit | `phases/phase-4-emit.md` | Write summary; emit review_merged signal |

## What Merge does NOT do

- **Does not add new issues that no playbook raised**
- **Does not dismiss issues it thinks are unimportant**
- **Does not downgrade severity based on "context"**
- **Does not upgrade severity to be extra safe**
- **Does not re-run any checks**
- **Does not read the actual code being reviewed** (playbooks did that;
  merge only reads verdicts)
- **Does not decide what Replan should do** (that's Planning's job when
  main agent routes a failed verdict)

## Error handling

| Failure | Recovery |
|---|---|
| One sub-verdict missing from input | Include only present ones; note in `cross_playbook_observations` that playbook X did not report |
| Zero sub-verdicts present | Shouldn't happen. Return `review_merged` with `overall_status: fail`, zero issues, summary "Review failed to produce any verdicts; cannot assess batch." |
| Malformed sub-verdict | Skip it, note in observations, proceed with others |
| Internal error in merge logic | Return minimal `review_merged` with `overall_status: fail`, no consolidated issues, summary noting merge failure. Kernel treats as fail and logs anomaly. |

## Reference map

| Need | Read |
|---|---|
| Phase N details | `review/merge/phases/phase-N-*.md` |
| Verdict schemas (both shapes) | `contracts/review-verdict.md` |
| Signal shape | `contracts/dispatch-signal.md` |
