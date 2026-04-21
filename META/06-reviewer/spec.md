# Room 06 · Reviewer

> Evaluate a batch's changed code against a domain-specific checklist;
> emit a structured verdict.

- **Generic flow**: [`skills/robin-reviewer/SKILL.md`](../../skills/robin-reviewer/SKILL.md)
- **Domain checklists**: [`skills/robin-reviewer/domains/`](../../skills/robin-reviewer/domains/)
- **Example domain instance**: [`agents/robin-reviewer-code-quality.md`](../../agents/robin-reviewer-code-quality.md)
- **Intent**: [`specs/intent-reviewer-001.yaml`](specs/intent-reviewer-001.yaml)

## Role in the dispatch loop

- **Upstream**: Review-Planner (dispatches N domain-parameterized Reviewer instances per batch)
- **Downstream**: Merger (via `review-verdict`)
- **Side effects**: emits structured verdict (pass / warn / fail + observations)

## Domain model

Reviewer is a single shared flow parameterized by a domain checklist.
New domains = new file under `skills/robin-reviewer/domains/`; no new
agent, no kernel changes. Today the only always-on domain is
`code-quality`. Domain checklists are pluggable — this is the **only
place** in Robin today where domain knowledge lives natively.

## Relevant roadmap items

- [#5](https://github.com/waynewangyuxuan/Robin/issues/5) — the capability pack system aims to generalize this domain-plug-in pattern beyond review (into exec and plan).

## What lives here

Add `contract-review-verdict-*.yaml` if the verdict schema evolves
beyond what `contracts/review-verdict.md` specifies.
