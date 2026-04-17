# AI-Robin — Current State Summary

Stages A + B + C complete. All core SKILL files + phase files + depth
methodology files + Research agent + code-quality playbook in place.

## File inventory — 70 files, ~10,800 lines

### Top-level (3 files)
- `DESIGN.md` (432 lines) — full design doc
- `SKILL.md` (230 lines) — main agent kernel
- `SUMMARY.md` (this file)

### Contracts (5 files, 1,436 lines)
- `contracts/dispatch-signal.md` (477 lines) — all signal types
- `contracts/session-ledger.md` (297 lines) — append-only audit log
- `contracts/escalation-notice.md` (251 lines) — degradation report
- `contracts/review-verdict.md` (235 lines) — sub-verdict + merged verdict
- `contracts/stage-state.md` (176 lines) — kernel working memory

### Stdlib (7 files, 1,719 lines)
- `stdlib/feature-room-spec.md` (362 lines)
- `stdlib/degradation-policy.md` (274 lines)
- `stdlib/iteration-budgets.md` (266 lines)
- `stdlib/kernel-discipline.md` (242 lines)
- `stdlib/state-lifecycle.md` (209 lines)
- `stdlib/anchor-tracking.md` (192 lines)
- `stdlib/confidence-scoring.md` (174 lines)

### Consumer (Stage 0) — 14 files
- `SKILL.md` (133 lines) — thin shell
- 10 phase files (30-130 lines each)
- `decision-taxonomy.md` (263 lines) — per-project-type decision points
- `question-prioritization.md` (252 lines) — question ranking methodology
- `completeness-check.md` (232 lines) — pre-return checklist

### Planning (Stage 1) — 13 files
- `SKILL.md` (107 lines) — thin shell
- 9 phase files
- `contract-design.md` (393 lines) — Planning's most important output
- `parallelism-identification.md` (311 lines) — concurrent-safe rules
- `replan-protocol.md` (309 lines) — incremental revision with supersedes

### Execute-Control (Stage 2) — 7 files
- `SKILL.md` (98 lines) — thin shell
- 5 phase files
- `concurrency-rules.md` (290 lines) — parallel/serial decision rules

### Execute (Stage 3) — 8 files
- `SKILL.md` (134 lines) — thin shell
- 5 phase files
- `context-pulling.md` (253 lines) — minimal context loading
- `commit-preparation.md` (322 lines) — change spec + progress update

### Research — 1 file
- `research/SKILL.md` (255 lines) — minimal starter version

### Review (Stage 4) — 11 files
- `review/SKILL.md` (195 lines) — Stage 4 overview
- `review/review-plan/SKILL.md` (99 lines) + 4 phase files
- `review/merge/SKILL.md` (87 lines) + 4 phase files
- `review/playbooks/code-quality/SKILL.md` (402 lines) — always-on playbook

## Architecture at a glance

```
                    Main Agent (Kernel, permanently light)
                              │
       ┌────────┬─────────────┼──────────────┬───────────┐
       ▼        ▼             ▼              ▼           ▼
   Consumer  Planning  Execute-Control  Execute × N   Review Stage
   (human)   (design)  (scheduling)     (coding)       │
                                                       ├─ Review-Plan
                                                       ├─ N playbooks
                                                       │  (currently: code-quality)
                                                       └─ Merge
```

## What's NOT yet written

### Additional review playbooks

Already supported architecturally; each is a separate sub-skill to write:

- `review/playbooks/frontend-component/SKILL.md`
- `review/playbooks/frontend-a11y/SKILL.md`
- `review/playbooks/backend-api/SKILL.md`
- `review/playbooks/db-schema/SKILL.md`
- `review/playbooks/agent-integration/SKILL.md`
- `review/playbooks/test-coverage/SKILL.md`
- `review/playbooks/spec-anchors/SKILL.md`

These are meant to be added gradually, with content drawn from external
skill packages (gstack, etc.) at build-time.

### References directory (doc-only)

- `references/architecture.md` — visual / simplified DESIGN.md
- `references/feature-room-mapping.md` — data compatibility with
  original Feature Room
- `references/skill-extraction-log.md` — which stdlib came from which
  external skill

### Planned enhancements

Not urgent; worth considering after dog-fooding:

- Resume-from-degradation: AI-Robin invoked with specific milestone as
  starting point
- Cross-project learning: shared knowledge across runs (currently each
  run is isolated)
- Richer research playbooks (security research vs perf benchmarking)

## What was fixed during the split

- Proxy decisions: `state: active` (not draft) — tracked via signal +
  ledger instead
- `autonomy-taxonomy.md` reference (non-existent) replaced with
  `confidence-scoring.md` (now written)
- Hardcoded "5 minutes" removed from Consumer; runtime-agnostic
- Style A/B question modes collapsed to single iterative style
- Planning triggers collapsed from 5 to 3 (`initial`/`replan`/
  `sub_planning`); `post_research` folded into `replan` with
  `rework_reason.kind: "research_return"`

## Status by stage of the build plan

- ✅ **Stage A** (骨架): done
- ✅ **Stage B** (5 agent SKILLs as thin shells): done
- ✅ **Stage C** (per-agent stdlib depth): done
- 🔄 **Stage D** (Review playbooks): started with code-quality; other
  playbooks TBD based on actual use
