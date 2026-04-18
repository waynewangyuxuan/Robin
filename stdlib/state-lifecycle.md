# State Lifecycle

Rules for managing the `state` field on a spec. When and how specs
transition through their lifecycle.

Used by: all sub-agents that produce or modify specs.

---

## The six states

```
draft  ──▶  active  ──▶  stale
              │
              ├──▶  deprecated
              │
              ├──▶  superseded (by another spec)
              │
              └──▶  degraded (AI-Robin extension)
```

Each state has a specific meaning and a defined set of allowed
transitions.

### `draft`

"Just created, not yet validated."

In the original Feature Room, `draft` meant "waiting for human review
before becoming authoritative". In AI-Robin, `draft` is a transient
internal state within a single sub-agent's work:

- A sub-agent may internally track a spec as `draft` while it's still
  gathering information
- **Before returning**, the sub-agent MUST promote draft specs to
  `active` (or another terminal state). Sub-agents do not leave
  drafts for downstream agents to interpret.
- **Exception**: Intake's return signal may include explicitly
  `draft` specs in the rare case that Intake is uncertain and
  hasn't resolved via asking or proxying. These go in
  `unresolved_but_deferred` of the return signal, signaling Planning
  that these need finalization.

**Rule**: if you're a sub-agent about to return with any `draft`
specs, STOP. Either promote them or flag them explicitly in your
return signal's `unresolved_but_deferred`.

### `active`

"Current, authoritative, in-effect."

Default state for all non-trivial specs. Downstream agents read
`active` specs as truth.

Transitions allowed from `active`:
- → `stale` (anchor tracking detected drift; see
  `anchor-tracking.md`)
- → `deprecated` (no longer applicable; kept for history)
- → `superseded` (replaced by a newer spec)
- → `degraded` (AI-Robin extension; scope was attempted but abandoned)

### `stale`

"Anchored code has changed in a way that may have invalidated the
spec's claim."

Not a failure — a signal to Review or next Planning iteration to
decide: update the spec, update the code, or mark superseded.

Automatically set by:
- Execute Agent when it knowingly changes behavior at an anchored
  location
- Review sub-agent when it detects semantic mismatch between spec
  and code
- Anchor tracking (build-time check) when hash mismatch + behavior
  uncertainty

Transitions allowed from `stale`:
- → `active` (after fix — spec was updated or code was reverted)
- → `superseded` (replaced by a more accurate spec)
- → `deprecated` (spec is simply no longer relevant)

### `deprecated`

"No longer applicable but kept for history."

Used when:
- A feature was removed and the spec describing it is no longer
  relevant, but we want to remember it existed
- An approach was tried and rejected; keep the spec as a record

`deprecated` specs are NOT loaded by `prompt-gen`-equivalent context
pulling. They're pure history.

No transitions out of `deprecated`. Once deprecated, that's it.

### `superseded`

"Replaced by a newer spec."

Used when a new spec takes the place of an old one (e.g., Planning
replan produces a new decision that replaces the old).

The new spec references the old via `relations[].supersedes`:

```yaml
# new-spec
relations:
  - type: supersedes
    ref: "old-spec-id"
```

And the old spec's state becomes `superseded`.

`superseded` specs are NOT loaded by context pulling — the successor
is loaded instead (via the `supersedes` relation traversal).

No transitions out of `superseded`.

### `degraded` (AI-Robin extension)

"Scope was attempted but could not be completed; recorded for
transparency."

Not in original Feature Room taxonomy. Added for AI-Robin's
degradation policy.

Applied when:
- A scope's budget was exhausted (review iterations, replan
  iterations, research depth)
- Degradation was triggered per `stdlib/degradation-policy.md`

`degraded` specs ARE visible to Planning in a replan — they inform
decisions about whether to rework or work around. They're also
prominently listed in the `ESCALATIONS.md` for the human verifier.

No transitions out of `degraded` within the same run. A subsequent
AI-Robin run (after the user addresses the cause) may start a fresh
spec that `supersedes` the degraded one, effectively moving past it.

---

## Transition matrix

| From | To | When |
|---|---|---|
| `draft` | `active` | Sub-agent self-check passed; spec is authoritative |
| `draft` | (none) | Cannot return with draft specs (see rule above) |
| `active` | `stale` | Anchor tracking / Review detects drift |
| `active` | `deprecated` | Feature removed or approach abandoned |
| `active` | `superseded` | Newer spec takes its place |
| `active` | `degraded` | Scope bounded by this spec was degraded |
| `stale` | `active` | Fixed — spec updated or code reverted |
| `stale` | `superseded` | Replaced by more accurate spec |
| `stale` | `deprecated` | Spec no longer relevant |

All other transitions are invalid and should trigger an anomaly log
if attempted.

---

## Who can promote what

- **Intake**: may leave some specs `draft` if flagged in
  `unresolved_but_deferred`; promotes the rest to `active` before
  returning
- **Planning**: promotes to `active`; marks previous specs
  `superseded` when replan produces replacements
- **Research**: produces `active` specs with confidence reflecting
  research quality
- **Execute**: updates anchors; may mark specs `stale` if
  behavior-changing
- **Review**: flags stale; does not promote/demote directly but
  surfaces issues for the next Planning to address
- **Main agent**: writes `context-degraded-*.yaml` specs and marks
  affected specs `degraded` per degradation protocol

---

## Rules

1. **Every spec has a state.** No spec should exist without one.
2. **State field is semantically lifecycle, not audit.** Don't use
   state to mark "made by agent vs user" — that's `provenance.
   source_type`. Don't use state to mark "needs review" — in
   AI-Robin, no human review happens after Intake, so
   `draft`-as-marker is not meaningful.
3. **Transitions are recorded in the spec yaml** — when a state
   changes, update the spec's `produced_at` or add a history note in
   `intent.detail`. The ledger's `commit` entries capture the git
   side; the spec yaml captures the content side.
4. **Never delete specs.** Deprecate or supersede. Deletion destroys
   audit trail.

---

## Context pulling with states

Execute Agent's context pulling (per `skills/robin-executor/context-pulling.md`)
respects state:

| State | Pulled? |
|---|---|
| `active` | YES — authoritative |
| `draft` | YES — but flagged as tentative (should be rare) |
| `stale` | YES — but flagged as cautionary |
| `deprecated` | NO |
| `superseded` | NO — successor pulled instead |
| `degraded` | NO for execution context; YES for replan context (Planning reads to know what was attempted) |
