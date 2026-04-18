---
name: robin-reviewer
description: AI-Robin generic reviewer skill. The shared review flow used by all domain-specific reviewer agents (robin-reviewer-code-quality, robin-reviewer-frontend-a11y, etc.). Defines how to load scope, walk a domain checklist, and emit a structured verdict. Domain-specific checklists live in `domains/{domain}.md`.
---

# Robin Reviewer — Generic Flow

This is the shared reviewer skill loaded by every `robin-reviewer-{domain}` agent wrapper. Each wrapper tells you which domain you're reviewing; you follow the flow below and consult `skills/robin-reviewer/domains/{domain}.md` for the domain-specific checklist.

This file is **domain-agnostic**. The "what to look for" lives in the domain file.

---

## Trigger

Review-Planner dispatches a `robin-reviewer-{domain}` agent when the domain applies to a batch's changes. `code-quality` is always dispatched; other domains are dispatched based on file patterns / change character (see `skills/robin-review-planner/SKILL.md` for dispatch rules).

---

## Prerequisites

1. `contracts/review-verdict.md` — verdict format (Part 1: Sub-Verdict)
2. `contracts/dispatch-signal.md` — return signal format
3. `skills/robin-reviewer/domains/{your-domain}.md` — checklist for this invocation's domain (the wrapper tells you which domain you are)

---

## Input

From main agent at spawn:

```json
{
  "invocation_id": "string",
  "batch_id": "string",
  "playbook_name": "string — e.g. 'code-quality', 'frontend-a11y'",
  "scope": {
    "files": ["string — paths in working tree to review"],
    "specs": ["string — spec_ids to inspect"]
  },
  "severity_focus": "'blocking' | 'quality' | 'advisory'",
  "project_root": "string"
}
```

---

## Output contract

Return a `review_sub_verdict` signal with the verdict per `contracts/review-verdict.md` Part 1.

---

## Execution

### Phase 1: Load scope

Read all files listed in `scope.files`. Load all specs in `scope.specs`.

Skip files that can't be read (mark in `scope_reviewed.skipped` with reason).

### Phase 2: Walk the domain checklist

Load `skills/robin-reviewer/domains/{playbook_name}.md` and apply each section to the loaded files.

For each finding, create an entry in the `issues[]` list of your verdict with:

- `severity` — per each section's default in the domain file (blocking / quality / advisory)
- `category` — one of the section names from the domain file
- `location` — file + line_start + line_end
- `description` — what's wrong
- `rationale` — which rule was violated + brief why; cite the domain section (e.g. "§2 readability")
- `suggested_action` — concrete fix

### Phase 3: Compute status

- Any `blocking` issues → `status: fail`
- Any `quality` issues (no blocking) → `status: pass_with_warnings`
- All clean → `status: pass`

### Phase 4: Write summary

One paragraph assessing the overall health of the reviewed code **through your domain's lens**.

### Phase 5: Compute metrics (optional)

Include `playbook_specific_metrics` if useful. Shape depends on domain; see your domain file for suggestions. A common minimum:

```json
{
  "files_analyzed": N,
  "issues_by_category": { "{cat}": N, ... }
}
```

### Phase 6: Emit signal

Write signal to `.ai-robin/dispatch/inbox/{signal_id}.json`.

`signal_id` format: `review-{playbook_name}-{batch_id}-{YYYYMMDDTHHMMSS}-{8-hex}`

---

## Scoring and severity calibration

Over-reporting dilutes signal. Under-reporting misses bugs. Calibration:

- **Typical clean PR**: 0 blocking, 0-3 quality, 0-5 advisory
- **PR with legitimate issues**: 0-1 blocking, 3-8 quality
- **PR with major issues**: 1+ blocking

If you're producing 20+ issues on a normal-size change, you're probably nit-picking — raise the threshold for `quality` and flag only as `advisory` where rule violation is minor.

If you're producing 0 issues on every change, you're probably not looking — review more carefully, or the rulebook is too lax.

---

## Output structure (reminder)

Each issue in the verdict:

```json
{
  "issue_id": "{domain-short}-N",
  "severity": "quality",
  "category": "<from domain checklist>",
  "location": {
    "file": "apps/api/src/routes/users.ts",
    "line_start": 45,
    "line_end": 134,
    "spec_id": null
  },
  "description": "handleCreate is 89 lines long.",
  "rationale": "§2 readability: functions should be under ~80 lines; splits improve testability and comprehension.",
  "suggested_action": "Extract validation into validateCreatePayload(), DB logic into createUserRecord()."
}
```

Always cite the section of the domain checklist in `rationale` so Merge can consolidate and Planner can address properly.

---

## Anti-patterns in reviewer use

- **Running all checks even on trivial changes**: a one-line bugfix PR doesn't need exhaustive analysis. Focus on what's relevant to the change.
- **Flagging things without severity**: every issue has a severity.
- **Citing "best practices" without a specific rule**: rationale must cite a specific rule from the domain checklist. "This could be better" is not a rule.
- **Reviewing the spec instead of the code**: code-focused domains (code-quality, frontend-a11y, backend-api) review code. Spec issues are for `spec-anchors` or other spec-focused playbooks.
- **Duplicating another domain's concerns**: if `backend-api` reviews contract compliance, don't re-flag the same issue under `code-quality`. Stick to your domain.

---

## Handoff to Merge

After emitting, main agent collects this verdict + other playbooks' verdicts, spawns Merger. Merger consolidates same-location same-concern issues. Your `rationale` field citing your domain checklist's sections lets Merger identify which issues come from which reviewer.

---

## Domain files currently available

- `domains/code-quality.md` — the always-on domain (correctness, readability, maintainability, error handling, testing, security basics, performance awareness, documentation)

Future domain files (not yet written; each gets its own agent wrapper when added):

- `domains/frontend-component.md`
- `domains/frontend-a11y.md`
- `domains/backend-api.md`
- `domains/db-schema.md`
- `domains/agent-integration.md`
- `domains/test-coverage.md`
- `domains/spec-anchors.md`
