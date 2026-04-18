# Intake Phase 1: Ingest and parse

**Autonomy: guided**

Read `user_raw_input` end to end before asking anything. Extract into a
mental model — do not write anything to disk yet.

## What to extract

1. **Overt intent**: what the user directly stated they want to build. One
   sentence capturing the north star.
2. **Inferred project type**: web app, CLI tool, agent/bot, data pipeline,
   library, mobile app, ML experiment, etc. Cross-check against
   `skills/robin-intake/decision-taxonomy.md` categories — classification determines
   which decision points must be covered in Phase 2.
3. **Constraints user mentioned**: budget, timeline, tech preferences,
   must-use X, must-not-use Y.
4. **Existing context**: mentions of existing repo, existing team
   conventions, existing deployment, prior attempts.
5. **Signals of urgency / thoroughness preference**: "quick prototype" vs
   "production-ready". These later influence how aggressive you are with
   proxy decisions (more thorough → ask more; prototype → proxy more).

## Output of this phase

A mental model with the five above items identified, plus a preliminary
project-type classification. No disk writes. You will revise this model as
Phases 2-5 progress.

## When input is too sparse

If after reading the raw input you cannot even classify the project type
with confidence, your Phase 4 opening question should be about that
("Which of these best describes what you want: web app / CLI / ...").
Don't skip this phase just because input is thin — do the classification,
note the gaps, and carry them into Phase 2.
