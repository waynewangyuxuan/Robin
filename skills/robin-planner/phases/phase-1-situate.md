# Planning Phase 1: Situate

**Autonomy: explicit (condition-driven)**

Branch based on the `trigger` field in your input.

## `trigger: "initial"`

First planning invocation for this scope.

1. Read all spec_ids listed in `consumer_output.specs_summary`. Build a
   mental model:
   - What does the user want?
   - What have they constrained?
   - What did Intake proxy-decide (and why)?
2. Ensure `META/00-robin-plan/` exists. If not, create it with:
   - `room.yaml` (owner: `ai-robin`, lifecycle: `planning`)
   - empty `spec.md`, empty `progress.yaml`, empty `specs/`
3. Proceed to Phase 2.

## `trigger: "replan"`

Review failed OR research came back — you're being re-invoked to revise.

**Do NOT restart from scratch.** Load `skills/robin-planner/replan-protocol.md`.

The `rework_reason.kind` in your input tells you which sub-case:

- `review_fail`: review verdict flagged issues. Address each consolidated
  issue. Preserve milestones that passed review.
- `research_return`: a previous Planning invocation returned
  `planning_needs_research`. Findings are at `rework_reason.details.
  findings_path`. Integrate them into your mental model, resume from the
  phase that was originally blocked (typically Phase 2 for decisions,
  Phase 4 for contracts).

Either way: make minimal, targeted revisions using `supersedes` relations
rather than overwriting. You don't necessarily walk all 9 phases again —
go only to phases where something changes.

## `trigger: "sub_planning"`

You're producing a sub-plan within a parent's scope.

1. Read `parent_plan_refs` — these specs are non-negotiable constraints
   for your sub-plan
2. Your sub-plan's contracts must honor the parent's contracts at the
   sub-scope's boundary
3. Work within a sub-room (e.g., `META/00-robin-plan-{scope}/`)
4. Proceed to Phase 2, but scope everything to the sub-scope

## Output of this phase

A clear mental model of:
- What scope you're planning (initial / replan / sub / post-research)
- What constraints bind you (from Intake, from parent plan, from
  previous replan iterations)
- What the "fresh work" is vs what's already settled

No disk writes in this phase. Just understanding.
