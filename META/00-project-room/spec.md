# AI-Robin · Project Room

Entry point for the AI-Robin repo's own Feature Room. We dogfood the same
spec format that Robin expects downstream projects to use.

**If you're new here**, start with this file. Each section points into
specs under `specs/` where the structured detail lives. The yaml is the
source of truth; this page is the Human Projection.

---

## What Robin is

> [`specs/intent-project-001.yaml`](specs/intent-project-001.yaml)

AI-Robin turns a one-shot human intake into an autonomously-delivered
software project via a dispatched multi-agent workflow. Framework, not
domain expert. Canonical design detail lives in [DESIGN.md](../../DESIGN.md).

## Load-bearing design decisions

Three decisions shape most other trade-offs in this repo:

- [`decision-kernel-agnostic-001`](specs/decision-kernel-agnostic-001.yaml) —
  kernel embeds no frontend / backend / devops / business knowledge;
  domain capability lives exclusively in packs.
- [`decision-pack-as-dependency-001`](specs/decision-pack-as-dependency-001.yaml) —
  capability packs are declared dependencies; Planner tags milestones,
  Executor loads packs. **No** MCP-style runtime discovery.
- [`decision-protocol-before-ui-001`](specs/decision-protocol-before-ui-001.yaml) —
  intervention protocol and structured ledger events come before any
  dashboard UI.

## Conventions

- [`convention-agent-split-001`](specs/convention-agent-split-001.yaml) —
  thin proxy in `agents/`, methodology in `skills/`.

## Filesystem map

See [`context-filesystem-001`](specs/context-filesystem-001.yaml) for the
30-second tour. Tight summary of easy-to-confuse pairs:

- `agents/` (harness-facing thin proxies) vs `skills/` (methodology).
- `contracts/` (inter-agent data shapes) vs `stdlib/` (shared reasoning).
- `docs/` (prose) vs `META/` (structured project state — this folder).

## Roadmap

See [`context-roadmap-001`](specs/context-roadmap-001.yaml). Canonical
tracking is on GitHub issues
(<https://github.com/waynewangyuxuan/Robin/issues>) — spec is a snapshot.

## Per-agent rooms

Each sub-agent has its own room. Start with the room's `spec.md` for
orientation; the yaml specs inside each `specs/` hold the structured truth.

| Room | Agent | Methodology root |
|---|---|---|
| [01-intake](../01-intake/spec.md) | Intake | [`skills/robin-intake/`](../../skills/robin-intake/) |
| [02-planner](../02-planner/spec.md) | Planner | [`skills/robin-planner/`](../../skills/robin-planner/) |
| [03-scheduler](../03-scheduler/spec.md) | Scheduler | [`skills/robin-scheduler/`](../../skills/robin-scheduler/) |
| [04-executor](../04-executor/spec.md) | Executor | [`skills/robin-executor/`](../../skills/robin-executor/) |
| [05-review-planner](../05-review-planner/spec.md) | Review-Planner | [`skills/robin-review-planner/`](../../skills/robin-review-planner/) |
| [06-reviewer](../06-reviewer/spec.md) | Reviewer (generic + domains) | [`skills/robin-reviewer/`](../../skills/robin-reviewer/) |
| [07-merger](../07-merger/spec.md) | Merger | [`skills/robin-merger/`](../../skills/robin-merger/) |
| [08-committer](../08-committer/spec.md) | Committer | [`skills/robin-committer/`](../../skills/robin-committer/) |
| [09-degrader](../09-degrader/spec.md) | Degrader | [`skills/robin-degrader/`](../../skills/robin-degrader/) |
| [10-finalizer](../10-finalizer/spec.md) | Finalizer | [`skills/robin-finalizer/`](../../skills/robin-finalizer/) |
| [11-researcher](../11-researcher/spec.md) | Researcher | [`skills/robin-researcher/`](../../skills/robin-researcher/) |
| [12-kernel](../12-kernel/spec.md) | Kernel (orchestrator) | [`skills/robin-kernel/`](../../skills/robin-kernel/) |

Each per-agent room currently holds a single `intent-{name}-001.yaml` plus
the standard room files (`room.yaml`, `progress.yaml`, `spec.md`).
Add `decision-*` / `contract-*` / `convention-*` specs as substantive
design changes happen.

---

## Why META/ on Robin itself

Robin expects downstream projects to maintain a Feature Room under `META/`.
It would be awkward to require that without running it on ourselves. This
folder is the dogfood test: if maintaining Feature Room for this repo is
painful, users of Robin will feel it too — and we want that signal early.
