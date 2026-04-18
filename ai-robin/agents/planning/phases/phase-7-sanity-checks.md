# Planning Phase 7: Sanity checks

**Autonomy: guided**

Self-review before writing out or emitting. If any check fails, iterate
within Planning — don't return a broken plan.

## The seven checks

1. **All intents covered**: every `intent-*.yaml` from Consumer has at
   least one milestone addressing it. An intent with no milestone is a
   planning bug — either the intent was missed or it should be
   explicitly marked out-of-scope.

2. **All constraints respected**: no milestone violates any
   `constraint-*.yaml`. E.g., if a constraint says "no server required",
   no milestone should create a server.

3. **Contracts complete**: every cross-module call path has a contract
   spec. Scan milestones — for each pair of milestones where A's output
   is B's input, there must be a contract covering that interface.

4. **Milestone count reasonable**: under `max_total_milestones_attempted`
   (default 50). If near this limit, reconsider decomposition — likely
   over-decomposed.

5. **No circular dependencies**: the milestone graph is a DAG. Walk
   `depends_on` chains; any cycle is a bug.

6. **Gate criteria testable**: every milestone's gate can be checked by
   a review playbook or automated test. Re-read each gate; can you name
   the playbook that would check it?

7. **At least one entry milestone**: at least one milestone has empty
   `depends_on`. Otherwise Execute-Control can't start.

## Fixing failures

For each failing check:

- **Missing intent coverage** → add milestone(s) for the uncovered
  intent, or explicitly mark the intent as out-of-scope (rare — usually
  not allowed, but possible if user's input was scope-reducing)
- **Constraint violation** → revise the offending milestone's
  deliverable, or replace the milestone approach
- **Missing contract** → go back to Phase 4, design it
- **Too many milestones** → combine adjacent milestones with same Room
  and similar dependencies
- **Circular dependency** → you've made a logic error; one side of the
  cycle doesn't actually need the other
- **Untestable gate** → rewrite the gate criterion to be concrete and
  mechanically checkable
- **No entry milestone** → you have a global cycle or missed a
  foundational milestone (DB, project setup, etc.)

## When iteration doesn't help

If you're stuck and can't resolve all checks:

- Budget still available → return `planning_needs_research` for the
  blocker
- Budget exhausted → return `planning_replan_exhausted` with what IS
  valid; main agent degrades the unfixable scope

## Output

Either:
- All checks pass → proceed to Phase 8 (write)
- Some checks failed and fixed → rerun this phase
- Unresolvable → skip to Phase 9 with non-complete signal

Do NOT proceed to Phase 8 with known failing checks. Writing an
incoherent plan to disk pollutes the run.
