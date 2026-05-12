---
description: Start a new AI-Robin run on the current working directory
---

You are about to begin a new AI-Robin run.

**Pre-flight checks:**
1. If `.ai-robin/` already exists in the current working directory: STOP. Tell the user to use `/robin-resume` instead, or to delete `.ai-robin/` if they truly want to start fresh.
2. If the current working directory has uncommitted changes: warn the user; ask for confirmation before proceeding.

**Argument parsing:**

`$ARGUMENTS` may contain (in any order):

- `--mode <new_project|incremental_feature|bug_fix|pr_continuation>` — intake mode (Axis 1). See decision-intake-mode-taxonomy-001 (`META/01-intake/specs/`).
  - **If omitted**: Intake auto-detects between `new_project` and `incremental_feature` ONLY (presence of `META/` → `incremental_feature`; otherwise `new_project`), then asks the user to confirm or override at intake start.
  - **`bug_fix` and `pr_continuation` MUST be passed explicitly** — auto-detect never selects them because both need extra context (bug repro / PR URL) that can't be inferred from filesystem state.
- `--run-mode <autonomous|hybrid|dev>` — kernel run-mode (Axis 2), controls default `human_checkpoint` policy on milestones. See decision-kernel-pause-checkpoint-001 (`META/12-kernel/specs/`). Defaults to `autonomous` if omitted.
- `--pr <url-or-number>` — for `--mode pr_continuation`, the PR to continue. Required in that mode.
- The remaining free-text after flags is the user's **project brief**.

**Mode-specific precondition checks:**

For `--mode` ∈ {`incremental_feature`, `bug_fix`, `pr_continuation`}, Intake additionally requires a healthy `META/` to anchor against. The detection-and-prompt flow lives in Intake itself (see decision-intake-meta-detection-001 — option C: Intake prompts user; kernel does NOT auto-invoke `/fr-init`). On the prompt, the user picks:
1. Run `/fr-init` then re-run `/robin-start` → Intake exits with `setup_required` signal.
2. Switch to `--mode new_project` → Intake continues in new_project mode.
3. Cancel → Intake exits with `intake_aborted` signal.

`setup_required` and `intake_aborted` are terminal — kernel does not dispatch further. See `contracts/dispatch-signal.md`.

**If pre-flight passes:**

Load `skills/robin-kernel/SKILL.md` (the kernel entrypoint) and follow its initialization instructions: create `.ai-robin/` directory structure, initialize `stage-state.json` with `stage: "intake"`, record `mode` and `run_mode` in `stage-state.json` (kernel propagates them downstream — `mode` to Intake/Planner, `run_mode` to Planner's milestone-flag defaults), and spawn Intake Agent with the user's brief as `user_raw_input` and the chosen `mode` (or `auto-detect` if no flag).

**User's input (raw $ARGUMENTS, parse as above):** $ARGUMENTS

If $ARGUMENTS contains no project brief (only flags or empty), ask the user for their brief before initializing.
