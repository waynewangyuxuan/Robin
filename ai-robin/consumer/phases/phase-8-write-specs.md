# Consumer Phase 8: Write specs

**Autonomy: guided (per `stdlib/feature-room-spec.md`)**

Convert everything you gathered (Phases 1-6) into spec yamls. Load
`stdlib/feature-room-spec.md` for the exact schema.

## Typical outputs

- **`intent-*.yaml`** — one per top-level functional goal
- **`constraint-*.yaml`** — one per explicit user-stated constraint
  (tech, deployment, scope)
- **`convention-*.yaml`** — one per rule/convention the user specified
  (e.g., "use our existing TypeScript conventions")
- **`context-*.yaml`** — background info that doesn't fit the above
  (e.g., "deploying to a team with existing Clerk auth")
- **`decision-*.yaml`** — for:
  - Decisions user clearly made ("use Postgres" is a decision)
  - Agent proxy decisions from Phase 6 (with the Agent proxy note)

## Placement rules

- **Project-wide specs** → `00-project-room/specs/`
  - Global conventions
  - Top-level intent
  - Project-wide constraints (budget, timeline, tech stack)
- **Feature-specific specs** → `{feature-room}/specs/`
  - Intents for that feature area
  - Decisions specific to that area
- **Contract specs** — Consumer does NOT write contract specs. Those
  come from Planning. Consumer writes intents that will require
  contracts, but lets Planning design them.

## State is always active

All specs `state: active`, including agent_proxy decisions. Rationale:

- Downstream agents (Planning) need authoritative specs to act on.
  Draft specs create "should I use this?" ambiguity that Consumer's
  whole job is to prevent.
- Proxy decisions are tracked via the `intake_complete` signal's
  `agent_proxy_decisions` field + the ledger. That's the audit
  channel — not the `state` field.

The exception is if Consumer itself is uncertain about user's stated
intent (rare — if you're uncertain, ask in Phase 4). In that rare case
leave it `draft` and include it in `unresolved_but_deferred` of the
return signal.

## Provenance

Every spec has a `provenance` block. Consumer's four main
`source_type` values:

- `user_input` — extracted directly from what user said (confidence
  0.9-1.0)
- `user_implied` — derived from user's statements via clear inference
  (confidence 0.75-0.85) (see `stdlib/confidence-scoring.md`)
- `agent_proxy` — decided by Consumer on user's behalf, with Agent
  proxy note (confidence 0.6-0.8)
- `manual_input` — rarely used; reserved for when Consumer writes
  structural conventions not from user

## Sync to `spec.md`

After writing specs for a room, update that room's `spec.md` to
aggregate them. This is the human-readable view. Consumer fills it
once; later agents (Planning, Execute) keep it in sync.

Format (see original Feature Room room skill for full format):

```markdown
# {Room Name}

## Intent
{list of intent summaries, one per bullet}

## Decisions
{table: summary | rationale | source}

## Constraints
{list}

## Conventions
{list, with note of inherited vs room-specific}

## Context
{list}
```

## Do NOT do

- Do not write `contract-*.yaml` specs. That's Planning.
- Do not write `change-*.yaml` specs. Those come from Execute.
- Do not leave specs without `anchors[]` if the intent is about
  specific code — but Consumer rarely has code to anchor to (no code
  exists yet at intake). Leave `anchors: []` for most intent specs.
