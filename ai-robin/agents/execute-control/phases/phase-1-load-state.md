# Execute-Control Phase 1: Load state and identify executable milestones

**Autonomy: explicit**

## Load plan state

Read:
- `META/00-ai-robin-plan/progress.yaml` — global milestone registry
- Each affected Room's `progress.yaml` — Room-level milestone status
- `META/00-ai-robin-plan/specs/` — all plan specs (decisions, contracts)
- Any `constraint-*.yaml` tagged with `parallel` or `serial` concerns

Build the dependency graph:
- Nodes = milestones
- Edges = `depends_on` relationships

## Identify executable milestones

A milestone is **executable now** if:
- Status is `pending`
- All `depends_on` milestones are `completed` (not `in_progress`, not
  `degraded`, not `blocked`)

Compute the set of executable milestones.

## Early exit: nothing to do

If executable set is empty:

- **If `pending_milestones` is also empty** → all plan milestones are
  complete or degraded → skip to Phase 5 and return `all_complete`
- **If `pending_milestones` has items but none executable** → they're
  blocked by degraded/blocked dependencies → handle per Phase 4 (mark
  blocked), then skip to Phase 5 and return `dispatch_exhausted` if
  all blocked

## Output

- Executable milestones list
- Dependency graph (needed in Phase 3 for concurrency)
- Any blocked milestones flagged
