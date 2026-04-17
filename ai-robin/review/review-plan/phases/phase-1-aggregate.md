# Review-Plan Phase 1: Aggregate change and enumerate playbooks

**Autonomy: explicit**

Two parallel data-gathering tasks.

## Aggregate the batch's changes

Build a combined picture across all tasks in the batch:

- **All files touched**: union of `files_created` + `files_modified`
  across all tasks
- **All specs touched**: union of `specs_created` + `specs_updated`
- **File type distribution**: what languages, frameworks, file
  categories appear (e.g., "3 `.ts` API routes + 1 `.sql` migration +
  2 `.tsx` frontend components")
- **Known issues self-reported**: aggregate `self_assessment.
  known_issues` from all tasks. These hint at what to scrutinize.
- **Failed tasks**: any `execute_failed` results? Note them — their
  partial artifacts still need review.

## Enumerate available playbooks

Read `review/playbooks/` directory. For each subdirectory, load its
`SKILL.md` frontmatter to get:

- `name`
- `description` (which typically states trigger conditions)
- Any declared triggers in the skill body

Build a list of `(playbook_name, trigger_conditions, typical_severity)`.

## Output

- Batch change profile (files, specs, types, known issues)
- Full list of available playbooks with their triggers

Feeds Phase 2 (matching).
