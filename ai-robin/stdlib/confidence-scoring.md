# Confidence Scoring

How to assign the `provenance.confidence` value (0.0-1.0) on a spec. Used by
every sub-agent that produces specs (Intake, Planning, Research, Execute).

This module is adapted from Feature Room's random-contexts confidence table
and expanded for AI-Robin's additional source types.

---

## The scale

Confidence is a scalar 0.0-1.0 representing how sure the producing agent is
that the spec's content accurately reflects what the user / project needs.

- **1.0**: Certainty. User stated this directly; or it's a structural fact
  that can't be wrong.
- **0.85-0.95**: High confidence. Direct user statement with minor caveats,
  OR a planning decision with clear justification.
- **0.7-0.85**: Moderate confidence. Derived from user statements via clear
  inference, OR an agent_proxy decision with strong signal in the user's
  input.
- **0.55-0.7**: Lower confidence. Proxy decisions with weak signal; research
  findings that aren't fully conclusive.
- **0.4-0.55**: Low confidence. Best-effort guess in the absence of clear
  signal.
- **Below 0.4**: Spec should typically NOT be persisted. If unavoidable,
  mark it explicitly low in `intent.detail` and consider whether the work
  should be deferred (e.g., `unresolved_but_deferred`).

**Below 0.5 triggers scrutiny.** Sub-agents should think hard before
writing a spec with confidence < 0.5; it's usually a sign that either
research is needed or the thing shouldn't be a spec at all.

---

## By source type

### `user_input`

User said it directly in their input.

| Signal | Confidence |
|---|---|
| Direct, unambiguous statement ("use Postgres") | 1.0 |
| Direct statement with minor hedging ("I think Postgres is fine") | 0.9 |
| Direct answer to a Intake question | 1.0 |
| Quoted from a pasted document | 0.95 |

### `user_implied`

Not said directly; inferred from what the user said.

| Signal | Confidence |
|---|---|
| Implied by an unambiguous larger statement ("Next.js app" → React + JSX) | 0.85 |
| Inferred from multiple consistent hints | 0.75 |
| Inferred from a single indirect hint | 0.65 |

### `agent_proxy` (Intake's proxy decisions)

Intake filled a gap with a defensible default.

| Signal | Confidence |
|---|---|
| Default aligns with clear user context (e.g., user said "web app" → Next.js default) | 0.75 |
| Default is a sensible convention but user gave no direct hint | 0.65 |
| Default is a best guess among multiple equally-plausible options | 0.55 |

### `planning_derived`

Planning Agent's technical decisions.

| Signal | Confidence |
|---|---|
| Choice is essentially forced by constraints | 0.95 |
| Choice is clearly preferred given constraints; alternatives were weaker | 0.85 |
| Reasonable choice among two or three similar options | 0.75 |
| Best-available choice but weak differentiation | 0.65 |

### `research_derived`

Research Agent's findings incorporated into a spec.

| Signal | Confidence |
|---|---|
| Research found authoritative source and clear answer | 0.85 |
| Research found partial consensus (e.g., most sources agree) | 0.7 |
| Research found competing answers; chose best fit | 0.55 |
| Research inconclusive; spec is a best guess | 0.45 |

Specs marked with `research_derived` confidence < 0.5 should typically
not exist — prefer `research_inconclusive` and let requesting stage
decide how to proceed (often: make decision with best_guess, mark
relevant spec as having low confidence).

### `anchor_tracking`

Automatic anchor update after code change.

| Signal | Confidence |
|---|---|
| Structural change (rename, move) tracked deterministically | 1.0 |
| Symbol signature change tracked deterministically | 1.0 |
| Logic change detected but semantic impact uncertain (stale flag) | 0.8 |

### `prd_extraction`, `chat_extraction`

Intake extracting from documents or chat logs.

| Signal | Confidence |
|---|---|
| Clear direct quote from PRD | 0.9 |
| Paraphrased with obvious meaning | 0.8 |
| Extracted from chat with ambiguity | 0.65 |

### `degradation_trigger`

AI-Robin specific — context spec recording a degradation event.

| Signal | Confidence |
|---|---|
| Always 1.0 (the degradation happened; the fact is certain even if the underlying scope wasn't completed) | 1.0 |

---

## How confidence is used

- **Below 0.5 filtering**: some workflows filter out or flag specs with
  confidence < 0.5 before consumption. If you're producing a spec and find
  yourself tempted to set it at 0.5 "to sneak it through", reconsider —
  your instinct is telling you the spec shouldn't be persisted.
- **State-aware context pulling**: Execute Agent's `context-pulling.md`
  may warn when loading a spec with low confidence.
- **Review scrutiny**: Review sub-agents use confidence as a hint — a
  low-confidence spec warrants closer inspection.
- **Audit signal**: human verifier, reading ledger, sees confidence
  values and can quickly spot where the system made weak-signal decisions.

---

## Anti-patterns

- **Default to 1.0** — if you don't think about it, you default high. That's
  a bug. Think about the actual evidence behind the spec.
- **Use confidence to express ambivalence** — confidence measures evidence
  strength, not your personal feeling about the decision. A decision you
  don't love but which follows clear user constraints is still 1.0.
- **Use 0.5 as a catch-all** — 0.5 is a specific threshold ("right at the
  edge of scrutiny"). If you're tempted to pick 0.5, pick 0.55 or 0.45 to
  make the direction explicit.
- **Drift high during planning** — as you make many planning decisions, it's
  easy to start assigning 0.95 everywhere. Recalibrate periodically: if
  every Planning decision is 0.95, you're not distinguishing between solid
  and speculative.

---

## Recording confidence

Every spec's `provenance` block has `confidence`:

```yaml
provenance:
  source_type: planning_derived
  confidence: 0.85
  source_ref: "Planning iter 1 decision; alternatives: Express, Fastify"
  produced_by_agent: "planning"
  produced_at: "2026-04-16T14:30:00Z"
```

Confidence is immutable after write. If later context shows the value
was wrong, the spec is updated with a new `state` (e.g., `stale`,
`superseded`) rather than editing confidence in place.
