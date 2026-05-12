---
description: Resume an interrupted AI-Robin run, or resolve a paused milestone checkpoint
---

You are resuming an AI-Robin run. There are two distinct shapes of resume:

**A. Interrupted resume** — the previous run was killed mid-loop (process died, session ended, etc.). No verb needed; the kernel replays from `stage-state.json`.

**B. Pause-checkpoint resume** — the previous run reached a milestone with `human_checkpoint: true` and is now in `paused_for_human` state, awaiting your decision. Requires one of three verbs (Axis 2 — see decision-kernel-pause-checkpoint-001).

**Pre-flight check:**
1. If `.ai-robin/stage-state.json` does not exist: STOP. Tell the user there's no run to resume; suggest `/robin-start` instead.

**Argument parsing:**

`$ARGUMENTS` may be empty (shape A) or contain exactly one verb (shape B):

- `--ack` — acknowledge the pause; continue to the next planned routing
- `--abort` — stop the run; remaining milestones marked not_built; spawn Finalizer for a partial delivery bundle
- `--replan` — re-spawn Planner with current state as context (use this if reviewing the just-built milestone changed your mind about what should come next)

Optionally, any free-text after the verb becomes a note appended to the resume's ledger entry (for `--replan`, this note is also passed to Planner as the user's reasoning).

**Verb requirements vs. stage:**

| `current_stage` (from stage-state) | Allowed args |
|---|---|
| `paused_for_human` | One of `--ack` / `--abort` / `--replan` REQUIRED; no verb → STOP and tell the user the run is paused, list the three verbs, point at the PAUSED-{milestone_id}.md artifact |
| any other (interrupted) | No verb expected; ignore any verb passed |

**If the check and arg parsing pass:**

Load `skills/robin-kernel/SKILL.md` and follow its resume protocol from the "Initialization: the first turn" section:

- If `current_stage == "paused_for_human"`: do NOT auto-resume the dispatch loop. Apply the verb per the "Pause resume protocol" table in `skills/robin-kernel/discipline.md`.
- Otherwise: read stage-state, identify where the run was when it stopped, handle any active invocations, and continue the dispatch loop.

**User's resume args (raw $ARGUMENTS):** $ARGUMENTS
