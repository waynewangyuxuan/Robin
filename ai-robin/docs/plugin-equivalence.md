# AI-Robin Plugin Equivalence Spec

This document defines what the Claude Code plugin adapter preserves from the
abstract AI-Robin design (in `ai-robin/`) and what it concretely adds. It is
the contract between the runtime-agnostic NLP and its first runtime adapter.

## What the plugin preserves (MUST be invariant)

Per `ai-robin/DESIGN.md §8`:

1. **File-based signal inbox is authoritative.** Plugin hooks read from and
   write to `.ai-robin/dispatch/inbox/` — they do not bypass it. Task tool
   return values are secondary; the signal file is the source of truth for
   audit.
2. **One signal per sub-agent invocation.** Each invocation ends with exactly
   one signal file.
3. **Lexicographic signal ordering.** When multiple signals are in inbox,
   kernel processes them in lexicographic signal_id order (per
   `skills/robin-kernel/discipline.md §3.5`).
4. **Sub-skill files have no YAML frontmatter.** `skills/robin-*/SKILL.md`
   remain frontmatter-less. The plugin's own `.claude-plugin/agents/*.md`
   wrappers have frontmatter (needed by Claude Code's agent-registration
   mechanism) but never contain methodology content — they only `Read` the
   sibling source SKILL.md.
5. **Kernel never reads domain content.** Commit messages, degradation
   narratives, delivery bundles are all produced by delegated sub-agents
   (Commit Agent, Degradation Agent, Finalization Agent). The kernel
   dispatches and passes payloads through verbatim.
6. **Ledger append-only and monotonic.** The kernel never rewrites prior
   entries. Hooks enforce entry_id monotonicity at Stop time.

## What the plugin adds

1. **Slash-command entry points.** `/robin-start`, `/robin-resume`,
   `/robin-status` replace natural-language skill activation.
   Reliability ↑.
2. **First-class agent wrappers.** Each sub-agent is addressable via
   `Task(subagent_type: "robin-...")`. Claude Code's tool system enforces
   that these names route correctly; accidental activation from user NL is no
   longer possible (Severe #6 from the pre-reorg audit).
3. **Hook-based ordering enforcement.** `pre_task.py` and `post_task.py`
   mechanically enforce the ledger-append-before-routing rule that was
   previously prose in `skills/robin-kernel/discipline.md §4`. The abstract rule
   remains in the prose for portability to other runtimes; the hooks are one
   concrete implementation.
4. **Auto-resume hint at SessionStart.** `session_start.py` detects
   `.ai-robin/stage-state.json` and prints a one-line summary. User no longer
   needs to say "resume"; the runtime signals the state automatically.
5. **Integrity check at Stop.** `stop.py` validates ledger invariants on
   session end; warns if run ended without `run_end` entry.

## What the plugin deliberately does NOT do

- Does not replace the abstract methodology (still in
  `skills/robin-*/SKILL.md`).
- Does not enforce tool scopes per-agent beyond what each wrapper's
  frontmatter `tools:` field declares (Claude Code's own enforcement applies).
- Does not run any end-to-end behavioral validation automatically — that
  remains future work (see "Future work" below).
- Does not mutate the abstract NLP spec. The kernel's routing table, the
  contract's signal types, the stdlib's methodology all live in `ai-robin/`
  and are runtime-agnostic.

## Delegation map (kernel-relief)

Three sub-agents introduced in Phase 2B of the plugin migration, each
corresponding to a specific signal-handling path:

| Trigger signal | Kernel spawns | Returns | Resolves |
|---|---|---|---|
| `review_merged` | Commit Agent | `commit_complete` | Severe #2 (kernel composing commit messages) |
| `stage_exhausted` / budget-exhausted | Degradation Agent → Commit Agent | `degradation_spec_written` → `commit_complete` | Severe #2 (kernel reading spec content to write degraded YAMLs) |
| `all_complete` | Finalization Agent | `delivery_bundle_ready` | Kernel no longer synthesizes DELIVERY.md |

## Version pairing

| ai-robin spec version | Plugin version |
|---|---|
| 0.1.x (pre-plugin) | N/A |
| 0.2.x | 0.2.x |

Plugin version must match minor version of `ai-robin/SKILL.md` frontmatter
(when versioned).

## Test coverage today

- **Structural tests** (pass):
  - `ai-robin/tests/routing-coverage.md` — 20/20 signal coverage in routing
    table (grep-diff empty)
  - Broken-refs grep — 0 unacceptable missing references
- **Hook unit tests** (pass):
  - `.claude-plugin/hooks/tests/` — 30 tests across 6 modules (ledger,
    state, pre_task, post_task, session_start, stop)
  - Run: `/opt/anaconda3/bin/pytest .claude-plugin/hooks/tests/ -v`
- **Behavioral end-to-end test** (NOT run): deferred per user's Phase 1.5
  skip decision. A baseline run through a minimal project would produce a
  ledger whose shape (entry_type sequence, signal types observed, stage
  transitions) can be snapshotted as a reference for future plugin changes.
  See Future work.

## Future work (out of scope for this migration)

- End-to-end baseline run to capture a reference ledger shape.
- Additional runtime adapters (Claude Agent SDK, custom orchestrators, cron +
  `claude -p`).
- Parallel dispatch verification (DESIGN.md §8 claims parallel Task calls in
  one message run concurrently; unverified by an actual run).
- Auto-invoke-Commit-Agent via SubagentStop hook (currently a no-op stub).
- Budget decrement enforcement via `pre_task.py` (currently only tracks
  dispatch entries; budget counters are kernel's responsibility).
