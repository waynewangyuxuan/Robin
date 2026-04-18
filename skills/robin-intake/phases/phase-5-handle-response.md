# Intake Phase 5: Handle the user's responses

**Autonomy: guided**

For each response the user gives:

## Step 1: Parse

Classify what the user said as one of:
- A **decision** (e.g., "use Postgres" → decision spec)
- A **constraint** (e.g., "must work offline" → constraint spec)
- A **context** (e.g., "our team is 2 people" → context spec)
- A **non-answer** (e.g., "I don't know", "you decide") → move the
  pending gap to proxy-able bucket

Write down what spec(s) this response produces. You don't have to write
them to disk yet — that's Phase 8 — but have them ready.

## Step 2: Detect new gaps

User's answer may open new questions. Examples:

- "Use Clerk for auth" → opens: "which Clerk plan / which auth pages /
  OAuth providers?"
- "Deploy to Vercel" → opens: "serverless or edge runtime?"
- "Use Postgres" → if DB schema not covered, may open schema questions

Add new gaps to the gap list. Re-prioritize: is this new gap more
important than remaining planned questions?

## Step 3: Detect ambiguity in the answer

If the answer itself is ambiguous, ask one targeted follow-up. Counts
against budget. Example:

> User: "Keep it simple."
> You: "To be sure I'm simplifying the right thing — do you mean:
> (a) simple architecture (minimal services, few abstractions),
> (b) simple UI (few screens, no fancy interactions),
> (c) simple deployment (one-click, no infra)? All of these, or some
> specific one?"

## Step 4: Loop or exit

- If more must-ask questions remain and budget allows → Phase 4 again
- If all must-ask questions answered → Phase 6
- If budget exhausted → Phase 6 (remaining gaps become proxies)

## When the user goes silent

User-response timing in the chat runtime is not strictly bounded, so do
**not** hard-code a wait duration.

- If the user's previous message clearly indicated they're done ("just
  figure it out", "proceed", no response after a wrap-up prompt from
  you) → treat all remaining gaps as proxy-decidable and move to
  Phase 6.
- If you're unsure whether the user is still engaged → state your plan
  explicitly in your last message ("If no further response, I'll
  proxy-decide the rest and proceed") and then proceed.

If the user's absence leaves you unable to meet minimum coverage (core
must-ask items have no answer), return `intake_blocked` with partial
work saved.

## Calibration

A well-answered 5-question intake takes about 5-10 Q&A turns total
(original 5 + follow-ups + minor ambiguity resolutions).

If you're hitting 12+ turns, you're either:
- Asking poorly-framed questions (user keeps needing clarification)
- Surfacing too many new gaps (not ruthless enough about what's
  must-ask vs proxy-able)

In both cases: stop, accept what you have, proxy the rest.
