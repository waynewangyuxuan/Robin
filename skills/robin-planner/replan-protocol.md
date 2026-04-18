# Replan Protocol

How Planning responds when re-invoked (triggered by review failure,
research return, or degradation). Used in Planning Phase 1 when
`trigger: "replan"`.

**Core principle**: replan is **incremental revision**, not rewrite.
The previous plan mostly worked; only the parts Review flagged, or the
parts impacted by new research findings, need change. Preserve
everything else.

---

## Two sub-cases of replan

Planning receives `trigger: "replan"` in two sub-situations, indicated by
`rework_reason.kind`:

### A. `review_fail`

Review produced a failing merged verdict. One or more milestones'
implementations didn't meet their gate criteria.

### B. `research_return`

Earlier Planning returned `planning_needs_research` for a specific
question. Research has produced findings. You're re-invoked to
incorporate them.

Both are replans, handled similarly but with different inputs.

---

## Step-by-step for `review_fail`

### Step 1: Read the merged verdict

Load the `merged_verdict_path` from your input. It contains:

- `overall_status: fail`
- `consolidated_issues` with severity, location, description, rationale,
  suggested_action

Focus on **blocking** issues first. Quality and advisory issues may or
may not require plan changes.

### Step 2: For each blocking issue, diagnose the root cause

Every blocking issue falls into one of three categories:

#### Category 2A: Plan-level problem

The spec / contract / decision / convention was wrong or ambiguous.
Example:

- Contract said "endpoint returns user object" without specifying
  email uniqueness behavior. Execute implemented without the
  uniqueness check. Review flagged. **Root cause**: contract was
  under-specified.

**Action**: revise the contract. Write new spec version (new spec_id,
`relations[].supersedes: old-spec-id`). Old spec goes to `state:
superseded`.

#### Category 2B: Execute-level problem

Plan was correct; Execute misinterpreted or missed it. Example:

- Contract clearly specified uniqueness, but Execute didn't implement
  the check. Review flagged.

**Action**: don't change the plan. Add a `context-*.yaml` spec that
will guide the next Execute attempt:

```yaml
spec_id: "context-rework-batch3-m2-001"
type: context
state: active

intent:
  summary: "Rework guidance for m2-api-users: enforce uniqueness check"
  detail: |
    Previous execute attempt of m2-api-users did not implement the
    uniqueness check required by contract-api-users-001. The check is
    explicit in that contract and must be added.

    Specifically, before INSERT, the handler must query by email and
    return EmailTakenError (409) if exists.
indexing:
  type: context
  priority: P0
  layer: task
  tags: ["rework-guidance", "batch-3"]

provenance:
  source_type: planning_derived
  confidence: 1.0
  source_ref: "replan after review-merged batch-3 iter 1"
  produced_by_agent: "planning-replan"
  produced_at: "{timestamp}"

relations:
  - type: relates_to
    ref: "contract-api-users-001"
anchors: []
```

The rework context spec is picked up by the next Execute invocation
of this milestone via its `context_refs`.

#### Category 2C: Both

The plan had a gap AND Execute's interpretation was off. Address both:
revise the plan AND write rework guidance.

### Step 3: For `pass_with_warnings` / quality issues

Optional to address. If the quality issue points to a systemic
convention gap (e.g., "no error handling anywhere"), consider adding
a `convention-*.yaml` spec so future Execute iterations follow it.

If it's a one-off quality issue (e.g., "this function is 5 lines over
limit"), usually not worth revising the plan — note in a rework
context spec and move on.

### Step 4: Mark the failed milestone(s) for retry

The milestone(s) whose execute output failed review need another
Execute pass. Update their status in progress.yaml:

