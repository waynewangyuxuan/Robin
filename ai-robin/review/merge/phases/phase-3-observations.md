# Merge Phase 3: Cross-playbook observations

**Autonomy: autonomous**

Look for patterns visible ONLY across playbook boundaries. These are
not issues (no severity, no suggested action) — they're advisory notes
for the next Planning iteration.

## What to look for

### Hotspot files

Files flagged by multiple playbooks for DIFFERENT reasons suggest
architectural problems.

Example:

> `users.ts` was flagged by 3 playbooks for independent issues (length,
> error handling, testing). This suggests the file has accumulated
> too many responsibilities and should be considered for refactoring
> in the next Planning iteration.

### Consistent findings

The same category of issue flagged across several files suggests a
systemic convention gap.

Example:

> Typed error handling was absent in 4 files flagged by backend-api.
> Consider adding a convention spec for typed errors in the next
> Planning iteration.

### Conflicting findings

Rare but possible — playbook A says "do X", playbook B says "don't do
X". This is a plan-level inconsistency worth flagging.

Example:

> frontend-component says components should use Tailwind classes,
> but code-quality flags some components for "excessive Tailwind
> class composition, consider extracting". Tension between conventions.

## Format

```json
{
  "description": "plain-language observation about a pattern",
  "example": "optional — specific citation or file reference"
}
```

## How many observations

0-5 typically. If you find yourself writing 10+, you're fabricating.

Empty list is fine. Don't force observations when there are no
patterns.

## Distinction from issues

- **Issues**: concrete problems with location, severity, suggested
  action
- **Observations**: higher-level patterns, no severity, no specific
  action — they're for Planning to mull over, not Execute to fix

If something sounds like an issue, it belongs in `consolidated_issues`
(Phase 2), not here.

## Output

`cross_playbook_observations[]` — 0 to 5 entries. Feeds Phase 4
(summary + emit).
