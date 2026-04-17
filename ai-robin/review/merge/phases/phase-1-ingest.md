# Merge Phase 1: Ingest sub-verdicts and compute overall status

**Autonomy: explicit**

Load all sub-verdicts and compute the mechanical part of the merge.

## Ingest

Load each sub-verdict from the input. Normalize:

- Every sub-verdict should have `status`, `issues[]`, `playbook_name`,
  `scope_reviewed`
- If any sub-verdict is malformed (missing required fields), record
  it in `cross_playbook_observations` as "Playbook X returned
  malformed verdict; excluded from merge." Then proceed with the
  remaining.

## Compute overall status

Mechanical computation — no judgment:

- If **any** sub-verdict has `status: "fail"` → overall `fail`
- Else if **any** has `status: "pass_with_warnings"` → overall
  `pass_with_warnings`
- Else (all `pass`) → overall `pass`

Enum ordering: `pass < pass_with_warnings < fail`. Take the max.

## Catalog all issues

Collect every issue from every sub-verdict into a flat working list,
preserving for each:

- Source playbook name
- Original issue_id within that playbook
- Severity
- Location
- Description
- Rationale
- Suggested action

Do NOT yet assign new merged issue_ids — that happens in Phase 2 after
consolidation.

## Output

- `overall_status` value
- Flat catalog of all issues across playbooks

Feeds Phase 2 (consolidation).
