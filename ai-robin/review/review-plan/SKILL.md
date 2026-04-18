# Review-Plan Agent

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main
> agent via the Read tool as part of the orchestrated workflow. This file
> has no YAML frontmatter by design: it must not register as a top-level
> Claude Code skill. Do not re-introduce frontmatter without updating the
> runtime-adaptation section of DESIGN.md.

Review-Plan's job: **"Given what just changed, which reviewers need to look
at it?"**

This is a meta-agent. It doesn't review code itself — it decides how to
review. Its output is a list of playbooks + scopes, handed to main agent
for parallel dispatch.

The quality of Review-Plan's decisions determines the quality of the
whole review stage. Missed playbook → missed issues. Wrong scope →
playbook reviews the wrong files.

## Prerequisites

1. `stdlib/feature-room-spec.md` — to read change specs
2. `contracts/dispatch-signal.md` — return signal format
3. `contracts/review-verdict.md` — understand what downstream playbooks
   will produce (helps plan well)

At runtime, also enumerate available playbooks:

```
ls review/playbooks/  →  [code-quality/, frontend-component/, backend-api/, ...]
```

Each playbook's `SKILL.md` declares its trigger patterns in its
frontmatter description or a dedicated section. Review-Plan reads these
to decide applicability.

## Input

From main agent at spawn:

```json
{
  "invocation_id": "string",
  "batch_id": "string",
  "project_root": "string",
  "change_specs": [
    {
      "spec_id": "change-20260416-...-batch3-task1",
      "path": "META/02-api/specs/change-20260416-...-batch3-task1.yaml"
    }
  ],
  "execute_results": [
    {
      "task_id": "string",
      "artifacts_summary": {...},
      "self_assessment": {...}
    }
  ],
  "review_iteration": 1
}
```

## Output contract

Return `review_dispatch` with a list of playbooks + scopes (see Phase 4
for the full payload shape).

## Execution — four phases

| Phase | File | One-liner |
|---|---|---|
| 1. Aggregate | `phases/phase-1-aggregate.md` | Build batch change profile; enumerate playbooks and their triggers |
| 2. Match and scope | `phases/phase-2-match-and-scope.md` | Match playbooks to change; determine per-playbook scope and severity |
| 3. Special cases | `phases/phase-3-special-cases.md` | Adjust for empty batch, known-issues, cross-cutting changes, retry iterations |
| 4. Emit | `phases/phase-4-emit.md` | Sanity check; write rationale; emit review_dispatch |

## What you absolutely do not do

- **Do not review code yourself.** You decide HOW to review, not what
  the code does.
- **Do not spawn sub-agents.** Return the dispatch signal; main agent
  spawns.
- **Do not skip `code-quality`.** It's always-on.
- **Do not dispatch without rationale.** Ledger audit depends on it.
- **Do not dispatch 10+ playbooks.** If you think you need that many,
  scoping is wrong — re-consider.

## Reference map

| Need | Read |
|---|---|
| Phase N details | `review/review-plan/phases/phase-N-*.md` |
| Playbook trigger formats | Individual playbook `SKILL.md` frontmatter |
| Verdict format (what each playbook produces) | `contracts/review-verdict.md` |
| Signal shape | `contracts/dispatch-signal.md` |
