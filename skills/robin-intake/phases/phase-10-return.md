# Intake Phase 10: Emit return signal

**Autonomy: explicit**

Produce the `dispatch-signal` return object and write it to
`.ai-robin/dispatch/inbox/`.

## If Phase 9 passed: `intake_complete`

Payload (see `contracts/dispatch-signal.md` for exact schema):

```json
{
  "project_root": "string — absolute path",
  "rooms_created": ["string — list of room ids you created"],
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

`intake_blocked` is the only signal that ends the run without any
downstream work. Be sure before emitting.

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
