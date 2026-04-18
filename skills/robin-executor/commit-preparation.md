# Commit Preparation

How Execute Agent prepares the change artifact that kernel will commit
to git after Review passes. Used in Execute Phase 4 after self-check.

Adapted from Feature Room's `commit-sync` skill (Phases 1-4), with the
git commit step itself removed — kernel handles that post-Review.

---

## What "commit preparation" means here

Execute doesn't commit. Kernel does, after Review blesses the batch.
"Commit preparation" means producing everything kernel needs to make a
clean, informative commit:

- Source code changes on disk (already done by Phase 2-3)
- Updated spec anchors (done by Phase 3)
- A `change-*.yaml` spec recording what happened (done here)
- Progress.yaml updates (done here)
- Self-assessment to inform kernel's audit (done here)

---

## The change spec

Every Execute invocation produces one `change-*.yaml` spec recording
its work. This spec:

- Is immutable once created (never edited later)
- Lives in the scope's Room under `specs/`
- Serves as the audit record of what this Execute did
- Gets included in the git commit alongside code changes

### Filename and spec_id

Format:
```
change-{YYYYMMDD-HHMMSS}-{batch_id}-{task_id}.yaml
```

Example:
```
change-20260416-143000-batch3-task1.yaml
```

The spec_id matches the filename (without `.yaml`).

### Full format

```yaml
spec_id: "change-20260416-143000-batch3-task1"
type: change
state: active

intent:
  summary: "Implement user CRUD endpoints per contract-api-users-001"
  detail: |
    **Batch**: batch-3
    **Task**: batch-3-task-1
    **Milestone**: m2-api-users
    **Invocation**: inv-execute-batch3-task1-abc123

    **Files created**:
    - apps/api/src/routes/users/create.ts (89 lines)
    - apps/api/src/routes/users/read.ts (42 lines)
    - apps/api/src/routes/users/update.ts (55 lines)
    - apps/api/src/routes/users/delete.ts (31 lines)
    - apps/api/src/routes/users/index.ts (12 lines — router exports)

    **Files modified**:
    - apps/api/src/app.ts: registered users router at /api/users
    - apps/api/src/schemas/user.ts: added UpdateUserInput type

    **Specs updated (anchors)**:
    - contract-api-users-001: added anchors to all 4 endpoint files
    - contract-type-user-001: added anchor to updated schema file

    **Tests added**:
    - apps/api/tests/routes/users.test.ts (172 lines, 14 test cases)

    **Self-assessment**:
    declared_complete: true
    known_issues:
    - None

    **Dependencies**:
    - Relies on contract-db-schema-users-001 (users table) — used via
      existing ORM model
    - Consumes convention-errors-001 for error response format

indexing:
  type: change
  priority: P1
  layer: task
  domain: "api"
  tags: ["change", "batch-3", "milestone-m2-api-users"]

provenance:
  source_type: manual_input
  confidence: 1.0
  source_ref: "Execute invocation inv-execute-batch3-task1-abc123"
  produced_by_agent: "execute-batch3-task1"
  produced_at: "2026-04-16T14:30:00Z"

relations:
  - type: relates_to
    ref: "m2-api-users"  # the milestone
  - type: relates_to
    ref: "contract-api-users-001"

anchors: []  # change specs themselves don't anchor to code
```

---

## The `intent.detail` sections

Required sections in `intent.detail`:

### Files changed

List every file touched:

```
**Files created**:
- {path} ({line count})

**Files modified**:
- {path}: {brief summary of change}

**Files deleted** (rare):
- {path}: {reason}
```

Line counts help Reviewers estimate review scope. Modification summaries
help reviewers know what to focus on.

### Specs updated

For every spec whose anchors changed:

```
**Specs updated (anchors)**:
- {spec_id}: {anchor change summary — new anchor / updated path / etc.}
```

If a spec was marked `state: stale` during your work, note it here:

```
- contract-api-users-001: marked state: stale; new auth behavior in
  create endpoint may invalidate original spec's claim
```

### Tests added

Separate callout for tests:

```
**Tests added**:
- {path} ({line count}, {test count or key tests})
```

