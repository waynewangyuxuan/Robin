# Execute Phase 2: Plan changes and implement

**Autonomy: guided** (for implementation details), **explicit**
(for adherence to contracts and conventions)

## Internal planning first

Before writing any code, produce an internal plan (scratch, not
persisted):

1. **What files will be created / modified / deleted?**
2. **What is the natural implementation order?** (e.g., types before
   functions that use them; schema before queries)
3. **What existing anchors will need updating?** (if code at a spec's
   anchor location is being changed)
4. **What tests will you write?** (per project's convention specs)

This is a tactical plan, not a strategic one. Planning Agent did the
strategic planning. You're deciding HOW, not WHAT.

## Implementation rules

Follow the loaded context:

### Contracts strictly

The API shapes, function signatures, data types, and error shapes
declared in `contract-*.yaml` are binding. Don't deviate.

**If you find yourself thinking a contract is wrong, DO NOT silently
change it.** Return `execute_failed` with
`reason: "contract_needs_revision"` so Planning can address it.

### Decisions fully

Chosen framework, chosen patterns, chosen libraries. Don't introduce a
new library because you like it better — that's a plan-level decision.

### Conventions consistently

Naming, file organization, error handling. Pattern-match existing code
in the project when unsure.

### Tests per convention

If the project specifies test coverage, write tests. If not, use
reasonable defaults (happy path + a few edge cases for any public API).

## Stay in scope

Only modify files matching `task.scope.files_or_specs`. If you find
you need to change something outside your scope:

- If it's a minor fix (a single-line import path update), note it
- If it's a real change (modifying another module's logic), STOP.
  Return `execute_failed` with `reason: "scope_insufficient"` — this
  is Execute-Control's problem to solve.

## Output

Source code files written to the working tree. Feeds Phase 3
(anchor maintenance).
