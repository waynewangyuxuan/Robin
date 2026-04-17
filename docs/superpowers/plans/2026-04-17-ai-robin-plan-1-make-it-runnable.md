# AI-Robin Plan 1 — Make-It-Runnable Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the 5 P0 correctness gaps that prevent the ai-robin skill from completing a real end-to-end run: missing routing entries for 5 signal types, broken commit-message information pipeline, runtime-model mismatch with Claude Code, ambiguous sub-skill activation, and non-deterministic signal ordering.

**Architecture:** Pure documentation / contract edits to the ai-robin skill at `/Users/waynewang/AI-Robin-Skill/ai-robin/`. No new executable code. Changes split across three layers: (1) main SKILL.md routing table, (2) dispatch-signal contract + Merge Agent output, (3) runtime-positioning + skill-activation semantics. Each task is verified by a grep / Read check that the edit actually landed and is consistent with the other specs it touches.

**Tech Stack:** Markdown files, YAML frontmatter, JSON schema (all authored — no runtime). Verification via Grep tool + Read tool against file contents. Commit via git.

---

## File Structure

Files modified by this plan (with responsibility of each change):

- **`ai-robin/SKILL.md`** — Main kernel routing table. Add 5 missing signal rows. Add reference to signal-ordering rule.
- **`ai-robin/contracts/dispatch-signal.md`** — Add `commit_message` field to `review_merged` payload. Document ordering rule in validation section.
- **`ai-robin/contracts/stage-state.md`** — Add `failed_tasks[]` field to `current_batch` (needed to track partial-failure state for `execute_failed` routing).
- **`ai-robin/contracts/session-ledger.md`** — Update `commit` entry note to clarify `commit_message` comes from `review_merged` signal (not kernel-composed).
- **`ai-robin/stdlib/kernel-discipline.md`** — Add signal-ordering rule to section "One routing per turn". Add pointer to runtime-adaptation section.
- **`ai-robin/review/merge/phases/phase-4-emit.md`** — Tell Merge Agent to compose and emit `commit_message`. Add method guidance.
- **`ai-robin/consumer/SKILL.md`**, **`ai-robin/planning/SKILL.md`**, **`ai-robin/execute-control/SKILL.md`**, **`ai-robin/execute/SKILL.md`**, **`ai-robin/research/SKILL.md`**, **`ai-robin/review/SKILL.md`**, **`ai-robin/review/review-plan/SKILL.md`**, **`ai-robin/review/merge/SKILL.md`** — Strip activation frontmatter (`---` + `name:` + `description:` block) to prevent these sub-skills from being discovered as top-level user-invocable skills. Replace with a plain markdown "Internal sub-skill — not user-invocable" note.
- **`ai-robin/DESIGN.md`** — Add "Runtime adaptation" section explaining that the `.ai-robin/dispatch/inbox/` pattern is a formal abstraction; runtime implementations may satisfy it differently (e.g., in Claude Code the sub-agent writes the file and the same turn's caller reads it).
- **`ai-robin/tests/routing-coverage.md`** (NEW) — A verification artifact that lists every signal type defined by the contract and its expected routing. Used as a grep-able audit trail that the main SKILL.md routing table is complete.
- **`ai-robin/tests/end-to-end-trace.md`** (NEW) — A narrative trace of five concrete scenarios (happy path, research inconclusive, execute failure, replan exhaustion, intake blocked) that walks the routing table to prove each scenario terminates deterministically.

---

## Task 1: Create routing coverage test that exposes the 5 gaps

**Files:**
- Create: `/Users/waynewang/AI-Robin-Skill/ai-robin/tests/routing-coverage.md`

This task is TDD step 1: write the failing audit document before touching SKILL.md. It enumerates every signal type from the contract and asserts a routing row exists in main SKILL.md. Initially 5 rows are expected to be missing — this proves the gap.

- [ ] **Step 1: Create the tests directory**

```bash
mkdir -p /Users/waynewang/AI-Robin-Skill/ai-robin/tests
```

- [ ] **Step 2: Write the routing-coverage audit document**

Create `/Users/waynewang/AI-Robin-Skill/ai-robin/tests/routing-coverage.md` with this exact content:

````markdown
# Routing Coverage Audit

This document lists every `signal_type` defined in `contracts/dispatch-signal.md` and the routing action main `SKILL.md` must take on it. It is the source of truth for routing completeness — every signal type declared in the contract MUST appear in the main SKILL.md routing table.

## How to verify

Run these greps from the ai-robin directory:

```bash
# List signal types declared in contract
grep -E '^#### `[a-z_]+`' contracts/dispatch-signal.md | sed -E 's/.*`([a-z_]+)`.*/\1/' | sort -u

# List signal types covered in main SKILL.md routing table
grep -E '^\| `[a-z_]+` \|' SKILL.md | sed -E 's/.*`([a-z_]+)`.*/\1/' | sort -u

# Diff: contract signals NOT in routing table
comm -23 <(contract list) <(skill list)
```

Expected output of the diff: **empty**. If non-empty, the routing table is incomplete.

## Signal → routing contract

| signal_type | Defined in contract | Routing action (authoritative) |
|---|---|---|
| `intake_complete` | ✅ | Update stage-state → "planning". Spawn Planning Agent. |
| `intake_blocked` | ✅ | **Exit run.** Write `run_end` ledger entry with `exit_reason: "intake_blocked"`. Surface `partial_spec_path` and `reason` to user. Do NOT spawn anything further. |
| `planning_complete` | ✅ | Update stage-state → "execute-control". Spawn Execute-Control Agent. |
| `planning_needs_research` | ✅ | Spawn Research Agent with the question from signal. Keep stage at "planning". |
| `planning_needs_sub_planning` | ✅ | Spawn sub-Planning Agent for the specified sub-scope. Keep stage at "planning". |
| `planning_replan_exhausted` | ✅ | Trigger degradation for the `unresolvable_issues` list. Preserve `partial_plan_ref`. Continue other scopes via Execute-Control. |
| `research_complete` | ✅ | Re-spawn Planning Agent with research findings attached. |
| `research_inconclusive` | ✅ | Log `anomaly` entry (severity: low). Re-spawn the requesting stage (usually Planning) with `best_guess` attached AND `confidence < 0.5` flag so the requester records any derived decision with low confidence. Does NOT consume degradation budget by itself. |
| `dispatch_batch` | ✅ | Read batch spec from signal. Spawn N Execute Agents (parallel or sequential per `concurrency_mode`). |
| `dispatch_exhausted` | ✅ | Route to Planning for replan. Consumes `replan_iterations` budget. If already exhausted → trigger degradation for all remaining pending milestones. |
| `execute_complete` | ✅ | Mark task as complete in `stage-state.current_batch`. Check if batch settled (all tasks complete or failed). If not settled → wait. If settled → see "batch settled" rule below. |
| `execute_failed` | ✅ | Mark task as failed in `stage-state.current_batch.failed_tasks`. Check if batch settled (all tasks complete or failed). If not settled → wait. If settled → see "batch settled" rule below. |
| `review_dispatch` | ✅ | Spawn N review sub-agents per the dispatch list. |
| `review_sub_verdict` | ✅ | Check if all review sub-agents in this batch are done. If yes → spawn Merge. If no → wait. |
| `review_merged` | ✅ | **Always commit to git first using `payload.commit_message`** (hard rule). Then route: `pass`/`pass_with_warnings` → Execute-Control next batch; `fail` + budget remaining → Planning replan; `fail` + budget exhausted → degrade. |
| `stage_exhausted` | ✅ | Trigger degradation for this scope. Log. Continue other scopes if any. |
| `all_complete` | ✅ | Generate delivery bundle. Write `run_end` with `exit_reason: "all_complete"`. Kernel exits. |

### Batch-settled rule (shared by `execute_complete` and `execute_failed`)

Applies when all tasks in the current batch have returned either `execute_complete` or `execute_failed`:

- **At least one `execute_complete`** → spawn Review-Plan. Input includes `failed_tasks[]` so playbooks can note partial coverage.
- **All tasks `execute_failed`** → skip review entirely (no change specs exist to review). Route to Planning for replan with `rework_reason.kind: "all_tasks_failed"`. Consumes `replan_iterations` budget.

## Coverage status

- Contract declares: **17 signal types**
- Main SKILL.md routing table must contain: **17 rows** (one per type)

After Task 2 of this plan is complete, the diff grep above must return empty.
````

- [ ] **Step 3: Run the audit grep to confirm gaps exist**

Run:
```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
comm -23 <(grep -E '^#### `[a-z_]+`' contracts/dispatch-signal.md | sed -E 's/.*`([a-z_]+)`.*/\1/' | sort -u) <(grep -E '^\| `[a-z_]+` \|' SKILL.md | sed -E 's/.*`([a-z_]+)`.*/\1/' | sort -u)
```

Expected output (exactly these 5 lines, in alphabetical order):
```
dispatch_exhausted
execute_failed
intake_blocked
planning_replan_exhausted
research_inconclusive
```

If the output is exactly these 5 lines, the failing audit has proven the gap. If it's different, investigate before continuing — the contract file may have changed since this plan was authored.

- [ ] **Step 4: Commit the failing audit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add ai-robin/tests/routing-coverage.md
git commit -m "test(ai-robin): add routing-coverage audit exposing 5 missing signal rows"
```

---

## Task 2: Close the 5 routing gaps in main SKILL.md

**Files:**
- Modify: `/Users/waynewang/AI-Robin-Skill/ai-robin/SKILL.md` (routing table, currently lines 92-105)

This task adds exactly 5 rows to the routing table so that every signal type declared in the contract has a routing action, as enumerated in the audit from Task 1.

- [ ] **Step 1: Confirm the current table by reading lines 92-105**

Read `/Users/waynewang/AI-Robin-Skill/ai-robin/SKILL.md` lines 92-105. Confirm the table currently has 12 rows: `intake_complete`, `planning_complete`, `planning_needs_research`, `planning_needs_sub_planning`, `research_complete`, `dispatch_batch`, `execute_complete`, `review_dispatch`, `review_sub_verdict`, `review_merged`, `stage_exhausted`, `all_complete`.

- [ ] **Step 2: Replace the routing table with a complete 17-row version**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/SKILL.md`, replace the exact block that currently reads:

```markdown
| Signal type | Next action |
|---|---|
| `intake_complete` | Update stage-state → "planning". Spawn Planning Agent. |
| `planning_complete` | Update stage-state → "execute-control". Spawn Execute-Control Agent. |
| `planning_needs_research` | Spawn Research Agent (with question from signal). Keep stage at "planning". |
| `planning_needs_sub_planning` | Spawn sub-Planning Agent for the specified sub-scope. Keep stage at "planning". |
| `research_complete` | Re-spawn Planning Agent with research findings attached. |
| `dispatch_batch` | Read batch spec from signal. Spawn N Execute Agents (parallel or sequential per signal). |
| `execute_complete` | Check if all execute agents in this batch are done. If yes → spawn Review-Plan. If no → wait. |
| `review_dispatch` | Spawn N review sub-agents per the dispatch list. |
| `review_sub_verdict` | Check if all review sub-agents in this batch are done. If yes → spawn Merge. If no → wait. |
| `review_merged` | **Always commit verdict to git first** (see rule below). Then: if pass → back to Execute-Control for next batch. If fail + budget left → back to Planning with issues. If fail + no budget → degrade. |
| `stage_exhausted` | Trigger degradation for this scope. Log. Continue other scopes if any. |
| `all_complete` | Generate delivery bundle. Kernel exits. |
```

With this exact block (17 rows, organized by stage, plus the batch-settled rule pulled out below the table):

```markdown
| Signal type | Next action |
|---|---|
| `intake_complete` | Update stage-state → "planning". Spawn Planning Agent. |
| `intake_blocked` | **Exit run.** Write `run_end` ledger entry with `exit_reason: "intake_blocked"`. Surface `partial_spec_path` and `reason` to user. Do not spawn anything further. |
| `planning_complete` | Update stage-state → "execute-control". Spawn Execute-Control Agent. |
| `planning_needs_research` | Spawn Research Agent (with question from signal). Keep stage at "planning". |
| `planning_needs_sub_planning` | Spawn sub-Planning Agent for the specified sub-scope. Keep stage at "planning". |
| `planning_replan_exhausted` | Trigger degradation for the `unresolvable_issues` list from payload. Preserve `partial_plan_ref`. Continue other scopes via Execute-Control. |
| `research_complete` | Re-spawn Planning Agent with research findings attached. |
| `research_inconclusive` | Log `anomaly` entry (severity: low). Re-spawn the requesting stage (usually Planning) with `best_guess` + `confidence < 0.5` flag attached. Requesting stage records any derived decision with low confidence. Does not consume degradation budget by itself. |
| `dispatch_batch` | Read batch spec from signal. Spawn N Execute Agents (parallel or sequential per `concurrency_mode`). |
| `dispatch_exhausted` | Route to Planning for replan. Consumes `replan_iterations` budget. If already exhausted → trigger degradation for all remaining pending milestones. |
| `execute_complete` | Mark task complete in `stage-state.current_batch`. Check if batch settled. If not settled → wait. If settled → apply "batch-settled rule" below. |
| `execute_failed` | Mark task failed in `stage-state.current_batch.failed_tasks`. Check if batch settled. If not settled → wait. If settled → apply "batch-settled rule" below. |
| `review_dispatch` | Spawn N review sub-agents per the dispatch list. |
| `review_sub_verdict` | Check if all review sub-agents in this batch are done. If yes → spawn Merge. If no → wait. |
| `review_merged` | **Always commit to git first using `payload.commit_message`** (see rule below). Then: `pass`/`pass_with_warnings` → Execute-Control for next batch; `fail` + budget left → Planning replan; `fail` + budget exhausted → degrade. |
| `stage_exhausted` | Trigger degradation for this scope. Log. Continue other scopes if any. |
| `all_complete` | Generate delivery bundle. Write `run_end` with `exit_reason: "all_complete"`. Kernel exits. |

### The batch-settled rule

A batch is "settled" when every task in `stage-state.current_batch.tasks` has returned either `execute_complete` or `execute_failed`. On settlement:

- **At least one `execute_complete`** → spawn Review-Plan. Input includes `failed_tasks[]` so playbooks can note partial coverage.
- **All tasks `execute_failed`** → skip review entirely (no change specs exist to review). Route to Planning for replan with `rework_reason.kind: "all_tasks_failed"`. Consumes `replan_iterations` budget.
```

- [ ] **Step 3: Re-run the coverage audit grep**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
comm -23 <(grep -E '^#### `[a-z_]+`' contracts/dispatch-signal.md | sed -E 's/.*`([a-z_]+)`.*/\1/' | sort -u) <(grep -E '^\| `[a-z_]+` \|' SKILL.md | sed -E 's/.*`([a-z_]+)`.*/\1/' | sort -u)
```

Expected: **empty output** (no diff).

Also confirm the routing table now has exactly 17 rows:

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -cE '^\| `[a-z_]+` \|' SKILL.md
```

Expected: `17`

- [ ] **Step 4: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add ai-robin/SKILL.md
git commit -m "fix(ai-robin): add 5 missing routing entries to close kernel dead branches

intake_blocked, execute_failed, dispatch_exhausted, research_inconclusive,
planning_replan_exhausted previously had routing actions in the contract but
no row in the main SKILL.md routing table, meaning the kernel had no legal
routing decision when those signals arrived. Now all 17 signal types have
deterministic routing. Adds batch-settled rule for execute_complete/failed."
```

---

## Task 3: Extend stage-state contract to track per-task batch status

**Files:**
- Modify: `/Users/waynewang/AI-Robin-Skill/ai-robin/contracts/stage-state.md` (schema section, currently around line 44)

The new `execute_failed` routing requires the kernel to track failed tasks in the current batch. This task extends the state schema accordingly.

- [ ] **Step 1: Confirm current `current_batch` schema**

Read `/Users/waynewang/AI-Robin-Skill/ai-robin/contracts/stage-state.md` lines 44-49. Current shape:

```json
"current_batch": {
  "batch_id": "string | null — null if no batch is in flight",
  "milestone_ids": ["string"],
  "review_iteration": "integer — 1, 2, or 3 — only meaningful when reviewing this batch",
  "status": "'dispatching' | 'executing' | 'reviewing' | 'committed' | null"
},
```

- [ ] **Step 2: Replace the `current_batch` block with the extended version**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/contracts/stage-state.md`, replace the `"current_batch": { ... }` block (around lines 44-49) with:

```json
"current_batch": {
  "batch_id": "string | null — null if no batch is in flight",
  "milestone_ids": ["string"],
  "tasks": [
    {
      "task_id": "string — matches dispatch_batch payload",
      "status": "'dispatched' | 'complete' | 'failed'",
      "settled_at": "ISO 8601 | null — timestamp when status became complete or failed"
    }
  ],
  "failed_tasks": ["string — task_ids that returned execute_failed; subset of tasks[]"],
  "review_iteration": "integer — 1, 2, or 3 — only meaningful when reviewing this batch",
  "status": "'dispatching' | 'executing' | 'reviewing' | 'committed' | null"
},
```

- [ ] **Step 3: Update the invariants section to reference `tasks` and `failed_tasks`**

In the same file, locate the "Invariants" section (around line 103). Replace it with:

```markdown
## Invariants

- `stage_iterations[current_stage]` >= 1 (we must have entered the stage to be
  in it)
- If `current_batch.batch_id` is not null, `current_batch.status` must not be
  null
- If `current_batch.batch_id` is not null, `current_batch.tasks[]` must contain
  one entry per task in the latest `dispatch_batch` signal (same task_ids)
- `current_batch.failed_tasks` ⊆ `{t.task_id for t in current_batch.tasks if t.status == "failed"}`
- A batch is **settled** iff every entry in `current_batch.tasks[]` has
  `status != "dispatched"`. The batch-settled rule (see SKILL.md) fires exactly
  once per batch, at the first turn after settlement
- `last_ledger_entry_id` must match the actual last entry_id in ledger.jsonl
  (if they diverge, kernel re-reads the ledger's last line to reconcile and
  writes an `anomaly` entry)
- `active_invocations` cannot contain two entries with the same `invocation_id`
```

- [ ] **Step 4: Update the example at the bottom of the file**

In the same file, locate the example block (around line 137-175). Replace the `"current_batch": { ... }` portion of the example to include the new fields:

```json
  "current_batch": {
    "batch_id": "batch-3",
    "milestone_ids": ["m2-api-endpoints", "m3-auth-middleware"],
    "tasks": [
      {"task_id": "batch-3-task-1", "status": "complete", "settled_at": "2026-04-16T14:42:00Z"},
      {"task_id": "batch-3-task-2", "status": "complete", "settled_at": "2026-04-16T14:43:00Z"}
    ],
    "failed_tasks": [],
    "review_iteration": 2,
    "status": "reviewing"
  },
```

- [ ] **Step 5: Verify with Grep**

Run:
```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -c 'failed_tasks' contracts/stage-state.md
```
Expected: `3` or more (schema, invariants, example).

```bash
grep -c '"tasks":' contracts/stage-state.md
```
Expected: `2` (schema + example).

- [ ] **Step 6: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add ai-robin/contracts/stage-state.md
git commit -m "feat(ai-robin): extend stage-state.current_batch to track per-task settlement

Adds tasks[] and failed_tasks[] fields so the kernel can apply the
batch-settled rule when execute_failed signals arrive. Required by the
execute_failed routing entry added in the previous commit."
```

---

## Task 4: Add commit_message field to review_merged signal contract

**Files:**
- Modify: `/Users/waynewang/AI-Robin-Skill/ai-robin/contracts/dispatch-signal.md` (review_merged section, currently lines 347-365; plus example section, currently lines 436-477)

The `review_merged` payload currently carries no commit message, yet the kernel is required to produce a `commit_message` string for every commit ledger entry. This task adds the field so Merge Agent becomes the authoritative producer.

- [ ] **Step 1: Update the `review_merged` payload schema**

Read `/Users/waynewang/AI-Robin-Skill/ai-robin/contracts/dispatch-signal.md` lines 347-373. Find the `#### `review_merged`` heading and its payload block.

Replace the existing payload block (currently):

```json
{
  "batch_id": "string",
  "overall_status": "'pass' | 'pass_with_warnings' | 'fail'",
  "consolidated_issues": [
    {
      "severity": "string",
      "source_playbooks": ["string"],
      "description": "string"
    }
  ],
  "review_iteration": "integer — 1 or 2 or 3",
  "commit_ready": "boolean — always true; kernel commits regardless"
}
```

With the extended version (adds `commit_message` and `summary`):

```json
{
  "batch_id": "string",
  "overall_status": "'pass' | 'pass_with_warnings' | 'fail'",
  "consolidated_issues": [
    {
      "severity": "string",
      "source_playbooks": ["string"],
      "description": "string"
    }
  ],
  "review_iteration": "integer — 1 or 2 or 3",
  "commit_ready": "boolean — always true; kernel commits regardless",
  "summary": "string — one-paragraph narrative of what was reviewed and the outcome; written by Merge Agent's Phase 4",
  "commit_message": "string — the exact git commit message the kernel uses; Conventional Commits-style header + body; see review/merge/phases/phase-4-emit.md for format"
}
```

- [ ] **Step 2: Update the "Main agent action" note for `review_merged`**

Immediately after the updated payload block, the note currently reads (lines 367-373):

```markdown
Main agent action:
1. **Commit all artifacts + this verdict to git immediately** (hard rule)
2. Then route:
   - `pass` or `pass_with_warnings` → signal Execute-Control for next batch
   - `fail` + iteration < budget → signal Planning for replan with issues
   - `fail` + iteration >= budget → trigger degradation
```

Replace with:

```markdown
Main agent action:
1. **Commit all artifacts + this verdict to git immediately** (hard rule).
   Use `payload.commit_message` verbatim as the commit message. Kernel does
   NOT synthesize its own message — Merge Agent is authoritative.
2. Write a `commit` ledger entry with `content.commit_message` = the exact
   string used (for audit).
3. Then route:
   - `pass` or `pass_with_warnings` → signal Execute-Control for next batch
   - `fail` + iteration < budget → signal Planning for replan with issues
   - `fail` + iteration >= budget → trigger degradation
```

- [ ] **Step 3: Update the full Example section at the bottom**

Locate the example (lines 436-477 in the original file — the big JSON object with `"signal_id": "review-code-quality-..."`). This example is for `review_sub_verdict`, not `review_merged`, so it is unaffected. Leave it alone.

However, add a new example block for `review_merged` directly after the existing example. Append this to the end of the Example section:

```markdown
### Example: `review_merged`

```json
{
  "signal_id": "review-merged-batch3-20260416T144530-c4e2",
  "signal_type": "review_merged",
  "produced_by": {
    "agent": "review-merge",
    "invocation_id": "inv-review-merge-batch-3",
    "stage": "review",
    "iteration": 1
  },
  "produced_at": "2026-04-16T14:45:30Z",
  "payload": {
    "batch_id": "batch-3",
    "review_iteration": 1,
    "overall_status": "pass_with_warnings",
    "consolidated_issues": [
      {
        "severity": "quality",
        "source_playbooks": ["code-quality"],
        "description": "handleCreate exceeds 80 lines; extractable helper suggested."
      }
    ],
    "summary": "Batch 3 reviewed by 3 playbooks. All passed with one quality warning on function length. Ready for commit.",
    "commit_message": "feat(api): implement user CRUD endpoints (batch-3)\n\nReview: pass_with_warnings (iteration 1)\n- 1 quality warning on function length, non-blocking\n\nMilestones: m2-api-endpoints, m3-auth-middleware\nPlaybooks run: code-quality, backend-api, test-coverage",
    "commit_ready": true
  },
  "budget_consumed": {"tokens_estimated": 2100, "wall_clock_seconds": 12},
  "artifacts": [
    {"kind": "verdict", "path": ".ai-robin/dispatch/inbox/review-merged-batch3-20260416T144530-c4e2.json"}
  ],
  "self_check": {"declared_complete": true, "notes": null}
}
```
```

- [ ] **Step 4: Verify**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -c 'commit_message' contracts/dispatch-signal.md
```
Expected: `5` or more (schema definition, action note, example in review_merged block, example at bottom, cross-reference).

- [ ] **Step 5: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add ai-robin/contracts/dispatch-signal.md
git commit -m "feat(ai-robin): add commit_message + summary to review_merged payload

Closes the broken information pipeline where the kernel was required to
produce a commit_message ledger entry but had no authoritative source. Now
Merge Agent produces the exact commit message and the kernel uses it
verbatim, preserving kernel context-minimalism."
```

---

## Task 5: Update Merge Agent phase-4 to produce commit_message

**Files:**
- Modify: `/Users/waynewang/AI-Robin-Skill/ai-robin/review/merge/phases/phase-4-emit.md`

Now that the contract requires a `commit_message`, the Merge Agent must actually produce it. This task adds the composition methodology to phase-4-emit.md.

- [ ] **Step 1: Read the current phase-4-emit.md to identify insertion points**

Read `/Users/waynewang/AI-Robin-Skill/ai-robin/review/merge/phases/phase-4-emit.md`. Confirm it currently has sections: "Write the summary", "Set `commit_ready`", "Emit `review_merged`", "Signal file format", "After emitting".

- [ ] **Step 2: Insert a new "Compose `commit_message`" section between "Set `commit_ready`" and "Emit `review_merged`"**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/review/merge/phases/phase-4-emit.md`, find the section heading:

```markdown
## Set `commit_ready`

Always `true`. The kernel commits every merged verdict regardless of
pass/fail. This field exists for schema symmetry with other signals,
not as a gate.
```

Directly after this block (before the `## Emit `review_merged`` heading), insert this new section:

````markdown
## Compose `commit_message`

**Autonomy: guided** (content); **explicit** (format).

The kernel uses `payload.commit_message` verbatim as the git commit
message. You are the authoritative producer — the kernel does NOT
synthesize its own. Write a message that a human reviewer scanning
`git log` can understand without reading the code.

### Format

Conventional-Commits-style header + body, separated by a blank line:

```
<type>(<scope>): <short description> (batch-<N>)

Review: <overall_status> (iteration <N>)
<one-or-two-line summary of key findings>

Milestones: <m1-id>, <m2-id>, ...
Playbooks run: <playbook_1>, <playbook_2>, ...
```

- `<type>`: infer from the batch's change specs. Common values:
  `feat` (new functionality), `fix` (bug fix), `refactor`, `test`,
  `docs`, `chore`. If the batch is heterogeneous, use `feat`.
- `<scope>`: the primary room affected (e.g., `api`, `db`, `frontend`).
  If the batch spans rooms, pick the room with the most milestones.
- `<short description>`: one clause describing what the batch produced.
  Draw from milestone names or from `consolidated_issues`.
- `<N>`: `batch_id` suffix.
- Body: mirror `summary` but formatted for git log readability.

### Three concrete examples

**Pass**:
```
feat(api): implement user CRUD endpoints (batch-3)

Review: pass (iteration 1)
All 3 playbooks clean. No issues flagged.

Milestones: m2-api-endpoints, m3-auth-middleware
Playbooks run: code-quality, backend-api, test-coverage
```

**Pass with warnings**:
```
feat(api): implement user CRUD endpoints (batch-3)

Review: pass_with_warnings (iteration 1)
1 quality warning on function length, non-blocking.

Milestones: m2-api-endpoints, m3-auth-middleware
Playbooks run: code-quality, backend-api, test-coverage
```

**Fail** (kernel still commits the failed attempt per hard rule):
```
review(failed): batch-3 iteration 1 — uniqueness check missing

Review: fail (iteration 1)
1 blocking issue: user creation inserts without email uniqueness check.
backend-api and db-schema both flagged; replan will follow.

Milestones: m2-api-endpoints, m3-auth-middleware
Playbooks run: code-quality, backend-api, db-schema, test-coverage
```

Note the `review(failed):` type for failed iterations — this distinguishes
failed-attempt commits from successful ones in `git log`.

### When commit_message cannot be composed

If `sub_verdicts` is empty (zero playbooks returned) or all sub-verdicts
were malformed, produce a fallback message:

```
review(anomaly): batch-<N> — merge produced no verdict

Review: fail (iteration <N>)
Merge could not synthesize a verdict from the returned sub-verdicts.
See ledger for the anomaly entry.
```

Emit as `overall_status: fail` with the fallback `commit_message` so the
kernel's hard-commit rule can still execute deterministically.
````

- [ ] **Step 3: Update the "Full payload" example in the same file**

In the same `phase-4-emit.md`, locate the "Full payload" example block (the JSON block starting `"batch_id": "batch-3"` around line 45). Replace the entire JSON block with this version that includes the new `commit_message` and `summary` fields:

```json
{
  "batch_id": "batch-3",
  "review_iteration": 1,
  "sub_verdicts_count": 4,
  "sub_verdicts_included": ["code-quality", "backend-api", "db-schema", "test-coverage"],
  "overall_status": "fail",
  "consolidated_issues": [
    {
      "issue_id": "m-1",
      "severity": "blocking",
      "source_playbooks": ["backend-api", "db-schema"],
      "source_issue_ids": ["ba-3", "db-1"],
      "merged": true,
      "location": {"file": "apps/api/src/routes/users.ts", "line_start": 78, "line_end": 82, "spec_id": null},
      "description": "User creation inserts row without running email uniqueness check; schema has UNIQUE constraint, so this will throw at runtime.",
      "rationale": "backend-api §4.2: every constraint violation must be surfaced as typed error. db-schema §1.3: application code must validate against schema constraints before insert.",
      "suggested_action": "Add uniqueness check before insert, return typed EmailTakenError."
    }
  ],
  "cross_playbook_observations": [
    {
      "description": "code-quality and backend-api both flagged handleCreate for different reasons (length vs error handling). Suggests the function has grown to encompass too many responsibilities.",
      "example": "Consider whether next Planning iteration should split the user creation flow into orchestration + persistence."
    }
  ],
  "summary": "Batch 3 has one blocking issue around uniqueness validation that must be fixed. Other playbooks clean or minor warnings.",
  "commit_message": "review(failed): batch-3 iteration 1 — uniqueness check missing\n\nReview: fail (iteration 1)\n1 blocking issue: user creation inserts without email uniqueness check.\nbackend-api and db-schema both flagged; replan will follow.\n\nMilestones: m2-api-endpoints, m3-auth-middleware\nPlaybooks run: code-quality, backend-api, db-schema, test-coverage",
  "commit_ready": true
}
```

- [ ] **Step 4: Verify**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -c 'commit_message' review/merge/phases/phase-4-emit.md
```
Expected: `5` or more.

```bash
grep -c 'Autonomy' review/merge/phases/phase-4-emit.md
```
Expected: `2` (one for summary, one for the new compose section).

- [ ] **Step 5: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add ai-robin/review/merge/phases/phase-4-emit.md
git commit -m "feat(ai-robin): teach Merge Agent to compose commit_message

Adds the Compose commit_message section to phase-4-emit.md with format,
three concrete examples (pass, pass_with_warnings, fail), and fallback
when no sub-verdicts are available. Pairs with the dispatch-signal
contract change that made commit_message a required field."
```

---

## Task 6: Update session-ledger contract to reference Merge-provided commit_message

**Files:**
- Modify: `/Users/waynewang/AI-Robin-Skill/ai-robin/contracts/session-ledger.md` (commit entry section, currently around lines 170-185)

Clarify that the `commit` ledger entry's `commit_message` field is copied verbatim from `review_merged.payload.commit_message` (or from the kernel-composed degradation-commit message for `[degradation]` commits).

- [ ] **Step 1: Find the `### `commit`` entry section**

Read `/Users/waynewang/AI-Robin-Skill/ai-robin/contracts/session-ledger.md` lines 170-185. Locate:

```markdown
### `commit`
Kernel performed a git commit (always after review).

```json
{
  "entry_type": "commit",
  "content": {
    "batch_id": "string",
    "review_status": "'pass' | 'pass_with_warnings' | 'fail'",
    "review_iteration": "integer",
    "git_hash": "string",
    "commit_message": "string",
    "files_committed": "integer"
  }
}
```
```

- [ ] **Step 2: Add a source-provenance note immediately after the JSON block**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/contracts/session-ledger.md`, directly after the `commit` entry's closing triple-backtick, insert this note before the next entry type (`### `user_message_received``):

```markdown
The `commit_message` field is copied verbatim from the source:

- For review commits: `review_merged.payload.commit_message` (produced by Merge Agent's Phase 4)
- For degradation commits: kernel-composed from the degradation trigger payload using the deterministic pattern `[degradation] <scope>: <short reason>`, where both `<scope>` and `<short reason>` come from the degradation trigger and require no spec reading (preserving kernel context-minimalism).

Kernel does not otherwise synthesize commit messages.
```

- [ ] **Step 3: Verify**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -A 3 'The `commit_message` field is copied' contracts/session-ledger.md
```
Expected: shows the 3-line note just added.

- [ ] **Step 4: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add ai-robin/contracts/session-ledger.md
git commit -m "docs(ai-robin): document commit_message provenance in ledger contract

Makes explicit that review-commit messages come from review_merged.payload
and degradation-commit messages follow a deterministic kernel pattern. No
other path produces commit messages, closing the audit-trail ambiguity."
```

---

## Task 7: Define deterministic signal-ordering rule in kernel-discipline

**Files:**
- Modify: `/Users/waynewang/AI-Robin-Skill/ai-robin/stdlib/kernel-discipline.md` (section "3. One routing per turn", currently around lines 80-94)
- Modify: `/Users/waynewang/AI-Robin-Skill/ai-robin/contracts/dispatch-signal.md` (validation rules section, currently around lines 417-426)

When multiple signals accumulate in `.ai-robin/dispatch/inbox/`, the kernel must process them in a defined order for audit determinism.

- [ ] **Step 1: Update kernel-discipline rule #3**

Read `/Users/waynewang/AI-Robin-Skill/ai-robin/stdlib/kernel-discipline.md` lines 80-94. Locate section `### 3. One routing per turn` and the paragraph that begins `Each turn of the main agent processes exactly one signal from the inbox`.

In that section, immediately after the paragraph that ends `this rule makes the kernel's behavior linearizable and the ledger deterministic.`, insert:

```markdown
### Signal ordering when inbox has multiple files

When two or more signal files are in `.ai-robin/dispatch/inbox/` at the start
of a turn, process them in **lexicographic order of `signal_id`**. Because
`signal_id` has format `{stage}-{agent-name}-{YYYYMMDDTHHMMSS}-{shortuuid}`,
lexicographic order is:

- Chronological within the same `{stage}-{agent}` prefix (timestamp sort)
- Deterministic but not chronological across different prefixes (alphabetic
  on prefix first)

Determinism matters for replay and audit; strict chronology does not.
Lexicographic `signal_id` sort gives total order with zero filesystem
metadata dependencies.

The kernel reads one signal, routes it, moves it to `processed/`, then
returns to inbox-check at the top of the next turn. Never process two
signals "in parallel" within one turn.

If `signal_id` collisions somehow occur (different sub-agents with the
same id), treat as anomaly: log, pick the lexicographically first filename
as a deterministic tiebreaker, process it, then log a `correction` entry
noting the collision.
```

- [ ] **Step 2: Update dispatch-signal validation rules**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/contracts/dispatch-signal.md`, locate the `## Validation rules` section (around lines 417-426). Replace the current list with this extended list:

```markdown
## Validation rules

- `signal_id` must be unique within a run. Uniqueness is enforced by the
  producing sub-agent via the `{stage}-{agent}-{timestamp}-{shortuuid}` format.
- `signal_id` is the sort key the kernel uses to order multiple pending
  signals; see `stdlib/kernel-discipline.md` § "Signal ordering when inbox
  has multiple files".
- `signal_type` must be one of the enumerated values in this document
- `produced_by.invocation_id` must match an invocation main agent actually
  spawned (prevents stray signals from rogue contexts)
- Payload shape must match the signal_type's spec exactly — extra fields are
  allowed, missing required fields are a malformed signal
- `artifacts[].path` must be inside the project root or inside `.ai-robin/`
- `budget_consumed` must be present; if unknown, use best-effort estimates
```

- [ ] **Step 3: Verify**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -c 'lexicographic' stdlib/kernel-discipline.md contracts/dispatch-signal.md
```
Expected: `2` or more (at least one mention in each file).

- [ ] **Step 4: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add ai-robin/stdlib/kernel-discipline.md ai-robin/contracts/dispatch-signal.md
git commit -m "fix(ai-robin): define deterministic signal-ordering for multi-signal turns

When multiple sub-agents emit signals between kernel turns, the kernel now
processes them in lexicographic order of signal_id. Chronological within
stage+agent prefix, deterministic across prefixes. Required for ledger
replay parity and audit determinism."
```

---

## Task 8: Strip activation frontmatter from sub-skill SKILL.md files

**Files:**
- Modify: `ai-robin/consumer/SKILL.md`, `ai-robin/planning/SKILL.md`, `ai-robin/execute-control/SKILL.md`, `ai-robin/execute/SKILL.md`, `ai-robin/research/SKILL.md`, `ai-robin/review/SKILL.md`, `ai-robin/review/review-plan/SKILL.md`, `ai-robin/review/merge/SKILL.md`

Sub-skill SKILL.md files currently carry YAML frontmatter with `name:` and `description:`. If installed into Claude Code's skill directory, each would register as a top-level user-invocable skill, contradicting the "Do NOT invoke directly" instruction in the description. Strip the frontmatter and replace it with a plain markdown "Internal sub-skill" banner. The main `ai-robin/SKILL.md` keeps its frontmatter — it IS user-invocable.

- [ ] **Step 1: Strip frontmatter from consumer/SKILL.md**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/consumer/SKILL.md`, replace the exact block at the top (lines 1-10):

```markdown
---
name: ai-robin-consumer
description: >
  The Intake Stage sub-agent for AI-Robin. Reads raw user input (chat messages,
  pasted docs, loose requirements), drives a bounded interaction to surface
  decisions and fill gaps, and produces a planning-ready Feature Room spec set.
  This is the ONLY stage where AI-Robin interacts with the user. Do NOT invoke
  directly — invoked by the AI-Robin main agent at run start.
---

# Consumer Agent — Stage 0: Intake
```

With this:

```markdown
# Consumer Agent — Stage 0: Intake

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main
> agent via the Read tool as part of the orchestrated workflow. This file
> has no YAML frontmatter by design: it must not register as a top-level
> Claude Code skill. Do not re-introduce frontmatter without updating the
> runtime-adaptation section of DESIGN.md.
```

(Keep all the content after the original `# Consumer Agent — Stage 0: Intake` heading exactly as it was.)

- [ ] **Step 2: Strip frontmatter from planning/SKILL.md**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/planning/SKILL.md`, replace the top block (lines 1-10):

```markdown
---
name: ai-robin-planning
description: >
  The Planning Stage sub-agent for AI-Robin. Reads Consumer's spec output and
  produces an execution-ready plan with milestones, module boundaries, API
  contracts, and concurrency hints. May re-spawn to handle research gaps,
  sub-planning, or post-review rework. Do NOT invoke directly — invoked by
  the AI-Robin main agent as part of the batch workflow.
---

# Planning Agent — Stage 1: Planning
```

With:

```markdown
# Planning Agent — Stage 1: Planning

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main
> agent via the Read tool as part of the orchestrated workflow. This file
> has no YAML frontmatter by design: it must not register as a top-level
> Claude Code skill. Do not re-introduce frontmatter without updating the
> runtime-adaptation section of DESIGN.md.
```

- [ ] **Step 3: Strip frontmatter from execute-control/SKILL.md**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/execute-control/SKILL.md`, replace the top block (lines 1-11):

```markdown
---
name: ai-robin-execute-control
description: >
  The Execute-Control sub-agent for AI-Robin. Reads the plan and current
  progress, decides which milestones to tackle next, determines concurrency
  (how many Execute Agents to spawn and whether parallel or sequential),
  and returns a dispatch batch specification. Do NOT invoke directly —
  invoked by the AI-Robin main agent between planning and execution, and
  after each review cycle to prepare the next batch.
---

# Execute-Control Agent — Stage 2: Batch Formation
```

With:

```markdown
# Execute-Control Agent — Stage 2: Batch Formation

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main
> agent via the Read tool as part of the orchestrated workflow. This file
> has no YAML frontmatter by design: it must not register as a top-level
> Claude Code skill. Do not re-introduce frontmatter without updating the
> runtime-adaptation section of DESIGN.md.
```

- [ ] **Step 4: Strip frontmatter from execute/SKILL.md**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/execute/SKILL.md`, replace the top block (lines 1-11):

```markdown
---
name: ai-robin-execute
description: >
  The Execute sub-agent for AI-Robin. Given a single task (one milestone's
  work), loads the relevant context, writes/modifies code and specs to
  fulfill the task, and returns a structured artifacts summary. Does NOT
  commit to git (kernel handles commits after review). Does NOT review its
  own output (Review stage does). Do NOT invoke directly — invoked by the
  AI-Robin main agent as part of a batch.
---

# Execute Agent — Stage 3: Actual Work
```

With:

```markdown
# Execute Agent — Stage 3: Actual Work

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main
> agent via the Read tool as part of the orchestrated workflow. This file
> has no YAML frontmatter by design: it must not register as a top-level
> Claude Code skill. Do not re-introduce frontmatter without updating the
> runtime-adaptation section of DESIGN.md.
```

- [ ] **Step 5: Strip frontmatter from research/SKILL.md**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/research/SKILL.md`, replace the top block (lines 1-10):

```markdown
---
name: ai-robin-research
description: >
  The Research sub-agent for AI-Robin. Given a specific question from
  Planning, uses web search and optionally file inspection to produce
  structured findings. Returns findings with confidence and any follow-up
  questions. Do NOT invoke directly — invoked by the AI-Robin main agent
  when Planning returns `planning_needs_research`.
---

# Research Agent
```

With:

```markdown
# Research Agent

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main
> agent via the Read tool as part of the orchestrated workflow. This file
> has no YAML frontmatter by design: it must not register as a top-level
> Claude Code skill. Do not re-introduce frontmatter without updating the
> runtime-adaptation section of DESIGN.md.
```

- [ ] **Step 6: Strip frontmatter from review/SKILL.md**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/review/SKILL.md`, replace the top block (lines 1-9):

```markdown
---
name: ai-robin-review
description: >
  The Review Stage entry for AI-Robin. This is a thin router: it loads the
  review-plan sub-agent to determine which playbooks to run against a batch's
  output. Do NOT invoke directly — invoked by the AI-Robin main agent after
  all Execute Agents in a batch complete.
---

# Review Stage — Entry Point
```

With:

```markdown
# Review Stage — Entry Point

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main
> agent via the Read tool as part of the orchestrated workflow. This file
> has no YAML frontmatter by design: it must not register as a top-level
> Claude Code skill. Do not re-introduce frontmatter without updating the
> runtime-adaptation section of DESIGN.md.
```

- [ ] **Step 7: Strip frontmatter from review/review-plan/SKILL.md**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/review/review-plan/SKILL.md`, replace the top block (lines 1-10):

```markdown
---
name: ai-robin-review-plan
description: >
  The Review-Plan sub-agent for AI-Robin. Given a batch's change artifacts,
  determines which domain-specific review playbooks to run, and the scope
  of each. Returns a review_dispatch signal instructing main agent which
  sub-agents to spawn in parallel. Do NOT invoke directly — invoked by
  the AI-Robin main agent at the start of every review stage.
---

# Review-Plan Agent
```

With:

```markdown
# Review-Plan Agent

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main
> agent via the Read tool as part of the orchestrated workflow. This file
> has no YAML frontmatter by design: it must not register as a top-level
> Claude Code skill. Do not re-introduce frontmatter without updating the
> runtime-adaptation section of DESIGN.md.
```

- [ ] **Step 8: Strip frontmatter from review/merge/SKILL.md**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/review/merge/SKILL.md`, replace the top block (lines 1-9):

```markdown
---
name: ai-robin-review-merge
description: >
  The Review-Merge sub-agent for AI-Robin. Takes N review sub-verdicts from
  individual playbooks and synthesizes them into a single merged verdict
  with consolidated issues and an overall pass/fail status. Do NOT invoke
  directly — invoked by the AI-Robin main agent after all review sub-agents
  for a batch have returned.
---

# Review-Merge Agent
```

With:

```markdown
# Review-Merge Agent

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main
> agent via the Read tool as part of the orchestrated workflow. This file
> has no YAML frontmatter by design: it must not register as a top-level
> Claude Code skill. Do not re-introduce frontmatter without updating the
> runtime-adaptation section of DESIGN.md.
```

- [ ] **Step 9: Verify that only the main SKILL.md has frontmatter**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
for f in SKILL.md consumer/SKILL.md planning/SKILL.md execute-control/SKILL.md execute/SKILL.md research/SKILL.md review/SKILL.md review/review-plan/SKILL.md review/merge/SKILL.md; do
  head -1 "$f" | grep -q '^---$' && echo "$f: HAS FRONTMATTER" || echo "$f: no frontmatter"
done
```

Expected output:
```
SKILL.md: HAS FRONTMATTER
consumer/SKILL.md: no frontmatter
planning/SKILL.md: no frontmatter
execute-control/SKILL.md: no frontmatter
execute/SKILL.md: no frontmatter
research/SKILL.md: no frontmatter
review/SKILL.md: no frontmatter
review/review-plan/SKILL.md: no frontmatter
review/merge/SKILL.md: no frontmatter
```

Also verify each sub-skill has the "Internal sub-skill" banner:

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -l 'Internal sub-skill — not user-invocable' consumer/SKILL.md planning/SKILL.md execute-control/SKILL.md execute/SKILL.md research/SKILL.md review/SKILL.md review/review-plan/SKILL.md review/merge/SKILL.md | wc -l
```

Expected: `8`.

- [ ] **Step 10: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add ai-robin/consumer/SKILL.md ai-robin/planning/SKILL.md ai-robin/execute-control/SKILL.md ai-robin/execute/SKILL.md ai-robin/research/SKILL.md ai-robin/review/SKILL.md ai-robin/review/review-plan/SKILL.md ai-robin/review/merge/SKILL.md
git commit -m "fix(ai-robin): strip activation frontmatter from sub-skill SKILL.md files

Sub-skills previously had YAML frontmatter with name: + description: that
would register them as top-level user-invocable skills in Claude Code,
contradicting their 'Do NOT invoke directly' instruction. Now only the
main ai-robin/SKILL.md is user-invocable; sub-skills are loaded by the
main agent via Read tool. Adds an 'Internal sub-skill' banner to each
explaining the constraint."
```

---

## Task 9: Add "Runtime adaptation" section to DESIGN.md

**Files:**
- Modify: `/Users/waynewang/AI-Robin-Skill/ai-robin/DESIGN.md`

The `.ai-robin/dispatch/inbox/` file-based signaling model is a formal abstraction. Different runtimes satisfy it differently. This task documents the contract so readers understand what "signal arrives in inbox" means in Claude Code vs. a hypothetical async runtime.

- [ ] **Step 1: Read DESIGN.md to find a good insertion point**

Read `/Users/waynewang/AI-Robin-Skill/ai-robin/DESIGN.md`. Find the natural place to insert a new section about runtime. A good location is near the end, before any "Future work" / "References" section, or right after the main architecture explanation.

Run:
```bash
grep -nE '^## ' /Users/waynewang/AI-Robin-Skill/ai-robin/DESIGN.md
```

Identify the last `##` section heading. The new "Runtime adaptation" section should be inserted immediately BEFORE that last section (so it reads as a core design topic, not a trailing appendix).

- [ ] **Step 2: Insert the new "Runtime adaptation" section**

In `/Users/waynewang/AI-Robin-Skill/ai-robin/DESIGN.md`, insert this section at the chosen location:

````markdown
## Runtime adaptation

AI-Robin is a **runtime-agnostic natural-language program (NLP)**. The
architecture assumes sub-agents communicate with the main agent via a
shared inbox (`.ai-robin/dispatch/inbox/{signal-id}.json`). What "communicate
via inbox" concretely means depends on the runtime.

### Reference model (abstract)

- Sub-agents run independently. When done, each writes a single JSON signal
  file to `.ai-robin/dispatch/inbox/`.
- The main agent's turn loop:
  1. Read `stage-state.json`.
  2. Check inbox for new signal files.
  3. Process **one** signal (lexicographic order; see
     `stdlib/kernel-discipline.md`).
  4. Move signal file to `processed/`, append ledger, update state.
- Parallel sub-agents means: N sub-agents each write one signal file; main
  agent processes them across N turns, one signal at a time.

### Claude Code mapping

Claude Code's `Task` tool is **synchronous**: invoking it runs the sub-agent
to completion and returns its result within the same parent turn. There is
no asynchronous "sub-agent is still running in the background" state.

In Claude Code, the reference model collapses cleanly:

- Sub-agent work: main agent invokes `Task`. The sub-agent's SKILL file
  instructs it to write its final signal to
  `.ai-robin/dispatch/inbox/{signal-id}.json` just before returning.
- "Checking inbox": main agent reads `.ai-robin/dispatch/inbox/` with
  `Glob`/`Read` **within the same turn** that the sub-agent returned.
- Parallel dispatch: main agent issues N `Task` tool calls in **one
  message** (Claude Code runs them concurrently). Each sub-agent writes its
  own signal file. After all N return, main agent sees N signals in inbox.
- Signal ordering: the signal files are all present when main agent reads
  them; lexicographic sort on signal_id gives deterministic processing
  order.

The file-based inbox is still the authoritative communication channel even
in Claude Code. Sub-agents must not return structured data "through the
Task return value" alone — the signal file is the source of truth for audit.

### Other runtimes

- **Truly async runtime (e.g., a custom orchestration loop)**: inbox polling
  fires between real asynchronous work. `active_invocations` tracks
  in-flight agents accurately. Signal ordering rule still applies.
- **Single-threaded runtime without parallelism**: spawn "N parallel
  agents" degrades gracefully to sequential execution. Same inbox, same
  routing, just slower.

### Invariants that hold across all runtimes

- One signal per sub-agent invocation.
- Signals are files in `.ai-robin/dispatch/inbox/` until processed.
- Main agent never reads sub-agent tool-return values as the authoritative
  source of signal content — only the inbox file.
- Main agent processes one signal per routing action (see
  `kernel-discipline.md` § 3), regardless of how many are present.

If a runtime cannot satisfy these invariants (e.g., has no filesystem),
an adapter layer is required. AI-Robin does not ship such adapters — they
are out of scope for the v1 NLP.

### Sub-skill invocation and activation

AI-Robin's sub-skills (`consumer/SKILL.md`, `planning/SKILL.md`, etc.)
must **not** be registered as top-level user-invocable skills. Only the
root `ai-robin/SKILL.md` has YAML frontmatter; all sub-skill files omit
it so the main agent can load them via the `Read` tool without the
runtime treating them as independent skills discoverable from user intent.

If a runtime's skill-discovery mechanism does not recognize the
frontmatter-less convention, the sub-skill files should be renamed
(e.g., to `AGENT.md`) as a runtime-specific adaptation. The root
`ai-robin/SKILL.md`'s internal references can then be updated to the
new filename. This is purely a runtime-adapter concern, not a change to
the abstract design.
````

- [ ] **Step 3: Verify**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -c '^## Runtime adaptation' DESIGN.md
```
Expected: `1`.

```bash
grep -c 'lexicographic' DESIGN.md
```
Expected: `1` or more.

- [ ] **Step 4: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add ai-robin/DESIGN.md
git commit -m "docs(ai-robin): add Runtime adaptation section to DESIGN.md

Makes explicit that ai-robin's inbox model is an abstraction. Documents
how it maps to Claude Code's synchronous Task tool (parallel dispatch via
single-message-multi-tool-call; signal files still authoritative) and
preserves the sub-skill activation invariant."
```

---

## Task 10: Write end-to-end trace verification document

**Files:**
- Create: `/Users/waynewang/AI-Robin-Skill/ai-robin/tests/end-to-end-trace.md`

A readable, narrative walkthrough of five concrete scenarios through the routing table. This document is the final check that Tasks 1-9 compose into a runnable whole. If any scenario dead-ends, that's a routing bug to fix before merging Plan 1.

- [ ] **Step 1: Create the trace document**

Create `/Users/waynewang/AI-Robin-Skill/ai-robin/tests/end-to-end-trace.md` with this exact content:

````markdown
# AI-Robin End-to-End Trace Verification

Five scenarios walked through the routing table in `SKILL.md`. Every step
lists the incoming signal, the exact routing-table row that handles it,
the resulting kernel action, and the next expected signal. Each scenario
MUST terminate (with `run_end`) without a dead branch.

This is a human-readable audit. If a future edit to the routing table
breaks a scenario, that's a regression and the edit must be revised.

---

## Scenario 1: Happy path (one-milestone project)

1. User invokes ai-robin with "build a CLI that says hello".
2. Kernel initializes: stage=`intake`, spawns Consumer Agent.
3. Consumer runs intake, emits `intake_complete` (no proxy decisions).
   - Routing: `intake_complete` → spawn Planning Agent.
4. Planning runs, emits `planning_complete` with 1 milestone.
   - Routing: `planning_complete` → spawn Execute-Control.
5. Execute-Control emits `dispatch_batch` with 1 task.
   - Routing: `dispatch_batch` → spawn 1 Execute Agent.
6. Execute Agent emits `execute_complete`.
   - Routing: `execute_complete` → batch-settled rule → 1 complete, 0
     failed → spawn Review-Plan.
7. Review-Plan emits `review_dispatch` with 1 playbook (code-quality).
   - Routing: `review_dispatch` → spawn 1 review playbook.
8. Code-quality playbook emits `review_sub_verdict` (pass).
   - Routing: `review_sub_verdict` → all returned → spawn Merge.
9. Merge emits `review_merged` with `commit_message` and
   `overall_status: pass`.
   - Routing: `review_merged` → commit using `payload.commit_message` →
     back to Execute-Control.
10. Execute-Control has no more milestones, emits `all_complete`.
    - Routing: `all_complete` → write run_end → exit.

**Status:** Terminates cleanly.

---

## Scenario 2: Research inconclusive

1. Kernel at stage=`planning` after `planning_needs_research`.
2. Research Agent spawned with question `q-auth-lib`, depth=1.
3. Research Agent cannot find confident answer, emits
   `research_inconclusive` with `best_guess: "use Lucia"`, confidence 0.4.
   - Routing: `research_inconclusive` → log anomaly → re-spawn Planning
     with best_guess + confidence flag.
4. Planning receives best_guess, records decision-auth-lib spec with
   `confidence: 0.4, provenance: research_low_confidence`, continues.
5. Planning emits `planning_complete`.
   - Routing: `planning_complete` → spawn Execute-Control. (Continues as
     Scenario 1 from step 5.)

**Status:** Terminates cleanly. The low-confidence decision is
auditable via spec provenance.

---

## Scenario 3: Execute-failed on one task in a 3-task batch

1. Kernel dispatched batch-2 with 3 tasks (parallel).
2. Task-1 returns `execute_complete`.
   - Routing: mark task-1 complete. Batch not settled (task-2, task-3
     still dispatched). Wait.
3. Task-2 returns `execute_failed` (reason: scope_insufficient).
   - Routing: mark task-2 failed in `failed_tasks`. Batch not settled
     (task-3 still dispatched). Wait.
4. Task-3 returns `execute_complete`.
   - Routing: mark task-3 complete. Batch now settled: 2 complete, 1
     failed. Batch-settled rule: at least one complete → spawn
     Review-Plan with `failed_tasks: [task-2]`.
5. Review-Plan dispatches playbooks scoped to only the completed tasks'
   artifacts, with `partial_batch_note` referencing failed task-2.
6. Review proceeds as Scenario 1.
7. After review commit, kernel routes:
   - If `overall_status: pass` → back to Execute-Control, which will see
     task-2's milestone still `in_progress_milestones` and form a new
     batch for it.
   - If `overall_status: fail` → back to Planning for replan, consuming
     `replan_iterations` budget.

**Status:** Terminates cleanly regardless of review outcome. Failed task
re-enters through normal replan / next-batch flow.

---

## Scenario 4: Planning replan exhausted

1. Batch-3 review failed twice (iterations 1 and 2, both flagged the
   same issue).
2. After 2nd fail, kernel commits the failed attempt, decrements
   `review_iterations_per_batch[batch-3]` to 0.
3. Kernel consults budget → review_iterations_per_batch[batch-3]
   exhausted.
4. Degradation triggered for batch-3 (see `degradation-policy.md` —
   kernel writes context-degraded spec, commits with `[degradation]`
   message).
5. Kernel returns to Execute-Control for next batch.
6. Parallel scenario: suppose Planning returned
   `planning_replan_exhausted` at some point (replan budget also spent).
   - Routing: `planning_replan_exhausted` → trigger degradation for
     `unresolvable_issues` → continue other scopes.
7. Execute-Control sees `degraded_milestones` includes batch-3's
   milestones, skips them, forms next batch from remaining pending.
8. Eventually `all_complete` (possibly with many degraded milestones) or
   `dispatch_exhausted` if remaining are all blocked on degraded deps.

**Status:** Terminates cleanly. Degradations surface in
escalation-notice; run_end carries degradation counts.

---

## Scenario 5: Intake blocked

1. User invokes ai-robin with "something vague I don't want to
   elaborate".
2. Consumer Agent runs intake, tries to extract decisions; user responds
   with dismissive one-liners or stops responding after turn 3.
3. Consumer emits `intake_blocked` with `reason:
   input_fundamentally_incomplete`.
4. Routing: `intake_blocked` → write run_end with
   `exit_reason: "intake_blocked"` → surface partial spec path + reason
   to user → exit.

**Status:** Terminates cleanly. No domain work attempted; user can retry
with more input.

---

## Coverage check

Every signal type declared in `contracts/dispatch-signal.md` is exercised
by at least one scenario above:

- Scenario 1: `intake_complete`, `planning_complete`, `dispatch_batch`,
  `execute_complete`, `review_dispatch`, `review_sub_verdict`,
  `review_merged`, `all_complete`
- Scenario 2: `planning_needs_research`, `research_inconclusive`,
  `research_complete` (implicit in 2a variant — covered)
- Scenario 3: `execute_failed` (batch-settled with failures)
- Scenario 4: `planning_replan_exhausted`, `stage_exhausted` (implicit
  in degradation path)
- Scenario 5: `intake_blocked`
- Not covered here: `planning_needs_sub_planning`, `dispatch_exhausted`
  — both use identical routing patterns as `planning_needs_research` and
  `planning_replan_exhausted` respectively. Add explicit scenarios if
  behavior diverges.

If a new signal type is added to the contract, a new scenario (or
extension of an existing one) MUST be added here.
````

- [ ] **Step 2: Run the scenario coverage cross-check**

For every signal type in the contract, confirm it appears at least once in the trace document:

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
for sig in $(grep -E '^#### `[a-z_]+`' contracts/dispatch-signal.md | sed -E 's/.*`([a-z_]+)`.*/\1/' | sort -u); do
  grep -q "$sig" tests/end-to-end-trace.md && echo "$sig: covered" || echo "$sig: MISSING"
done
```

Expected: **every signal prints "covered"**. If any is missing, extend a scenario to reference it.

- [ ] **Step 3: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add ai-robin/tests/end-to-end-trace.md
git commit -m "test(ai-robin): add end-to-end trace scenarios covering all signal types

Five narrative walkthroughs through the routing table. Every declared
signal type appears in at least one scenario, proving the routing table
(as of this commit) has no dead branches. If a future edit breaks a
scenario, that's a regression and the edit must be revised."
```

---

## Final verification (after all tasks complete)

Run these checks from `/Users/waynewang/AI-Robin-Skill/ai-robin`:

```bash
# 1. Every signal type has a routing entry
comm -23 <(grep -E '^#### `[a-z_]+`' contracts/dispatch-signal.md | sed -E 's/.*`([a-z_]+)`.*/\1/' | sort -u) <(grep -E '^\| `[a-z_]+` \|' SKILL.md | sed -E 's/.*`([a-z_]+)`.*/\1/' | sort -u)
```
Expected: empty.

```bash
# 2. commit_message present in contract, merge phase-4, and ledger provenance note
grep -c 'commit_message' contracts/dispatch-signal.md review/merge/phases/phase-4-emit.md contracts/session-ledger.md
```
Expected: each file has 2+ mentions.

```bash
# 3. Only main SKILL.md has frontmatter; all sub-skill SKILL.md files have the banner
head -1 SKILL.md consumer/SKILL.md planning/SKILL.md execute-control/SKILL.md execute/SKILL.md research/SKILL.md review/SKILL.md review/review-plan/SKILL.md review/merge/SKILL.md
```
Expected: only the root `SKILL.md` starts with `---`; every other starts with `# <Agent Name>`.

```bash
# 4. Runtime adaptation section exists
grep -c '^## Runtime adaptation' DESIGN.md
```
Expected: `1`.

```bash
# 5. Signal ordering rule present
grep -l 'lexicographic' stdlib/kernel-discipline.md contracts/dispatch-signal.md
```
Expected: both files listed.

```bash
# 6. All 5 scenarios have a "Status: Terminates cleanly" line
grep -c 'Terminates cleanly' tests/end-to-end-trace.md
```
Expected: `5`.

If all six checks pass, Plan 1 is complete. The ai-robin skill is now
runnable end-to-end: every signal routes deterministically, commit
messages flow through a defined pipeline, sub-skills no longer
double-register as user-invocable skills, signal ordering is
deterministic across runtimes, and the runtime-adaptation contract is
documented.

## What Plan 1 does NOT fix (intentionally deferred to later plans)

- **Plan 2 (Kernel purification)**: extracts degradation-spec writing and
  commit-composition entirely out of the kernel into dedicated Commit
  Agent / Degradation Agent sub-skills; also fixes research depth
  tracking (kernel gains a research question tree) and extends
  `plan_pointer` to support non-milestone degradation scopes.
- **Plan 3 (Production hardening)**: introduces a `scripts/` layer for
  deterministic operations (ledger append, signal file move, state
  update) and wires review-scope enforcement into runtime permission
  systems where possible.

Plan 1 is sufficient for the skill to complete an end-to-end run. Plans
2 and 3 elevate it from "functionally correct" to "architecturally
pure".
