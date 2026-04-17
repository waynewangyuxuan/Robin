# Review-Plan Phase 2: Match playbooks and scope them

**Autonomy: guided**

Decide which playbooks run and what each sees.

## Match playbooks to the batch

For each enumerated playbook, evaluate its trigger conditions against
the batch's change profile.

### Trigger types

- **File pattern triggers**: playbook applies if any changed file
  matches a glob. E.g., `frontend-component` → `**/*.{tsx,jsx,vue,svelte}`.
- **Spec-type triggers**: playbook applies if certain spec types were
  touched. E.g., `spec-anchors` triggers if any change spec references
  anchor updates.
- **Content triggers**: playbook applies based on what's IN the change,
  not just filenames. E.g., `agent-integration` triggers if changed
  code contains prompt strings or tool definitions, regardless of
  filename.
- **Always-on triggers**: playbook always applies. Currently only
  `code-quality` has this.

Produce a shortlist of matched playbooks.

## Scope each playbook

For each matched playbook, determine its scope:

- **`files`**: subset of changed files that fall within this
  playbook's responsibility. Not every changed file — only the
  relevant ones.
- **`specs`**: subset of touched specs this playbook should inspect.
  E.g., `backend-api` sees `contract-*.yaml` for APIs; `code-quality`
  sees everything.

Scoping prevents playbooks from wading through unrelated changes. A
frontend playbook shouldn't try to review a database migration.

### Coverage rule

Every changed file should be in at least one playbook's scope, EXCEPT
files that fall outside every playbook's domain. If any such files
exist, flag them in Phase 4's rationale — they may need a new
playbook added.

## Determine severity focus per playbook

Set `severity_focus`:

- **`blocking`**: this playbook treats its rules as hard gates. Used
  for correctness checks (API correctness, schema integrity, contract
  compliance).
- **`quality`**: rules produce quality issues that warn but don't
  block. Used for style, structure, convention adherence.
- **`advisory`**: rules produce suggestions only. Used for test
  coverage hints, refactoring ideas.

Most playbooks have a natural severity (e.g., `backend-api` is always
`blocking`; `code-quality` is always `quality`). Context can shift —
on a prototype, even `backend-api` might run in `quality` mode,
preferring warnings over hard fails.

**Default**: use each playbook's declared severity. Do not override
unless there's a clear reason from user intent (e.g., a convention
spec explicitly sets "prototype mode").

## Output

A scoped playbook list ready for dispatch. Feeds Phase 3 (special
cases) and Phase 4 (sanity + emit).