### Self-assessment

Copy verbatim what will be in the return signal's
`self_assessment`:

```
**Self-assessment**:
declared_complete: true
known_issues:
- Rate limiting not implemented (deferred per milestone gate m2)
- Passwords stored in plaintext (TODO — deferred to m3-auth)
```

Even if there are no known issues, say `None` explicitly.

### Dependencies

Optional section, noting which specs / libraries / other code this
change depends on for context:

```
**Dependencies**:
- Relies on {spec_id} for {what}
- Uses library {name} per decision-{spec_id}
```

---

## Progress.yaml update

In addition to the change spec, update the milestone's progress in
`{scope.room}/progress.yaml`:

```yaml
milestones:
  - id: "m2-api-users"
    status: in_progress   # was: pending
    # (don't mark completed — Review does that)
```

### Add a commit placeholder to progress.yaml's commits array

```yaml
commits:
  - hash: "PENDING"           # kernel fills in after git commit
    date: "2026-04-16T14:30:00Z"
    message: "PENDING — will be filled after Review + commit"
    files_changed: 8
    specs_affected:
      - change-20260416-143000-batch3-task1 (created)
      - contract-api-users-001 (anchor update)
      - contract-type-user-001 (anchor update)
    milestones_affected:
      - m2-api-users (→ in_progress)
    ai_robin_context:
      batch_id: batch-3
      stage: execute
      review_status: pending
```

Kernel updates `hash` and `message` after the git commit succeeds
post-Review.

---

## What NOT to include

### Don't put actual git commit messages in change spec

The git commit message is the kernel's job. The change spec is the
audit record; its format is for humans and for spec-system tooling.

### Don't duplicate code in change spec

Change spec references files by path. It does NOT include code.
`Files modified: - users.ts: added validateCreatePayload()` is right.
`Files modified: - users.ts: [500 lines of code]` is wrong.

### Don't prospect

Change spec records what WAS done, not what WILL be done. "TODO: add
rate limiting" goes in `known_issues`, not in the main files-changed
section.

### Don't editorialize

"Great implementation of uniqueness check" — no. Change spec is
factual. Editorializing pollutes audit.

---

## How kernel uses the change spec at commit time

After Review passes:

1. Kernel reads the change spec
2. Kernel composes a git commit message using the `intent.summary` plus
   batch and milestone info
3. Kernel runs `git add` with the changed files PLUS the change spec
   itself PLUS updated spec yamls PLUS progress.yaml
4. Kernel runs `git commit`
5. Kernel gets the hash
6. Kernel updates the progress.yaml commit entry's `hash` and
   `message` fields
7. Kernel writes a ledger `commit` entry

The change spec is the source of truth for what this execution did.
Everything downstream derives from it.

### Git commit message format

Kernel uses this template:

```
[{stage}][{room_ids}] {type}: {change.intent.summary}

Batch: {batch_id}
Milestone: {milestone_id}
Review: {pass | pass_with_warnings}
```

Type is inferred from the change's nature (feat / fix / refactor /
docs / test / chore).

---

## If Review fails

If Review returns `fail`, kernel STILL commits the change (per the
always-commit rule) but with a commit message signaling failure:

```
[review-fail] batch-{batch_id} iter {N}: {summary}

Review flagged: {issue summaries}
Replan will be triggered.
```

The change spec stays on disk, still records what was attempted.
Subsequent replan may produce new change specs superseding this work's
artifacts — old change specs remain in place as history.

---

## Anti-patterns

- **Vague change spec summaries**: "made some changes" — useless.
  Be specific: "implemented user CRUD endpoints per contract X".
- **Missing Self-assessment section**: always include it, even if
  `known_issues: None`.
- **Forgetting progress.yaml update**: change spec alone isn't
  enough; progress.yaml is where Scheduler tracks milestone
  status.
- **Marking milestone `completed` in progress.yaml**: only Review
  can do that. Execute sets `in_progress`.
- **Creating multiple change specs per invocation**: one change spec
  per Execute invocation. If you felt the need to create multiple,
  either the task was too big (return `execute_failed` with
  `scope_too_large`) or you misunderstood the format.
