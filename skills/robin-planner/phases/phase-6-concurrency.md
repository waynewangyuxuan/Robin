# Planning Phase 6: Concurrency identification

**Autonomy: guided**

For each pair of milestones with no `depends_on` between them, determine
whether they can truly execute in parallel OR must be serialized for some
other reason.

Load `skills/robin-planner/parallelism-identification.md` for full methodology.

## Quick rules

- **A doesn't depend on B AND they touch disjoint file paths** →
  parallel-safe
- **Both touch the same file** → serial (or redesign so they don't)
- **A defines a contract B consumes** → A before B (but once A is
  committed, B can parallelize with other sibling milestones)
- **A and B both edit `packages/shared/*` (or equivalent shared
  interface layer)** → serial — single-writer rule; shared interfaces
  don't tolerate concurrent edits without merge conflicts

## Output of this phase

Annotations on milestones:

- **`depends_on`** captured in Phase 5 (strict ordering)
- Optionally **`parallel_safe_with`** listing sibling milestones this
  one is explicitly safe to run alongside (Scheduler uses this
  as a hint)
- **`serial_with`** listing sibling milestones this must NOT run
  alongside despite no explicit dependency (e.g., shared file scope)

## Architectural rules become constraints

Some concurrency constraints are architectural, not per-milestone:

- "packages/shared/src/ changes flow through one owner at a time"
- "Database migrations are strictly sequential"
- "Deployment changes happen after all feature work"

These become `convention-*.yaml` or `constraint-*.yaml` specs in
`00-project-room/specs/`, referenced by affected milestones. Write
these once; they apply to every relevant milestone.

## Don't over-serialize

The default instinct is to be cautious and serialize more than
necessary. Resist. Un-needed serialization means longer runs and worse
utilization.

**Two milestones are parallel-safe unless you can name a specific
reason they aren't.** If the reason is "maybe something could go wrong"
— that's not a reason. If the reason is "they both modify auth.ts" —
that's a real reason.

## Output feeds Scheduler

Scheduler reads these annotations when forming batches. Good
concurrency annotations let Scheduler dispatch 3-5 parallel
Execute Agents when the dependency graph allows; bad annotations
force single-agent batches even when parallelism was available.
