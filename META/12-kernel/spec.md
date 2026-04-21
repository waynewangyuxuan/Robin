# Room 12 · Kernel (orchestrator)

> Orchestrate the full dispatch loop: Intake → Planning → Scheduling →
> Executing → Reviewing → Merging → Committing → (Degrading) → Finalizing.
> Route sub-agent return signals; do not produce specs.

- **Methodology**: [`skills/robin-kernel/`](../../skills/robin-kernel/)
- **Discipline (policies)**: [`skills/robin-kernel/discipline.md`](../../skills/robin-kernel/discipline.md)
- **Entry points**: [`commands/robin-start.md`](../../commands/robin-start.md), [`commands/robin-resume.md`](../../commands/robin-resume.md)
- **Intent**: [`specs/intent-kernel-001.yaml`](specs/intent-kernel-001.yaml)

## Role in the dispatch loop

Kernel IS the dispatch loop. Unlike other agents, it has no proxy in
`agents/` — it's loaded by slash commands (`/robin-start`,
`/robin-resume`) into the main agent turn.

- **Upstream**: user (via `/robin-start <brief>`) or stored state (via `/robin-resume`)
- **Downstream**: all sub-agents (dispatched per signal routing)
- **Side effects**: reads/writes `.ai-robin/stage-state.json`, `.ai-robin/ledger.*`; emits no Feature Room specs

## Why kernel is different

Kernel is pure orchestration. It does not write application code and
does not write Feature Room specs. It keeps two shared state artifacts
(stage-state and session-ledger) and routes signals between agents
per `contracts/dispatch-signal.md`. All autonomy policies (when to
escalate, when to degrade, iteration budgets) live in
`discipline.md`.

## Relevant roadmap items

Nearly all roadmap items touch kernel behavior:

- [#3](https://github.com/waynewangyuxuan/Robin/issues/3) auto-worktree (kernel creates worktree on start)
- [#4](https://github.com/waynewangyuxuan/Robin/issues/4) mid-run HITL (kernel adds pause states)
- [#8](https://github.com/waynewangyuxuan/Robin/issues/8) auto-approve mode (kernel flag)
- [#9](https://github.com/waynewangyuxuan/Robin/issues/9) structured ledger schema (kernel is the ledger writer)
- [#10](https://github.com/waynewangyuxuan/Robin/issues/10) intervention protocol (kernel defines pause states + resume contracts)

When those land, add corresponding `decision-*.yaml` entries here.
