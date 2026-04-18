# Review-Plan Phase 4: Sanity check and emit

**Autonomy: explicit**

## Sanity check the dispatch

Before emitting:

1. **At least one playbook selected** (minimum: `code-quality`)
2. **No playbook scoped to zero files AND zero specs** — if any, drop it
3. **All changed files in at least one playbook's scope** (or
   justified in rationale for uncovered files)
4. **Total playbook count reasonable** — typically 2-5, rarely >7

If any check fails, go back to Phases 2-3 to fix.

## Write the rationale

The rationale is prose explaining the dispatch decisions. Write for
the ledger — future human audit should understand why this review
strategy was chosen.

### Good rationale

> "Batch touched API route files and DB migrations. Selected:
> code-quality (always-on; quality focus), backend-api (blocking —
> the API contract changes), db-schema (blocking — migration
> integrity), test-coverage (advisory — flagging coverage on new
> endpoints). Skipped frontend playbooks (no frontend files changed).
> Skipped agent-integration (no prompt/tool definitions in change)."

### Bad rationale

> "Selected some playbooks."

The rationale should explain:
- Which playbooks were selected and why they matched
- Which playbooks were explicitly skipped and why
- Any special case handling applied (Phase 3)

## Emit `review_dispatch`

Write the return signal to `.ai-robin/dispatch/inbox/`.

Payload:

```json
{
  "batch_id": "batch-3",
  "playbooks": [
    {
      "playbook_name": "code-quality",
      "scope": {
        "files": ["src/routes/users/create.ts", "src/schemas/user.ts"],
        "specs": ["contract-api-users-001"]
      },
      "severity_focus": "quality"
    },
    {
      "playbook_name": "backend-api",
      "scope": {
        "files": ["src/routes/users/create.ts"],
        "specs": ["contract-api-users-001"]
      },
      "severity_focus": "blocking"
    }
  ],
  "rationale": "string"
}
```

## Playbook trigger examples (reference)

For recognizing patterns:

### Always-on
- `code-quality` — triggers on any batch

### File-pattern triggers
- `frontend-component`: `**/*.{jsx,tsx,vue,svelte}`, `**/components/**`
- `frontend-a11y`: same as frontend-component PLUS presence of ARIA
  attributes, keyboard handlers, or user-facing text
- `backend-api`: API route files (`**/routes/**`, `**/api/**`, files
  defining endpoints)
- `db-schema`: migration files, schema files (`*.sql`, `prisma/*`,
  `migrations/**`)

### Content triggers
- `agent-integration`: prompt strings, tool definitions, LLM SDK calls
- `spec-anchors`: any change spec reporting anchor updates
- `test-coverage`: test file additions or changes

## Signal file format

`signal_id` format: `review-plan-{batch_id}-{YYYYMMDDTHHMMSS}-{8-hex}`

See `contracts/dispatch-signal.md` for full wrapping schema.

## After emitting

Your work is done. Main agent picks up the signal, spawns the N
review sub-agents in parallel per your dispatch, and eventually spawns
Merge. The invocation terminates after writing the signal file.
