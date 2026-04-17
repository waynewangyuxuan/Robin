# Execute-Control Phase 3: Determine concurrency mode

**Autonomy: guided**

Load `execute-control/concurrency-rules.md`. For the batch selected in
Phase 2, decide how tasks execute relative to each other.

## Three modes

### `parallel`
All tasks run simultaneously, each as its own Execute Agent invocation.

**Condition**: tasks don't share files; no task depends on another's
output in this batch.

**Ideal case** — maximum throughput. Aim for this when possible.

### `sequential`
Tasks run one after another.

**Condition**: tasks share files OR one depends on another's output.

Fallback when parallel can't work safely.

### `mixed`
Some tasks are parallel groups, some are serial stages.

**Encoding**: tasks have `depends_on_tasks` entries. Main agent spawns
in dependency order; independent groups run in parallel.

Use mixed only when there's a clear structural reason. Most batches
should be pure parallel or pure sequential.

## Hard rules (from concurrency-rules.md)

Regardless of how nice parallel would be, these force serialization:

- Two tasks touching the **same file** → serial
- Two tasks touching **`packages/shared/*`** (or similar cross-cutting
  code) → serial (single writer rule)
- Contract-producing task **before** contract-consuming task → serial
  with dependency
- Schema/migration task **before** API tasks using the schema → serial

## Over-serialization is bad

The default instinct is to be cautious and serialize more than
necessary. Resist. Un-needed serialization means longer runs and worse
utilization.

**Two tasks are parallel-safe unless you can name a specific reason
they aren't.** "Maybe something could go wrong" is not a reason.
"Both modify auth.ts" is a reason.

## Output

- `concurrency_mode`: `parallel` | `sequential` | `mixed`
- If mixed: per-task `depends_on_tasks` populated

Feeds Phase 4 (task spec building).
