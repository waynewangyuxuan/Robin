# AI-Robin End-to-End Trace Verification

Six scenarios walked through the routing table in `SKILL.md`. Every step
lists the incoming signal, the exact routing-table row that handles it,
the resulting kernel action, and the next expected signal. Each scenario
MUST terminate (with `run_end` or equivalent) without a dead branch.

This is a human-readable audit. If a future edit to the routing table
breaks a scenario, that's a regression and the edit must be revised.

---

## Scenario 1: Happy path (one-milestone project)

1. User invokes ai-robin with "build a CLI that says hello".
2. Kernel initializes: stage=`intake`, spawns Consumer Agent.
3. Consumer runs intake, emits `intake_complete` (no proxy decisions).
   - Routing: `intake_complete` → spawn Planning Agent.
4. Planning runs, emits `planning_complete` with 1 milestone.
   - Routing: `planning_complete` → spawn Execute-Control.
5. Execute-Control emits `dispatch_batch` with 1 task.
   - Routing: `dispatch_batch` → spawn 1 Execute Agent.
6. Execute Agent emits `execute_complete`.
   - Routing: `execute_complete` → mark task complete in
     `current_batch.tasks[0].status`. Batch settled (1/1 complete).
     Apply batch-settled rule → always spawn Review-Plan.
7. Review-Plan emits `review_dispatch` with 1 playbook (code-quality).
   - Routing: `review_dispatch` → spawn 1 review playbook.
8. Code-quality playbook emits `review_sub_verdict` (pass).
   - Routing: `review_sub_verdict` → all returned → spawn Merge.
9. Merge emits `review_merged` with `commit_message` and
   `overall_status: pass`.
   - Routing: `review_merged` → commit using `payload.commit_message`
     verbatim → back to Execute-Control.
10. Execute-Control has no more milestones, emits `all_complete`.
    - Routing: `all_complete` → write `run_end` ledger entry → exit.

**Status:** Terminates cleanly.

---

## Scenario 2: Research inconclusive

1. Kernel at stage=`planning` after `planning_needs_research`.
2. Research Agent spawned with question `q-auth-lib`, depth=1.
3. Research Agent cannot find confident answer, emits
   `research_inconclusive` with `best_guess: "use Lucia"`, confidence 0.4.
   - Routing: `research_inconclusive` → log `anomaly` entry (severity:
     low) → re-spawn Planning with `best_guess` + `confidence < 0.5`
     flag.
4. Planning receives best_guess, records decision-auth-lib spec with
   `confidence: 0.4, provenance: research_low_confidence`, continues.
5. Planning emits `planning_complete`.
   - Routing: `planning_complete` → spawn Execute-Control. (Continues as
     Scenario 1 from step 5.)

**Status:** Terminates cleanly. The low-confidence decision is
auditable via spec provenance. `research_inconclusive` did NOT by itself
consume degradation budget.

---

## Scenario 3: Mixed-result batch (one failed, two complete)

1. Kernel dispatched batch-2 with 3 tasks (parallel).
2. Task-1 returns `execute_complete`.
   - Routing: mark task-1 complete in `tasks[]`. Batch not settled
     (task-2, task-3 still dispatched). Wait.
3. Task-2 returns `execute_failed` (reason: scope_insufficient).
   - Routing: set `tasks[1].status = "failed"`, append task-2 to
     `failed_tasks[]`. Batch not settled (task-3 still dispatched). Wait.
4. Task-3 returns `execute_complete`.
   - Routing: mark task-3 complete. Batch now settled (all 3 tasks have
     non-`dispatched` status; 2 complete, 1 failed).
     Apply batch-settled rule → **always spawn Review-Plan** with
     `failed_tasks: ["batch-2-task-2"]` in the input.
5. Review-Plan inspects change specs from task-1 and task-3 + the
   failure of task-2. Dispatches playbooks over the completed scopes
   plus a note about partial coverage.
6. Review proceeds as Scenario 1 (sub-verdicts → Merge).
7. Merge emits `review_merged`. For failed/mixed batches the Merge Agent
   typically composes a `review(failed):` header in `commit_message`
   (see `review/merge/phases/phase-4-emit.md`).
   - Routing: commit verbatim. Then:
     - If `overall_status: pass`/`pass_with_warnings` → back to
       Execute-Control (which will see task-2's milestone still
       `in_progress` and form a new batch).
     - If `overall_status: fail` + budget left → Planning replan.
     - If `overall_status: fail` + `review_iterations_per_batch`
       exhausted → degrade.

**Status:** Terminates cleanly regardless of review outcome. No task
is silently skipped; every failure is verdict-logged per the
`contracts/dispatch-signal.md` line-292 rule.

