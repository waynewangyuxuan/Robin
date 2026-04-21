# Room 07 · Merger

> Consolidate N review sub-verdicts into one merged verdict with a
> composed git commit message.

- **Methodology**: [`skills/robin-merger/`](../../skills/robin-merger/)
- **Proxy**: [`agents/robin-merger.md`](../../agents/robin-merger.md)
- **Intent**: [`specs/intent-merger-001.yaml`](specs/intent-merger-001.yaml)

## Role in the dispatch loop

- **Upstream**: all Reviewer instances for the batch
- **Downstream**: Committer (consumes the composed commit message verbatim)
- **Side effects**: emits merged verdict + commit message string

## Why this is a separate agent

Isolating commit-message composition here (plus in Degrader) keeps
policy decisions — what goes in the message, how verdicts are summarized
— in one reducer. Committer becomes a thin shell-out.

## What lives here

Add a `convention-commit-message-*.yaml` here once the commit message
format is formally pinned (currently implicit in methodology).
