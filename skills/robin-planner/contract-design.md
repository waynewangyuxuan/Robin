# Contract Design Methodology

How Planning Agent designs contract specs. Loaded during Planning Phase 4.

**Contracts are the single most important output of Planning.** They determine
whether Execute Agents can work in parallel, whether Review will find
integration bugs, and whether replan cycles are cheap (contract-local) or
expensive (contract-breaking).

---

## What a contract is

A contract spec defines an **agreement at a module boundary**: what the
producing side guarantees, what the consuming side can rely on, and the
invariants both must honor.

Contracts cover:

- HTTP / RPC APIs (endpoint shape, request/response)
- Function signatures exposed across module boundaries
- Data types passed between modules
- Events / messages (pub-sub, queues)
- Database schemas (the DB is shared; schema is a contract between
  everyone who touches it)
- File formats exchanged between processes
- Shared conventions (naming, error handling, logging) that function as
  cross-cutting contracts

---

## The three elements of every contract

Every `contract-*.yaml` must specify:

### 1. What is exposed

The external surface. Concrete signatures, not handwaves.

Bad:
> "Users endpoint returns user data"

Good:
> ```
> POST /api/users
>   Request body: { email: string, name: string }
>     - email: RFC-5322-valid string, unique across all users
>     - name: string, 1-100 chars, non-empty after trim
>   Response 201: { id: UUIDv4, email, name, created_at: ISO8601 }
>   Response 400: { error: "ValidationError", field: string, message: string }
>   Response 409: { error: "EmailTakenError" }
> ```

### 2. What callers can rely on

Invariants, ordering, idempotency, error behavior. The things the
consuming side needs to know but the surface shape alone doesn't
capture.

Examples:
- "Calling POST /api/users twice with the same email returns 409 on the
  second call; no duplicate is created."
- "Events on the `user-created` topic arrive in insertion order, with
  at-least-once delivery."
- "Reads after a successful write observe the write (read-after-write
  consistency)."
- "The function throws `EmailTakenError` (not a generic error) when email
  is duplicated."

### 3. What the producer assumes

Preconditions callers must satisfy.

Examples:
- "Caller must be authenticated (Authorization header with valid JWT)."
- "Request body must be valid JSON; malformed JSON returns 400 with a
  parse error before any validation runs."
- "Caller's clock is synchronized within 5 minutes of server time."

---

## Contracts are specs, not code

A contract specifies WHAT and WHY. Code specifies HOW.

✅ "Returns a user object with id, email, and created_at, where id is
UUIDv4"

❌ "Uses Postgres `INSERT INTO users (...) RETURNING *`"

If you find yourself writing implementation details in a contract, stop.
Those belong in Execute's code, guided by decision specs about
framework/libraries/patterns.

---

## Failure modes are part of the contract

The happy path is only half of it. Contract must specify:

- What errors are thrown / returned
- Their exact shape (typed errors, error codes, status codes)
- When each error occurs (preconditions for each failure)

Intake code cannot handle errors it doesn't know about. Skipping error
specification is how "unexpected behavior" bugs get planted in the
integration.

---

## Anchors on contracts

Every contract spec has `anchors[]` pointing to where its implementation
will live. Even if the code doesn't exist yet (fresh project), anchor the
file path:

```yaml
anchors:
  - file: "apps/api/src/routes/users/create.ts"
    symbols: []  # filled in by Execute after file is written
    line_range: null
```

This gives Execute a clear target and lets Review find the implementation
easily.

If a contract spans multiple files (e.g., "the User API" with several
routes), multiple anchors are fine. Prefer one anchor per file to avoid
ambiguity about what implements what.

---

## How to design contracts

### Step 1: Identify boundaries

For each module you've decomposed into (Planning Phase 3), list the
boundaries: where does this module interact with others?

- What does it expose to others?
- What does it consume from others?

### Step 2: Draft the surface

For each exposed interface, write the surface (endpoint signatures,
function signatures, data shapes). Be specific. Use concrete types.

### Step 3: Add invariants and failure modes

What must callers know beyond the surface? What can go wrong?

### Step 4: Check both sides

Walk through:

- **Producer side**: can this actually be implemented? Are preconditions
  specifiable? Can errors be detected and reported?
- **Intake side**: does the caller have enough information to use this
  correctly? Can they distinguish errors?

If either side has gaps, refine.

### Step 5: Write the spec

Use the format in `stdlib/feature-room-spec.md`. Contract's `intent.detail`
should have three sections: **Exposed**, **Invariants**, **Preconditions**.

---

## Contract granularity

Too fine:
- One contract per endpoint with 2-sentence descriptions. The
  relationships between endpoints (shared types, error patterns) get lost.

Too coarse:
- One contract for "the whole API" with 40 endpoints. Changing one
  endpoint forces the whole contract to `state: stale`.

Right:
- One contract per cohesive set of related endpoints (e.g., "Users API"
  covering CRUD on users; "Auth API" covering login/logout/token
  refresh). 3-8 endpoints per contract is typical.

---

## Types and data shapes

Data types shared across modules get their own contract specs. Don't embed
complex types inline in every consuming spec.

