# Parallelism Identification

How Planning Agent identifies which milestones can run concurrently.
Used in Phase 6.

The goal: maximize parallelism where safe; force serialization only
where necessary. Over-serialization wastes wall-clock time and
defeats the point of multiple Execute Agents.

---

## The guiding principle

**Two milestones are parallel-safe unless you can name a specific
reason they aren't.** Defaulting to serial "just to be safe" gives up
the main benefit of AI-Robin's architecture.

The burden is on identifying why serial is required, not on proving
parallel is safe.

---

## Four sources of serial-requirement

Milestones must be serialized if any of these hold:

### 1. Direct dependency

Milestone B needs artifacts from milestone A: B imports A's code, B
tests call A's functions, B's UI consumes A's API endpoint.

Encoded as: `B.depends_on: [A]`

### 2. File overlap

Milestones A and B both write to the same file. Two Execute Agents
writing to the same file in parallel create merge conflicts or
clobbering.

If file overlap exists, either:
- Redesign so the file is owned by one milestone (preferred)
- Serialize the milestones
- Split the file so each milestone owns a distinct part

### 3. Shared interface layer

Even without file-level overlap, milestones touching the same shared
interface (e.g., `packages/shared/src/`, a common type definition file,
a shared schema) may conflict. The "single writer rule" for shared
interfaces: at any moment, only one milestone may be editing the
shared layer.

### 4. Contract ordering

A milestone that **defines** a contract must complete before a
milestone that **consumes** that contract — at least to the point where
the contract's producing side is implemented and committed.

After A establishes the contract's producing side, siblings of A that
consume that contract CAN parallelize (they all consume the same
stable contract).

---

## The parallelism analysis, step by step

For each pair of milestones (A, B) with no `depends_on` between them:

### Step 1: Check file overlap

Read both milestones' `rooms_affected` and anchored file paths. Do
they share any file paths?

- Yes → serialize (or annotate as `serial_with`)
- No → continue to Step 2

### Step 2: Check shared interface layer

Do either milestone's file paths include `packages/shared/`, `types/`,
`schemas/`, or the project's designated shared-interface directory?

- Both do → serialize
- One does, one doesn't → parallel is usually safe, but note in
  ledger
- Neither does → continue to Step 3

### Step 3: Check contract boundaries

Does either milestone define a contract that the other consumes (even
transitively)?

- If A defines contract X and B consumes X → add `B.depends_on: [A]`
  (this may already be captured in Phase 5 milestone dependencies;
  verify)
- No contract overlap → parallel-safe

### Step 4: Check architectural conventions

Does a `convention-*.yaml` spec say "changes to X flow through one
owner"? Such conventions force serialization for any milestone
touching X.

Example: `convention-schema-001: all schema changes flow through
single-writer`.

### Step 5: Conclude

If steps 1-4 don't identify a reason to serialize, the pair is
parallel-safe.

---

## Annotations on milestones

Based on the analysis, annotate milestones:

### `depends_on` (from Step 3 or Phase 5)

Strict order. Milestone B with `depends_on: [A]` will NOT be dispatched
by Scheduler until A is `completed`.

```yaml
milestones:
  - id: "m3-api-users"
    depends_on: ["m1-db-schema"]
```

### `serial_with` (optional, from Steps 1-2 and 4)

Explicit annotation that this milestone cannot run in parallel with
another. Unlike `depends_on`, `serial_with` is symmetric — neither
needs to finish before the other starts; they just can't overlap.

```yaml
milestones:
  - id: "m4-shared-types-a"
    serial_with: ["m5-shared-types-b"]
  - id: "m5-shared-types-b"
    serial_with: ["m4-shared-types-a"]
```

Scheduler uses this to avoid placing both into the same batch.

### `parallel_safe_with` (optional hint)

For milestones where parallel safety is non-obvious, annotate
explicitly. Helps Scheduler decide confidently.

```yaml
milestones:
  - id: "m6-api-expenses"
    parallel_safe_with: ["m3-api-users"]
```

---

## Architectural rules as spec-level constraints

Some serialization rules apply across every affected milestone, not per
pair. Write these as `convention-*.yaml` or `constraint-*.yaml` specs in
`00-project-room/specs/`:

