# Review Stage — Architectural Overview

A reference document describing the structure of AI-Robin's Review stage. This is not a skill — the actual execution lives in the agents listed below.

## The shape

Review is the most structurally complex stage. Unlike other stages (single agent), Review is **plan-then-fan-out-then-merge**:

```
Executor Agents complete batch
  ↓
Review-Planner (robin-review-planner) analyzes change → decides which reviewer agents to dispatch
  ↓
Kernel spawns N reviewer agents (robin-reviewer-{domain}) in parallel
  ↓
Each reviewer returns a sub-verdict
  ↓
Merger (robin-merger) consolidates into one merged verdict
  ↓
Kernel spawns Committer (hard rule: always commit), then routes next
```

## When this stage runs

Review runs after every batch's Executor stage completes — after ALL Executor agents in a batch have returned `execute_complete` or `execute_failed`. It runs even when some tasks failed: completed tasks still need review, and failed tasks may need their partial artifacts evaluated.

## Agent roles

| Agent | Skill | Role |
|---|---|---|
| `robin-review-planner` | `skills/robin-review-planner/` | Decides which reviewer agents to dispatch based on the batch's change profile (file types, spec classes) |
| `robin-reviewer-{domain}` | `skills/robin-reviewer/` (shared generic) + `skills/robin-reviewer/domains/{domain}.md` (domain rules) | N parallel instances, one per dispatched domain. Each reads code + domain checklist and emits a sub-verdict |
| `robin-merger` | `skills/robin-merger/` | Consolidates N sub-verdicts into one merged verdict + composes the git commit message |
| `robin-committer` | `skills/robin-committer/` | Executes the git commit using merger's verbatim message |

## Review-Planner's dispatch logic

The reviewer catalog — domains that can be dispatched:

| Domain | Trigger condition | Severity focus | Status |
|---|---|---|---|
| `code-quality` | Always spawned | quality | Implemented |
| `frontend-component` | Changed files match `**/*.{jsx,tsx,vue,svelte}` | quality + blocking | Planned |
| `frontend-a11y` | Changed files match frontend component patterns | quality | Planned |
| `backend-api` | Changed files match `**/api/**`, `**/routes/**`, etc. | blocking | Planned |
| `db-schema` | Changed files match `**/migrations/**`, `**/schema*` | blocking | Planned |
| `agent-integration` | Changed files match agent/prompt/tool definitions | quality + blocking | Planned |
| `test-coverage` | Any source file changed | advisory | Planned |
| `spec-anchors` | Any change spec references anchor updates | blocking | Planned |

Adding a new domain is: (1) write `skills/robin-reviewer/domains/{domain}.md`, (2) add an `agents/robin-reviewer-{domain}.md` wrapper. Review-Planner reads the agents directory + wrapper descriptions to know what's available.

## The review flow (kernel's reference)

1. Batch's Executor phase ends — last `execute_complete` / `execute_failed` signal arrives.
2. Kernel spawns Review-Planner with `batch_id` + change specs.
3. Review-Planner returns `review_dispatch` with a list of domains + per-domain scope.
4. Kernel spawns N `robin-reviewer-{domain}` agents in parallel. Each reads the shared generic flow + its specific domain checklist + the scoped files/specs.
5. Each reviewer emits a `review_sub_verdict` signal.
6. Kernel collects all sub-verdicts; when all in, spawns Merger.
7. Merger returns `review_merged` with an overall verdict + commit message.
8. Kernel spawns Committer with the verbatim commit message (hard rule: always commit, pass or fail).
9. Kernel routes per `overall_status`:
   - `pass` / `pass_with_warnings` → Scheduler for next batch
   - `fail` + within review_iterations budget → Planner for replan
   - `fail` + budget exhausted → Degrader

## Rules for the stage as a whole

### Rule 1: Always commit, pass or fail

The kernel delegates the commit to Committer after every review regardless of outcome. A failed review creates a commit recording the attempt + the verdict, followed (eventually) by another commit when the rework completes. This preserves the full history for audit.

### Rule 2: Review iterations are budgeted

`review_iterations_per_batch` defaults to 2. After 2 fails on the same batch, degrade that batch's scope instead of a 3rd attempt.

### Rule 3: Reviewers are stateless

Each reviewer agent is invoked fresh. They do not know about previous runs of themselves on earlier iterations of this batch. If a reviewer flagged issue X in iteration 1, and iteration 2 still has X, it'll flag it again — that's correct, that's what we want. The iteration count is tracked by kernel, not by the reviewers.

### Rule 4: Merger does not second-guess reviewers

Merger's job is synthesis, not re-evaluation. If a reviewer says "blocking", merge preserves that. Merge can CONSOLIDATE similar issues from multiple reviewers, but it cannot downgrade severity or dismiss issues.

### Rule 5: Reviewers operate only within their declared scope

A reviewer has a scope (files, specs). It reads within that scope. It does not read other reviewers' scopes, does not read the full project, does not explore beyond what was given. This keeps reviewer results predictable and parallelizable.

## Relationship to Feature Room's commit-sync

Feature Room's `commit-sync` skill contained several review-like checks inline:

- Phase 2: Anchor tracking (what anchors need updating)
- Phase 3: Draft-to-active detection
- Phase 4: Cross-room conflict detection (via contract anchors)

In AI-Robin, these checks are distributed:

- **Anchor tracking** — done by Executor during Phase 4, validated by `spec-anchors` reviewer (future)
- **Draft-to-active detection** — not applicable in AI-Robin (all sub-agents promote specs to active before returning; agent-proxy decisions are also active, tracked for audit via signal payloads and ledger rather than via draft state)
- **Cross-room conflict detection** — done by Review-Planner (which looks at the full batch) and validated by `backend-api` / `db-schema` reviewers for the specific conflict patterns

This redistribution is deliberate — in Feature Room, these were bundled into commit-sync because a human was doing the final review. In AI-Robin, they belong to the review stage which has time and autonomy to be more thorough.

## Failure modes

| Mode | Symptom | What to do |
|---|---|---|
| Review-Planner dispatches zero reviewers | Empty reviewer list in `review_dispatch` | Kernel treats as anomaly; code-quality must always run |
| A reviewer crashes mid-run | Sub-agent returns malformed signal or timeout | Kernel logs anomaly, treats that reviewer as "did not run"; merger proceeds without it with a note |
| Merger finds cross-reviewer conflicts | E.g., every reviewer said pass, but merge sees contradictions | Merger surfaces the conflict as a cross-reviewer observation; overall verdict is the worst sub-verdict |
| Pass review but code doesn't work | Integration test failure in reality vs. reviewer checks being too shallow | Long-term: expand domain checklists; short-term: known limitation, relies on project-level test convention |