```yaml
spec_id: contract-type-user-001
type: contract

intent:
  summary: "User entity data shape"
  detail: |
    **Exposed type**:
    ```
    type User = {
      id: UUIDv4
      email: string           // RFC-5322 valid
      name: string            // 1-100 chars
      created_at: ISO8601
      updated_at: ISO8601
    }
    ```

    **Invariants**:
    - id is immutable once assigned
    - email is unique across the User collection
    - updated_at ≥ created_at always
```

Then API contracts reference `contract-type-user-001` instead of
re-describing the type.

---

## Database schemas as contracts

The database schema is a shared contract between every service that reads
or writes it. Treat it with the same rigor as an API contract.

```yaml
spec_id: contract-db-schema-users-001
type: contract

intent:
  summary: "users table schema"
  detail: |
    **Table: users**
    Columns:
    - id: UUID PRIMARY KEY, default gen_random_uuid()
    - email: TEXT NOT NULL UNIQUE
    - name: TEXT NOT NULL CHECK (length(trim(name)) > 0)
    - created_at: TIMESTAMPTZ NOT NULL DEFAULT now()
    - updated_at: TIMESTAMPTZ NOT NULL DEFAULT now()

    Indexes:
    - idx_users_email on email (for login lookups)

    Triggers:
    - touch_updated_at trigger on UPDATE

    **Invariants** enforced at schema level:
    - email uniqueness (UNIQUE constraint — violated = 23505 in Postgres)
    - name non-empty (CHECK constraint — violated = 23514)

    Application code must validate these BEFORE INSERT to provide typed
    error responses. Relying solely on DB constraint violation as the
    error path produces generic 500s in most frameworks.
```

Last paragraph is key: the schema contract *and* its application-level
behavior are both part of the contract.

---

## Events / messages

For pub-sub or queue-based systems, the contract covers the message shape
+ delivery guarantees.

```yaml
spec_id: contract-event-user-created-001
type: contract

intent:
  summary: "user-created event payload and delivery"
  detail: |
    **Topic**: user-created

    **Payload**:
    ```
    {
      event_id: UUIDv4        // unique per event, for dedup
      event_at: ISO8601       // when emission started
      user_id: UUIDv4
      email: string           // denormalized for consumer convenience
    }
    ```

    **Delivery guarantees**:
    - At-least-once (consumers must be idempotent by event_id)
    - Order: not guaranteed across users; within one user, roughly ordered
      by event_at but NOT strict
    - Retry: consumers that return error are retried with exponential
      backoff up to 5 times; then dead-lettered

    **Producer preconditions**:
    - User row must be committed to DB before event is emitted
    - Event emission failure must not fail the user creation (dual-write
      pattern; accept eventual consistency on event delivery)
```

---

## Conventions as cross-cutting contracts

Some rules apply across every module. Write them as `convention-*.yaml`
specs, but they function like contracts (everyone must honor them).

Common examples:

```yaml
spec_id: convention-errors-001
type: convention

intent:
  summary: "Typed error responses across all APIs"
  detail: |
    Every HTTP API returns errors in this shape:
    ```
    {
      error: string             // error code, e.g. "ValidationError"
      message: string           // human-readable
      field?: string            // for field-specific errors
      retry_after?: number      // for rate-limit errors, seconds
    }
    ```

    Standard error codes (enumerated):
    - ValidationError
    - AuthError
    - PermissionDenied
    - NotFound
    - Conflict
    - RateLimited
    - InternalError (fallback only)

    Frameworks that allow custom error classes should map to these names
    at the HTTP boundary.
```

Convention specs get anchored to wherever the enforcement lives (error
middleware, shared utility module).

---

## What not to put in a contract

- Implementation choices (those are decision specs)
- Internal module structure
- Performance targets that aren't part of the interface contract (those
  are constraint specs)
- UX / UI details (those are design specs, if your project has them)

---

## Contract versioning

In AI-Robin's typical run (one project, linear evolution), version 1 is
implicit. You don't need a `version` field.

If contracts change during a replan, use the Feature Room state mechanism:

- Old contract: `state: superseded`
- New contract: new spec_id (e.g., `contract-api-users-002`),
  `relations[].supersedes: contract-api-users-001`
- All specs referencing the old contract should be checked (Review
  catches this) and updated to reference the new one

---

## Anti-patterns

- **Vague contracts** ("endpoint returns user info"). Guaranteed
  integration bugs.
- **Implementation-first contracts** ("uses Postgres with..."). Conflates
  what and how.
- **No error spec**. Intake code can't handle what's not documented.
- **Contract-as-documentation-only**. Contracts must be actionable by
  Execute; abstract diagrams aren't enough.
- **One giant contract** covering the whole project. Use one per
  cohesive module boundary.
- **Contracts without anchors**. Review can't verify them; they drift
  into aspirational prose.

---

## Output

After Planning Phase 4, `contract-*.yaml` specs are written to the
relevant Room's `specs/` directory (or `00-project-room/specs/` for
cross-cutting contracts). Each contract has:

- The three elements (Exposed / Invariants / Preconditions)
- At least one anchor to its implementation target
- `state: active`, `provenance.source_type: planning_derived`,
  confidence 0.85-0.95
- References to depended-upon type contracts via `relations[]`
