# Room 09 · Degrader

> When a scope is abandoned, write the `context-degraded-*.yaml`
> narrative and update `escalation-notice`.

- **Methodology**: [`skills/robin-degrader/`](../../skills/robin-degrader/)
- **Proxy**: [`agents/robin-degrader.md`](../../agents/robin-degrader.md)
- **Policy**: [`stdlib/degradation-policy.md`](../../stdlib/degradation-policy.md)
- **Intent**: [`specs/intent-degrader-001.yaml`](specs/intent-degrader-001.yaml)

## Role in the dispatch loop

- **Upstream**: kernel (on degradation trigger — iteration budget exhausted, unresolvable review failure, etc.)
- **Downstream**: Committer (via degradation commit message); escalation surfaces at Finalizer
- **Side effects**: writes `context-degraded-*.yaml` spec on target project; updates `escalation-notice.md`

## Why this agent exists

Robin deliberately does not ship `draft` to `active` automation that
blocks on human — so when a scope can't be completed, someone has to
write down **what was attempted and why it was abandoned**, with enough
context that the user can triage at delivery time. That "someone" is
Degrader.

## What lives here

Degradation is a normal exit path, not an error — keep specs about it
first-class. Add `convention-degradation-narrative-*.yaml` if narrative
format becomes formal.
