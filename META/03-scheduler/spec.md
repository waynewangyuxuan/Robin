# Room 03 · Scheduler

> Read the plan + current progress; decide which milestones run in the
> next batch and at what concurrency.

- **Methodology**: [`skills/robin-scheduler/`](../../skills/robin-scheduler/)
- **Proxy**: [`agents/robin-scheduler.md`](../../agents/robin-scheduler.md)
- **Intent**: [`specs/intent-scheduler-001.yaml`](specs/intent-scheduler-001.yaml)

## Role in the dispatch loop

- **Upstream**: Planner (via `planning_complete`), or loops back after previous batch completion
- **Downstream**: Executor instance(s) via batch manifest
- **Side effects**: read-mostly; produces no specs, only a batch manifest

## Relevant roadmap items

- [#3](https://github.com/waynewangyuxuan/Robin/issues/3) — worktree isolation affects how Scheduler may launch parallel Executors in separate worktrees.

## What lives here

Minimal today: single intent spec. Scheduler has the narrowest contract
surface of the agents. Add specs here if concurrency rules or batch
bounds become formal enough to need their own contract.
