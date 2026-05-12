# Intake Phase 10: Emit return signal

**Autonomy: explicit**

Produce the `dispatch-signal` return object and write it to
`.ai-robin/dispatch/inbox/`. The signal type depends on which
phase reached terminal state:

- **Phase 9 passed** → `intake_complete`
- **Phase 9 failed irreparably** → `intake_blocked`
- **Phase 0 short-circuited** (META precondition unmet + user chose
  "run /fr-init") → `setup_required` (see Phase 0 Step 5)
- **Phase 0 short-circuited** (user cancelled at setup prompt) OR
  **user explicitly stopped mid-Q&A** → `intake_aborted`

Phase 10 just writes the signal; phases 0 and 9 decide which.

## If Phase 9 passed: `intake_complete`

Payload (see `contracts/dispatch-signal.md` for exact schema):

```json
{
  "mode": "string — resolved mode from Phase 0 (one of new_project / incremental_feature / bug_fix / pr_continuation)",
  "pr_ref": "string | null — non-null iff mode == 'pr_continuation' (URL or repo#number); null otherwise",
  "project_root": "string — absolute path",
  "rooms_created": ["string — list of room ids you created (new_project) OR updated (other modes)"],
  "rooms_referenced": ["string — for non-new_project modes, pre-existing room ids that new specs reference via relations.extends; empty list for new_project"],
  "specs_count": {
    "intent": N,
    "constraint": N,
    "context": N,
    "convention": N,
    "decision": N
  },
  "agent_proxy_decisions": [
    {
      "decision_spec_id": "decision-{scope}-{NNN}",
      "reason": "one-line summary of what was filled and why"
    }
    // ... one entry PER proxy decision, no exceptions
  ],
  "unresolved_but_deferred": [
    "string — things you consciously deferred to Planning, e.g.,
    'API endpoint shapes deferred to Planning; user specified data model
     but not API shape.'"
  ]
}
```

## Critical: `agent_proxy_decisions` is complete

Every spec with `provenance.source_type: agent_proxy` MUST appear in
`agent_proxy_decisions`. This is the audit channel — if a proxy
decision isn't listed here, the human verifier has no way to find and
audit it.

Self-check:
```
count(specs where provenance.source_type == agent_proxy)
   == length(agent_proxy_decisions)
```

If not, fix before emitting.

## `unresolved_but_deferred` semantics

This is different from `agent_proxy_decisions`:

- **agent_proxy_decisions**: I decided this myself. Listed for audit.
- **unresolved_but_deferred**: I did NOT decide this. I left it for
  Planning. Listed so Planning knows to handle.

Typical deferrals:
- "Specific API endpoint design — user specified what the app does
  but not the API surface. Planning will design."
- "Database schema details (tables, relationships, indices) — user
  specified the data model conceptually but not schema. Planning will
  design."

## Send a final summary to the user

Before emitting the signal, send a human-facing summary:

> "Intake complete. Summary:
> - {N} top-level goals recorded
> - {M} constraints captured
> - {K} decisions made on your behalf (see ESCALATIONS.md at end of
>   run if you want to review them)
> - Rooms created: [list]
>
> Handing off to Planning now. AI-Robin will run autonomously until
> delivery. Expected wall-clock: roughly {estimate based on scope}.
> You'll see a summary and any ESCALATIONS when it finishes."

Only after this summary do you write the signal to inbox. The summary
is your last communication — user knows the framework is now running
without them.

## If Phase 9 failed irreparably: `intake_blocked`

Payload:

```json
{
  "reason": "'user_unresponsive' | 'input_fundamentally_incomplete' |
              'conflicting_requirements'",
  "details": "string — what blocked completion",
  "partial_spec_path": "string — where partial work was saved"
}
```

Before emitting `intake_blocked`:

- Save whatever specs you did manage to write (partial Feature Room
  structure)
- Send the user an honest summary:

> "I wasn't able to complete intake because {reason}. Here's what I
> did gather: {summary}. Partial work saved at {path}. To resume,
> {concrete next step the user can take — add more input and
> re-invoke, or clarify the specific blocker}."

`intake_blocked` ends the run without downstream work. Be sure
before emitting. Use this only when Intake itself gave up — if the
user explicitly cancelled, emit `intake_aborted` instead.

## If Phase 0 emitted early-exit: `setup_required` or `intake_aborted`

These are short-circuits — Phase 1-9 never ran. Phase 0 hands you the
payload it composed and you write the signal file. Templates:

`setup_required`:

```json
{
  "missing_precondition": "'no_meta_folder' | 'no_project_room' | 'meta_broken'",
  "requested_mode": "string — the mode the user wanted (one of new_project / incremental_feature / bug_fix / pr_continuation)",
  "user_next_action": "string — exactly what to run next, e.g., 'Run /fr-init then re-run /robin-start --mode incremental_feature'",
  "details": "string — what was missing or broken"
}
```

Send the user:

> "Setup needed before Robin can run in {mode} mode: {details}. Next:
> {user_next_action}. Once done, re-invoke /robin-start."

`intake_aborted`:

```json
{
  "stage_when_aborted": "'setup_prompt' | 'mode_questions' | 'spec_review'",
  "reason": "string — verbatim user reply if available, or 'user_unresponsive_at_X' / 'user_cancelled_at_X'"
}
```

Send the user:

> "Intake cancelled at {stage}. Nothing was committed downstream. To
> restart, /robin-start again."

Both are terminal; the kernel does not dispatch anything further. See
the `setup_required` and `intake_aborted` rows in
`skills/robin-kernel/SKILL.md` routing table for kernel-side handling.

## Signal file format

Write to `.ai-robin/dispatch/inbox/{signal_id}.json`.

`signal_id` format: `intake-consumer-{YYYYMMDDTHHMMSS}-{8-char-hex}`

The top-level signal object wraps your payload — see
`contracts/dispatch-signal.md` for the full schema including
`produced_by`, `budget_consumed`, `artifacts`, `self_check`.

## After emitting

Your work is done. The main agent picks up the signal on its next turn.
Do not output anything else. The sub-agent invocation terminates after
writing the signal file.
