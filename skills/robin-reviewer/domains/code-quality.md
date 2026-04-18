# Code Quality Domain Rules

Checklist for the `code-quality` reviewer. Loaded by `robin-reviewer-code-quality` agent wrapper via the generic `robin-reviewer` flow in `skills/robin-reviewer/SKILL.md`.

**Severity default**: `quality`. Most findings are non-blocking warnings encouraging better code. Truly broken code (compile errors, missing implementations) is rare to reach Review and is flagged `blocking`.

This is a **starting rulebook**. Expected to evolve with team norms; sections marked "TODO: user to add" indicate where project-specific rules should be added.

---

## The 8 pillars of code quality

Based on industry-standard code review checklists (Google, Microsoft, OWASP + 2025 consensus). These are starting rules; extend as the project's conventions mature.

### 1. Correctness

**Default severity: blocking** (if provably wrong) or `quality` (if suspicious but not clearly broken)

Check for:

- **Off-by-one errors**: loops using `<` where they should use `<=`, index starting at 1 where 0-based is expected. Especially in pagination, boundary iterations, range slicing.
- **Null / undefined dereference**: accessing a property of a value that could be null/undefined without check. TypeScript strict mode catches many of these; if not using strict mode, flag manually.
- **Returning unvalidated input**: function returns `null` or an empty result on failure; caller doesn't check before using.
- **Misuse of equality**: `==` vs `===` in JS, `is` vs `==` in Python. Usually the wrong one is a bug.
- **Concurrency**: race conditions, check-then-act sequences, locking inconsistencies. Often indicate design issues.
- **Logic inversions**: condition is flipped from intent (`if (!valid)` where `if (valid)` was meant).
- **Dead / unreachable code**: code after `return`/`throw` that can't run.

**Blocking** when: code clearly won't work (compile error, proven-wrong logic against the contract it's supposed to implement).

**Quality** when: suspicious pattern that might be intentional but deserves a second look.

### 2. Readability

**Default severity: quality**

Check for:

- **Unclear naming**: variables like `x`, `tmp`, `data`; functions like `doThing()`. Names should describe purpose.
- **Too-short abbreviations**: `usr`, `mgr`, `ctl` save keystrokes at cognitive cost.
- **Magic numbers**: `setTimeout(callback, 86400000)` — should be `const ONE_DAY_MS = 86400000`.
- **Deep nesting**: 4+ levels of nested if/for suggest early returns or extract function.
- **Long functions**: functions over ~80 lines usually have multiple responsibilities.
- **Complex conditionals**: `if (a && (b || c) && !d && e)` — extract to a named boolean.

Advisory level (not quality): formatting, quote style, etc. — those are formatter's job, not reviewer's.

### 3. Maintainability

**Default severity: quality**

Check for:

- **Copy-paste code**: same logic in multiple places. Suggests extract helper.
- **Unused imports / variables / functions**: dead code is maintenance-only.
- **Deprecated API usage**: if language / framework has marked something deprecated, flag.
- **Commented-out code**: delete it (git history has it); leaving commented code is noise.
- **TODO / FIXME without context**: `// TODO` with no explanation or ticket ref is abandoned work. Acceptable: `// TODO: handle pagination (see contract-api-users-001 §4)`.
- **Inconsistency with surrounding code**: new code uses a different pattern than neighboring code. Either match, or justify.

### 4. Error handling

**Default severity: blocking** (if missing where required) or `quality` (if present but weak)

Check for:

- **Swallowed errors**: `try { ... } catch (e) { }` with no handling. Either handle or rethrow; silently ignoring is a bug.
- **Generic catch**: `catch (Exception e)` or `catch (e: any)` that loses type info. Catch specific errors.
- **Missing input validation**: function accepts input without validating. Especially for:
  - API route handlers (validate request body against contract)
  - Functions receiving user input
- **Missing precondition check**: contract says "caller must be authenticated" but code doesn't check.
- **Stringly-typed errors**: `throw new Error("not found")`. Prefer typed errors (e.g., `throw new NotFoundError(id)`).
- **Returning error codes instead of throwing**: in languages with exceptions, this is unidiomatic.

