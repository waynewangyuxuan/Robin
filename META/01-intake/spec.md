# Room 01 · Intake

> Conduct the one-time human Q&A at the start of a Robin run; surface
> decisions and gaps; produce planning-ready Feature Room specs.

- **Methodology**: [`skills/robin-intake/`](../../skills/robin-intake/)
- **Proxy**: [`agents/robin-intake.md`](../../agents/robin-intake.md)
- **Intent**: [`specs/intent-intake-001.yaml`](specs/intent-intake-001.yaml)

## Role in the dispatch loop

- **Upstream**: user brief (via `/robin-start`)
- **Downstream**: Planner (via `intake_complete` dispatch signal)
- **Side effects**: writes Feature Room (intent / constraint / convention / context / decision) for the target project; may leave specs in `draft` state (the only agent allowed to do so)

## Relevant roadmap items

- [#7](https://github.com/waynewangyuxuan/Robin/issues/7) — add `code_extraction` source so Intake can populate Feature Room from an existing codebase instead of only from Q&A.

## What lives here

Structured specs about the Intake agent itself. Canonical methodology is
in the linked SKILL.md — this room does not duplicate it. Add
`decision-*` / `contract-*` / `convention-*` as substantive design
changes happen (e.g. when #7 lands, a `decision-code-extraction-*.yaml`
will document the new source type).
