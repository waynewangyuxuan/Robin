# Room 08 · Committer

> Execute a git commit on the kernel's behalf using the verbatim message
> provided by Merger or Degrader. Never composes commit messages itself.

- **Methodology**: [`skills/robin-committer/`](../../skills/robin-committer/)
- **Proxy**: [`agents/robin-committer.md`](../../agents/robin-committer.md)
- **Intent**: [`specs/intent-committer-001.yaml`](specs/intent-committer-001.yaml)

## Role in the dispatch loop

- **Upstream**: Merger (successful batch) OR Degrader (degradation commit)
- **Downstream**: Finalizer (at end of run) or next dispatch iteration
- **Side effects**: runs `git commit`; this is the **only** agent that does

## Why this is a separate agent

Isolating `git commit` to a single narrow agent:
1. Makes the shell-out auditable (one place to log what committed).
2. Prevents commit-message policy from leaking into Merger/Executor code
   paths — the message is already a string by the time it arrives here.
3. Gives the kernel a single clean point to enforce commit-related
   invariants (no amend, no skip-hooks, etc.).

## Relevant roadmap items

- [#8](https://github.com/waynewangyuxuan/Robin/issues/8) — auto-approve mode: Committer is part of the allowlisted set by definition.
