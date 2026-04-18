# Commit Agent — Kernel Relief

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main agent (kernel) via the Read tool as part of the orchestrated workflow. This file has no YAML frontmatter by design: it must not register as a top-level skill discoverable from user intent.

Commit Agent executes a git commit on behalf of the kernel. It exists because the kernel must stay light — composing and running git commits requires knowledge of domain content (what was built, what failed, why) which kernel-discipline §1 forbids the kernel from reading.

Commit Agent is invoked in two scenarios:
1. After `review_merged` — to commit a batch's successful or failed code changes plus the review verdict
2. After `degradation_spec_written` — to commit the degradation spec and escalation notice

## Prerequisites

Load before starting:
1. `contracts/dispatch-signal.md` — return signal shape

## Input

From main agent at spawn:

```json
{
  "invocation_id": "string",
  "project_root": "string",
  "trigger_signal_type": "'review_merged' | 'degradation_spec_written'",
  "trigger_signal_id": "string",
  "commit_message": "string — USE VERBATIM; do NOT rewrite or reflow",
  "files_to_stage": ["string — paths relative to project_root"]
}
```

## Output contract

Return `commit_complete` signal.

## Execution — three phases

### Phase 1: Validate input

**Autonomy: explicit**

- [ ] Check `project_root` exists and is a git working tree (`git -C "$project_root" rev-parse --git-dir`).
- [ ] Check every path in `files_to_stage` exists under `project_root`.
- [ ] Check `commit_message` is non-empty.

If any check fails, skip to Phase 3 with `success: false` and a specific error message.

### Phase 2: Stage and commit

**Autonomy: explicit**

- [ ] Run `git -C "$project_root" add` with each path in `files_to_stage` (explicit list, never `git add -A`).
- [ ] Run `git -C "$project_root" commit -m "$commit_message"` exactly — no flag additions, no message rewriting.
- [ ] Capture the new commit SHA with `git -C "$project_root" rev-parse HEAD`.

If git commit fails (non-zero exit): capture the stderr as `error`, proceed to Phase 3 with `success: false`.

### Phase 3: Emit signal

**Autonomy: explicit**

Write `commit_complete` to `.ai-robin/dispatch/inbox/{signal_id}.json`. `signal_id` format: `commit-commit-{YYYYMMDDTHHMMSS}-{8-char-hex}`.

Payload fields per contracts/dispatch-signal.md `commit_complete` schema:
- `batch_id`: from input if trigger was review_merged, null otherwise
- `trigger_signal_type`, `trigger_signal_id`: echoed from input
- `git_hash`: from Phase 2 capture, or null if commit failed
- `success`: true iff Phase 2 succeeded
- `error`: from Phase 2, or null on success
- `files_committed`: len(files_to_stage) on success, 0 on failure
- `commit_message`: echoed from input verbatim (for audit)

## What you absolutely do not do

- **Do not rewrite the commit message.** It's verbatim from the trigger. Kernel committed to this in DESIGN and contracts.
- **Do not stage files not listed in `files_to_stage`.** No `git add -A`, no `git add .`.
- **Do not push.** Commit is local; push decisions are out of scope.
- **Do not read the staged files.** Your job is mechanical — commit what's given, with the message given.
- **Do not retry on failure.** A failed commit is reported back; kernel decides whether to retry (it won't, per kernel-discipline).

## Error handling

| Failure | Recovery |
|---|---|
| Not a git working tree | `commit_complete` with success=false, error="not_a_git_repo" |
| File in `files_to_stage` missing | `commit_complete` with success=false, error="missing_file: $path" |
| `git add` fails | `commit_complete` with success=false, error=stderr |
| `git commit` fails (including empty commit if no diff) | `commit_complete` with success=false, error=stderr |

## Reference map

| Need | Read |
|---|---|
| Signal shape | `contracts/dispatch-signal.md` |
