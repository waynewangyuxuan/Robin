# Context Pulling

How Execute Agent loads only the context it needs, nothing more. Used
in Phase 1.

Adapted from Feature Room's `prompt-gen` skill, with modifications:
AI-Robin's context pulling runs inside Execute (not as a separate
skill), skips human-facing prompt formatting, and respects AI-Robin's
state-lifecycle rules.

---

## The discipline

**Load the minimum context needed to complete the task.** Over-loading
pollutes your own working memory, slows Execute, and increases the
chance of following irrelevant conventions.

Under-loading causes you to miss a constraint or contract and produce
wrong code.

Getting this right is the difference between Execute that's fast and
accurate vs. Execute that drifts.

---

## What's in `task.context_refs`

Main agent (via Execute-Control) provides `context_refs` — a list of
spec_ids. These are the specs Execute-Control determined are needed
for this specific task.

Default trust: if a spec is in `context_refs`, it's relevant. Load it.

Exception: if a referenced spec doesn't exist or is malformed, return
`execute_failed` with `reason: "missing_context"`.

---

## Loading order

Load specs in this order (from high-level to detail):

1. **Project-level conventions** (from `00-project-room/specs/
   convention-*.yaml`) — these apply broadly; internalize first
2. **Constraints** relevant to your scope — bounds you must respect
3. **Decisions** relevant to your scope — tech choices
4. **Contracts** you must honor — the interface you produce/consume
5. **Intent** specs — the "why" for the milestone you're implementing
6. **Context** specs — background info, any rework guidance

Processing in this order lets later items be interpreted in the light
of earlier ones (e.g., a contract's error handling makes more sense
after loading the typed-error convention).

---

## State-aware filtering

For each spec in `context_refs`, check its state and handle:

| State | Action |
|---|---|
| `active` | Load, use as authoritative |
| `draft` | Load but flag internally as "tentative". Rare at Execute stage — if it appears, note in `known_issues` |
| `stale` | Load but flag as "cautionary — code may need to be updated to match intent, or spec may need revision" |
| `deprecated` | DO NOT load; skip silently |
| `superseded` | DO NOT load; find the successor via `relations[].superseded_by` and load that instead |
| `degraded` | DO NOT load for implementation; the scope was abandoned |

If a superseded spec's successor is also superseded, chain through
until you find an `active` (or `stale`) successor. If chain ends in
`deprecated`, skip.

---

## Loading related specs

Each spec's `relations[]` may point to others:

- **`depends_on`**: the referenced spec is a precondition; load if
  within scope
- **`relates_to`**: optional context; load only if the spec is itself
  in `context_refs` (don't auto-pull relatives)
- **`supersedes` / `superseded_by`**: used for chain traversal (above)
- **`conflicts_with`**: surface in self-check as a potential issue

**Rule**: only auto-load specs in your `context_refs`. Don't follow
`relates_to` relations into untagged specs — that's how context
bloats. If a relation is important, Execute-Control should have
included it explicitly.

---

## Type-aware context pulling hints

Based on your task's nature, certain spec types weigh more:

### If you're writing API route code

Prioritize:
- Contract specs (the API contract itself; shared type contracts)
- Decision specs (framework, ORM)
- Convention specs (error handling, authentication)

### If you're writing frontend component code

Prioritize:
- Intent specs (what the component is for)
- Contract specs (API contracts the component calls)
- Convention specs (styling, component library, a11y)
- Decision specs (framework)

### If you're writing DB migrations / schema

Prioritize:
- Contract specs (schema contracts)
- Convention specs (migration naming, indexing, etc.)
- Decision specs (DB engine)

### If you're writing tests

Prioritize:
- The contract being tested (defines what to test)
- Convention specs (test conventions, assertion style)
- Intent spec (what "correct" looks like)

---

## Reading existing code

After loading specs, read existing code in your scope:

- Files matching `task.scope.files_or_specs` that already exist
- Look for patterns to follow (imports, naming, error handling
  patterns)
- Note where existing code might need modification vs. where new files
  go

### How much existing code to read

Read files in your scope in full if:
- The task modifies them (you need full context to avoid breaking)
- They're small-to-medium (<300 lines)

Read selectively if:
- A file is very long (>500 lines) — read just the section(s) you'll
  modify, plus imports and top-level declarations
- A file is in your scope but you'll create parallel new files (e.g.,
  your scope is `src/routes/**` but you're creating `src/routes/
  users/create.ts` and only minor tangential reading of existing
  routes helps)

### Read for pattern-matching

When unsure how to structure new code, pattern-match existing code in
the project (if any):

- Naming conventions
- Import paths and organization
- Error handling style
- Test placement
- File structure

Patterns established by existing code are usually right for the
project. Follow them unless a convention spec explicitly overrides.

---

## What NOT to load

- **Other Rooms' internal specs** — only load specs in your
  `context_refs`. If another Room's spec was relevant, Execute-Control
  would have included it.
- **Previous change specs** — change specs record history.
  Historical context isn't useful for writing new code.
- **The plan at large** — you have your milestone and your context.
  You don't need the other milestones or the master plan.
- **Other Execute Agents' outputs** — isolation rule. You work from
  specs, not from other agents' work-in-progress.
- **Degraded specs** — the scope was abandoned.

---

## When context is insufficient

If, while working, you realize the provided context isn't enough:

### Scenario: Contract references a type that isn't in your context

Example: contract-api-users-001 references `contract-type-user-001`,
but `contract-type-user-001` isn't in `context_refs`.

**Action**: load it anyway (follow the `relations[]` explicitly within
the contract system), since this is a direct reference. Note in
`known_issues`: "task spec's context_refs missed
contract-type-user-001; loaded via relation from contract-api-users-001."

Execute-Control should have caught this, but occasionally misses
transitive relations.

### Scenario: Need info that isn't in any spec

Example: you need to know the project's Node.js version; no spec
says.

**Action**: check project configuration files (package.json,
tsconfig.json, Dockerfile) which are in-scope as project reality, not
specs. Use reasonable defaults if still unclear.

Don't fabricate. If a decision is truly needed and not available,
return `execute_failed` with `reason: "missing_context"` and the
specific gap.

### Scenario: Context references contradict

Example: constraint-001 says "no external dependencies" but
decision-001 says "use library X".

**Action**: flag it. Return `execute_failed` with
`reason: "context_contradiction"` and describe the conflict. Planning
should resolve in replan.

---

## Efficiency targets

Rough guidance:

- Task's Phase 1 (context pull) should take a small fraction of total
  Execute time
- Total context loaded: typically 5-15 specs + 1-5 existing code
  files
- Token count of loaded context: ideally < 20k tokens

If you find yourself with 50 specs and 20 files loaded, something's
off — either Execute-Control gave too broad a scope, or the milestone
is too big.

---

## Anti-patterns

- **Load everything just in case**: pollutes working memory; slows
  Execute; models convention inconsistencies across too many files
  into your output.
- **Skip convention specs**: they're short but impactful. Always
  load convention specs in your context_refs.
- **Load degraded or superseded specs "to see what happened"**:
  history isn't your job. If rework guidance is needed, it's in a
  `context-*.yaml` rework spec.
- **Trust context without checking state**: a `stale` spec loaded as
  authoritative produces wrong code. Always check state.
