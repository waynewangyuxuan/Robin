# Room 02 · Planner

> Turn Intake's specs into an executable plan: milestones, module
> boundaries, inter-module contracts.

- **Methodology**: [`skills/robin-planner/`](../../skills/robin-planner/)
- **Proxy**: [`agents/robin-planner.md`](../../agents/robin-planner.md)
- **Intent**: [`specs/intent-planner-001.yaml`](specs/intent-planner-001.yaml)

## Role in the dispatch loop

- **Upstream**: Intake (via `intake_complete`)
- **Downstream**: Scheduler (via `planning_complete`) — or loops back via Researcher (`planning_needs_research`) or self (`replan` after post-review feedback)
- **Side effects**: writes the `00-robin-plan/` room (target project side) with `decision-*`, `contract-*`, `constraint-*` specs + milestones

## Relevant roadmap items

- [#5](https://github.com/waynewangyuxuan/Robin/issues/5) — Planner will tag milestones with domain when capability pack system lands.

## What lives here

Structured specs about Planner's role / contracts / conventions. When
capability pack tagging (#5) lands, add a `contract-milestone-tag-*.yaml`
documenting the domain-tag schema.
