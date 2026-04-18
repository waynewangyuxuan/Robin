# Scheduler Phase 2: Bound the batch

**Autonomy: guided**

From the executable milestones, select which to include in the next batch.

## Don't dispatch all at once

Even if 10 milestones are executable, you don't dispatch all 10 in one
batch. Reasons:

- Large batches make Review harder (more content to verify)
- If one fails, the whole batch is subject to replan
- Budget exhaustion risk mid-batch

## Pick batch size

**Default: 2-5 milestones per batch**, adjusted for size.

Target batch duration: 15-45 minutes wall-clock for execute + review.

### Smaller batches when

- Budgets are getting tight (see Phase 2 budget rules below)
- Review of recent batches has been shaky (iterate in smaller chunks to
  fail fast)
- There's a natural architectural boundary about to be crossed

### Larger batches when

- Recent batches have been clean passes
- Executable milestones are all leaf nodes (independent, small)
- Budget is comfortable

## Budget-aware batching

If `remaining_budgets.wall_clock_seconds < 1800` (30 min) → shrink
batch aggressively, one task per batch. Maximizes chance of finishing
some work even if budget runs out.

If `remaining_budgets.tokens_total_estimated < 500000` → similarly be
conservative.

## Prioritization within the executable set

When you have more executable milestones than fit the batch, prioritize:

- **High dependency fan-out** first. If milestone A has 5 dependents,
  completing A unlocks a lot.
- **Foundational milestones** first (DB schema, shared types).
- **Leaf nodes** can be batched together later.

## Output

A selected subset of executable milestones that will form this batch.
Feeds Phase 3 (concurrency).
