# Room 10 · Finalizer

> Generate the end-of-run delivery bundle (`.ai-robin/DELIVERY.md`)
> summarizing what was built vs degraded.

- **Methodology**: [`skills/robin-finalizer/`](../../skills/robin-finalizer/)
- **Proxy**: [`agents/robin-finalizer.md`](../../agents/robin-finalizer.md)
- **Intent**: [`specs/intent-finalizer-001.yaml`](specs/intent-finalizer-001.yaml)

## Role in the dispatch loop

- **Upstream**: kernel on `all_complete`
- **Downstream**: user (final human touchpoint before the run ends)
- **Side effects**: writes `.ai-robin/DELIVERY.md`; does not modify application code

## Relevant roadmap items

- [#6](https://github.com/waynewangyuxuan/Robin/issues/6) — post-run Q&A agent will read what Finalizer produces + ledger to answer user questions after delivery.

## What lives here

Thin today — delivery format will likely formalize into a
`convention-delivery-format-*.yaml` or `contract-delivery-*.yaml` when
the post-run Q&A agent (#6) lands and needs a stable contract.