```yaml
spec_id: "convention-shared-single-writer-001"
type: convention

intent:
  summary: "Shared interface files are edited by one milestone at a time"
  detail: |
    Files under `packages/shared/` constitute the project's shared
    interface layer. Any milestone touching these files must be
    serialized with any other milestone also touching them.

    Rationale: shared interfaces are consumed by multiple other
    modules; concurrent edits produce merge conflicts and
    integration-time breakage. Even small TypeScript type additions
    can conflict at the type-checker level.

    Enforcement: Scheduler respects this when batching; Review
    flags if violations occur.
```

These architectural specs are referenced by any milestone touching the
affected files, so Scheduler sees the constraint when planning
batches.

---

## Examples

### Example 1: Pure parallel

Milestones A, B, C each touch separate rooms, no shared files, no
contracts between them (A produces `auth`, B produces `expenses`, C
produces `reporting`; none consume each others' contracts yet because
foundation milestones already established the cross-cutting types).

**Analysis**: no file overlap, no shared interface, no contract
dependency. Fully parallel-safe.

**Annotations**: none needed; Scheduler can dispatch all three
in one batch, `concurrency_mode: parallel`.

### Example 2: Contract dependency forces ordering

- `m1-db-schema`: creates users table, writes contract
  `contract-db-schema-users-001`
- `m2-api-users`: implements `/api/users/*`, consuming
  `contract-db-schema-users-001`

**Analysis**: m2 consumes m1's contract → `m2.depends_on: [m1]`.

**Annotations**:
```yaml
- id: "m2-api-users"
  depends_on: ["m1-db-schema"]
```

Scheduler can parallelize m2 with *siblings* of m2, but not with
m1 itself.

### Example 3: Shared interface layer

- `m4-shared-types-a`: adds `User` and `Session` types to
  `packages/shared/src/types.ts`
- `m5-shared-types-b`: adds `Expense` and `Category` types to the same
  file

**Analysis**: both write to `packages/shared/src/types.ts`. Single-writer
rule applies.

**Annotations**:
```yaml
- id: "m4-shared-types-a"
  serial_with: ["m5-shared-types-b"]
- id: "m5-shared-types-b"
  serial_with: ["m4-shared-types-a"]
```

### Example 4: Plausible parallel but with a subtle gotcha

- `m7-add-login-page`: creates `app/(auth)/login/page.tsx`
- `m8-add-signup-page`: creates `app/(auth)/signup/page.tsx`

Different files. But both might modify `app/(auth)/layout.tsx` for
shared navigation.

**Analysis**: if both milestones modify the shared layout, serialize or
redesign. If one milestone handles the shared layout and the other only
its own page, parallel is safe.

**Resolution**: a good Planning splits this so `m7` includes the layout
(since it goes first), and `m8` only adds its own page. Now it's
parallel-safe after m7 completes.

---

## What Scheduler does with these annotations

Scheduler reads the plan in its Phase 2-3:

- For the executable-set-of-milestones in the next batch, check
  annotations
- Exclude pairs that are `serial_with` from the same batch
- Honor `depends_on` (only include if dependencies are completed)
- Use `parallel_safe_with` as a hint for `concurrency_mode: parallel`

---

## Common mistakes

### Over-serialization

"I'll make B depend on A just to be safe" — no. If there's no actual
reason, the serialization only costs time.

Test: what would go wrong if A and B ran in parallel? If you can't
name a concrete failure, they should run in parallel.

### Under-serialization

Forgetting the shared interface layer. Two milestones independently
adding shared types break each other at the type-check level, not at
runtime. Easy to miss.

Always check whether milestones touch the shared interface directory.

### Missing transitive contract dependencies

"m2 doesn't depend on m1 because m2 doesn't call m1's code" — but m2
consumes a type defined in m1, which was supposed to be in shared
first. Walk the contract graph fully.

### Parallelism across architectural layers

"Frontend and backend are different modules, clearly parallel" — often
true, but check shared types, shared validation schemas, shared
conventions. Those get violated by parallel execution on them.

---

## Output

Milestones annotated with `depends_on` (strict ordering),
`serial_with` (mutual exclusion), and optionally `parallel_safe_with`
(hints).

Architectural conventions written as `convention-*.yaml` specs where
they apply across the project.

Scheduler uses these to form valid batches.
