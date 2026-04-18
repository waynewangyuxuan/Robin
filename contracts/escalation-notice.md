# Escalation Notice

A markdown document included in the final delivery bundle that lists every
scope that was degraded during the run. This is the **only** communication
channel from AI-Robin to the human verifier about unresolved problems.

**Written to**: `{project_root}/.ai-robin/escalation-notice.md`
**Also copied to**: `{project_root}/ESCALATIONS.md` in the delivery bundle, so
it's prominent at the project root for the human to notice immediately.

**Written by**: main agent, appending one section per degradation event.
If no degradations occurred, the file is still created but states "No
escalations — run completed without degrading any scope."

---

## Purpose

The human verifier, when opening the delivered project, needs to answer:

- Did anything go wrong I should look at?
- What was the problem?
- What did AI-Robin try?
- What's the current state — partial work, backed out, placeholder?
- What would it take to resolve?

The escalation notice answers all five questions per degradation, in plain
prose.

---

## Structure

```markdown
# AI-Robin Escalation Notice

Run ID: {run_id}
Project: {project_name}
Run completed: {timestamp}
Degradations: {count}

{If count > 0:}

## Summary

{one-paragraph plain-language overview: what's generally working, what's not,
severity assessment. Example: "The backend and database layers completed
without degradation. Two scopes in the frontend layer required degradation
due to ambiguous requirements that could not be resolved within replan budget.
The project is deliverable but needs human attention on the two items below
before user-facing release."}

## Degradations

### 1. {scope name — e.g. "Frontend: Authentication UI"}

**What was being attempted**
{The original milestone or task description, quoting the relevant spec.}

**Why it degraded**
{Plain-language reason. One of:
 - "Review rejected 2 iterations of implementation; 3rd iteration blocked by
   circular dependency in contract spec."
 - "Research agent could not confidently resolve the question ... after 2
   levels of sub-research."
 - "Required library X was discovered to be deprecated; no equivalent was
   specified in the intake."
 - ...}

**What was tried**
{Bullet list of the attempts, in order. Reference ledger entry_ids so verifier
can dig in.}
- Attempt 1 (entry #34): {summary}
- Attempt 2 (entry #41): {summary}
- Replan attempt (entry #48): {summary}

**Current state**
{Exactly what exists on disk now. One of:
 - "No code produced; spec written but implementation blocked."
 - "Partial implementation in {file paths}; does not pass review."
 - "Stub/placeholder code in {file paths}; structurally correct but not
   functional."
 - "Original code intact from before this scope was attempted; no changes
   committed."}

**Suggested resolution**
{Concrete advice for the human. Examples:
 - "Clarify which auth provider is intended (Clerk vs NextAuth vs custom) and
   re-run AI-Robin with updated intake."
 - "Manual implementation needed — the problem requires product judgment that
   couldn't be proxied."
 - "Library Y is a drop-in replacement for the deprecated X; adding that
   choice to the intake and re-running should resolve."}

**Affected files / specs**
- `{file path}` or `{spec_id}`
- ...

**Ledger references**
- Entry #{N}: degradation_triggered
- Entry #{M}: last budget_exhausted
- Entry range #{A}-#{B}: the attempts

---

### 2. {next scope name}

{same structure}

---

{End of degradations}

## Appendix: How to read this

- Every degradation above corresponds to a `degradation_triggered` entry in
  `.ai-robin/ledger.jsonl`. Use the referenced entry_ids to trace the full
  decision path.
- Specs marked `state: degraded` in the project's Feature Room correspond to
  the scopes above.
- If you want to re-run AI-Robin on a specific degraded scope after
  addressing its cause, you can invoke the framework with the scope's
  milestone_id as the starting point (rather than running from scratch).
```

---

## Rules

1. **Every degraded scope gets one section.** No combining multiple degradations
   into one section, even if they seem related. Each is a distinct decision
   trail.

2. **Write for a human who wasn't there.** The verifier did not observe the run.
   Assume they have access to the ledger and filesystem, but no context. Be
   explicit.

3. **Do not blame or excuse.** The notice reports facts. "Review failed twice"
   not "The code agent didn't understand the requirements". Interpretive
   editorializing belongs in `suggested_resolution` only.

