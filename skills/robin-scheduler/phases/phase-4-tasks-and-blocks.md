# Scheduler Phase 4: Build task specs and handle blocks

**Autonomy: explicit**

Two things happen here: populate the `tasks[]` array for the batch, and
handle any milestones that turned out to be blocked.

## Populate task specs

For each milestone in the selected batch, build a `tasks[]` entry:

```json
{
  "task_id": "{batch_id}-task-{N}",
  "scope": {
    "room": "02-api",
    "milestone": "m2-api",
    "files_or_specs": ["src/routes/users/**", "src/schemas/user.ts"]
  },
  "context_refs": [
    "intent-api-001",
    "contract-api-users-001",
    "decision-api-framework-001",
    "convention-project-001"
  ],
  "depends_on_tasks": []
}
```

## Rules for task specs

- **`task_id`**: `{batch_id}-task-{N}` with zero-padded N
- **`scope.files_or_specs`**: BE SPECIFIC. Don't say `src/**`; say
  `src/routes/users/**, src/schemas/user.ts`. Over-broad scopes cause
  collisions.
- **`context_refs`**: minimal — this is kernel discipline applied to
  Execute Agent. List only what's directly needed:
  - The milestone's intent spec
  - All `contract-*.yaml` the milestone must honor
  - Relevant `decision-*.yaml` for tech choices
  - Relevant `constraint-*.yaml` for bounds
  - Project-level `convention-*.yaml` (usually always included)
- **`depends_on_tasks`**: only in mixed concurrency; task_ids that must
  finish before this one

## Handle blocked milestones

If Phase 1 found milestones whose dependencies are degraded (not
pending, not in-progress, not completed — **degraded**):

1. **Mark them `blocked`** in their Room's `progress.yaml`
2. **Write a `context-*.yaml`** explaining why each is blocked
   (references the degraded dependency spec)
3. **Do NOT invent workarounds** — that's a Planning decision. If the
   user wants a workaround, they re-invoke with updated intake.

If ALL remaining pending milestones are blocked, this invocation's
outcome will be `dispatch_exhausted` (Phase 5).

## Sanity check the batch

Before moving to Phase 5:

1. Every task's `context_refs` point to existing specs
2. File scopes don't overlap — unless the tasks are serial with a
   dependency
3. `depends_on_tasks` form a DAG (no cycles within the batch)
4. `concurrency_mode` matches the structure:
   - `parallel`: zero `depends_on_tasks` anywhere
   - `sequential`: linear chain
   - `mixed`: DAG
5. Batch isn't empty

If any sanity check fails, you have a bug in Phases 1-3 — fix and redo.

## Output

- Fully populated `tasks[]` array
- Any blocked milestones recorded in Rooms' `progress.yaml` and via
  `context-*.yaml` specs
