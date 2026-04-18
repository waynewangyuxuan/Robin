# Planning Phase 4: Contract design

**Autonomy: guided** (most of the spec); **explicit** (spec format)

**This is Planning's most important phase.** Contract specs are what
enable parallel execution. A well-designed contract lets module A and
module B be built concurrently without those agents ever needing to see
each other's work. A poorly-designed contract forces serial execution
or causes review failures.

Load `skills/robin-planner/contract-design.md` for full methodology.

## What needs a contract

For every inter-module boundary identified in Phase 3, produce a
contract:

- **HTTP / RPC APIs** between modules
- **Function signatures** exposed from one module to another
- **Data shapes** passed between modules (types, schemas, DB rows)
- **Events / messages** exchanged (pub/sub, queues)
- **Shared conventions** (naming, error handling, logging) — these are
  `convention-*.yaml` but functionally act as cross-cutting contracts
- **File formats** if modules exchange via filesystem
- **Database schemas** — the DB is a shared contract between everyone
  who touches it

## Contract spec content

Every contract spec must define:

- **What is exposed**: exact function signatures, endpoint shapes, data
  types, event payloads
- **What callers rely on**: invariants, error behavior, ordering
  guarantees, idempotency
- **What the producer assumes**: preconditions callers must satisfy
- **Failure modes**: not just happy path — "throws EmailTakenError on
  duplicate", "returns 409 on conflict"

## Contracts are specs, not code

- ✅ "Returns a User object with id, email, created_at, where id is
  UUIDv4 and email is RFC-5322 valid"
- ❌ "Uses Postgres SELECT * FROM users WHERE ..." (that's
  implementation)

## Placement

- Contract between two specific modules → the Room of the **producer**
  (the module that implements the contract's declared side)
- Cross-cutting contract (used by many modules) →
  `00-project-room/specs/`
- Database schema contracts → usually `00-project-room/specs/` or a
  dedicated `infrastructure/` room

Every contract spec's `anchors[].file` should point to where the code
implementing the producer side will live — even if that code doesn't
exist yet. Execute Agent will create it at that path.

## Confidence and state

Contracts are `state: active`, `provenance.source_type:
planning_derived`, confidence typically 0.85-0.95 (you're designing
deliberately, not guessing).

## Output

A set of `contract-*.yaml` specs covering every module boundary.
Feeds Phase 5 (milestones reference contract IDs).

## If you can't design a contract

If you have two modules and cannot define a clean contract between them,
something is wrong. Three common causes:

1. The boundary is in the wrong place → go back to Phase 3, re-split
2. You need more information → return `planning_needs_research` with
   the specific question about what the contract should look like
3. Decisions haven't been made that the contract depends on → go back
   to Phase 2, make the missing decisions

Do not return a plan with ambiguous contracts. Ambiguous contracts are
the single biggest source of review failures in AI-Robin.
