# Intake Phase 7: Initialize Room structure

**Autonomy: explicit (follows feature-room-spec conventions)**

Based on the project's scope and scale inferred in Phases 1-2, create the
Feature Room directory structure.

## Two common patterns

### Single-scope project

A small project with one coherent feature area:

```
{project_root}/META/
├── project.yaml
├── 00-project-room/          # Global conventions and constraints
│   ├── room.yaml
│   ├── spec.md
│   ├── progress.yaml
│   └── specs/
├── 01-core/                  # The one main feature area
│   ├── room.yaml
│   ├── spec.md
│   ├── progress.yaml
│   └── specs/
└── 00-robin-plan/         # Empty, for Planning Agent
    ├── room.yaml
    └── specs/
```

### Multi-scope project

A larger project with distinct functional domains:

```
{project_root}/META/
├── project.yaml
├── 00-project-room/
├── 01-auth/
├── 02-dashboard/
├── 03-api/
├── 04-infrastructure/
└── 00-robin-plan/
```

## How many rooms at this stage

Intake does **epic-level** decomposition only. Planning does finer
decomposition.

- Single-scope or tiny project: 1 feature room + `00-project-room` +
  `00-robin-plan` = 3 rooms total
- Medium project: 2-5 feature rooms + infrastructure
- Large project: 3-8 feature rooms

**Never more than 8 rooms at Intake stage.** If you're tempted, the
extras are either:
- Sub-features that Planning will split out → leave as one room here
- Parallel-deployable subsystems → OK to split, but cap at 8

## Per-room files

For each room you create:

- **`room.yaml`**: metadata (id, name, parent, lifecycle: `planning`,
  owner: `ai-robin`, depends_on: [])
- **`spec.md`**: initial template with empty "Intent / Decisions /
  Constraints / Contracts / Conventions / Context" sections. Populated
  by Phase 8.
- **`progress.yaml`**: empty milestones list. Planning will fill it.
- **`specs/`**: empty directory. Phase 8 writes here.

## `00-robin-plan` is special

This room is Planning's workspace. Create it with:
- Empty `room.yaml` (owner: `ai-robin`, lifecycle: `planning`)
- Empty `specs/` directory
- No `spec.md`, no `progress.yaml` (Planning will create as needed)

Intake does not write anything into this room.

## `_tree.yaml`

Write `META/00-project-room/_tree.yaml` indexing all rooms created. This
is the canonical room index that downstream agents use to find things.

## Do NOT do

- Do not decompose into micro-rooms. Planning does that.
- Do not create rooms for things that don't have corresponding
  intent-level specs. A room without intent is noise.
- Do not skip creating `00-robin-plan` — Planning will fail without
  it.