4. **Cite specifics.** File paths, spec_ids, ledger entry_ids. The verifier
   should be able to jump directly from the notice to the evidence.

5. **Current state must be actually true.** Main agent, before writing a "current
   state" field, reads the filesystem to confirm. "No code produced" when
   there's partial code on disk is a lie that breaks trust.

---

## When escalation-notice is written

- **Initialized** at the start of every run with a header and "Degradations: 0".
- **Appended to** each time `degradation_triggered` is logged to ledger, adding
  one section.
- **Finalized** at `run_end`, which updates the header count, writes the summary
  paragraph, and ensures the appendix is present.
- **Copied** to `{project_root}/ESCALATIONS.md` at `run_end` so the human sees
  it prominently.

If no degradations occurred, the file still exists with a brief "no
escalations" message, so the verifier knows to expect it (and knows its
absence would mean something went wrong with AI-Robin itself).

---

## Example

```markdown
# AI-Robin Escalation Notice

Run ID: run-20260416-my-app-7f3a
Project: my-app (Expense Tracker)
Run completed: 2026-04-16T16:42:11Z
Degradations: 1

## Summary

Backend, database, and most of the frontend completed without degradation. One
scope in the authentication layer required degradation because the intake did
not specify which auth provider to use, and Research Agent could not determine
a sensible default within budget (two candidates had roughly equal fit). The
project runs locally and passes all non-auth tests. The auth flow exists as a
stubbed placeholder that accepts any login; this must be addressed before
deployment.

## Degradations

### 1. Auth: Provider Selection and Integration

**What was being attempted**
Milestone `m3-auth` required implementing a full authentication flow with
signup, login, and session management. From intent-auth-001: "Users must be
able to sign up with email/password and log in to view their own expense
data."

**Why it degraded**
The intake did not specify an auth provider. Planning Agent spawned a
Research Agent to determine a sensible default. Research compared Clerk,
NextAuth.js, and Lucia, and concluded that all three were viable — the
choice depends on deployment context (serverless vs long-running) and
compliance needs, neither of which were in the spec. Research returned
`research_inconclusive`. Planning then attempted to make a default choice
(NextAuth.js) and proceed, but Review rejected both implementation
iterations due to missing configuration details that only the user can
provide (OAuth app credentials, session secret, database adapter choice).

**What was tried**
- Attempt 1 (entry #62): Research Agent spawned to determine auth provider.
  Returned inconclusive.
- Attempt 2 (entry #71): Planning proceeded with NextAuth.js default. Execute
  Agent implemented basic flow. Review failed: missing environment
  configuration, unclear session storage decision.
- Attempt 3 (entry #84): Replan attempted to use a simpler JWT-only flow.
  Execute implemented. Review failed: insecure defaults, no password reset
  flow which was implied by intake.
- Degradation triggered at entry #91 when review budget exhausted for this
  milestone.

**Current state**
Stub auth implementation in `apps/web/src/lib/auth.ts` and
`apps/web/src/app/api/auth/route.ts`. It accepts any email/password
combination and creates a session, so the rest of the app can be tested, but
it is insecure and not production-ready. The rest of the app's auth-dependent
flows (expense creation, dashboard) do work against this stub.

**Suggested resolution**
Decide on an auth provider — the main question is serverless vs long-running
deployment. If deploying to Vercel/Netlify → Clerk or NextAuth with a JWT
strategy. If deploying to a persistent server → NextAuth with a database
adapter, or Lucia. Once chosen, re-run AI-Robin with the updated intake
specifying the provider and deployment context; the framework can pick up at
the auth milestone.

**Affected files / specs**
- `apps/web/src/lib/auth.ts`
- `apps/web/src/app/api/auth/route.ts`
- `contract-auth-001` (state: degraded)
- `decision-auth-provider-001` (state: degraded)
- `context-degraded-auth-001`

**Ledger references**
- Entry #62: research_complete (inconclusive)
- Entry #71, #78: commit entries for attempts 1 and 2
- Entry #84: replan triggered
- Entry #91: degradation_triggered

## Appendix: How to read this

[standard appendix]
```
