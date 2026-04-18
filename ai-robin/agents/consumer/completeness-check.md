# Completeness Check

The last gate before Consumer returns. Used in Phase 9 (Self-Check).

Consumer is the entry point for the entire AI-Robin run. A premature
`intake_complete` with gaps is the single worst Consumer failure mode —
it causes Planning to consume replan budget on gaps Consumer should
have caught, or forces later stages to proxy-decide with less context
than Consumer had.

**Bias toward asking one more question rather than returning early.**

---

## The six core checks

Run each of these. Mark pass / fail. If any fail, fix before returning
(or block if unfixable).

### Check 1: Coverage against decision taxonomy

For the project type you inferred in Phase 1, walk through
`agents/consumer/decision-taxonomy.md`'s must-ask list for that type. For each
item, verify:

- A spec covers the decision, OR
- The decision was explicitly deferred in `unresolved_but_deferred`,
  OR
- A proxy decision spec covers it with an Agent proxy note

Fail if any must-ask item from the taxonomy is unaccounted for.

### Check 2: User-stated constraints captured

Go back to `user_raw_input`. For each explicit constraint the user
stated ("must use X", "no more than Y", "deploy to Z"), verify:

- A `constraint-*.yaml` or `decision-*.yaml` spec captures it
- The spec accurately reflects what the user said
- Nothing was paraphrased into something different

Fail if user said something and you didn't record it.

### Check 3: Agent proxy notes well-formed

For every spec with `provenance.source_type: agent_proxy`:

- `intent.detail` has the five-field Agent proxy note:
  - Gap filled
  - Chosen default
  - Reasoning
  - Hint from user input
  - What would have changed this
- All five fields are filled (not blank, not "N/A" unless truly
  applicable)
- The spec is listed in `intake_complete`'s `agent_proxy_decisions`
  field

Fail if any proxy spec has an incomplete note or is missing from the
signal.

### Check 4: Ambiguities resolved

For every ambiguity identified in Phase 2, verify resolution:

- Asked the user and got an answer, OR
- Proxy-decided with the Agent proxy note explaining the ambiguity
  resolution, OR
- Explicitly deferred in `unresolved_but_deferred` (rare — only if
  Planning can genuinely resolve it)

Fail if any ambiguity is still floating without a path forward.

### Check 5: Room structure sensible

- Not one giant room (if project is multi-feature, decompose to epic
  level at least)
- Not 30 tiny rooms (over-decomposition is Planning's job to extend)
- Each room has the four files: `room.yaml`, `spec.md`, `progress.yaml`,
  `specs/`
- `00-ai-robin-plan/` exists and is empty (Planning's workspace)
- `00-project-room/_tree.yaml` indexes all rooms

Typical target: 1-8 feature rooms + `00-project-room` + `00-ai-robin-plan`.

Fail if structure is badly skewed in either direction or missing
foundational rooms.

### Check 6: The Planning-ready test — THE key test

Simulate: you are Planning Agent, you just got spawned with
`trigger: "initial"`, handed `consumer_output.specs_summary`. Walk
through what Planning does (per `agents/planning/SKILL.md`):

- **Phase 1 (Situate)**: can you read the specs and understand what's
  being asked? Or is anything unclear or internally inconsistent?
- **Phase 2 (Decisions)**: are there too many undecided technical
  choices for Planning to reasonably handle? (A few is fine; 20 is
  too many.)
- **Phase 3 (Modules)**: are the module boundaries implied or
  specifiable from the specs? Or is the intent so vague Planning
  can't even draw boundaries?
- **Phase 4 (Contracts)**: are there enough constraints and intents to
  design contracts? Or would Planning immediately need to ask the
  user?

If any of Planning's phases would be blocked on missing info from
Consumer, that's a failure of Check 6.

Fail if Planning couldn't proceed unambiguously from your output.

---

## If a check fails

Try to fix in order of escalation:

### Level 1: Write missing content

- **Missing spec** → Phase 8 write it (proxy-decide if user wasn't
  asked)
- **Missing proxy note** → Phase 8 add the Agent proxy note
- **Missing room structure element** → Phase 7 create it

### Level 2: Consult user (if budget permits)

- **Unresolved ambiguity with budget left** → go back to Phase 4, ask
  one more targeted question
- **Inconsistency user could clarify** → ask

### Level 3: Proxy-decide and document

- **Unresolved ambiguity without budget** → Phase 6 proxy-decide, full
  note
- **Gap where user didn't answer the ask** → proxy with note

### Level 4: Block

Only after exhausting levels 1-3:

- **Coverage gap where neither user nor defensible default works**
- **Internal contradictions in user input that user won't resolve**
- **Input so sparse that aggressive proxying still doesn't yield
  workable specs**

In these cases, return `intake_blocked` from Phase 10 instead of
`intake_complete`.

---

## Common failure modes to watch for

### "Everything is covered" without actually checking

Don't declare checks pass by assertion. Walk them. Mentally simulate
Planning reading your output. Find the gap before Planning does.

### Proxy-deciding too many things

If you're proxy-deciding 15+ things, you're probably under-asking.
Check: did you use the budget? If interactions were few, that's fine;
if interactions were many and you still have unresolved stuff, asking
more is warranted.

### Proxy note that doesn't actually explain

Bad note:
> "Agent proxy: chose Next.js. Reasoning: Next.js is good."

Good note:
> "Agent proxy note:
>  - Gap filled: frontend framework choice
>  - Chosen default: Next.js 14 with App Router
>  - Reasoning: User said 'web app' (implying full-stack with one codebase).
>    Next.js is the current ecosystem default for this pattern; App Router
>    is the recommended entry point.
>  - Hint from user input: 'web app' phrasing (full-stack, not
>    'frontend+backend separately')
>  - What would have changed this: user saying 'I already know Remix' /
>    'separate frontend + API' / 'Astro for static' / etc."

The human verifier can judge only as well as the note explains.

### Specs with contradictions

If `decision-db-001` says "use Postgres" and `constraint-deploy-001`
says "serverless only, no persistent infra", you have a contradiction
that needs resolving before Planning hits it.

Surface contradictions to the user in Phase 4 if identified mid-intake;
at minimum, flag in `unresolved_but_deferred`.

### Over-broad intents

`intent-core-001: "Build the app"` is not an intent, it's a
placeholder. Intents should be specific enough that Planning can
produce meaningful milestones.

Minimum intent specificity: names a functional capability, not just "the
project". "User can add and view expenses" is intent. "Build a good
app" is not.

---

## What Consumer MUST NOT skip

Even under time pressure, these are non-negotiable:

- **Every proxy decision has a well-formed note.** No shortcuts.
- **The `agent_proxy_decisions` field in the return signal is
  complete.** Every proxy spec listed.
- **Every user statement is captured in at least one spec.** User
  said something; it's in the output.
- **The `00-ai-robin-plan/` room exists.** Planning will fail without
  it.

If any of these can't be done, return `intake_blocked`, don't fake
completeness.

---

## Positive signals of a healthy intake

When these are true, your output is probably solid:

- Most decision-taxonomy items are covered by extracted specs (high
  coverage)
- A modest number of proxies (5-15 typical), each with good notes
- No ambiguities left open
- Rooms are named meaningfully (not "module-1", "module-2")
- Planning-ready test imaginatively passes: you can see Planning
  producing contracts and milestones without needing more from the user
