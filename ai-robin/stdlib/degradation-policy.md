# Degradation Policy

What AI-Robin does when something can't be finished cleanly. Degradation is
the **systematic** alternative to crashing or escalating to human mid-run.
It replaces "escalate" with "set aside, continue, report at end".

Used by: main agent (triggers degradations), Planning Agent (responds to
degraded dependencies when planning), Consumer Agent (sees user's degradation
preferences at intake, rarely).

---

## Core principle

**Degradation preserves the run.** When a scope cannot be completed, the run
does not terminate. The scope is marked, notated, and the kernel continues
with other scopes. The final delivery contains everything that worked plus a
clear notice of what didn't.

This is the structural replacement for "stop and ask human". There is no
human to stop for.

---

## Triggers

Degradation is triggered by exactly one of these conditions:

1. **A hard budget (from `iteration-budgets.md`) hits zero for a scope.**
   - Review iterations exhausted for a batch
   - Replan iterations exhausted for a scope
   - Research depth exhausted for a question
   - Global wall-clock or token budget exhausted (triggers a different kind of
     degradation — see "Global degradation" below)

2. **A sub-agent returns an "exhausted" signal type.**
   - `planning_replan_exhausted`
   - `dispatch_exhausted`
   - `research_inconclusive` (may or may not lead to degradation depending on
     requesting stage's tolerance)
   - `stage_exhausted` (generic)

3. **Repeated anomalies on the same sub-agent.** Per `kernel-discipline.md`,
   the 2nd malformed signal from the same sub-agent triggers
   stage-appropriate degradation.

No other triggers. The kernel cannot degrade on a hunch.

---

## Degradation procedure

When any trigger fires, the kernel executes this sequence:

### Step 1: Identify the scope

"What exactly is being degraded?" — one of:

- A **batch**: a specific batch_id's execution cannot be completed.
- A **milestone**: this milestone (and potentially milestones that depend on
  it) cannot be completed.
- A **research question**: the question will not be definitively answered;
  requesting stage gets "best effort" answer.
- A **plan scope**: a whole plan section cannot be made coherent.
- **All remaining work** (global): wall-clock or token limit means we must
  stop everything.

The scope is recorded in a `context-degraded-*.yaml` spec (see below for
format).

### Step 2: Write the degradation spec

A new spec is created in the relevant Room (or in the root project Room for
cross-cutting degradations):

```yaml
spec_id: "context-degraded-{scope-short-name}-{NNN}"
type: context
state: degraded  # special state — not in normal Feature Room taxonomy, but valid
intent:
  summary: "Scope {X} was degraded; see escalation-notice"
  detail: |
    **Scope**: {description}

    **What was being attempted**: {from the original spec(s)}

    **Why degraded**: {trigger description, e.g., "review_iterations_per_batch
    exhausted after 2 failed reviews"}

    **What was tried**:
    - {attempt 1 summary, ref ledger entry N}
    - {attempt 2 summary, ref ledger entry M}
    - ...

    **Current state on disk**: {exactly what exists}

    **Suggested resolution**: {concrete advice for human verifier}
constraints: []
indexing:
  type: context
  priority: P0
  layer: project
  domain: "degradation"
  tags: ["degraded", "{scope-type}"]
provenance:
  source_type: degradation_trigger
  confidence: 1.0
  source_ref: "ledger entry {degradation_triggered entry_id}"
relations:
  - type: "relates_to"
    ref: "{the spec_id(s) of the scope being degraded}"
anchors: []
```

Note: `state: degraded` is an AI-Robin-specific extension of the Feature Room
state taxonomy. It is NOT draft (not waiting for review), NOT stale (not out
of sync with code), NOT deprecated (we didn't deprecate anything). It means
"this represents a scope that was attempted but could not be completed".

Any existing spec that was part of the degraded scope is ALSO marked
`state: degraded` (not deleted), with a `relations[].supersedes` pointing to
the degradation context spec if appropriate.

### Step 3: Update stage-state

Move the degraded scope from `in_progress_milestones` to
`degraded_milestones` in `stage-state.plan_pointer`. If the degraded scope is
something other than a milestone (e.g., a research question, or a whole plan
section), update appropriately — the structure of `plan_pointer` may need
extension for non-milestone degradations.

### Step 4: Propagate

If the degraded scope is something other scopes depended on, those downstream
scopes may also need to degrade or re-plan. This is NOT the kernel's
decision — it invokes Planning Agent with the degradation as input, and
Planning either:
- Adjusts the plan to skip the degraded dependency (if possible)
- Marks dependent scopes as blocked (which may in turn become degraded)

Planning's response to degradation is defined in `planning/replan-protocol.md`.

### Step 5: Append to escalation-notice

Main agent writes a new section to `.ai-robin/escalation-notice.md` per the
format in `contracts/escalation-notice.md`. This is append-only; once written,
the section is not edited (only corrected with a new section if needed).

### Step 6: Commit the degradation

The degradation itself is a state change visible to the human verifier. It
gets committed to git:

```
git add <new context-degraded spec> <updated specs with state:degraded>
         <.ai-robin/escalation-notice.md>
git commit -m "[degradation] <scope>: <short reason>"
```

This preserves the degradation in git history alongside code changes. The
commit message convention uses `[degradation]` as the room-id-equivalent.

### Step 7: Log to ledger

```json
{
  "entry_type": "degradation_triggered",
  "content": {
    "scope": "batch-3",
    "reason": "review_iterations_per_batch exhausted after 2 fails",
    "known_issue_spec_id": "context-degraded-batch3-001"
  }
}
```

### Step 8: Continue

Kernel returns to its dispatch loop. `current_batch` clears. Next routing
action is typically back to Execute-Control to form the next batch, skipping
the degraded scope's downstream work if Planning has re-planned around it.

---

## Global degradation

When a **global budget** is exhausted (wall-clock or tokens), the procedure
is different:

1. Kernel stops accepting new dispatches (doesn't spawn anything new).
2. In-flight sub-agents are allowed to complete (do not kill mid-run).
3. As each in-flight agent returns, its signal is processed normally BUT
   routing always goes to degrade-remaining instead of next stage.
4. Once all in-flight agents have returned, kernel marks every remaining
   pending scope as degraded (simultaneous mass degradation).
5. Escalation-notice gets one large section describing global exhaustion
   plus a list of all degraded scopes.
6. Single large commit finalizes everything.
7. `run_end` ledger entry with `exit_reason: "global_budget_exhausted"`.

---

## What degradation is NOT

- **Not silent failure.** Every degradation is loudly documented.
- **Not retry-later.** Degradations stop being attempted within this run. If
  the user wants to retry, they address the root cause and invoke AI-Robin
  again, possibly with the previous run's state as a starting point.
- **Not partial completion.** A degraded scope is not "completed 80%". It's
  "attempted and stopped". Whatever partial artifacts exist on disk are
  described in the context-degraded spec with clear labeling (e.g., "stub
  implementation that accepts any input", "no code produced, only spec").
- **Not a judgment of fault.** The degradation spec describes facts, not
  blame. Whether the problem was unclear requirements, a fundamentally hard
  problem, or a sub-agent limitation is for the human to decide.

---

## Degradation severity

Some degradations are more serious than others. The kernel does not make this
judgment — it reports degradations equally — but the escalation-notice's
"summary" paragraph (written at run_end) may characterize severity:

- **Low-severity**: small, isolated scope; rest of project unaffected. Example:
  one optional feature couldn't be implemented.
- **Medium-severity**: moderately important scope with downstream effects.
  Example: a shared library degraded, so dependent features had to be
  simplified.
- **High-severity**: core scope that undermines the run's value. Example:
  authentication degraded, so the whole app isn't secure.

This characterization is written by main agent at run_end based on the
position of degraded milestones in the plan's dependency graph. It's a hint
for the human verifier, not a normative judgment.

---

## Interaction with git

Every degradation produces a commit. This means a run with 2 degradations has
at least 2 degradation-commits plus all the normal commits. The git log tells
the story:

```
feat(api): implement user CRUD endpoints (batch-1 review pass)
feat(db): add users table migration (batch-2 review pass)
review(failed): batch-3 iteration 1 — uniqueness check missing
review(failed): batch-3 iteration 2 — uniqueness check still missing
degradation: auth (batch-3): review_iterations_per_batch exhausted
feat(frontend): expense dashboard shell (batch-4 review pass)
...
```

The failed review commits (also hard-rule from `kernel-discipline.md`) show
the path that led to degradation. The degradation commit marks the decision
to stop.

---

## Recovering from degradation (user flow)

After a run with degradations, the user looks at `ESCALATIONS.md` and decides
per each degradation:

1. **Accept it** — the degraded scope isn't needed, accept partial delivery.
2. **Address the cause and re-run** — modify intake to resolve the ambiguity,
   invoke AI-Robin again. The new run can be told to resume at the degraded
   milestone(s) rather than restart.
3. **Hand off to human engineer** — degraded scope is something a person
   should do by hand, not the AI.

Supporting "resume from degradation" requires that AI-Robin be invokable with
a starting scope. This is implementation detail, not currently in the design
scope, but the context-degraded specs contain everything needed to resume.
