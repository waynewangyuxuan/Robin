# Iteration Budgets

The hard limits that bound AI-Robin's execution. Budgets are the mechanism that
turns "autonomous agent" into "autonomous batch job" — without them, a stuck
sub-loop could run forever.

Used by: main agent (every turn, to check before routing), Consumer Agent (to
record per-run overrides from user), every sub-agent (to check its own
per-invocation sub-budget before returning).

---

## Philosophy

Budgets are **hard kill switches**, not soft guidelines. When a budget hits
zero, the protocol does exactly one thing: **degrade the scope bounded by
that budget** (see `degradation-policy.md`). There is no retry, no extension,
no "let me think about it one more time".

This is deliberate. The alternative is a system that decides, on its own,
whether to push past its own limits. That way lies context overflow and
indeterminate runs. Budgets make the worst case bounded.

---

## Budget taxonomy

Budgets are organized by what scope they bound. Each budget is tracked as a
separate counter in `.ai-robin/budgets.json`.

### Per-batch budgets (reset per batch)

#### `review_iterations_per_batch`
**Default: 2**

Maximum number of times a single batch's output can go through
execute-review-replan loop. If review fails twice in a row for the same batch
and we're about to start a 3rd iteration, instead we degrade the batch's
scope.

**Decrement rule**: +1 every time a batch's review returns `fail` AND triggers
a replan (not when review passes; not when failure triggers degradation).

**Reset**: when a new batch is formed by Execute-Control.

### Per-scope budgets (reset per top-level scope)

#### `replan_iterations`
**Default: 3**

Maximum number of times Planning Agent can be re-invoked for the same plan
scope. After this, if planning still can't produce an executable plan,
degrade the whole scope.

**Decrement rule**: +1 every time Planning is re-invoked *after* the first
invocation of a scope. (The initial Planning dispatch doesn't count — only
re-invocations triggered by research gaps, sub-planning needs, or review
failures.)

**Reset**: when moving to a new top-level scope (rare; usually only at Consumer
-> Planning transition).

#### `research_depth_per_question`
**Default: 2**

Research agents can recursively trigger sub-research (e.g., Research Agent
asks a question that requires further research). This bounds the depth.

**Decrement rule**: Each research spawn's `depth` field is one level. Initial
research from Planning = depth 1. Sub-research = depth 2. A depth-3 request
would trigger `research_inconclusive` instead.

**Reset**: per research question (each new top-level question from Planning
resets the depth counter).

### Global budgets (one counter for the entire run)

#### `wall_clock_total_seconds`
**Default: 14400 (4 hours)**

Maximum total wall-clock time the run can take. Can be overridden at Consumer
stage (user-specified "don't run more than 1 hour" → 3600).

**Decrement rule**: kernel checks elapsed time on every routing turn against
`stage-state.run_started_at`. If elapsed > budget, next action is
**global degrade**: stop all in-flight sub-agents, degrade all pending
scopes, write escalation-notice, end run.

#### `tokens_total_estimated`
**Default: 10,000,000**

Rough cap on total tokens consumed across all sub-agent invocations.
Sub-agents self-report their consumption in `dispatch-signal.budget_consumed.
tokens_estimated`. Kernel sums these.

**Decrement rule**: kernel sums reported tokens after each signal. If cumulative
> budget, trigger global degrade.

Defaults are generous; users can tighten via Consumer intake.

#### `max_total_milestones_attempted`
**Default: 50**

Hard cap on how many milestones can be attempted in a run. Prevents a plan
from exploding into hundreds of tiny milestones that overwhelm the runtime.

If planning produces >50 milestones, Planning Agent's self-check catches
this and the first attempt is truncated with an `anomaly` entry; user's
intake may need to narrow scope.

### Per-sub-agent budgets (sub-agents self-enforce)

Each sub-agent's SKILL.md defines its own internal budget (e.g., "Consumer
Agent caps at 15 Q&A turns with user"). Those are separate from the budgets
in this file, but the sub-agent reports consumption to main agent on return.

---

## Interaction between budgets

Some budgets compose. A single review failure on batch 3 consumes
`review_iterations_per_batch[batch-3]`; if that exhausts AND we trigger a
replan, it also consumes `replan_iterations`. Both decrements are logged in
ledger.

If either per-batch or replan budget hits zero, the scope is degraded.

---

## Overrides at intake

Consumer Agent may ask the user for budget adjustments. Common cases:

- "I only have 30 minutes" → wall_clock_total_seconds = 1800
- "This is a large project" → max_total_milestones_attempted = 100
- "Be thorough, take your time" → review_iterations_per_batch = 3

Any override is recorded in the `run_start` ledger entry and in
`.ai-robin/budgets.json`'s initial state.

