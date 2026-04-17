# Planning Phase 2: Technical decisions

**Autonomy: guided**

Decisions are the spine of a plan. Every contract and milestone rests on
decisions, so decisions come first.

## What decisions need making

Walk through these categories, make one decision per relevant item:

- **Framework/stack** — if not already decided by Consumer. Often Consumer
  decides, sometimes proxies.
- **Architectural pattern** — monolith / services / serverless / worker
  pattern. Must be justified against constraints.
- **Data storage** — DB engine, schema-first vs migrations approach.
- **Key libraries** — routing, state management, validation, testing.
- **Testing strategy** — unit-first, integration-first, E2E coverage level.
- **Deployment specifics** — user may have said "Vercel" but you decide
  "Vercel with Edge Functions for these routes".

## For each decision point

1. **Check if Consumer already decided it.** If yes, reference the spec.
   Don't duplicate.
2. **Check if research is needed.** If you genuinely don't know the right
   choice AND no clear default exists → return `planning_needs_research`
   with a specific question (see Phase 9 for when to return this).
3. **Otherwise, make the decision.** Write a `decision-*.yaml` spec.

## Decision spec must include

- **What was decided** (in `intent.summary`)
- **At least two alternatives considered** (in `intent.detail`)
- **Why this choice beats the alternatives** given the constraints
- **Anchor to driving constraints** (via `relations[].depends_on` to
  relevant constraint specs)

Use `provenance.source_type: planning_derived`, confidence typically
0.75-0.95.

## Don't over-decide

Not every choice needs a decision spec. A decision spec is warranted when:
- The choice is non-trivial (more than one reasonable option)
- The choice has downstream impact (affects other modules / code)
- The choice might be revisited in replan (you want to record the
  reasoning)

Skip decision specs for:
- Trivially obvious picks (e.g., "use TypeScript" in a Next.js app when
  everyone uses TypeScript)
- Implementation details left to Execute Agent's judgment

## When you can't decide without research

Return `planning_needs_research` (see Phase 9 for format). Be specific:

- ❌ "What's the best auth approach?"
- ✅ "For a Next.js 14 app on Vercel with ~1000 users, compare Clerk vs
  NextAuth.js vs Lucia for: OAuth support, session management, total
  cost of ownership at that scale"

Research consumes budget. Only ask when you genuinely can't make a
reasonable call with current info.

## Output

A set of decision specs written to `META/00-ai-robin-plan/specs/`. These
feed into Phase 3 (module decomposition) and Phase 4 (contract design).