---

## Scenario 4: All-failed batch (every task fails)

1. Kernel dispatched batch-5 with 2 tasks.
2. Both tasks return `execute_failed` (task-1 reason:
   `environment_blocker`; task-2 reason: `scope_insufficient`).
   - Routing on first: mark failed, append to `failed_tasks`. Batch not
     settled. Wait.
   - Routing on second: mark failed, append to `failed_tasks`. Batch
     settled. Apply batch-settled rule → **always spawn Review-Plan**
     (per I1 fix; do not skip review even when all failed).
3. Review-Plan receives input where every task is in `failed_tasks`.
   May dispatch zero playbooks (nothing reviewable) OR dispatch a
   code-quality playbook scoped to `partial_artifacts[]` if any
   artifacts exist.
4. If zero playbooks dispatched: `review_dispatch.playbooks = []`.
   Kernel treats as the "zero sub-verdicts" path: Merge is still spawned
   per `review/merge/SKILL.md` line 77. Merge produces the fallback
   `review(anomaly):` verdict with `overall_status: fail`.
5. If playbooks dispatched over partial artifacts: normal
   sub-verdict → Merge flow.
6. Kernel commits verbatim using `payload.commit_message` (either a
   `review(failed):` or `review(anomaly):` header).
7. `fail` + budget-remaining → Planning replan. `fail` +
   `review_iterations_per_batch` exhausted → degrade batch-5.

**Status:** Terminates cleanly. All failures are verdict-logged; the
audit trail records the exact attempt via the commit + ledger.

---

## Scenario 5: Planning replan exhausted

1. Batch-3 review failed twice (iterations 1 and 2, both flagged the
   same issue).
2. After 2nd fail, kernel commits the failed attempt verbatim via
   `payload.commit_message`, decrements
   `review_iterations_per_batch[batch-3]` to 0.
3. Kernel consults budget → `review_iterations_per_batch[batch-3]`
   exhausted.
4. Degradation triggered for batch-3 (see `degradation-policy.md` —
   kernel writes context-degraded spec, commits with the deterministic
   `[degradation] <scope>: <short reason>` kernel-composed message).
5. Kernel returns to Execute-Control for next batch.
6. Parallel scenario: suppose Planning returned
   `planning_replan_exhausted` at some point (replan budget also spent).
   - Routing: `planning_replan_exhausted` → trigger degradation for
     `unresolvable_issues` list → continue other scopes via
     Execute-Control.
7. Execute-Control sees `degraded_milestones` includes batch-3's
   milestones, skips them, forms next batch from remaining pending.
8. Eventually `all_complete` (possibly with many degraded milestones) or
   `dispatch_exhausted` if all remaining are blocked on degraded deps.

**Status:** Terminates cleanly. Degradations surface in
escalation-notice; `run_end` carries degradation counts.

---

## Scenario 6: Intake blocked

1. User invokes ai-robin with "something vague I don't want to
   elaborate".
2. Consumer Agent runs intake, tries to extract decisions; user responds
   with dismissive one-liners or stops responding after turn 3.
3. Consumer emits `intake_blocked` with `reason:
   input_fundamentally_incomplete`.
   - Routing: `intake_blocked` → write `run_end` with
     `exit_reason: "intake_blocked"` → surface `partial_spec_path` +
     `reason` to user → exit. No domain work attempted.

**Status:** Terminates cleanly. User can retry with more input.

---

## Coverage check

Every signal type declared in `contracts/dispatch-signal.md` is exercised
by at least one scenario above:

- Scenario 1: `intake_complete`, `planning_complete`, `dispatch_batch`,
  `execute_complete`, `review_dispatch`, `review_sub_verdict`,
  `review_merged`, `all_complete`
- Scenario 2: `planning_needs_research`, `research_inconclusive`,
  `research_complete` (Scenario 2 implies the happy-path variant too)
- Scenario 3: `execute_failed` in a mixed batch; exercises the
  "at least one complete" branch of the batch-settled rule
- Scenario 4: `execute_failed` exclusively; exercises the "all failed"
  branch, including the `review(anomaly):` fallback
- Scenario 5: `planning_replan_exhausted`, `stage_exhausted` (implied in
  degradation path)
- Scenario 6: `intake_blocked`
- Not covered explicitly: `planning_needs_sub_planning`,
  `dispatch_exhausted` — both share routing patterns with
  `planning_needs_research` and `planning_replan_exhausted`
  respectively. Add scenarios if behavior diverges.

If a new signal type is added to the contract, a new scenario (or
extension of an existing one) MUST be added here.