Budgets cannot be increased mid-run. They can only be decreased or kept same.

---

## `budgets.json` format

```json
{
  "per_batch": {
    "review_iterations_per_batch": {
      "default": 2,
      "current": {
        "batch-3": { "limit": 2, "consumed": 1 }
      }
    }
  },
  "per_scope": {
    "replan_iterations": { "limit": 3, "consumed": 1 },
    "research_depth_per_question": {
      "default": 2,
      "active": {
        "q-auth-provider-choice": { "limit": 2, "consumed": 2 }
      }
    }
  },
  "global": {
    "wall_clock_total_seconds": {
      "limit": 14400,
      "consumed_at_last_check": 4200,
      "last_checked_at": "2026-04-16T11:10:00Z"
    },
    "tokens_total_estimated": { "limit": 10000000, "consumed": 1240000 },
    "max_total_milestones_attempted": { "limit": 50, "consumed": 7 }
  }
}
```

---

## Kernel workflow: checking budgets

Before every routing decision, the kernel runs this check:

```
1. Read budgets.json
2. For each relevant budget:
   a. Determine if the current routing action would consume it
   b. Check if consumption would bring it to zero or below
3. If any would-consume budget is exhausted:
   - Log budget_exhausted entry
   - Route to degradation instead of the originally-intended action
   - Log degradation_triggered entry
4. Otherwise:
   - Proceed with original routing
   - After action completes, decrement budgets and log budget_decrement
```

Global budgets are checked more aggressively — every turn, not just on
decrement actions. A long-running sub-agent could silently consume hours of
wall-clock; the kernel must catch this even when no signal arrived.

---

## Degradation is not "failure"

When a budget is exhausted and a scope is degraded, the run **continues** for
other scopes. A degraded batch 3 doesn't stop batches 4, 5, 6 from running
(assuming they don't depend on batch 3's output).

Only when every remaining scope has been either completed, degraded, or
blocked on a degraded dependency does the run end with partial delivery.

The escalation-notice tells the human exactly what happened.

---

## Examples

### Example 1: Review fails twice

```
Batch 3 review: iteration 1 → fail → decrement review_iterations_per_batch[batch-3] from 2 to 1 → replan
Batch 3 replan: Planning spawned → decrement replan_iterations from 3 to 2
Batch 3 execute: new code produced → Review-Plan → review
Batch 3 review: iteration 2 → fail → decrement review_iterations_per_batch[batch-3] from 1 to 0
Kernel: budget_exhausted on review_iterations_per_batch[batch-3]
Kernel: skip replan (would have decremented replan_iterations), route to degrade-batch-3
Kernel: write context-degraded-batch3.yaml spec, write escalation-notice section
Kernel: mark batch 3 as degraded in stage-state.plan_pointer.degraded_milestones
Kernel: return to Execute-Control for batch 4
```

### Example 2: Wall clock nearly exhausted

```
Kernel turn starts, reads budgets.json
Kernel: wall_clock_total_seconds consumed = 14380 of 14400 (20 seconds left)
Kernel: no signal in inbox; an Execute Agent is running
Kernel: normally would wait, but wall_clock check fails
Kernel: write budget_exhausted entry for wall_clock
Kernel: write anomaly entry describing abnormal termination
Kernel: does NOT kill the in-flight Execute Agent (might produce orphan state);
        instead sets stage-state.pending_termination = true
Kernel: when the in-flight Execute returns, kernel processes the signal but
        routes to degrade-all instead of next stage
Kernel: writes all remaining pending milestones as degraded
Kernel: writes escalation-notice
Kernel: writes run_end entry
Kernel: exits dispatch loop
```

---

## Rationale (why these specific numbers)

| Budget | Default | Why |
|---|---|---|
| review_iterations_per_batch | 2 | User explicitly requested this in design discussion. 2 iterations gives the system one retry after initial fail; 3rd iteration rarely produces materially different output. |
| replan_iterations | 3 | Plans benefit from more iteration than reviews because planning problems are higher-level. 3 allows initial plan + 2 significant revisions. |
| research_depth_per_question | 2 | Deeper nesting rapidly returns diminishing info-per-token. 2 captures "look up X, look up X's sub-aspect Y" but stops at 3. |
| wall_clock 4 hours | generous default | Typical AI-Robin run on a medium project should finish in 1-2 hours; 4 hours tolerates unusual scope. User should tighten if they want cost control. |
| tokens 10M | generous default | Similar rationale. A medium run uses 1-3M; 10M tolerates larger or iteration-heavy runs. |
| milestones 50 | plan-sanity | Prevents pathological plans. Most projects break into 5-25 milestones. 50 is a ceiling, not a target. |

All defaults can be tuned based on operating experience once AI-Robin has run
on real projects.
