# Room 11 · Researcher

> Answer a specific factual question that Planner needs to finalize its
> plan. Uses web search + targeted analysis.

- **Methodology**: [`skills/robin-researcher/`](../../skills/robin-researcher/)
- **Proxy**: [`agents/robin-researcher.md`](../../agents/robin-researcher.md)
- **Intent**: [`specs/intent-researcher-001.yaml`](specs/intent-researcher-001.yaml)

## Role in the dispatch loop

- **Upstream**: Planner (via `planning_needs_research` dispatch signal)
- **Downstream**: Planner (resumes with research findings folded in)
- **Side effects**: emits `research-*.yaml` spec with confidence

## Positioning

Researcher is an on-demand side-channel, not a happy-path stage.
Planner decides when to invoke; Researcher answers narrow factual
questions; Planner decides how to use the answer. Research results
come with confidence so Planner can choose to degrade instead of
commit when confidence is too low.

## What lives here

Thin today. If research caching / deduplication becomes a thing, a
`convention-research-cache-*.yaml` will document it here.
