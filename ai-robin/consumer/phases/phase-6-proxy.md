# Consumer Phase 6: Proxy decisions

**Autonomy: autonomous**

For every decision point classified as "proxy-able with a reasonable
default" in Phase 2 (plus any gaps deferred here from Phases 4/5), make
the decision yourself and record it as a spec.

## The spec

Write a `decision-*.yaml` spec with:

- `state: active` (you're committing to this decision; downstream
  treats it as authoritative)
- `provenance.source_type: agent_proxy`
- `provenance.confidence`: typically 0.6-0.8 (you're defaulting, not
  inferring from user)

## The "Agent proxy note"

The `intent.detail` field must include a clearly-labeled section:

```markdown
**Agent proxy note**:
- Gap filled: {what was missing from user input}
- Chosen default: {what was decided}
- Reasoning: {why this default makes sense for the project type + user's
  other signals}
- Hint from user input: {what in user_raw_input pointed toward this
  default, or "none explicit"}
- What would have changed this: {concrete user statement that would have
  selected something else}
```

This note is what the human verifier reads at final delivery to audit
your decisions. Make it specific enough that they can judge without
reading the whole Feature Room.

## How to pick defaults

Load `consumer/decision-taxonomy.md` — it lists sensible defaults per
project type for each decision point. Use those unless the user's
other input points elsewhere.

General principles for picking:
- **Modern conventions** over legacy. (E.g., TypeScript over plain JS
  for new web apps.)
- **Productivity** over "more control". (The user didn't ask for
  control; they asked for a working project.)
- **Free/cheap hosting** unless user signaled budget for paid.
- **Ecosystem defaults** (what most people pick for this stack) unless
  user signaled specific expertise elsewhere.

## Tracking for the return signal

Every proxy decision gets added to a running list you'll include in the
`intake_complete` signal's `agent_proxy_decisions` field. Format:

```json
{
  "decision_spec_id": "decision-{scope}-{NNN}",
  "reason": "one-line summary of what was filled and why"
}
```

## When to NOT proxy (and return intake_blocked instead)

If a gap cannot be proxy-decided (no defensible default exists, and the
user didn't answer despite being asked), you can't fudge it. Return
`intake_blocked` at Phase 10 with this gap in the reason. Examples:

- User wants something that's technically infeasible and didn't clarify
  priorities
- User's constraints are mutually exclusive and they didn't pick
- Project type is fundamentally ambiguous and user didn't clarify

These are rare. Proxy aggressively for typical cases.