- Was: `in_progress` (Execute attempted but didn't pass review)
- To: `pending` (ready to be re-dispatched by Scheduler)

This lets Scheduler re-dispatch them in the next batch.

### Step 5: Do NOT restart already-passed milestones

If batch 3 had milestones {m2, m3, m4} and only m2 failed review,
leave m3 and m4 as-is (`completed`). Don't re-execute them.

### Step 6: Produce a minimal updated plan

After revisions, your output plan includes:

- Any superseded specs with relations updated
- Any new rework context specs
- Milestones marked `pending` for retry
- All previously-passing milestones untouched

Then emit `planning_complete` (iteration counter advances).

---

## Step-by-step for `research_return`

### Step 1: Read the findings

Findings are at `rework_reason.details.findings_path`. Read them.

Findings format typically:
- Question that was asked
- Research result (recommendation, with reasoning)
- Confidence
- Follow-up questions (optional)

### Step 2: Integrate findings into your model

Depending on what was asked, integrate into:

- **Decision**: write a `decision-*.yaml` spec using the research
  result. Use `provenance.source_type: research_derived` with
  confidence matching research's confidence.
- **Contract detail**: update an existing contract (supersede with new
  version) based on findings.
- **Constraint**: if findings revealed a constraint you didn't know
  about (e.g., "Vercel Postgres has 1GB free tier limit"), write a
  constraint spec.

### Step 3: Resume the phase that was blocked

The original `planning_needs_research` was returned from some phase.
Figure out which, and resume there.

Typically:
- Research about decisions → resume from Phase 2 (Decisions)
- Research about contract design → resume from Phase 4 (Contracts)

You may not need to re-run all phases — only the one that was blocked,
plus downstream phases that depend on its output.

### Step 4: Continue to completion or further replan

After integrating, either:

- Complete the plan and emit `planning_complete`
- Hit another blocker and emit `planning_needs_research` again (if
  budget allows)
- Run out of budget and emit `planning_replan_exhausted`

---

## Using `supersedes` correctly

When a spec is replaced:

### Old spec (was `active`):

```yaml
spec_id: "decision-auth-001"
state: superseded
# everything else unchanged
relations:
  - type: superseded_by
    ref: "decision-auth-002"
```

### New spec:

```yaml
spec_id: "decision-auth-002"
state: active
intent:
  summary: "Use Clerk for authentication (supersedes decision-auth-001)"
  detail: |
    Previous decision to use NextAuth.js is superseded. New decision:
    use Clerk.

    Reason for supersession: review revealed NextAuth required extensive
    custom configuration for the OAuth providers user specified; Clerk
    provides these out-of-box. Replan iter 2, batch 3 review fail.
    ...
relations:
  - type: supersedes
    ref: "decision-auth-001"
provenance:
  source_type: planning_derived
  confidence: 0.85
  source_ref: "replan iter 2 after batch-3 review fail"
  produced_by_agent: "planning-replan"
  produced_at: "..."
```

Both specs stay on disk. Context-pulling skips superseded specs (loads
the successor instead).

---

## Do NOT do

### Don't rewrite

It's tempting to "start fresh" when Review fails. Don't. Most of the
plan works; rewriting discards the working parts and costs
replan-budget.

### Don't increase scope

Replan fixes existing plan issues. It does NOT add new intents or new
features. If Review revealed a real new requirement, that's a
degradation of the original plan's completeness and a signal for the
user to re-invoke AI-Robin with updated intake — not for mid-run
scope creep.

### Don't make the same fix twice

If review iter 1 failed and your fix was "add uniqueness check", and
iter 2 failed the same way, the fix wasn't applied correctly. Don't
just re-add the same context spec. Investigate why iter 2's Execute
didn't pick up iter 1's rework guidance:

- Was the context spec `state: active`?
- Was it anchored appropriately?
- Was it listed in the milestone's effective context_refs?

A fix that didn't apply indicates a structural issue, not an Execute
mistake. Fix the structural issue.

### Don't silently change unrelated specs

Replan changes the specs flagged by Review. Leave unrelated specs
untouched. If you want to change something unrelated, that's scope
creep — don't.

---

## Budget tracking

Your `remaining_replan_budget` comes in the input. Each replan
invocation consumes 1.

If budget is at 0 and you still have unfixable issues → return
`planning_replan_exhausted`. Don't try to squeeze one more.

If budget is at 1 (this is your last replan) → your output must be
final. If Review fails again, main agent will degrade. So focus on the
most critical blocking issues; skip quality issues.

---

## Output

After replan, emit `planning_complete` with:

- Updated milestones (retry-ready milestones back to `pending`;
  others untouched)
- Updated `next_batch_suggestion` (typically the retry milestone)

The rest of the return signal matches initial planning's output.
Scheduler will pick up and re-dispatch.
