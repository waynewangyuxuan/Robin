# Intake Phase 1: Ingest and parse

**Autonomy: guided**

Read `user_raw_input` end to end before asking anything. Extract into a
mental model — do not write anything to disk yet.

## Mode-specific additional ingest

The `mode` field (resolved in Phase 0) determines what else you load
alongside the user's raw text. Treat the additional inputs as **frozen
context** — read them, never modify them in this phase.

| Mode | Additional ingest |
|---|---|
| `new_project` | Nothing beyond `user_raw_input`. |
| `incremental_feature` | Load every room's `room.yaml` + `spec.md` + `progress.yaml` from `META/`. Also enumerate `specs/*.yaml` filenames per room (you'll need them in Phase 8 to continue numbering and to find specs to extend). |
| `bug_fix` | Same as `incremental_feature` PLUS any failing-test / error-message / stack-trace content from the user's input. If the user mentions a file or function the bug lives in, locate the relevant room via `_tree.yaml`. |
| `pr_continuation` | Load the PR via `pr_ref` (the kernel provides `pr_url` or `pr_number`). Use the granted Bash tool with `gh` for the data fetch — see commands below. Also load existing META as in `incremental_feature`. |

### `pr_continuation` — concrete Bash commands

Intake's agent definition grants `Bash` for read-only `git` / `gh`
calls (see `agents/robin-intake.md` § Bash scope). Use these for PR
ingest:

```bash
# PR metadata + diff summary + reviews + commits in one JSON blob
gh pr view <pr_ref> --json title,body,state,headRefName,baseRefName,files,reviews,comments,commits

# Full diff (if needed for line-level reasoning beyond file list)
gh pr diff <pr_ref>

# Optional: see what's already committed
git log --oneline origin/<baseRefName>..origin/<headRefName>
```

`<pr_ref>` accepts a URL or a `<number>`. If the kernel passed
`pr_url`, extract the number from the URL or pass the URL directly.

Failure modes:
- `gh` not authenticated → emit `intake_aborted` with
  `reason: "gh_auth_required"` and tell user to run `gh auth login`.
- PR not found → emit `intake_aborted` with `reason: "pr_not_found"`.
- PR is a draft with no diff → continue but flag this as a known limitation
  in `agent_proxy_decisions`.

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
