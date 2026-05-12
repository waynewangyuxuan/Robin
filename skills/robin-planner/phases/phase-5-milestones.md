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
    risk: high                # see "Risk classification" below
    human_checkpoint: false   # see "Human checkpoint flag" below
```

## Risk classification (Axis 2 — drives hybrid-mode pausing)

Each milestone has a `risk` field — one of `low` / `medium` / `high`.
Defaults to `low` if omitted. Risk is **independent** of `gate`; gate is
"can Reviewer verify this objectively", risk is "if this goes wrong,
how hard is the recovery". They often correlate but not always (a
schema migration is high-risk regardless of whether its acceptance test
is automatable).

**Assignment heuristics** (use these as starting points; override per
project context):

| `risk: high` | `risk: medium` | `risk: low` (default) |
|---|---|---|
| Irreversible schema migrations | New endpoints over existing data | Internal utility code |
| Auth / credentials / PII handling | Frontend critical paths (login, checkout) | Tests, docs |
| Production deploy config / secrets | CI/CD changes that affect prod | Style / lint cleanups |
| External API integration with rate limits or contract drift | Refactors crossing 3+ files | Configuration in dev envs |
| Concurrent state mutations across modules | First-time use of a new framework feature | Adding a new isolated module |
| Cross-cutting / architectural changes | | |

**Bias toward `medium`** when uncertain. `high` should mean "Wayne
should look at this before more milestones build on top of it".

## Human checkpoint flag (Axis 2 — decision-kernel-pause-checkpoint-001)

Each milestone has a `human_checkpoint` boolean. When set to `true`, the
kernel pauses to `paused_for_human` state immediately after this
milestone's batch is committed (whether by Committer following a passed
Review or by a Degrader-triggered commit). Resume requires
`/robin-resume --ack` (continue), `--abort` (stop), or `--replan`
(re-spawn Planner).

**Default policy by run-mode** (set at `/robin-start --run-mode <mode>`):

| Run mode | Default for `human_checkpoint` |
|---|---|
| `autonomous` (default) | All milestones `false` |
| `hybrid` | `true` only for milestones with `risk: high`; `false` otherwise |
| `dev` | All milestones `true` |

**Per-milestone overrides**: Planner MAY set `human_checkpoint: true` on
a specific milestone regardless of run-mode if there's an inherent
reason (e.g., a milestone whose contracts are known to need human eyes
before next milestones build on them). Per-milestone explicit values
ALWAYS win over run-mode defaults.

**Decoupling from `gate`**: `gate`, `risk`, and `human_checkpoint` are
three independent fields:

- `gate` — "Reviewer must verify a concrete criterion before this is
  marked done"
- `risk` — "How costly is recovery if this milestone is wrong"
- `human_checkpoint` — "Pause execution after commit so the user
  can review before continuing"

`hybrid` mode couples `risk: high` → `human_checkpoint: true` by default,
but Planner can decouple per-milestone (e.g., a `risk: medium` milestone
with explicit `human_checkpoint: true` because its design has a
specific concern; a `risk: high` milestone with `human_checkpoint: false`
because the user said up-front "trust me on this one").

**When NOT to set human_checkpoint**: never set it on milestones with
no Reviewer gate AND no meaningful artifact. There's nothing for the
user to meaningfully ack — they'd just type `--ack` blindly. Use
checkpoints sparingly; their value is in the human actually reading
what was built.

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
