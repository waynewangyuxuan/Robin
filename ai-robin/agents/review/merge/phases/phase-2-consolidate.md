# Merge Phase 2: Consolidate similar issues

**Autonomy: guided**

Go through the flat catalog from Phase 1 and merge similar issues. This
is where most Merge judgment lives.

## Consolidation test

Two issues are candidates for consolidation if they refer to:

1. **Same location** (same file + same line range, OR same spec_id)
2. **Substantively similar concern** (the descriptions describe the
   same underlying problem, not just coincidentally touching the same
   spot)

Both conditions must hold. Same file + different concern → don't
consolidate.

## Examples

### Should consolidate

- A: code-quality flags `users.ts:45` "function name 'doStuff' not
  descriptive"
- B: backend-api flags `users.ts:45` "handler name 'doStuff' violates
  verb-noun convention"
- **Consolidate.** Same location, same concern (naming), different
  angles.

Merged:

```json
{
  "issue_id": "m-1",
  "severity": "quality",
  "source_playbooks": ["code-quality", "backend-api"],
  "source_issue_ids": ["cq-3", "ba-1"],
  "merged": true,
  "location": {"file": "users.ts", "line_start": 45, "line_end": 45},
  "description": "Function name 'doStuff' is not descriptive and does not follow handler naming convention.",
  "rationale": "code-quality §3.1; backend-api §2.3.",
  "suggested_action": "Rename to 'createUser' or similar verb-based name."
}
```

### Should NOT consolidate

- A: code-quality flags `users.ts:78` "variable name 'x' unhelpful"
- B: backend-api flags `users.ts:78` "SQL injection risk: user input
  concatenated into query"
- **Keep separate.** Same location but completely different concerns.
  Bundling a naming nit with a security bug would lose signal.

### Cross-angle same concern

- A: code-quality flags `users.ts:45` "function too long (89 lines)"
- B: test-coverage flags `users.ts:45` "long function, hard to test"
- **Consolidate.** Different angles on the same concern (excessive
  length).

## Merged issue format

```json
{
  "issue_id": "m-{N}",
  "severity": "...",
  "source_playbooks": ["all playbooks that raised it"],
  "source_issue_ids": ["original ids from each source"],
  "merged": true,
  "location": {...},
  "description": "synthesis of the source descriptions",
  "rationale": "may cite multiple playbook rules",
  "suggested_action": "synthesis"
}
```

## Unmerged issue format

Same structure, but:

- `source_playbooks`: one entry
- `source_issue_ids`: one entry
- `merged: false`
- Everything else copied from source

## Severity rules (strict)

1. **No upgrading severity.** If all source issues are `quality`,
   merged is `quality`, even if you feel it should be blocking.
   Playbooks decide severity; merge preserves it.
2. **No downgrading severity.** Symmetric.
3. **Max when consolidating.** If one source is `quality` and another
   is `blocking` for the same consolidated issue → `blocking`.
4. **`advisory` can co-exist with `quality`.** Consolidation happens
   if concern matches, but result is `quality`, not `advisory`.

## Issue IDs in merged verdict

Assign new `issue_id` starting from `m-1`, monotonically increasing
across all consolidated and unmerged issues. These are local to this
merged verdict, independent of the source sub-verdicts' IDs.

## Output

`consolidated_issues[]` with new merged IDs. Feeds Phase 3
(cross-playbook observations).
