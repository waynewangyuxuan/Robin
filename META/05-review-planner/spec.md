# Room 05 · Review-Planner

> Given a batch's change artifacts, decide which domain-specific reviewer
> playbooks to run.

- **Methodology**: [`skills/robin-review-planner/`](../../skills/robin-review-planner/)
- **Proxy**: [`agents/robin-review-planner.md`](../../agents/robin-review-planner.md)
- **Intent**: [`specs/intent-review-planner-001.yaml`](specs/intent-review-planner-001.yaml)

## Role in the dispatch loop

- **Upstream**: Executor (via `execute_complete`)
- **Downstream**: Reviewer instance(s), one per selected domain
- **Side effects**: produces a review plan (which reviewers to spawn)

## Why this agent exists

Review-Planner is the architectural template for domain-awareness in
Robin today. It lets the review stage specialize by domain without the
kernel knowing anything about frontend / backend / db / etc. — the
meta-agent does the selection. The same pattern is what
[decision-pack-as-dependency-001](../00-project-room/specs/decision-pack-as-dependency-001.yaml)
proposes extending to Planner + Executor (tracked in #5).

## What lives here

The selection rules (what counts as a frontend change, etc.) are
currently implicit in methodology. If we formalize them, add a
`convention-selection-rules-*.yaml` here.
