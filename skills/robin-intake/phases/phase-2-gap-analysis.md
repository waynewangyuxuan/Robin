# Intake Phase 2: Gap analysis

**Autonomy: guided**

Load `skills/robin-intake/decision-taxonomy.md`. For the project type you inferred in
Phase 1, walk through the checklist of decision points.

## Classify each decision point

For each point in the taxonomy, classify into one of four buckets:

- **Covered** — user's raw input directly addresses this.
- **Derivable with high confidence** — user didn't state it but input
  strongly implies the answer (e.g., "Next.js app" → implies React). These
  become specs without needing to ask.
- **Proxy-able with a reasonable default** — not stated, weakly implied or
  not at all, but a sensible default exists that won't materially surprise
  the user. Defer to Phase 6.
- **Must-ask** — not stated, no reasonable default, would materially
  affect outcome. Goes into the gap list for Phase 3/4.

## Flag ambiguities

In parallel with the classification walk, mark **ambiguities** — places
where user input admits multiple interpretations:

- "Keep it simple" — simple architecture? simple UI? simple deployment?
- "Use our existing stack" — which stack? (if not stated elsewhere)
- "Production-ready" — what level? (uptime SLA? error handling depth?)

Ambiguities go into the same "must-ask" bucket as gaps, unless you can
resolve them from context.

## Two outputs of this phase

1. **Gap list**: the must-ask items, each with a one-line description of
   what's missing.
2. **Ambiguity list**: ambiguous phrases with candidate interpretations.

Both feed into Phase 3 for prioritization.

## Calibration

A typical medium-complexity project has 10-30 decision points in its
taxonomy. Of those, for a thoughtful user's input: ~50% covered, ~20%
derivable, ~20% proxy-able, ~10% must-ask.

If your must-ask list is >10 items, input is unusually sparse — expect
Phase 4 to take multiple rounds.

If your must-ask list is 0, something is probably wrong (over-eager
proxying). Re-check — the user likely has non-trivial preferences you
missed.

## Mode-specific scope narrowing

The full decision-taxonomy applies to `new_project`. For other modes,
narrow the scope:

| Mode | Taxonomy scope |
|---|---|
| `new_project` | Full taxonomy, full classification. |
| `incremental_feature` | Skip decision points already answered in pre-existing active specs (loaded in Phase 1). The remaining set is the "delta surface". Typical must-ask count drops to 1-3 (vs ~10 for new_project). |
| `bug_fix` | Only ask points that affect bug resolution or acceptance criteria. Skip strategic / architectural points entirely — they're determined by existing code + the bug's root cause. Typical must-ask: 1-2 (repro steps + acceptance definition). |
| `pr_continuation` | Only ask points the PR diff and reviewer comments don't resolve. Reviewer asks themselves are de facto must-asks already. Typical must-ask: 0-2 (rarely needs a fresh question — comments cover most). |

**Why narrow**: re-asking the user about decisions encoded in existing
META is friction with no benefit. Trust the existing specs.
