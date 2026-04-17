# Routing Coverage Audit

This document lists every `signal_type` defined in `contracts/dispatch-signal.md` and the routing action main `SKILL.md` must take on it. It is the source of truth for routing completeness — every signal type declared in the contract MUST appear in the main SKILL.md routing table.

## How to verify

Run these greps from the ai-robin directory:

```bash
# List signal types declared in contract
grep -E '^#### `[a-z_]+`' contracts/dispatch-signal.md | sed -E 's/.*`([a-z_]+)`.*/\1/' | sort -u

# List signal types covered in main SKILL.md routing table
grep -E '^\| `[a-z_]+` \|' SKILL.md | sed -E 's/.*`([a-z_]+)`.*/\1/' | sort -u

# Diff: contract signals NOT in routing table
comm -23 <(contract list) <(skill list)
```

Expected output of the diff: **empty**. If non-empty, the routing table is incomplete.

## Signal → routing contract

| signal_type | Defined in contract | Routing action (authoritative) |
|---|---|---|
| `intake_complete` | ✅ | Update stage-state → "planning". Spawn Planning Agent. |
| `intake_blocked` | ✅ | **Exit run.** Write `run_end` ledger entry with `exit_reason: "intake_blocked"`. Surface `partial_spec_path` and `reason` to user. Do NOT spawn anything further. |
| `planning_complete` | ✅ | Update stage-state → "execute-control". Spawn Execute-Control Agent. |
| `planning_needs_research` | ✅ | Spawn Research Agent with the question from signal. Keep stage at "planning". |
| `planning_needs_sub_planning` | ✅ | Spawn sub-Planning Agent for the specified sub-scope. Keep stage at "planning". |
| `planning_replan_exhausted` | ✅ | Trigger degradation for the `unresolvable_issues` list. Preserve `partial_plan_ref`. Continue other scopes via Execute-Control. |
| `research_complete` | ✅ | Re-spawn Planning Agent with research findings attached. |
| `research_inconclusive` | ✅ | Log `anomaly` entry (severity: low). Re-spawn the requesting stage (usually Planning) with `best_guess` attached AND `confidence < 0.5` flag so the requester records any derived decision with low confidence. Does NOT consume degradation budget by itself. |
| `dispatch_batch` | ✅ | Read batch spec from signal. Spawn N Execute Agents (parallel or sequential per `concurrency_mode`). |
| `dispatch_exhausted` | ✅ | Route to Planning for replan. Consumes `replan_iterations` budget. If already exhausted → trigger degradation for all remaining pending milestones. |
| `execute_complete` | ✅ | Mark task as complete in `stage-state.current_batch`. Check if batch settled (all tasks complete or failed). If not settled → wait. If settled → see "batch settled" rule below. |
| `execute_failed` | ✅ | Mark task as failed in `stage-state.current_batch.failed_tasks`. Check if batch settled (all tasks complete or failed). If not settled → wait. If settled → see "batch settled" rule below. |
| `review_dispatch` | ✅ | Spawn N review sub-agents per the dispatch list. |
| `review_sub_verdict` | ✅ | Check if all review sub-agents in this batch are done. If yes → spawn Merge. If no → wait. |
| `review_merged` | ✅ | **Always commit to git first using `payload.commit_message`** (hard rule). Then route: `pass`/`pass_with_warnings` → Execute-Control next batch; `fail` + `review_iterations_per_batch` remaining → Planning replan; `fail` + `review_iterations_per_batch` exhausted → degrade. |
| `stage_exhausted` | ✅ | Trigger degradation for this scope. Log. Continue other scopes if any. |
| `all_complete` | ✅ | Generate delivery bundle. Write `run_end` with `exit_reason: "all_complete"`. Kernel exits. |

### Batch-settled rule (shared by `execute_complete` and `execute_failed`)

Applies when all tasks in the current batch have returned either `execute_complete` or `execute_failed`. On settlement, **always spawn Review-Plan** with the full batch input (both `execute_complete` and `execute_failed` task artifacts; `failed_tasks[]` listed separately so playbooks know which scopes are partial). Per `contracts/dispatch-signal.md`, review runs even when every task failed — partial artifacts and the failure itself still need verdict logging for audit integrity. Review-Plan may dispatch zero playbooks if there is nothing reviewable, producing a minimal verdict that records the failure.

## Coverage status

- Contract declares: **17 signal types**
- Main SKILL.md routing table must contain: **17 rows** (one per type)

After Task 2 of this plan is complete, the diff grep above must return empty.
