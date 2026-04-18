# Planning Phase 5: Milestones

**Autonomy: guided**

Define milestones — units of work dispatched to Execute Agents in batches.

## Each milestone has

- **`id`** like `m1-db-schema`, `m2-auth-endpoints`
- **Deliverable**: what will exist on disk after completion
- **Gate criterion**: concrete, testable condition for "done"
- **`depends_on`**: other milestone IDs that must complete first
- **Rooms affected**: which Rooms contain the work
- **Contract spec IDs**: contracts whose implementation this milestone
  produces

## Granularity

Target 5-25 milestones for a typical project.
- Fewer than 5: batches too large, review misses things
- More than 25: fragmentation and overhead

Each milestone should be 1-4 Execute Agent tasks. If a milestone needs
more than 5 tasks, split it.

## Milestones are written to

- The relevant Room's `progress.yaml` (if milestone scope is single-room)
- `META/00-robin-plan/progress.yaml` (the master plan's milestone
  list — always)

## Gate criteria must be verifiable by Review

Not by human. Every gate criterion must be checkable by a review
playbook or automated test.

**Good examples:**

- "All endpoints defined in `contract-api-users-001` respond to test
  requests with the declared schema"
- "Migration `users-table` runs against empty DB without errors"
- "Frontend `<LoginForm>` component renders with no console errors and
  matches `contract-api-users-001` request shape"

**Bad examples:**

- "Looks good" — not verifiable
- "User is happy" — no user in the loop
- "Works correctly" — too vague

If you can't write a concrete gate for a milestone, either:
- Simplify the milestone until you can
- Split it so each sub-part has its own verifiable gate

## Gate format in progress.yaml

```yaml
milestones:
  - id: "m1-db-schema"
    name: "Database schema + migrations"
    status: pending
    depends_on: []
    rooms_affected: ["02-database"]
    contract_spec_ids: ["contract-db-schema-001"]
    gate: true
    gate_criteria: "Migration runs cleanly against empty DB; schema
                    matches contract-db-schema-001."
```

## Dependencies

`depends_on` is **strict** — milestone B with `depends_on: [A]` will
NOT be dispatched by Scheduler until A has completed (pass review
OR been degraded).

Only list true dependencies:
- B needs A's contract to exist
- B imports from A's code
- B's tests require A's runtime

Do NOT list convenience dependencies ("B is easier to review after A
is reviewed"). That creates false serialization and starves parallelism.

## No circular dependencies

Every dependency graph must be a DAG. Sanity-check in Phase 7.

## Output

Populated `progress.yaml` files. Feeds Phase 6 (concurrency).
