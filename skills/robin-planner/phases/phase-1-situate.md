# Planning Phase 1: Situate

**Autonomy: explicit (condition-driven)**

Branch based on the `trigger` field in your input. Then, within
`trigger: "initial"`, sub-branch on `mode` (propagated from Intake's
`intake_complete.payload.mode`).

## `trigger: "initial"` — sub-branch by mode

First planning invocation for this scope.

Steps that always apply:

1. Read all spec_ids listed in `consumer_output.specs_summary`. Build a
   mental model:
   - What does the user want?
   - What have they constrained?
   - What did Intake proxy-decide (and why)?
2. Ensure `META/00-robin-plan/` exists. If not, create it with:
   - `room.yaml` (owner: `ai-robin`, lifecycle: `planning`)
   - empty `spec.md`, empty `progress.yaml`, empty `specs/`

Then sub-branch on `mode`:

### `mode: "new_project"`

The default flow. Proceed directly to Phase 2 with a blank canvas: no
pre-existing contracts to honor, no prior milestones, fresh numbering
throughout.

### `mode: "incremental_feature"`

3. Load **all rooms' existing active specs** — every `contract-*.yaml`,
   `decision-*.yaml`, `convention-*.yaml`, and `constraint-*.yaml` in
   each room — and treat them as **frozen context**. Do NOT supersede
   or revise any of them unless the Intake delta explicitly requires it.
4. Load the **existing `progress.yaml`** from `META/00-robin-plan/`
   (and any per-room `progress.yaml` files). Note the highest milestone
   ID used; your new milestones continue from there (e.g., if the
   highest is `m12`, new milestones start at `m13`).
5. The "fresh work" for this invocation is whatever Intake's new specs
   (those with `relations.extends` references in `consumer_output.specs_summary`)
   require — not the whole project.
6. Proceed to Phase 2 (decisions), but treat existing decisions as
   constraints rather than open choices. Phase 4 (contracts) prefers
   reusing existing contracts via `relations.extends`; only emit a
   new contract when the delta genuinely needs one.

### `mode: "bug_fix"`

3. Load existing active specs in the affected room(s) (identified by
   Intake from the bug intent's `relations.relates_to`). Frozen context.
4. Plan SHOULD have one or two milestones max: typically one for the
   fix + regression test, occasionally a second for related cleanup.
5. The acceptance-constraint spec from Intake provides the gate
   criterion for the fix milestone — copy it verbatim into the
   milestone's `gate_criteria`. Mark the milestone `risk: medium` by
   default (bug fixes touch existing code paths), or `high` if the
   bug is in a `risk: high`-classified area (auth, schema, payments).
6. Skip Phases 3 (modules) for trivial fixes — go straight to Phase 5
   (milestones).

### `mode: "pr_continuation"`

3. Load existing active specs same as `incremental_feature`.
4. **Also load the PR diff** from `consumer_output.pr_ref` (or
   `provenance.source_ref` on the Intake-emitted specs). The diff tells
   you what's already done; the plan covers only what remains.
5. Each reviewer-comment-derived constraint from Intake becomes a
   milestone or a check inside an existing milestone. Their `gate_criteria`
   must reference the comment (e.g., "Reviewer @alice's comment on
   apps/api/foo.ts:42 is addressed and the file passes lint+type check").
6. Proceed to Phase 2 but most decisions are already settled by the
   PR's existing implementation — Planner here is mostly closing
   open work, not opening new design space.

## `trigger: "replan"`

Review failed, research came back, OR human checkpoint asked for replan
— you're being re-invoked to revise.

**Do NOT restart from scratch.** Load `skills/robin-planner/replan-protocol.md`.

The `rework_reason.kind` in your input tells you which sub-case:

- `review_fail`: review verdict flagged issues. Address each consolidated
  issue. Preserve milestones that passed review.
- `research_return`: a previous Planning invocation returned
  `planning_needs_research`. Findings are at `rework_reason.details.
  findings_path`. Integrate them into your mental model, resume from the
  phase that was originally blocked (typically Phase 2 for decisions,
  Phase 4 for contracts).
- `human_checkpoint_replan` (Axis 2 — see decision-kernel-pause-checkpoint-001):
  the user paused at a milestone checkpoint and chose `/robin-resume
  --replan`. `rework_reason.paused_milestone_id` tells you which
  milestone they paused at; `rework_reason.user_note` (optional) carries
  their reasoning (free-text from the resume command). The completed
  milestones up to and including `paused_milestone_id` are settled —
  preserve them. The remaining pending milestones are open for revision
  if the user's note suggests changes (and if no note, default to
  re-validating the remaining plan against the just-built state — often
  a small refinement, occasionally a deeper rework).

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