Blocking when: required error handling per convention spec is missing (e.g., `convention-errors-001` says "all endpoints return typed errors" and an endpoint doesn't).

### 5. Testing

**Default severity: quality** (if tests are weak) or `advisory` (if tests are fine but could be more)

Check for:

- **No tests for new functions**: if the project's convention requires tests (per `convention-*.yaml`), flag missing tests. If no such convention, advisory only.
- **Tests that always pass**: asserting nothing meaningful; assertion that's trivially true.
- **Tests that depend on order or other tests**: should be independent.
- **Over-mocked tests**: so much mocking that the test tests the mocks, not the code.
- **Missing edge case coverage**: happy path tested but no tests for error paths, boundary values, or edge inputs.
- **Flaky-prone patterns**: time-dependent tests, tests using non-deterministic order, tests relying on exact sleep durations.

Advisory level: "you could add more tests" — only flag when a meaningful coverage gap exists.

### 6. Security basics

**Default severity: blocking** for any clear security issue; `quality` for patterns that could lead to security issues

Check for:

- **SQL injection**: string concatenation into SQL. Must use parameterized queries.
- **XSS**: unsafe rendering of user input in HTML. Frontend frameworks usually escape by default; `dangerouslySetInnerHTML` in React is a flag.
- **Hardcoded secrets**: API keys, passwords, tokens in code. Environment variables only.
- **Missing auth check**: endpoints accessible without checking authentication/authorization.
- **Insecure cryptography**: MD5/SHA1 for security (collision attacks), ECB mode, weak PRNG for security tokens.
- **Direct file path from user input**: `fs.readFile(userInput)` → path traversal risk.
- **Logging sensitive data**: passwords, full tokens, PII in logs.
- **Missing rate limiting**: auth endpoints, expensive endpoints, signup — if convention requires rate limiting, check.

Security basics are always `blocking`. Even if the user said "MVP quality", security issues go through to the human verifier.

### 7. Performance awareness

**Default severity: quality** (usually) or `advisory` (often)

Check for:

- **N+1 query pattern**: loop that queries DB per iteration — batch with `IN` or `JOIN`.
- **Loading more than needed**: `SELECT *` when only 2 columns are used.
- **No pagination**: endpoint returning arbitrary-size collections without pagination.
- **Syncronous heavy work on critical path**: blocking I/O where async would be idiomatic.
- **Missing indexes**: if the batch includes migrations, check whether frequently-filtered columns have indexes.
- **Unbounded memory**: reading entire file / whole DB table into memory for processing when streaming works.

For MVP projects, most performance findings are `advisory`. Only flag as `quality` if there's a clear issue (e.g., O(n²) when O(n) is straightforward) or `blocking` if performance is an explicit constraint in a constraint spec.

### 8. Documentation

**Default severity: advisory** (usually) or `quality` (if missing on public API)

Check for:

- **Missing docstrings / comments on complex logic**: non-obvious algorithms, regex patterns, complex business logic benefit from explanation.
- **Missing JSDoc / types on exported APIs**: for libraries or module-boundary code, types and docs matter more.
- **Comments that say what, not why**: `// increment i` is noise. `// skip leap years for this calendar per convention-dates-001` is useful.
- **Stale comments**: comment describing old behavior that's since changed. Delete or update.

Advisory for most internal code. Quality (or blocking) for code crossing a contract boundary where clients need docs.

---

## Project-specific conventions

TODO: user to add project-specific rules learned from gstack / other ecosystems.

Examples of what might go here:

- Team naming conventions (variable casing, file naming)
- Specific patterns required (always use Promise, always use async/await, never use var)
- Internal library usage patterns
- Specific linter rules promoted to blocking

Load `convention-*.yaml` specs from the project's Feature Room at runtime; evaluate them as code-quality rules. If a convention spec mentions a rule not covered by the 8 pillars above, still check it — the convention spec is authoritative for this project.

---

## Metrics (code-quality specific)

For Phase 5 of the generic flow, the code-quality reviewer can include:

```json
{
  "files_analyzed": N,
  "functions_analyzed": N,
  "average_function_length": N,
  "issues_by_category": {
    "correctness": N,
    "readability": N,
    "maintainability": N,
    "error-handling": N,
    "testing": N,
    "security": N,
    "performance": N,
    "documentation": N
  }
}
```
