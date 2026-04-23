# Execute Phase 1: Context pull

**Autonomy: guided** (per `skills/robin-executor/context-pulling.md`)

## Record phase start

Before anything else, run:

```bash
mkdir -p .ai-robin/trace && echo "$(date -u +%s) phase-1-start" >> .ai-robin/trace/{invocation_id}.log
```

Substitute `{invocation_id}` with the value from your input. This is the only timing substrate — `wall_clock_seconds` in your final signal will be computed from this log, not estimated.

## Load specs

Load the specs listed in `task.context_refs`. For each:

- Read the spec yaml
- Check its `state`:
  - `active` — authoritative
  - `draft` — flagged tentative (rare at Execute stage since Planning
    promoted to active)
  - `stale` — cautionary; may need updating during your work
  - `deprecated` / `superseded` — ignored in favor of successors

## Assemble a mental model

From your loaded specs, build:

- **Intent**: what this milestone produces (functionally)
- **Contracts**: the interfaces this code must honor (inputs, outputs,
  side effects, error shapes) — these are binding
- **Decisions**: tech choices that constrain how to implement
- **Conventions**: project-wide rules (naming, error handling, testing,
  code organization)
- **Constraints**: bounds on what you produce (performance, size)

## Do NOT load

- Other Rooms' internal specs (unless referenced by your contracts)
- Previous change specs (history doesn't help you write new code)
- The plan at large (you have the milestone, not the plan)
- Other Execute Agents' outputs (isolation rule)

## Read existing code in scope

- Files matching `scope.files_or_specs` that exist in the working tree
- If this is greenfield, the scope is where files will be CREATED —
  they don't exist yet, that's fine

## Record phase end

Before advancing to Phase 2, run:

```bash
echo "$(date -u +%s) phase-1-end" >> .ai-robin/trace/{invocation_id}.log
```

## Output

A mental model ready for Phase 2. No disk writes yet (the trace log is bookkeeping, not a real artifact).
