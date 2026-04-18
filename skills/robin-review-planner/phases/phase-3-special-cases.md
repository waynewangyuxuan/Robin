# Review-Plan Phase 3: Handle special cases

**Autonomy: guided**

Adjust Phase 2's dispatch list for edge cases.

## Empty batch

If no files changed (Execute produced only spec updates — e.g., anchor
refreshes), dispatch only `spec-anchors` playbook. Skip code-focused
playbooks.

## Known-issues heavy batch

If aggregated `known_issues` count is high (e.g., >5 issues
self-reported by Execute Agents), add an extra scrutiny note in the
rationale:

> "Batch self-reported {N} known issues; reviewers should verify each
> is genuinely deferred per gate or should have been addressed."

Don't add more playbooks; just signal higher scrutiny.

## Partial batch (some tasks failed)

If some `execute_results` were `execute_failed`, those tasks' scope may
have only partial artifacts. Still include them in review scope —
partial artifacts can be diagnosed and may still pass for what was
produced.

Flag in rationale: "Tasks {ids} failed; reviewers should note their
partial state."

## Cross-cutting mechanical changes

If a single change touches many files across many domains (e.g., a
project-wide rename, a dependency version bump applied everywhere),
consider a narrower focus:

- Include: `code-quality`, `spec-anchors`
- Skip: domain-specific playbooks

Rationale: mechanical changes don't need domain review — they're
syntactic, and the checkers that matter are the global ones.

## Review iteration context

If this is `review_iteration: 2` (retry after first failure), consider
narrowing scope to only the issue areas flagged in the previous
merged verdict. Don't re-review areas that already passed on
iteration 1.

Include in rationale: "Iteration 2 review narrowed to {areas} flagged
in iteration 1's verdict; other areas considered stable from prior
pass."

## Output

Final adjusted playbook list. Feeds Phase 4 (sanity + emit).
