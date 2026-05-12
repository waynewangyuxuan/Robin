# Intake Phase 0: Pre-flight (mode + META detection)

**Autonomy: explicit** (mode requires user confirmation or explicit flag)

This phase runs before any user Q&A. It establishes which intake mode
applies and ensures the project's META/ precondition is met. See
decision-intake-mode-taxonomy-001 and decision-intake-meta-detection-001.

## Inputs to this phase

From the kernel's spawn payload:
- `mode` — one of `new_project` / `incremental_feature` / `bug_fix` /
  `pr_continuation` / `auto-detect`
- `project_root` — absolute path
- `user_raw_input` — the user's brief
- (mode-specific) `pr_ref` — PR URL or number, required when
  `mode == pr_continuation`

## Step 1: Resolve mode

```
if mode == "auto-detect":
    if META/ exists AND META/00-project-room/ exists:
        resolved_mode = "incremental_feature"
    else:
        resolved_mode = "new_project"
    propose_to_user(resolved_mode)
    # user may confirm, or switch to bug_fix / pr_continuation / new_project
else:
    resolved_mode = mode
```

**Proposing to the user (when auto-detected)**:

```
Detected an existing META/ folder — defaulting to incremental_feature mode.
Confirm, or switch?
  [1] Keep incremental_feature (default)
  [2] new_project (fresh start; this will operate alongside the existing META)
  [3] bug_fix (narrow change; you'll need a repro / failing test)
  [4] pr_continuation (need a PR URL or number)
  [Enter to accept default]
```

If no META detected:

```
No META/ folder found — defaulting to new_project mode. Confirm, or switch?
  [1] Keep new_project (default)
  [2] bug_fix or [3] pr_continuation — both need an existing META; you'll
       need to run /fr-init first if you want these
  [Enter to accept default]
```

If the user picks a mode requiring META and META is missing, fall through
to **Step 2**.

## Step 2: META precondition check

If `resolved_mode in {incremental_feature, bug_fix, pr_continuation}`:

```
if NOT exists(META/00-project-room/):
    prompt user with three options (see below)
```

The prompt (verbatim text to surface):

```
This repo has no META/ folder. {resolved_mode} mode needs an existing
Feature Room to anchor against. Three options:

  1. Run /fr-init to bootstrap META, then re-run /robin-start
  2. Switch to new_project mode (start fresh; this will create META)
  3. Cancel

Which? [1/2/3]
```

Handle response:

| User choice | Action |
|---|---|
| `1` (run /fr-init) | Emit `setup_required` signal — see Step 5 |
| `2` (switch to new_project) | Set `resolved_mode = "new_project"`; continue to Step 3 |
| `3` (cancel) | Emit `intake_aborted` signal — see Step 5 |
| unparseable / silence > 3 turns | Emit `intake_aborted` with `reason: "user_unresponsive_at_setup_prompt"` |

**Edge case — META exists but broken** (referenced rooms missing,
dangling anchors, missing required files):

Run a quick internal sanity scan (read 00-project-room/room.yaml,
verify the listed rooms exist on disk, verify no dangling refs in
`relates_to` fields). If broken:

```
META/ exists but appears broken: {brief reason — e.g., "room 02-api referenced
in 00-project-room/room.yaml but the directory is missing"}.

  1. Run /fr-check to see full diagnostic, then fix manually, then re-run
  2. Switch to new_project mode (existing META stays; new specs go alongside)
  3. Cancel

Which? [1/2/3]
```

Handle response analogously (option 1 = `setup_required`).

## Step 3: Mode-specific arg validation

| Mode | Required extra args | If missing |
|---|---|---|
| `new_project` | none | continue |
| `incremental_feature` | `user_raw_input` non-empty | if empty, ask user for delta description as a normal Phase 4 question |
| `bug_fix` | `user_raw_input` should describe bug + ideally repro | if no repro, defer to Phase 2 gap-analysis to ask for it |
| `pr_continuation` | `pr_ref` (URL or number) | if missing, emit `intake_aborted` with `reason: "pr_continuation_requires_pr_ref"`; instruct user to re-invoke with `--pr <url>` |

## Step 4: Record mode in working state

Stash `resolved_mode` in your phase-1+ context. Every downstream phase
branches on it. The mode is also written verbatim to the final
`intake_complete.payload.mode` field.

## Step 5: Emit early-exit signals (only if Step 2 triggered)

`setup_required` payload:
```json
{
  "missing_precondition": "no_meta_folder" | "no_project_room" | "meta_broken",
  "requested_mode": "{resolved_mode}",
  "user_next_action": "Run /fr-init then re-run /robin-start --mode {resolved_mode}",
  "details": "{specifics — e.g., 'META/00-project-room/ not found at /Users/waynewang/proj/'}"
}
```

`intake_aborted` payload:
```json
{
  "stage_when_aborted": "setup_prompt",
  "reason": "{user's reply or 'user_unresponsive_at_setup_prompt'}"
}
```

Both are terminal — return them via Phase 10's return mechanism. Do NOT
proceed to Phase 1.

## Step 6 (normal path): proceed to Phase 1

If you got here, mode is resolved and META preconditions are met (or
the mode is new_project which doesn't need them). Phase 1 begins.

**Pass-through to Phase 1**: your working context now includes
`mode` as a first-class field. Phase 1 onward MUST branch on it.

## What you absolutely do not do

- **Do not auto-invoke `/fr-init`** or any feature-room plugin skill
  on the user's behalf. Robin and Feature Room are separate plugins
  (see decision-intake-meta-detection-001 — Option C). The user runs
  the next slash command themselves.
- **Do not silently fall back** when a mode's preconditions aren't met.
  Always prompt, even if it costs an extra turn.
- **Do not skip mode confirmation** when `mode == auto-detect`. The
  user may have a different intent than what filesystem state suggests
  (e.g., wants to fix a bug in a repo that has META, not extend it).

## Output of this phase

Either:
- `mode` resolved and stashed, META preconditions verified, ready for Phase 1, OR
- An early-exit signal (`setup_required` / `intake_aborted`) emitted via
  Phase 10's return mechanism.
