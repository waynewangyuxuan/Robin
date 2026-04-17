# Planning Phase 3: Module decomposition

**Autonomy: guided**

Decompose the project into modules — independent units that Execute Agents
can work on in parallel once contracts are defined.

## Module properties

Good modules are:

- **Independent**: can be worked on without blocking others (once contracts
  are defined)
- **Coherent**: group related functionality; not arbitrary slices
- **Sized for Execute**: roughly 50-300 lines of code per module. Small
  enough that one Execute invocation can produce it.

## Map modules to Rooms

Modules become sub-Rooms in the Feature Room structure:

```
META/
├── 00-project-room/
├── 00-ai-robin-plan/          # Your planning output
├── 01-{module-a}/
├── 02-{module-b}/
├── 03-{module-c}/
└── ...
```

If Consumer already created epic-level Rooms, further decompose those
into feature-level Rooms. If Consumer created feature-level, you may
just populate them.

## Don't over-decompose

A 5-module project shouldn't become 15 modules just because you can.
Parallelism gain trades off against coordination overhead (more contracts
to design, more milestones to track).

Rough guidance:
- Small project: 3-6 modules
- Medium: 6-12 modules
- Large: 12-20 modules
- More than 20 → you've over-decomposed; combine

When in doubt: fewer, larger modules.

## Boundaries should align with contracts

A good module boundary is one where:
- The contract between this module and its neighbors is well-definable
- Each side could be implemented with no knowledge of the other side's
  internals (only knowledge of the contract)
- Tests for this module don't require the other modules to exist

If you can't define a clean contract at a proposed boundary, the
boundary is wrong — either the two modules should be combined, or the
split should be elsewhere.

## Output

Updated Room structure (created missing Rooms, documented module mapping
in `META/00-ai-robin-plan/specs/`). Module list feeds Phase 4 (contracts)
and Phase 5 (milestones).
