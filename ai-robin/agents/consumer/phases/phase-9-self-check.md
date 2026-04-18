# Consumer Phase 9: Completeness self-check

**Autonomy: guided**

The final gate before return. If this check fails, fix it — don't just
return and hope.

Load `agents/consumer/completeness-check.md` for the detailed checklist. This
phase applies it.

## The six core checks

1. **Coverage**: for every must-ask decision point in the taxonomy, is
   there a spec covering it?
2. **Constraints captured**: every user-stated constraint has a spec
   recording it?
3. **Proxy notes well-formed**: every `agent_proxy` decision has the
   "Agent proxy note" section with all 5 sub-fields (Gap filled /
   Chosen default / Reasoning / Hint from user / What would have
   changed this)?
4. **Ambiguities resolved**: every ambiguity from Phase 2 has been
   either asked or proxied — none left hanging?
5. **Room structure sensible**: not one giant room, not 30 tiny rooms;
   matches the project's actual structure?
6. **Planning-ready test** — THE key test: if a hypothetical Planning
   Agent read only the specs you wrote, could it produce a plan
   without further clarification from the user?

## How to apply the Planning-ready test

Mentally simulate: you are Planning Agent, you just got spawned with
Consumer's output. Walk through what Planning does (per
`agents/planning/SKILL.md`):

- Phase 1: Understand the input — can you understand it? Is anything
  unclear or internally inconsistent?
- Phase 2: Identify decisions to make — are there too many open
  decisions for Planning to reasonably handle?
- Phase 3: Design contracts — are the module boundaries implied or
  specifiable? Or is the intent so vague Planning can't even draw
  boundaries?

If any step of Planning's job is blocked on missing info from
Consumer, that's a failure of this check.

## If a check fails

Try to fix in order:

1. **Missing spec** → go back to Phase 8, write it. Use proxy decision
   if the gap wasn't user-answered.
2. **Missing or malformed Agent proxy note** → go back to Phase 8,
   fix the note.
3. **Unresolved ambiguity with budget remaining** → go back to Phase 4,
   ask one more question.
4. **Unresolved ambiguity without budget** → go back to Phase 6, make
   a proxy decision and document it.

## When to return `intake_blocked`

Only if you've tried to fix and cannot:

- Coverage gap where neither user answer nor defensible default is
  available
- Internal contradictions in user input that user didn't resolve
- Input fundamentally too sparse to proceed even with aggressive
  proxying ("build me something" with zero signal)

Write a clear description of what couldn't be resolved. Save any
partial work. Then move to Phase 10 to emit `intake_blocked`.

## Bias toward asking

If you're at the borderline — "is this good enough, or should I ask
once more?" — **bias toward asking one more question** (if budget
allows). Your interaction budget is there to be used.

A Consumer that returns `intake_complete` prematurely with gaps is
much more damaging than one that uses 2 extra Q&A rounds.

## Output

A pass/fail on each of the 6 checks. Only if all 6 pass (or the only
failures are genuinely unresolvable) do you advance to Phase 10.
