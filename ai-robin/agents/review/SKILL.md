# Review Stage — Entry Point

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main
> agent via the Read tool as part of the orchestrated workflow. This file
> has no YAML frontmatter by design: it must not register as a top-level
> Claude Code skill. Do not re-introduce frontmatter without updating the
> runtime-adaptation section of DESIGN.md.

Review is the most structurally complex stage in AI-Robin. It's not a single
agent — it's a **plan-then-fan-out-then-merge** structure:

```
Execute Agents complete batch
  ↓
Review-Plan Agent analyzes change → decides which playbooks to run
  ↓
Main agent spawns N review sub-agents (one per playbook)
  ↓
Each playbook returns a sub-verdict
  ↓
Merge Agent consolidates into one merged verdict
  ↓
Kernel commits (hard rule), then routes next
```

This entry file (`agents/review/SKILL.md`) is just a pointer. It tells main agent:
"spawn `agents/review/review-plan/SKILL.md` to determine the review dispatch".

---

## When this stage runs

Review runs after every batch's Execute stage completes — meaning after ALL
Execute Agents in a batch have returned `execute_complete` (or their
`execute_failed` has been routed). It runs even if some tasks in the batch
failed — the completed tasks still need review, and failed tasks may need
their partial artifacts evaluated.

---

## Prerequisites

None loaded by this entry file. The actual sub-agents (review-plan, merge,
and each playbook) have their own prerequisites.

---

## Input

This entry file doesn't execute; it's just a reference. The actual input
flows to:

- `agents/review/review-plan/SKILL.md` when main agent spawns it
- `agents/review/playbooks/{name}/SKILL.md` for each playbook dispatch
- `agents/review/merge/SKILL.md` when all playbooks have returned

---

## The review flow (for main agent's reference)

1. **Batch's Execute phase ends**. Main agent receives the last
   `execute_complete` (or `execute_failed`) signal for the batch.

2. **Main agent spawns Review-Plan**. Load `agents/review/review-plan/SKILL.md`.
   Input: the batch_id and the list of all change specs produced.

3. **Review-Plan returns `review_dispatch`**. Contains a list of
   `playbooks` to run, each scoped to specific files/specs within the
   batch's changes.

4. **Main agent spawns N review sub-agents in parallel**. For each
   playbook in the dispatch:
   - Load `agents/review/playbooks/{playbook_name}/SKILL.md`
   - Input: the scope subset + the change specs in that scope
   - Each runs independently, produces a `review_sub_verdict` signal

5. **Main agent collects sub-verdicts**. When all N have returned, spawn
   Merge Agent.

6. **Merge Agent returns `review_merged`**. Consolidates all sub-verdicts
   into overall pass/fail + consolidated issues.

7. **Kernel commits**. The merged verdict and all batch artifacts are
   committed to git (hard rule from agents/kernel/discipline.md).

8. **Kernel routes**:
   - `overall_status: pass` or `pass_with_warnings` → Execute-Control for
     next batch
   - `overall_status: fail` + within review_iterations budget → Planning
     for replan
   - `overall_status: fail` + budget exhausted → degrade

---

## Playbook catalog

The set of available playbooks lives in `agents/review/playbooks/`. Each is a
sub-skill. At the time of this document:

| Playbook | Trigger condition | Severity focus |
|---|---|---|
| `code-quality` | Always spawned | quality |
| `frontend-component` | Changed files match `**/*.{jsx,tsx,vue,svelte}` | quality + blocking |
| `frontend-a11y` | Changed files match frontend component patterns | quality |
| `backend-api` | Changed files match `**/api/**`, `**/routes/**`, etc. | blocking |
| `db-schema` | Changed files match `**/migrations/**`, `**/schema*` | blocking |
| `agent-integration` | Changed files match agent/prompt/tool definitions | quality + blocking |
| `test-coverage` | Any source file changed | advisory |
| `spec-anchors` | Any change spec references anchor updates | blocking |

Review-Plan Agent decides which of these apply to a given batch.

New playbooks can be added over time — each is a self-contained sub-skill
under `agents/review/playbooks/{name}/SKILL.md`. Review-Plan Agent is responsible
for knowing which playbooks exist (it reads the directory listing).

---

## Rules for the Review stage as a whole

### Rule 1: Always commit, pass or fail

The kernel commits after every review regardless of outcome. A failed
review creates a commit recording the attempt + the verdict, followed
(eventually) by another commit when the rework completes. This preserves
the full history for audit.

### Rule 2: Review iterations are budgeted

`review_iterations_per_batch` defaults to 2. After 2 fails on the same
batch, degrade that batch's scope instead of a 3rd attempt.

### Rule 3: Sub-agents are stateless

Each review sub-agent (playbook) is invoked fresh. They do not know about
previous runs of themselves on earlier iterations of this batch. If a
playbook flagged issue X in iteration 1, and iteration 2 still has X, the
playbook will flag it again — that's correct, it's what we want. The
iteration count is tracked by main agent, not by the playbooks.

### Rule 4: Merge does not second-guess playbooks

Merge Agent's job is synthesis, not re-evaluation. If a playbook says
"blocking", merge preserves that. Merge can CONSOLIDATE similar issues
from multiple playbooks, but it cannot downgrade severity or dismiss
issues.

### Rule 5: Playbooks operate only within their declared scope

A playbook has a scope (files, specs). It reads within that scope. It does
not read other playbooks' scopes, does not read the full project, does not
explore beyond what was given. This keeps playbook results predictable
and parallelizable.

---

## Relationship to Feature Room's commit-sync

Feature Room's `commit-sync` skill contained several review-like checks
inline:

- Phase 2: Anchor tracking (what anchors need updating)
- Phase 3: Draft-to-active detection
- Phase 4: Cross-room conflict detection (via contract anchors)

In AI-Robin, these checks are distributed:

- **Anchor tracking** — done by Execute Agent during Phase 4, validated by
  `spec-anchors` playbook
- **Draft-to-active detection** — not applicable in AI-Robin (all sub-agents
  promote specs to active before returning; agent_proxy decisions are also
  active, tracked for audit via signal payloads and ledger rather than via
  draft state)
- **Cross-room conflict detection** — done by Review-Plan (which looks at
  the full batch) and validated by `backend-api` / `db-schema` playbooks
  for the specific conflict patterns

This redistribution is deliberate — in Feature Room, these were bundled
into commit-sync because a human was doing the final review. In AI-Robin,
they belong to the review stage which has time and autonomy to be more
thorough.

---

## Failure modes to watch

| Mode | Symptom | What to do |
|---|---|---|
| Review-Plan dispatches zero playbooks | Empty playbook list in `review_dispatch` | Kernel treats this as anomaly; ensure at least `code-quality` always runs |
| A playbook crashes mid-run | Sub-agent returns malformed signal or timeout | Kernel logs anomaly, treats that playbook as "did not run"; merge proceeds without it with a note |
| Merge finds no common ground | E.g., every playbook said pass, but merge sees conflicts | Merge surfaces the conflict as a cross-playbook observation; overall verdict is the worst sub-verdict |
| Pass review but code doesn't work | Integration test failure in reality vs. playbook checks being too shallow | Long-term: expand playbooks to cover; short-term: known limitation, relies on project-level test convention |
