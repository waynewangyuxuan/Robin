# Room 04 · Executor

> Given a single milestone task, load relevant context, write/modify code
> and specs, return a structured artifacts summary. Does NOT git commit.

- **Methodology**: [`skills/robin-executor/`](../../skills/robin-executor/) (including `phases/`, `commit-preparation.md`, `context-pulling.md`)
- **Proxy**: [`agents/robin-executor.md`](../../agents/robin-executor.md)
- **Intent**: [`specs/intent-executor-001.yaml`](specs/intent-executor-001.yaml)

## Role in the dispatch loop

- **Upstream**: Scheduler (via batch manifest)
- **Downstream**: Review-Planner (via `execute_complete`)
- **Side effects**: writes / modifies application code; writes `change-*.yaml` spec recording the change; updates anchors on affected specs

## Relevant roadmap items

- [#5](https://github.com/waynewangyuxuan/Robin/issues/5) — Executor will load capability packs for domain-tagged milestones.
- [#3](https://github.com/waynewangyuxuan/Robin/issues/3) — when worktree isolation lands, Executor runs inside the per-run worktree.

## What lives here

Executor is the only agent that writes application code — the room will
grow specs about contract honoring, anchor discipline, and pack loading
as #5 and related work progresses.
