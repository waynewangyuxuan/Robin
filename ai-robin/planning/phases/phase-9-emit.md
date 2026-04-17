# Planning Phase 9: Emit return signal

**Autonomy: explicit**

Write your return signal to `.ai-robin/dispatch/inbox/`. Signal type
depends on what happened in Phases 1-8.

## Signal: `planning_complete`

All sanity checks passed; plan is executable.

Payload:

```json
{
  "plan_room": "00-ai-robin-plan",
  "milestones": [
    {
      "milestone_id": "m1-db-schema",
      "depends_on": [],
      "rooms_affected": ["02-database"],
      "contract_spec_ids": ["contract-db-schema-001"]
    },
    {
      "milestone_id": "m2-user-api",
      "depends_on": ["m1-db-schema"],
      "rooms_affected": ["03-api"],
      "contract_spec_ids": ["contract-api-users-001"]
    }
    // ... every milestone
  ],
  "next_batch_suggestion": "m1-db-schema"
}
```

`next_batch_suggestion` is a hint to Execute-Control: which milestone(s)
to execute first. Typically those with empty `depends_on`, or whose
dependencies are already completed in a replan scenario.

## Signal: `planning_needs_research`

A specific question blocks decision-making or contract design.

Payload:

```json
{
  "question": "specific question",
  "context": "why this matters for the plan",
  "depth_hint": 1 | 2
}
```

Be specific:
- ❌ "What's the best auth approach?"
- ✅ "For a Next.js 14 app on Vercel with ~1000 users expected,
    compare Clerk vs NextAuth.js vs Lucia on OAuth support, session
    management, and TCO at that scale"

Main agent will spawn Research. When research returns, you'll be
re-spawned with `trigger: "replan"`, `rework_reason.kind:
"research_return"`.

Don't overuse research. It consumes budget and adds latency. If you can
make a reasonable decision with current info (recording alternatives
considered), do that instead.

## Signal: `planning_needs_sub_planning`

You identified a scope whose complexity rivals the top-level project
— it needs its own decomposition pass.

Example: "authentication" expanding to its own sub-tree of
user-management / session-management / oauth-integration /
email-verification.

Payload:

```json
{
  "sub_scope_description": "string",
  "parent_plan_refs": ["string — contracts and constraints the sub-plan
                        must honor"]
}
```

Main agent spawns a nested Planning. When it returns, you'll be
re-spawned to integrate the sub-plan.

## Signal: `planning_replan_exhausted`

Your replan budget is at zero and the current iteration can't produce a
valid plan.

Only return this if:
- `remaining_replan_budget == 0` in your input
- Phase 7 checks are still failing
- Iteration within this invocation can't fix it

Payload:

```json
{
  "exhausted_budget": "replan_iterations",
  "unresolvable_issues": ["string — what couldn't be resolved"],
  "partial_plan_ref": "string — path or description of the plan parts
                       that ARE valid; main agent preserves these"
}
```

Main agent will degrade affected scopes and continue with the partial
plan for everything else.

## Signal file format

Write to `.ai-robin/dispatch/inbox/{signal_id}.json`.

`signal_id` format: `planning-{YYYYMMDDTHHMMSS}-{8-char-hex}`

See `contracts/dispatch-signal.md` for the full wrapping schema
(produced_by, budget_consumed, artifacts, self_check).

## After emitting

Your work is done. Main agent picks up the signal on its next turn.
Output nothing else; the sub-agent invocation terminates after writing
the signal file.
