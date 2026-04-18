# Planning Phase 8: Write specs and milestones

**Autonomy: explicit**

Persist all generated specs to disk.

## What to write and where

- **Decision specs** → `META/00-robin-plan/specs/decision-*.yaml`
- **Contract specs** → the Room that owns the producing side, or
  `META/00-project-room/specs/` if cross-cutting
- **Derived constraint specs** → relevant Room's `specs/`
  (project-wide constraints → `00-project-room`)
- **Derived convention specs** → typically `00-project-room/specs/`
- **Milestones** → each affected Room's `progress.yaml`, plus the
  master list in `META/00-robin-plan/progress.yaml`

## State

All specs `state: active`. Planning is post-Intake; no human review
intercepts its output. Downstream agents (Scheduler, Execute)
treat Planning's specs as authoritative.

In replan mode, specs that superseded old specs are written new
(with `relations[].supersedes: old-spec-id`); old specs are left in
place but updated to `state: superseded`.

## Sync `spec.md`

After writing spec yamls, update each affected Room's `spec.md` to
reflect the new specs (the Human Projection). See Feature Room docs
for `spec.md` format.

## Sync `_tree.yaml`

If you created new Rooms in Phase 3, update
`META/00-project-room/_tree.yaml` to index them.

## Don't duplicate

If a spec already exists (e.g., Intake's or from a previous Planning
iteration), don't re-create it. Reference it in your new specs'
`relations[]` if needed.

## Output

Filesystem state is now consistent with your in-memory plan. Proceed to
Phase 9 (emit).
