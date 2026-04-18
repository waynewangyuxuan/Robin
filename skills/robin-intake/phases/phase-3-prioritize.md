# Intake Phase 3: Question prioritization

**Autonomy: guided**

Load `skills/robin-intake/question-prioritization.md` for the full ranking
methodology. This phase applies it to your gap + ambiguity lists.

## Three ranking dimensions

Rank questions by:

1. **Blast radius** — how much of the project downstream depends on this
   decision.
   - Auth provider choice ripples through auth, frontend, backend, DB →
     high blast radius.
   - UI color scheme affects only styling → low blast radius.

2. **Reversibility** — irreversible choices rank higher.
   - Database engine, deploy platform, monorepo vs polyrepo → expensive
     to change later.
   - Styling library, component library → relatively cheap to swap.

3. **Ask-ability** — some gaps are hard to ask without context.
   - "Deployment environment" is ask-able with concrete options.
   - "Preferred error handling philosophy" is hard to get useful
     answer without implementation context.

## Pick the top N

Budget is 15 Q&A turns total (per `budgets.max_qna_turns`), with a target
of 4-8 core questions. Going above 10 typically burns user patience
faster than value gained.

Strategy:
- Top 3-5 questions in Round 1 — highest blast radius + least
  reversibility + clearly ask-able.
- Reserve budget for follow-ups. User's Round 1 answers often generate
  Round 2 questions.
- Leave hard-to-ask items to proxy decisions (Phase 6).

## When the list is long

If you have >10 legitimate must-ask items, you have too many. Two moves:
- **Combine**: some decisions naturally bundle (e.g., "backend framework"
  and "DB ORM" often travel together; ask as one combined question).
- **Downgrade**: some items you thought were must-ask are actually
  proxy-able with a clearly stated default. Move them to the
  proxy-able bucket.

## Output

A prioritized list of questions for Phase 4. Each entry:

- The question text (draft, will refine in Phase 4)
- Which gap(s) or ambiguity(ies) it addresses
- Expected answer shape (yes/no, multiple choice, free-form short)
- What Phase 6-8 will do with each possible answer
