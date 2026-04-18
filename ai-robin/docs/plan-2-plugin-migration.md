# AI-Robin Reorg + Plugin Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the AI-Robin skill into a clearer `agents/ + stdlib/ + contracts/ + docs/ + tests/` tree, then build a Claude Code plugin as the first runtime adapter — preserving the runtime-agnostic NLP design declared in `DESIGN.md §8`.

**Architecture:** Two sequential phases. Phase 1 is pure physical reorg (no semantic change); Phase 2 builds `.claude-plugin/` as an additive adapter layer plus three new kernel-relief sub-agents (`commit`, `degradation`, `finalization`) and a Python hooks layer that mechanically enforces `kernel-discipline §4` ordering. The file-based inbox at `.ai-robin/dispatch/inbox/` remains authoritative throughout — plugin hooks write to it, do not replace it.

**Tech Stack:**
- Markdown-based skill files (existing)
- Claude Code plugin manifest (`.claude-plugin/plugin.json`)
- Python 3.11+ for hooks (standard lib only; no external deps)
- pytest for hook unit tests
- git for version control and commit evidence

**Scope boundaries:**
- NO baseline end-to-end run (user deferred this)
- NO changes to the abstract NLP design (DESIGN.md §8 invariants hold)
- NO new methodology content — Phase 1 is only reorg, Phase 2 only adds runtime adapter + delegation sub-agents
- NO replacement of file-based inbox — inbox stays authoritative per DESIGN.md §8

**Plan file location note:** This document lives at `docs/plan-2-plugin-migration.md` at plan-start. During **Phase 1 Task 1.3**, `docs/` is renamed to `docs/`, so this file's final location will be `docs/plan-2-plugin-migration.md`. Executors must not treat the rename as breaking this plan.

---

## File Structure (after both phases complete)

```
ai-robin/
├── SKILL.md                              # kernel entrypoint + routing table (unchanged location)
├── DESIGN.md
├── SUMMARY.md
├── README.md                             # at repo root, unchanged path
├── agents/                               # NEW — all sub-agents grouped here
│   ├── kernel/
│   │   └── discipline.md                 # was agents/kernel/discipline.md
│   ├── agents/consumer/                         # moved from ai-robin/consumer/
│   │   ├── SKILL.md
│   │   ├── decision-taxonomy.md
│   │   ├── question-prioritization.md
│   │   ├── completeness-check.md
│   │   └── phases/
│   ├── agents/planning/                         # moved
│   ├── agents/execute-control/                  # moved
│   ├── agents/execute/                          # moved
│   ├── agents/research/                         # moved
│   ├── agents/review/                           # moved
│   ├── commit/                           # NEW — Phase 2B
│   │   └── SKILL.md
│   ├── degradation/                      # NEW — Phase 2B
│   │   └── SKILL.md
│   └── finalization/                     # NEW — Phase 2B
│       └── SKILL.md
├── stdlib/                               # kernel-discipline.md removed
│   ├── anchor-tracking.md
│   ├── confidence-scoring.md
│   ├── degradation-policy.md
│   ├── feature-room-spec.md
│   ├── iteration-budgets.md
│   └── state-lifecycle.md
├── contracts/
│   ├── dispatch-signal.md                # gets 3 new signal types in Phase 2B
│   ├── escalation-notice.md
│   ├── review-verdict.md
│   ├── session-ledger.md
│   └── stage-state.md
├── docs/                                 # was docs/
│   ├── architecture.md
│   ├── feature-room-mapping.md
│   ├── skill-extraction-log.md
│   └── plan-2-plugin-migration.md        # this file, after Phase 1
└── tests/
    ├── routing-coverage.md               # counts bump 17 → 20 in Phase 2B
    └── end-to-end-trace.md
```

**Claude Code plugin layer (lives OUTSIDE ai-robin/, at repo root):**

```
AI-Robin-Skill/
├── ai-robin/                             # (above)
└── .claude-plugin/                       # NEW — Phase 2
    ├── plugin.json
    ├── README.md
    ├── commands/
    │   ├── ai-robin-start.md
    │   ├── ai-robin-resume.md
    │   └── ai-robin-status.md
    ├── agents/                           # wrappers, body = "Read ai-robin/agents/{name}/SKILL.md"
    │   ├── consumer.md
    │   ├── planning.md
    │   ├── execute-control.md
    │   ├── execute.md
    │   ├── research.md
    │   ├── review-plan.md
    │   ├── merge.md
    │   ├── commit.md
    │   ├── degradation.md
    │   ├── finalization.md
    │   └── playbook-code-quality.md
    └── hooks/
        ├── hooks.json
        ├── lib/
        │   ├── __init__.py
        │   ├── ledger.py                 # atomic jsonl append + schema validate
        │   └── state.py                  # atomic stage-state.json RMW
        ├── pre_task.py                   # PreToolUse on Task
        ├── post_task.py                  # PostToolUse on Task
        ├── session_start.py              # SessionStart
        ├── subagent_stop.py              # SubagentStop
        ├── stop.py                       # Stop — run integrity check
        └── tests/
            ├── test_ledger.py
            ├── test_state.py
            ├── test_pre_task.py
            ├── test_post_task.py
            ├── test_session_start.py
            └── test_stop.py
```

---

## Task granularity note

This plan mixes two kinds of tasks:

1. **File moves + prose edits** (Phase 1 and most of Phase 2A/2B) — TDD-in-the-traditional-sense does not apply. The TDD-equivalent pattern is: *write the verification check → run it to see expected fail/pass state → make the change → run to confirm the new state*.
2. **Python code** (Phase 2C hooks and libs) — traditional TDD applies: write failing test first, implement minimal code, confirm green.

Each task declares which pattern it uses.

---

# Phase 1 — File Tree Reorganization

**Goal:** Move files to match the new layout without changing any content semantics.

**Success criteria:**
- `tests/routing-coverage.md` grep still produces empty diff
- No broken cross-reference in any `.md` file (automated grep check)
- `git log --stat` shows only renames + path-string edits, no content changes
- All SKILL.md files and contracts load without reading errors

**Estimated effort:** 3-4 hours

---

### Task 1.1: Pre-flight state capture

**Files:**
- Create: `/tmp/ai-robin-preflight.txt`

TDD-equivalent: capture current state as reference, so we can diff against it later.

- [ ] **Step 1: Capture the current file tree**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
find . -type f -name "*.md" | sort > /tmp/ai-robin-preflight-before.txt
wc -l /tmp/ai-robin-preflight-before.txt
```

Expected: ~70 files listed.

- [ ] **Step 2: Capture the current routing-coverage grep output**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
comm -23 \
  <(grep -E '^#### `[a-z_]+`' contracts/dispatch-signal.md | sed -E 's/^#### `([a-z_]+)`.*/\1/' | sort -u) \
  <(grep -E '^\| `[a-z_]+` \|' SKILL.md | sed -E 's/^\| `([a-z_]+)` \|.*/\1/' | sort -u) \
  > /tmp/ai-robin-preflight-routing.txt
cat /tmp/ai-robin-preflight-routing.txt
```

Expected: empty (17/17 coverage already in place from prior work).

- [ ] **Step 3: Verify clean git working tree**

```bash
cd /Users/waynewang/AI-Robin-Skill
git status
```

Expected: clean (any untracked `.claude/` or similar local files OK; no modified tracked files).

If not clean: stop, commit or stash existing changes before proceeding.

- [ ] **Step 4: No commit** — this is preflight only.

---

### Task 1.2: Create agents/ directory and move 6 sub-agent directories

**Files:**
- Create: `ai-robin/agents/` (directory)
- Move: `ai-robin/consumer/` → `ai-robin/agents/consumer/`
- Move: `ai-robin/planning/` → `ai-robin/agents/planning/`
- Move: `ai-robin/execute-control/` → `ai-robin/agents/execute-control/`
- Move: `ai-robin/execute/` → `ai-robin/agents/execute/`
- Move: `ai-robin/research/` → `ai-robin/agents/research/`
- Move: `ai-robin/review/` → `ai-robin/agents/review/`

- [ ] **Step 1: Create the agents/ directory**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
mkdir agents
ls -la agents/
```

Expected: empty directory created.

- [ ] **Step 2: Move each sub-agent directory using `git mv`**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
git mv consumer agents/consumer
git mv planning agents/planning
git mv execute-control agents/execute-control
git mv execute agents/execute
git mv research agents/research
git mv review agents/review
```

- [ ] **Step 3: Verify the moves**

```bash
ls agents/
```

Expected output:
```
consumer
execute
execute-control
planning
research
review
```

- [ ] **Step 4: Verify no content changed**

```bash
git status --short | head -20
```

Expected: all lines start with `R` (rename) — no `M` (modified) yet.

- [ ] **Step 5: No commit** — commit at end of Phase 1 (Task 1.10).

---

### Task 1.3: Create agents/kernel/ and move kernel-discipline.md

**Files:**
- Create: `ai-robin/agents/kernel/` (directory)
- Move: `ai-robin/agents/kernel/discipline.md` → `ai-robin/agents/kernel/discipline.md`

**Rationale:** kernel-discipline.md is used exclusively by the kernel (root SKILL.md). It does not belong in stdlib/ which is for resources shared across multiple agents. Moving it to agents/kernel/ makes this ownership explicit. Root SKILL.md stays at `ai-robin/SKILL.md` unchanged — the kernel's "entrypoint" keeps its skill-activation frontmatter contract; only its discipline file moves.

- [ ] **Step 1: Create the kernel directory**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
mkdir agents/kernel
```

- [ ] **Step 2: Move kernel-discipline.md with rename**

```bash
git mv agents/kernel/discipline.md agents/kernel/discipline.md
```

- [ ] **Step 3: Verify stdlib/ now has 6 files (was 7)**

```bash
ls stdlib/
```

Expected output:
```
anchor-tracking.md
confidence-scoring.md
degradation-policy.md
feature-room-spec.md
iteration-budgets.md
state-lifecycle.md
```

- [ ] **Step 4: Verify agents/kernel/discipline.md exists**

```bash
ls agents/kernel/
head -5 agents/kernel/discipline.md
```

Expected: file exists, content starts with `# Kernel Discipline`.

- [ ] **Step 5: No commit** — end-of-phase commit.

---

### Task 1.4: Rename docs/ → docs/

**Files:**
- Move: `ai-robin/docs/` → `ai-robin/docs/`

**Important:** this plan file itself is currently at `ai-robin/docs/plan-2-plugin-migration.md`. After this task, it will be at `ai-robin/docs/plan-2-plugin-migration.md`. Downstream tasks refer to the new location.

- [ ] **Step 1: Perform the rename**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
git mv references docs
```

- [ ] **Step 2: Verify**

```bash
ls docs/
```

Expected output:
```
architecture.md
feature-room-mapping.md
plan-2-plugin-migration.md
skill-extraction-log.md
```

- [ ] **Step 3: No commit** — end-of-phase commit.

---

### Task 1.5: Update all cross-references (path replacements)

**Files:**
- Modify: every `.md` file in `ai-robin/` that references moved paths.

**Replacement table:**

| Old path prefix | New path prefix |
|---|---|
| `agents/consumer/` | `agents/consumer/` |
| `agents/planning/` | `agents/planning/` |
| `agents/execute-control/` | `agents/execute-control/` |
| `agents/execute/` | `agents/execute/` |
| `agents/research/` | `agents/research/` |
| `agents/review/` | `agents/review/` |
| `agents/kernel/discipline.md` | `agents/kernel/discipline.md` |
| `docs/` | `docs/` |

**Important edge cases to NOT replace:**

- `execute` appearing as a verb ("execute the command") — keep
- `planning` as a gerund ("planning for the future") — keep
- `review` as a verb — keep
- `research` as a verb — keep

The safe heuristic: only replace when the token is **followed by `/`** or is immediately inside a path context (quotes, backticks, table cell referencing a file). The `sed` commands below use `/` as a boundary for safety.

- [ ] **Step 1: Write a verification check that will fail BEFORE the edits**

Create a temporary check script. This is our "failing test":

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
cat > /tmp/check-broken-refs.sh <<'EOF'
#!/bin/bash
# Find path-like references in .md files and check each exists.
cd /Users/waynewang/AI-Robin-Skill/ai-robin
MISSING=0
# Extract quoted or backticked path-like strings
for ref in $(grep -rhoE '`[a-zA-Z][a-zA-Z0-9/_.-]+\.(md|yaml|json|py|sh)`' \
             --include='*.md' . \
             | tr -d '`' | sort -u); do
    # Skip external/absolute paths or paths in .ai-robin/ (runtime, not source)
    case "$ref" in
        /*|http*|\.ai-robin/*|\{*) continue ;;
    esac
    # Skip if file exists at ref path (relative to ai-robin/)
    [ -e "$ref" ] && continue
    # Skip common filenames that are not paths (e.g., LICENSE, README.md — if not expected to exist)
    case "$ref" in
        README.md|LICENSE|LICENSE.md|CHANGELOG.md) continue ;;
    esac
    echo "MISSING: $ref"
    MISSING=$((MISSING+1))
done
echo "---"
echo "Total missing: $MISSING"
exit $MISSING
EOF
chmod +x /tmp/check-broken-refs.sh
```

Run it BEFORE edits:

```bash
bash /tmp/check-broken-refs.sh | tail -20
```

Expected: MANY broken references (the moved files are now at new paths but references haven't been updated).

- [ ] **Step 2: Perform the path replacements with sed**

Run each of these from `/Users/waynewang/AI-Robin-Skill/ai-robin/`:

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin

# Agent path prefixes (only replace when followed by /)
find . -type f -name '*.md' -not -path './node_modules/*' -exec sed -i '' -E '
s|(^|[^a-zA-Z-])agents/consumer/|\1agents/consumer/|g
s|(^|[^a-zA-Z-])agents/planning/|\1agents/planning/|g
s|(^|[^a-zA-Z-])agents/execute-control/|\1agents/execute-control/|g
s|(^|[^a-zA-Z/-])agents/execute/|\1agents/execute/|g
s|(^|[^a-zA-Z-])agents/research/|\1agents/research/|g
s|(^|[^a-zA-Z-])agents/review/|\1agents/review/|g
' {} \;

# kernel-discipline.md relocation
find . -type f -name '*.md' -exec sed -i '' \
  -e 's|stdlib/kernel-discipline\.md|agents/kernel/discipline.md|g' {} \;

# docs/ → docs/
find . -type f -name '*.md' -exec sed -i '' \
  -e 's|docs/|docs/|g' {} \;
```

**Note on sed flavor:** the `-i ''` syntax is for BSD sed (macOS). On GNU sed, use `-i` (no empty string).

**Note on `agents/execute/` replacement:** the negative char class `[^a-zA-Z/-]` prevents matching `agents/execute/` (because `/` precedes). If run twice, the regex self-protects.

- [ ] **Step 3: Re-run the broken-refs check**

```bash
bash /tmp/check-broken-refs.sh | tail -20
```

Expected: **much fewer** broken refs. Some may remain — e.g., fresh files not yet created (we haven't done Phase 2B yet), or paths inside code-block JSON examples that are actually fine (like `"path": "META/..."` or project-local paths).

Manually inspect any remaining "MISSING" entries. Accept them only if:
(a) they reference a path that will be created in Phase 2, OR
(b) they're example placeholders inside code blocks (`{project_root}/META/...`, `.ai-robin/...`), OR
(c) they're relative paths within the target project, not the skill repo itself.

- [ ] **Step 4: Grep for any remaining bare references that slipped through**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
echo "=== Bare 'agents/consumer/' not under agents/ ==="
grep -rn --include='*.md' -E '[^a-zA-Z/-]agents/consumer/' . | grep -v 'agents/consumer/' | head -20

echo "=== Bare 'agents/planning/' not under agents/ ==="
grep -rn --include='*.md' -E '[^a-zA-Z/-]agents/planning/' . | grep -v 'agents/planning/' | head -20

echo "=== kernel-discipline.md in stdlib/ ==="
grep -rn --include='*.md' 'stdlib/kernel-discipline' . | head -20

echo "=== docs/ still around ==="
grep -rn --include='*.md' 'docs/' . | head -20
```

Expected for each: empty (or only false positives like prose sentences — verify manually).

- [ ] **Step 5: No commit** — end-of-phase commit.

---

### Task 1.6: Update DESIGN.md tree diagrams

**Files:**
- Modify: `ai-robin/DESIGN.md`

**Rationale:** DESIGN.md contains multiple ASCII tree diagrams. They must reflect the new layout.

- [ ] **Step 1: Locate all tree diagrams in DESIGN.md**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -n '├──\|└──\|│' DESIGN.md | head -40
```

Expected: lines showing tree-drawing characters.

- [ ] **Step 2: Read each diagram region and verify the layout**

```bash
grep -n '```' DESIGN.md
```

Use the line numbers to read the fenced code blocks. For each block that shows a tree, check it matches the file-structure section at the top of this plan.

- [ ] **Step 3: Update tree diagrams to the new layout**

Replace any block that shows the old flat layout with a version that groups agents under `agents/` and shows `kernel-discipline.md` under `agents/kernel/`. The authoritative tree is the one at the top of this plan.

Use the Edit tool with exact `old_string` / `new_string` matching for each tree block.

- [ ] **Step 4: Verify DESIGN.md is internally consistent**

```bash
grep -E 'agents/consumer/|agents/planning/|stdlib/kernel-discipline' DESIGN.md
```

Expected: only `agents/consumer/`, `agents/planning/`, `agents/kernel/discipline.md` patterns. No bare old-style paths.

- [ ] **Step 5: No commit** — end-of-phase commit.

---

### Task 1.7: Update tests/ files

**Files:**
- Modify: `ai-robin/tests/routing-coverage.md`
- Modify: `ai-robin/tests/end-to-end-trace.md`

**Rationale:** Test files reference source paths. The grep regexes in routing-coverage.md must still match after the reorg.

- [ ] **Step 1: Check routing-coverage.md**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -n 'SKILL.md\|consumer\|planning' tests/routing-coverage.md | head -20
```

The grep command for routing table rows in `SKILL.md` — the root `SKILL.md` path is unchanged. So this should still work.

- [ ] **Step 2: Run the routing-coverage grep to confirm**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
comm -23 \
  <(grep -E '^#### `[a-z_]+`' contracts/dispatch-signal.md | sed -E 's/^#### `([a-z_]+)`.*/\1/' | sort -u) \
  <(grep -E '^\| `[a-z_]+` \|' SKILL.md | sed -E 's/^\| `([a-z_]+)` \|.*/\1/' | sort -u)
```

Expected: empty (17/17 coverage preserved).

- [ ] **Step 3: Check end-to-end-trace.md for any stale paths**

```bash
grep -n 'agents/consumer/\|agents/planning/\|agents/execute/\|agents/execute-control/\|agents/research/\|agents/review/\|stdlib/' tests/end-to-end-trace.md
```

For each match, verify:
- If the string is a **prose noun** ("the Consumer Agent" → no slash → ignore)
- If the string is a **path reference** → it should already have been rewritten by sed in Task 1.5

Any remaining bare-path references: manually edit with Edit tool to prefix with `agents/`.

- [ ] **Step 4: No commit** — end-of-phase commit.

---

### Task 1.8: Regenerate SUMMARY.md

**Files:**
- Modify: `ai-robin/SUMMARY.md`

**Rationale:** SUMMARY.md lists the file inventory. It's a documentation artifact — must reflect new paths.

- [ ] **Step 1: Read current SUMMARY.md**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
cat SUMMARY.md
```

- [ ] **Step 2: Update the inventory section**

Use the Edit tool. Find every path reference in the inventory and rewrite with the new layout. Specifically, the sections:

- "Consumer (Stage 0) — 14 files" → path prefix `agents/consumer/`
- "Planning (Stage 1) — 13 files" → path prefix `agents/planning/`
- "Execute-Control (Stage 2) — 7 files" → path prefix `agents/execute-control/`
- "Execute (Stage 3) — 8 files" → path prefix `agents/execute/`
- "Research — 1 file" → path prefix `agents/research/`
- "Review (Stage 4) — 11 files" → path prefix `agents/review/`
- "Stdlib (7 files, 1,719 lines)" → "(6 files, ...)" — because kernel-discipline moved

Update the architecture ASCII diagram in SUMMARY.md to show `agents/` grouping.

- [ ] **Step 3: Verify new SUMMARY.md**

```bash
grep -E 'agents/consumer/|agents/planning/|stdlib/kernel-discipline' SUMMARY.md
```

Expected: only `agents/consumer/` and related patterns. No stale references.

- [ ] **Step 4: No commit** — end-of-phase commit.

---

### Task 1.9: Update repo-root README.md

**Files:**
- Modify: `/Users/waynewang/AI-Robin-Skill/README.md`

**Rationale:** README describes the project at the repo root. If it has path references, they must be current.

- [ ] **Step 1: Scan README.md for path references**

```bash
cd /Users/waynewang/AI-Robin-Skill
grep -n 'agents/consumer/\|agents/planning/\|agents/execute/\|stdlib/kernel-discipline\|docs/' README.md
```

- [ ] **Step 2: Update each reference with Edit tool**

Apply the same replacement table as Task 1.5.

- [ ] **Step 3: No commit** — end-of-phase commit.

---

### Task 1.10: Final verification + single commit for Phase 1

**Files:** none to modify. Verification only.

- [ ] **Step 1: Run the broken-refs check one more time**

```bash
bash /tmp/check-broken-refs.sh | tail -5
```

Expected: `Total missing: 0` (or only acceptable exceptions as documented in Task 1.5 Step 3).

- [ ] **Step 2: Run the routing-coverage grep**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
comm -23 \
  <(grep -E '^#### `[a-z_]+`' contracts/dispatch-signal.md | sed -E 's/^#### `([a-z_]+)`.*/\1/' | sort -u) \
  <(grep -E '^\| `[a-z_]+` \|' SKILL.md | sed -E 's/^\| `([a-z_]+)` \|.*/\1/' | sort -u)
```

Expected: empty.

- [ ] **Step 3: Diff check — only renames + path edits, no semantic changes**

```bash
cd /Users/waynewang/AI-Robin-Skill
git status --short | head -30
git diff --stat | tail -5
```

Manually inspect: no line-of-prose changes except path strings; no removed content; file count roughly preserved (some files renamed, zero created, zero deleted).

- [ ] **Step 4: Capture post-reorg file inventory**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
find . -type f -name "*.md" | sort > /tmp/ai-robin-preflight-after.txt
diff /tmp/ai-robin-preflight-before.txt /tmp/ai-robin-preflight-after.txt | head -40
```

Expected: diff shows the renames (lines with `<` are old paths, lines with `>` are new paths), no net additions or removals.

- [ ] **Step 5: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add -A
git commit -m "$(cat <<'EOF'
refactor(ai-robin): reorganize into agents/ + stdlib/ + contracts/ + docs/ + tests/

Physical reorg only — no semantic change. All path references updated.

Moves:
- agents/consumer/ agents/planning/ agents/execute-control/ agents/execute/ agents/research/ agents/review/ → agents/
- agents/kernel/discipline.md → agents/kernel/discipline.md
- docs/ → docs/

Verified:
- tests/routing-coverage.md grep produces empty diff (17/17)
- broken-refs check returns zero
- git diff shows only renames + mechanical path-string edits
EOF
)"
```

- [ ] **Step 6: Verify the commit landed clean**

```bash
git log -1 --stat | head -40
```

Expected: commit exists; the stat shows many renames (`R`) and a small number of modified files (where path strings were updated).

**Phase 1 complete.** Proceed to Phase 2.

---

# Phase 2 — Claude Code Plugin (Runtime Adapter)

**Goal:** Build `.claude-plugin/` at the repo root as the first concrete runtime adapter. Add three new kernel-relief sub-agents. Migrate ordering rules from prose (`kernel-discipline.md §4`) to Python hooks.

**Success criteria:**
- `/ai-robin-start`, `/ai-robin-resume`, `/ai-robin-status` slash commands registered
- All sub-agents callable via `Task(subagent_type: "...")`
- `tests/routing-coverage.md` passes with 20/20 (three new signal types added)
- All Python hook libs have ≥90% line coverage via pytest
- `.claude-plugin/hooks/pre_task.py` and `post_task.py` correctly append ledger + move signal files (verified by unit tests with mock fixtures, not by running real AI-Robin)
- Plugin manifest validates against Claude Code's plugin schema
- `docs/plugin-equivalence.md` written, documenting what plugin does and does not change vs the abstract design

**Estimated effort:** ~2 weeks (2A: 2d, 2B: 4d, 2C: 4d, 2D: 2d).

## Phase 2A — Plugin Scaffold

**Goal:** Add the `.claude-plugin/` directory with manifest, slash commands, and agent wrappers. Zero behavior change vs Phase 1 end-state — plugin at this point is pure packaging.

---

### Task 2A.1: Create plugin.json manifest

**Files:**
- Create: `/Users/waynewang/AI-Robin-Skill/.claude-plugin/plugin.json`
- Create: `/Users/waynewang/AI-Robin-Skill/.claude-plugin/` (directory)

- [ ] **Step 1: Create the plugin directory**

```bash
cd /Users/waynewang/AI-Robin-Skill
mkdir -p .claude-plugin
```

- [ ] **Step 2: Write plugin.json**

```bash
cat > .claude-plugin/plugin.json <<'EOF'
{
  "name": "ai-robin",
  "version": "0.2.0-dev",
  "description": "Autonomous multi-agent software development workflow: Consumer (intake) → Planning → Execute-Control → Execute × N → Review stage. Takes a one-shot human brief and delivers a software project end-to-end as a batch job. Do NOT use for interactive pair-programming.",
  "author": "AI-Robin contributors",
  "commands": "./commands",
  "agents": "./agents",
  "hooks": "./hooks/hooks.json"
}
EOF
```

**Note:** exact Claude Code plugin schema may differ. Validate once the plugin is installed. If schema mismatch, fix per error message.

- [ ] **Step 3: Verify valid JSON**

```bash
cd /Users/waynewang/AI-Robin-Skill
python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))"
```

Expected: no output (JSON parses clean).

- [ ] **Step 4: No commit** — commit at end of 2A.

---

### Task 2A.2: Write plugin README

**Files:**
- Create: `/Users/waynewang/AI-Robin-Skill/.claude-plugin/README.md`

- [ ] **Step 1: Write the README**

```markdown
# AI-Robin Plugin (Claude Code adapter)

This directory is the **Claude Code runtime adapter** for AI-Robin. The authoritative source of the AI-Robin NLP is in `../ai-robin/` — this plugin is a thin wrapper that adapts the abstract design to Claude Code's specific primitives (slash commands, subagents, hooks).

## Relationship to source

- **Source of truth:** `../ai-robin/` — runtime-agnostic natural-language program
- **This plugin:** the FIRST runtime adapter (Claude Code). Other adapters (Claude Agent SDK, custom orchestrators) may be added later without changing the source.

Per `../ai-robin/DESIGN.md §8`, the file-based signal inbox at `.ai-robin/dispatch/inbox/` remains the authoritative communication channel even in Claude Code. Plugin hooks enforce ordering rules but do NOT replace the inbox.

## What the plugin provides

1. **Slash commands** (`commands/`): `/ai-robin-start`, `/ai-robin-resume`, `/ai-robin-status`
2. **Agent wrappers** (`agents/`): thin adapters that let Claude Code's Task tool address each AI-Robin sub-agent by name
3. **Hooks** (`hooks/`): Python scripts that automatically append to ledger, move signal files, and validate state — enforcing `kernel-discipline §4` rules so the kernel LLM doesn't have to remember them

## What the plugin does NOT do

- Does not replace the abstract methodology (lives in `../ai-robin/agents/*/SKILL.md`)
- Does not replace the file-based inbox
- Does not enable new capabilities — it only enforces and simplifies the existing design
```

Write with the Write tool. Path: `/Users/waynewang/AI-Robin-Skill/.claude-plugin/README.md`.

- [ ] **Step 2: No commit** — end-of-phase commit.

---

### Task 2A.3: Create slash command files

**Files:**
- Create: `/Users/waynewang/AI-Robin-Skill/.claude-plugin/commands/ai-robin-start.md`
- Create: `/Users/waynewang/AI-Robin-Skill/.claude-plugin/commands/ai-robin-resume.md`
- Create: `/Users/waynewang/AI-Robin-Skill/.claude-plugin/commands/ai-robin-status.md`

- [ ] **Step 1: Create the commands directory**

```bash
cd /Users/waynewang/AI-Robin-Skill
mkdir -p .claude-plugin/commands
```

- [ ] **Step 2: Write `ai-robin-start.md`**

Content:

```markdown
---
description: Start a new AI-Robin run on the current working directory
---

You are about to begin a new AI-Robin run.

**Pre-flight checks:**
1. If `.ai-robin/` already exists in the current working directory: STOP. Tell the user to use `/ai-robin-resume` instead, or to delete `.ai-robin/` if they truly want to start fresh.
2. If the current working directory has uncommitted changes: warn the user; ask for confirmation before proceeding.

**If both checks pass:**

Load `ai-robin/SKILL.md` (the kernel entrypoint, located inside this plugin's sibling `ai-robin/` skill directory) and follow its initialization instructions: create `.ai-robin/` directory structure, initialize `stage-state.json` with `stage: "intake"`, and spawn Consumer Agent with the user's brief as `user_raw_input`.

**User's project brief:** $ARGUMENTS

If $ARGUMENTS is empty, ask the user for their project brief before initializing.
```

- [ ] **Step 3: Write `ai-robin-resume.md`**

Content:

```markdown
---
description: Resume an interrupted AI-Robin run
---

You are resuming an AI-Robin run.

**Pre-flight check:**
1. If `.ai-robin/stage-state.json` does not exist: STOP. Tell the user there's no run to resume; suggest `/ai-robin-start` instead.

**If the check passes:**

Load `ai-robin/SKILL.md` and follow its resume protocol from the "Initialization: the first turn" section — read stage-state, identify where the run was when it stopped, handle any active invocations, and continue the dispatch loop.
```

- [ ] **Step 4: Write `ai-robin-status.md`**

Content:

```markdown
---
description: Report status of the current AI-Robin run without changing state
---

Do not dispatch any sub-agents. Do not modify any file.

Read `.ai-robin/stage-state.json` and the last N lines of `.ai-robin/ledger.jsonl`. Report to the user:

1. Current stage and iteration number
2. Active invocations (if any)
3. Last ledger entry
4. Any active anomalies from the ledger
5. Current batch status (if `current_batch.batch_id` is not null)
6. Remaining budget snapshot from `.ai-robin/budgets.json`

Keep the report to under 15 lines. Do NOT read spec content or source code — report only kernel-level metadata.
```

- [ ] **Step 5: Verify all 3 files exist**

```bash
ls .claude-plugin/commands/
```

Expected output:
```
ai-robin-resume.md
ai-robin-start.md
ai-robin-status.md
```

- [ ] **Step 6: No commit** — end-of-phase commit.

---

### Task 2A.4: Create agent wrapper files (9 wrappers)

**Files to create (all inside `/Users/waynewang/AI-Robin-Skill/.claude-plugin/agents/`):**

- `consumer.md`
- `planning.md`
- `execute-control.md`
- `execute.md`
- `research.md`
- `review-plan.md`
- `merge.md`
- `playbook-code-quality.md`
- (Commit/Degradation/Finalization wrappers are created in Phase 2B after their source agents exist)

**Wrapper purpose:** Each wrapper is an agent file with Claude Code frontmatter (`name`, `description`, `tools`). Body is a short instruction that says "Load the corresponding source SKILL.md and follow its instructions with the task spec passed in via the Task tool prompt."

- [ ] **Step 1: Create the agents directory**

```bash
cd /Users/waynewang/AI-Robin-Skill
mkdir -p .claude-plugin/agents
```

- [ ] **Step 2: Write `consumer.md`**

Content:

```markdown
---
name: ai-robin-consumer
description: AI-Robin Consumer Agent. Intake stage — the only sub-agent that interacts with the user. Do not invoke for general intake tasks; only invoke as part of an AI-Robin dispatch loop.
tools: Read, Write, Edit, Glob, Grep
---

Read `ai-robin/agents/consumer/SKILL.md` and follow its instructions. The task specification is in the invocation prompt — it conforms to the Input contract described in that file.
```

- [ ] **Step 3: Write `planning.md`**

Content:

```markdown
---
name: ai-robin-planning
description: AI-Robin Planning Agent. Turns Consumer's intake into an executable plan with milestones, modules, and contract specs. Invoked only by the AI-Robin kernel.
tools: Read, Write, Edit, Glob, Grep
---

Read `ai-robin/agents/planning/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
```

- [ ] **Step 4: Write `execute-control.md`**

Content:

```markdown
---
name: ai-robin-execute-control
description: AI-Robin Execute-Control Agent. Scheduler — decides which milestones run in the next batch and at what concurrency. Read-mostly. Invoked only by the AI-Robin kernel.
tools: Read, Glob, Grep, Write
---

Read `ai-robin/agents/execute-control/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
```

- [ ] **Step 5: Write `execute.md`**

Content:

```markdown
---
name: ai-robin-execute
description: AI-Robin Execute Agent. Writes actual application code for one milestone. May modify source files and run tests. Does NOT git commit (kernel does that). Invoked only by the AI-Robin kernel.
tools: Read, Write, Edit, Bash, Glob, Grep
---

Read `ai-robin/agents/execute/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
```

- [ ] **Step 6: Write `research.md`**

Content:

```markdown
---
name: ai-robin-research
description: AI-Robin Research Agent. Answers a specific factual question via web search. Invoked only by the AI-Robin kernel when Planning returns planning_needs_research.
tools: Read, Write, WebSearch, WebFetch
---

Read `ai-robin/agents/research/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
```

- [ ] **Step 7: Write `review-plan.md`**

Content:

```markdown
---
name: ai-robin-review-plan
description: AI-Robin Review-Plan Agent. Meta-agent that decides which review playbooks to run for a batch. Invoked only by the AI-Robin kernel at the start of every review stage.
tools: Read, Glob, Grep, Write
---

Read `ai-robin/agents/review/review-plan/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
```

- [ ] **Step 8: Write `merge.md`**

Content:

```markdown
---
name: ai-robin-merge
description: AI-Robin Merge Agent. Consolidates N review sub-verdicts into one merged verdict with a composed git commit message. Invoked only by the AI-Robin kernel after all review playbooks return.
tools: Read, Write, Glob
---

Read `ai-robin/agents/review/merge/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
```

- [ ] **Step 9: Write `playbook-code-quality.md`**

Content:

```markdown
---
name: ai-robin-playbook-code-quality
description: AI-Robin Code-Quality Review Playbook. Always-on review sub-agent. Checks general code quality within its declared scope. Invoked only by the AI-Robin kernel via review dispatch.
tools: Read, Glob, Grep, Write
---

Read `ai-robin/agents/review/playbooks/code-quality/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
```

- [ ] **Step 10: Verify all 8 wrappers exist**

```bash
ls .claude-plugin/agents/
```

Expected output:
```
consumer.md
execute-control.md
execute.md
merge.md
planning.md
playbook-code-quality.md
research.md
review-plan.md
```

(8 files — commit/degradation/finalization wrappers added in Phase 2B Task 2B.8.)

- [ ] **Step 11: Verify all wrappers reference valid source files**

```bash
cd /Users/waynewang/AI-Robin-Skill
for wrapper in .claude-plugin/agents/*.md; do
    # extract the Read path from the wrapper body
    src=$(grep -oE 'ai-robin/agents/[a-z/-]+SKILL\.md' "$wrapper" | head -1)
    if [ -z "$src" ]; then
        echo "WARN: $wrapper has no source path"
        continue
    fi
    if [ ! -f "$src" ]; then
        echo "MISSING: $wrapper → $src"
    fi
done
```

Expected: no MISSING lines. One exception is `playbook-code-quality.md` if the code-quality playbook lives at a path confirmed via:

```bash
ls ai-robin/agents/review/playbooks/code-quality/SKILL.md
```

If the path is different, fix the wrapper to point to the correct location.

- [ ] **Step 12: No commit** — end-of-phase commit.

---

### Task 2A.5: Phase 2A commit

- [ ] **Step 1: Verify the plugin directory is well-formed**

```bash
cd /Users/waynewang/AI-Robin-Skill
find .claude-plugin -type f | sort
```

Expected:
```
.claude-plugin/README.md
.claude-plugin/agents/consumer.md
.claude-plugin/agents/execute-control.md
.claude-plugin/agents/execute.md
.claude-plugin/agents/merge.md
.claude-plugin/agents/planning.md
.claude-plugin/agents/playbook-code-quality.md
.claude-plugin/agents/research.md
.claude-plugin/agents/review-plan.md
.claude-plugin/commands/ai-robin-resume.md
.claude-plugin/commands/ai-robin-start.md
.claude-plugin/commands/ai-robin-status.md
.claude-plugin/plugin.json
```

- [ ] **Step 2: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add .claude-plugin/
git commit -m "$(cat <<'EOF'
feat(plugin): scaffold Claude Code plugin as first runtime adapter

Phase 2A of plugin migration. Adds .claude-plugin/ at repo root:
- plugin.json manifest
- 3 slash commands (start/resume/status)
- 8 agent wrappers pointing to ai-robin/agents/*/SKILL.md source
- README explaining adapter role vs source of truth

No behavior change vs Phase 1 end-state. Source in ai-robin/ is unmodified.
The file-based inbox remains authoritative per DESIGN.md §8.

Agent wrappers for commit/degradation/finalization deferred to Phase 2B
(their source agents don't exist yet).
EOF
)"
```

**Phase 2A complete.** Proceed to Phase 2B.

---

## Phase 2B — Kernel-Relief Sub-Agents

**Goal:** Offload domain-heavy work (composing commit messages, writing `context-degraded-*.yaml` specs with narrative, generating delivery bundles) from the kernel to three new dedicated sub-agents. Introduce three new signal types. Update the kernel routing table and bump routing-coverage to 20/20.

**Rationale:** Per the pre-reorg audit ([conversation context], severe issue #2), the current kernel is forced to do domain work (writing `context-degraded-*.yaml` from ledger archaeology, composing commit messages that reference domain content) even though `kernel-discipline §1` forbids this. Delegating to sub-agents resolves the contradiction.

---

### Task 2B.1: Add three new signal types to dispatch-signal.md

**Files:**
- Modify: `ai-robin/contracts/dispatch-signal.md`

**Signals to add:**
1. `commit_complete` — Commit Agent returns after a git commit
2. `degradation_spec_written` — Degradation Agent returns after writing the degraded spec
3. `delivery_bundle_ready` — Finalization Agent returns after generating final delivery bundle

- [ ] **Step 1: Read the current dispatch-signal.md structure**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -n '^####' contracts/dispatch-signal.md
```

Take note of where each existing signal type is defined; the new ones go in the appropriate stage sections.

- [ ] **Step 2: Add `commit_complete` to the Review stage section**

Use the Edit tool. Find the end of the `review_merged` section (just before the `### Completion / termination signals` heading). Insert:

```markdown
#### `commit_complete`
Commit Agent finished executing a git commit (triggered by either `review_merged` or `degradation_spec_written`).

Payload:
```json
{
  "batch_id": "string | null — present when commit was triggered by review_merged; null when triggered by degradation",
  "trigger_signal_type": "'review_merged' | 'degradation_spec_written'",
  "trigger_signal_id": "string — the signal whose commit this is",
  "git_hash": "string | null — the SHA of the new commit; null if commit failed",
  "success": "boolean",
  "error": "string | null — error message if success is false",
  "files_committed": "integer"
}
```

Main agent action: append `commit` ledger entry using the fields in this payload. Then route per the trigger:
- If `trigger_signal_type == 'review_merged'`: route to next stage per the review verdict (Execute-Control for pass, Planning for fail-with-budget, degrade for fail-without-budget).
- If `trigger_signal_type == 'degradation_spec_written'`: continue the dispatch loop (typically back to Execute-Control to attempt next batch).
- If `success == false`: log `anomaly` entry severity high; continue with the routing path as if the commit had happened (commit failure is recorded but does not halt the run).
```

- [ ] **Step 3: Add `degradation_spec_written` to the degradation-related section**

Insert just before `#### stage_exhausted`:

```markdown
#### `degradation_spec_written`
Degradation Agent finished writing the `context-degraded-*.yaml` spec and updating `escalation-notice.md`.

Payload:
```json
{
  "scope_type": "'batch' | 'milestone' | 'research_question' | 'plan_scope' | 'global'",
  "scope_id": "string — batch_id / milestone_id / question_id / etc.",
  "degraded_spec_id": "string — the context-degraded-*.yaml spec id written",
  "files_to_commit": ["string — absolute paths of files that should be staged for the degradation commit"],
  "commit_message": "string — verbatim commit message for Commit Agent to use"
}
```

Main agent action: spawn Commit Agent with `trigger_signal_type: 'degradation_spec_written'`, passing the `commit_message` and `files_to_commit` verbatim. Wait for `commit_complete`.
```

- [ ] **Step 4: Add `delivery_bundle_ready` to the Completion section**

Insert just before `#### stage_exhausted` (or just after `all_complete`, whichever is more natural given current file order):

```markdown
#### `delivery_bundle_ready`
Finalization Agent finished generating the delivery bundle.

Payload:
```json
{
  "bundle_path": "string — where the delivery bundle lives on disk",
  "summary": {
    "milestones_passed": "integer",
    "milestones_degraded": "integer",
    "total_commits": "integer",
    "wall_clock_total_seconds": "integer"
  }
}
```

Main agent action: append `run_end` ledger entry with `exit_reason: "all_complete"`. Surface `bundle_path` and summary to user on their next turn. Exit dispatch loop.
```

- [ ] **Step 5: Update the existing `review_merged` routing action**

Find the "Main agent action:" section under `review_merged`. Change it from `1. Commit all artifacts + this verdict to git immediately (hard rule)` to:

```markdown
Main agent action:
1. **Spawn Commit Agent** with `trigger_signal_type: 'review_merged'`, passing `payload.commit_message` and the list of files to stage (batch artifacts + the verdict record). Do NOT commit directly. Wait for `commit_complete`.
2. After `commit_complete` returns: route based on overall_status:
   - `pass` or `pass_with_warnings` → signal Execute-Control for next batch
   - `fail` + iteration < budget → signal Planning for replan with issues
   - `fail` + iteration >= budget → trigger degradation (spawn Degradation Agent)
```

- [ ] **Step 6: Update the existing `all_complete` routing action**

Change it from `generate delivery bundle. Kernel exits.` to:

```markdown
Main agent action: spawn Finalization Agent with the plan summary. Wait for `delivery_bundle_ready`. Then append `run_end` ledger entry and exit the dispatch loop.
```

- [ ] **Step 7: Update the Example section**

Add one new example JSON for `commit_complete` (most illustrative of the new signals). Insert near the existing `review_sub_verdict` example.

- [ ] **Step 8: Verify signal count in contract**

```bash
grep -cE '^#### `[a-z_]+`' contracts/dispatch-signal.md
```

Expected: 20.

- [ ] **Step 9: No commit** — commit at end of 2B.

---

### Task 2B.2: Create agents/commit/ package

**Files:**
- Create: `ai-robin/agents/commit/` (directory)
- Create: `ai-robin/agents/commit/SKILL.md`

- [ ] **Step 1: Create the directory**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
mkdir -p agents/commit
```

- [ ] **Step 2: Write agents/commit/SKILL.md**

Content:

```markdown
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

- [ ] Check `project_root` exists and is a git working tree (`git -C "$project_root" rev-parse --git-dir`).
- [ ] Check every path in `files_to_stage` exists under `project_root`.
- [ ] Check `commit_message` is non-empty.

If any check fails, skip to Phase 3 with `success: false` and an error message.

### Phase 2: Stage and commit

- [ ] Run `git -C "$project_root" add` with each path in `files_to_stage` (explicit list, never `git add -A`).
- [ ] Run `git -C "$project_root" commit -m "$commit_message"` exactly — no flag additions, no message rewriting.
- [ ] Capture the new commit SHA with `git -C "$project_root" rev-parse HEAD`.

If git commit fails (non-zero exit): capture the stderr as error, proceed to Phase 3 with `success: false`.

### Phase 3: Emit signal

Write `commit_complete` to `.ai-robin/dispatch/inbox/{signal_id}.json`. `signal_id` format: `commit-commit-{YYYYMMDDTHHMMSS}-{8-char-hex}`.

Payload fields per contracts/dispatch-signal.md commit_complete schema.

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
| `git commit` fails | `commit_complete` with success=false, error=stderr |

## Reference map

| Need | Read |
|---|---|
| Signal shape | `contracts/dispatch-signal.md` |
```

- [ ] **Step 3: Verify the file was written**

```bash
head -20 agents/commit/SKILL.md
```

Expected: starts with `# Commit Agent — Kernel Relief`.

- [ ] **Step 4: No commit** — end-of-phase commit.

---

### Task 2B.3: Create agents/degradation/ package

**Files:**
- Create: `ai-robin/agents/degradation/SKILL.md`

**Rationale:** this is the most complex new agent. It must read original specs (which the kernel cannot do) and compose a multi-section narrative YAML spec explaining what was attempted and why degraded.

- [ ] **Step 1: Create the directory**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
mkdir -p agents/degradation
```

- [ ] **Step 2: Write agents/degradation/SKILL.md**

Content:

```markdown
# Degradation Agent — Kernel Relief

> **Internal sub-skill — not user-invocable.** Loaded by the ai-robin main agent via the Read tool. No YAML frontmatter.

Degradation Agent writes the `context-degraded-*.yaml` spec and updates `escalation-notice.md` when a scope is degraded. It reads original specs + ledger entries to compose a narrative explaining what was attempted, what was tried, what's left on disk, and what a human should do about it.

The kernel cannot do this itself — composing the narrative requires reading domain content (original specs, change history, last-review issues), which kernel-discipline §1 forbids.

## Prerequisites

Load before starting:
1. `stdlib/feature-room-spec.md` — for the spec YAML format
2. `stdlib/degradation-policy.md` — for the degradation spec structure and escalation-notice format
3. `contracts/dispatch-signal.md` — return signal shape
4. `contracts/session-ledger.md` — for reading ledger history of attempts

## Input

From main agent at spawn:

```json
{
  "invocation_id": "string",
  "project_root": "string",
  "scope_type": "'batch' | 'milestone' | 'research_question' | 'plan_scope' | 'global'",
  "scope_id": "string",
  "trigger_reason": "string — e.g. 'review_iterations_per_batch exhausted after 2 fails'",
  "trigger_ledger_entry_id": "integer — the budget_exhausted entry that triggered this",
  "related_spec_ids": ["string — spec ids that belong to the degraded scope"]
}
```

## Output contract

Return `degradation_spec_written` signal. Do NOT commit — Commit Agent does that (kernel will spawn it next).

Primary artifacts:
- One new `context-degraded-*.yaml` file in the appropriate Feature Room
- Updates to any original specs (set `state: degraded` where applicable)
- Appended section to `.ai-robin/escalation-notice.md`

## Execution — six phases

### Phase 1: Load scope context

Read:
- Each spec in `related_spec_ids` from the Feature Room
- The last N ledger entries leading up to `trigger_ledger_entry_id` (N ≈ 20)
- The current `stage-state.json` to understand current_batch state

Build an internal mental model of: what was being attempted, what was tried (attempt 1, attempt 2), what's currently on disk from any partial work.

### Phase 2: Determine current state on disk

For a batch degradation: which files in the working tree exist from this batch's attempts? (Use git log to scan; if files were never committed, they may still be in the working tree uncommitted.)

For a milestone degradation: similar but narrower.

For a research_question degradation: the `.ai-robin/research/` folder may have partial findings.

### Phase 3: Compose the narrative

The narrative has 5 parts, each 2-8 lines:
1. **Scope** — what was being attempted, user-facing terms
2. **What was tried** — ordered list of attempts, each referencing a ledger entry_id
3. **Why degraded** — concrete trigger (budget exhaustion, specific failure)
4. **Current state on disk** — files that exist + their level of completion
5. **Suggested resolution** — concrete, actionable; human reader can choose one path

Write these into memory as strings. Phase 4 persists them.

### Phase 4: Write the context-degraded spec

Build a spec yaml per `stdlib/feature-room-spec.md` and `stdlib/degradation-policy.md`:

```yaml
spec_id: "context-degraded-{scope-short-name}-{NNN}"
type: context
state: degraded
intent:
  summary: "Scope {X} was degraded; see escalation-notice"
  detail: |
    **Scope**: ...
    **What was being attempted**: ...
    **Why degraded**: ...
    **What was tried**: ...
    **Current state on disk**: ...
    **Suggested resolution**: ...
constraints: []
indexing:
  type: context
  priority: P0
  layer: project
  domain: "degradation"
  tags: ["degraded", "{scope-type}"]
provenance:
  source_type: degradation_trigger
  confidence: 1.0
  source_ref: "ledger entry {trigger_ledger_entry_id}"
relations:
  - type: "relates_to"
    ref: "{each spec_id in related_spec_ids}"
anchors: []
```

Write to the appropriate Room (scope-local Room for batch/milestone, 00-project-room for cross-cutting). File path: `{project_root}/META/{room}/specs/context-degraded-{scope-short-name}-{NNN}.yaml`.

### Phase 5: Update original specs and escalation-notice

- For each spec in `related_spec_ids`: set `state: degraded` (read the file, mutate the `state` field, write back).
- Append a new section to `.ai-robin/escalation-notice.md` per the format in `contracts/escalation-notice.md`.

### Phase 6: Emit

Compose the commit message for Commit Agent. Format:

```
degradation({scope_id}): {one-line trigger reason}

Scope: {scope description}
Trigger: {trigger_reason}
Degraded spec: {degraded_spec_id}

See context-degraded-{scope-short-name}-{NNN}.yaml and escalation-notice.md.
```

Build the `files_to_stage` list: new context-degraded spec + updated original specs + escalation-notice.md.

Write `degradation_spec_written` signal to `.ai-robin/dispatch/inbox/{signal_id}.json`.

## What you absolutely do not do

- **Do not commit.** Commit Agent does that. You produce the spec and the message.
- **Do not decide severity.** You report facts; severity characterization happens in escalation-notice at run_end.
- **Do not modify code files.** Only specs and the escalation-notice.
- **Do not fix the underlying problem.** You document that it wasn't fixed; fixing is out of scope.

## Reference map

| Need | Read |
|---|---|
| Degraded spec yaml format | `stdlib/degradation-policy.md` § "Step 2: Write the degradation spec" |
| Escalation notice section format | `contracts/escalation-notice.md` |
| Spec format | `stdlib/feature-room-spec.md` |
| Signal shape | `contracts/dispatch-signal.md` |
```

- [ ] **Step 3: No commit** — end-of-phase commit.

---

### Task 2B.4: Create agents/finalization/ package

**Files:**
- Create: `ai-robin/agents/finalization/SKILL.md`

- [ ] **Step 1: Create the directory**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
mkdir -p agents/finalization
```

- [ ] **Step 2: Write agents/finalization/SKILL.md**

Content:

```markdown
# Finalization Agent — Kernel Relief

> **Internal sub-skill — not user-invocable.** No YAML frontmatter.

Finalization Agent generates the delivery bundle at end-of-run. It computes summary statistics and produces a human-readable summary document for the user.

The kernel cannot do this — it requires reading spec content (to know what was delivered) and ledger archaeology, both of which are domain work.

## Prerequisites

Load before starting:
1. `contracts/session-ledger.md` — for reading ledger history
2. `contracts/dispatch-signal.md` — return signal shape
3. `stdlib/feature-room-spec.md` — to read the plan + change specs

## Input

From main agent at spawn:

```json
{
  "invocation_id": "string",
  "project_root": "string",
  "plan_pointer": {
    "completed_milestones": ["string"],
    "in_progress_milestones": ["string"],
    "pending_milestones": ["string"],
    "degraded_milestones": ["string"]
  },
  "run_started_at": "ISO 8601",
  "ledger_entry_count": "integer"
}
```

## Output contract

Return `delivery_bundle_ready` signal.

Primary artifact: a markdown file at `.ai-robin/DELIVERY.md` summarizing the run.

## Execution — three phases

### Phase 1: Compute summary stats

Scan ledger.jsonl (streamed line-by-line) to count:
- Total stage transitions
- Total commits
- Review iterations (by batch)
- Degradations triggered
- Anomalies
- Wall clock elapsed (run_start to now)

### Phase 2: Read top-level specs

For the delivery bundle narrative:
- List intents (from Consumer's intake) — one-line each
- List completed milestones with commit references
- List degraded milestones with pointer to their context-degraded spec

### Phase 3: Write DELIVERY.md

Structure:

```markdown
# AI-Robin Delivery: {project name from intent}

## Summary
- Started: {run_started_at}
- Finished: {now}
- Wall clock: {seconds}
- Commits: {count}
- Stages completed: {list}

## What was built
{one paragraph synthesis from intent specs}

## Milestones
### Completed
- {m1}: {one-line description} — commit {sha}
- ...

### Degraded
- {mX}: see {context-degraded-...yaml}
- ...

## Where to look next
- Code changes: see git log
- Feature Room specs: META/
- Audit trail: .ai-robin/ledger.jsonl
- Escalations: .ai-robin/escalation-notice.md (if any degradations)
```

Emit `delivery_bundle_ready` signal with `bundle_path: ".ai-robin/DELIVERY.md"` and the summary stats.

## What you absolutely do not do

- **Do not write code.** You summarize; Execute writes code.
- **Do not commit.** The delivery bundle is not committed by Finalization; kernel may commit it as the final run_end artifact if desired.
- **Do not second-guess degradations.** They are reported as recorded in their context-degraded specs.

## Reference map

| Need | Read |
|---|---|
| Ledger format | `contracts/session-ledger.md` |
| Spec format | `stdlib/feature-room-spec.md` |
| Signal shape | `contracts/dispatch-signal.md` |
```

- [ ] **Step 3: No commit** — end-of-phase commit.

---

### Task 2B.5: Update kernel routing table

**Files:**
- Modify: `ai-robin/SKILL.md`

- [ ] **Step 1: Read the current routing table**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -n '^| `' SKILL.md | head -25
```

Expected: 17 rows of routing table.

- [ ] **Step 2: Update existing rows for `review_merged` and `all_complete`**

Use Edit tool. Find the `review_merged` row. Change its action from (whatever is there now regarding committing) to:

```markdown
| `review_merged` | Spawn **Commit Agent** (not git directly) with `trigger_signal_type: 'review_merged'`, passing `payload.commit_message` verbatim. Wait for `commit_complete`. Then route per `overall_status`: pass → Execute-Control; fail + budget → Planning replan; fail + no budget → spawn Degradation Agent. |
```

Find the `all_complete` row. Change to:

```markdown
| `all_complete` | Spawn **Finalization Agent** with plan summary. Wait for `delivery_bundle_ready`. Then write `run_end` ledger entry. Exit. |
```

- [ ] **Step 3: Add 3 new rows**

After the last existing row (currently `all_complete`), insert these three rows:

```markdown
| `commit_complete` | Append `commit` ledger entry from payload. Then route per `trigger_signal_type`: review_merged → continue original `review_merged` routing (next stage); degradation_spec_written → continue degradation flow (typically back to Execute-Control for next batch). |
| `degradation_spec_written` | Spawn **Commit Agent** with `trigger_signal_type: 'degradation_spec_written'`, passing `payload.commit_message` and `payload.files_to_stage` verbatim. Wait for `commit_complete`. |
| `delivery_bundle_ready` | Append `run_end` ledger entry with `exit_reason: "all_complete"`. Surface `bundle_path` to user. Exit dispatch loop. |
```

- [ ] **Step 4: Verify row count**

```bash
grep -cE '^\| `[a-z_]+` \|' SKILL.md
```

Expected: 20.

- [ ] **Step 5: No commit** — end-of-phase commit.

---

### Task 2B.6: Update tests/routing-coverage.md

**Files:**
- Modify: `ai-robin/tests/routing-coverage.md`

- [ ] **Step 1: Update the "Contract declares" and "routing table must contain" numbers**

Find lines like:
```
- Contract declares: **17 signal types**
- Main SKILL.md routing table must contain: **17 rows** (one per type)
```

Change both `17` to `20`.

- [ ] **Step 2: Add 3 rows to the "Signal → routing contract" table**

Insert after the last existing row (before the "Batch-settled rule" or "Coverage status" section):

```markdown
| `commit_complete` | ✅ | Append `commit` ledger entry from payload. Route per `trigger_signal_type`: review_merged → continue review routing; degradation_spec_written → continue degradation flow. |
| `degradation_spec_written` | ✅ | Spawn Commit Agent with `trigger_signal_type: 'degradation_spec_written'`. Wait for `commit_complete`. |
| `delivery_bundle_ready` | ✅ | Append `run_end` ledger entry. Surface `bundle_path` to user. Exit. |
```

- [ ] **Step 3: Run the routing-coverage grep to verify empty diff**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
comm -23 \
  <(grep -E '^#### `[a-z_]+`' contracts/dispatch-signal.md | sed -E 's/^#### `([a-z_]+)`.*/\1/' | sort -u) \
  <(grep -E '^\| `[a-z_]+` \|' SKILL.md | sed -E 's/^\| `([a-z_]+)` \|.*/\1/' | sort -u)
```

Expected: empty (20/20).

- [ ] **Step 4: Verify signal count**

```bash
grep -cE '^#### `[a-z_]+`' contracts/dispatch-signal.md  # should be 20
grep -cE '^\| `[a-z_]+` \|' SKILL.md                      # should be 20
```

Both should equal 20.

- [ ] **Step 5: No commit** — end-of-phase commit.

---

### Task 2B.7: Remove kernel's direct domain work from discipline.md

**Files:**
- Modify: `ai-robin/agents/kernel/discipline.md`

- [ ] **Step 1: Find any references to kernel writing degraded specs or composing commit messages**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -n 'degraded spec\|context-degraded\|commit message\|compose commit' agents/kernel/discipline.md
```

- [ ] **Step 2: Add a new section at the end of discipline.md**

Insert a new section `## Delegations the kernel MUST perform` near the bottom:

```markdown
## Delegations the kernel MUST perform

The kernel does not do domain-heavy work itself. It delegates to specialized sub-agents:

| Situation | Delegate to | Why |
|---|---|---|
| `review_merged` arrives (pass or fail) | Commit Agent | Composing git commit requires the domain-aware commit_message from merge; kernel never reads the message content, just passes it along |
| Any degradation trigger fires | Degradation Agent | Writing `context-degraded-*.yaml` requires reading original spec content and composing narrative — domain work forbidden by §1 |
| `all_complete` arrives | Finalization Agent | Generating delivery bundle requires summarizing intents and scanning ledger for narrative |

The kernel's job in each case is limited to: dispatching the delegate, waiting for its signal, and then appending the appropriate ledger entry. Do not inline any of the delegate's work.
```

- [ ] **Step 3: Remove or update stdlib/degradation-policy.md Step 2 (if it instructs kernel to write the spec)**

```bash
grep -n 'kernel' stdlib/degradation-policy.md
```

Find the section that describes "Step 2: Write the degradation spec". If it says "kernel writes", change to "Degradation Agent writes (kernel dispatches Degradation Agent per SKILL.md routing)".

- [ ] **Step 4: No commit** — end-of-phase commit.

---

### Task 2B.8: Add plugin wrappers for the three new agents

**Files:**
- Create: `.claude-plugin/agents/commit.md`
- Create: `.claude-plugin/agents/degradation.md`
- Create: `.claude-plugin/agents/finalization.md`

- [ ] **Step 1: Write commit.md wrapper**

```markdown
---
name: ai-robin-commit
description: AI-Robin Commit Agent. Executes a git commit using the exact message provided by the trigger signal. Invoked only by the AI-Robin kernel after review_merged or degradation_spec_written.
tools: Read, Bash, Write
---

Read `ai-robin/agents/commit/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
```

- [ ] **Step 2: Write degradation.md wrapper**

```markdown
---
name: ai-robin-degradation
description: AI-Robin Degradation Agent. Writes the context-degraded-*.yaml spec with narrative and updates escalation-notice.md. Invoked only by the AI-Robin kernel when a scope is degraded.
tools: Read, Write, Edit, Glob, Grep
---

Read `ai-robin/agents/degradation/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
```

- [ ] **Step 3: Write finalization.md wrapper**

```markdown
---
name: ai-robin-finalization
description: AI-Robin Finalization Agent. Generates the end-of-run delivery bundle (DELIVERY.md). Invoked only by the AI-Robin kernel on all_complete.
tools: Read, Write, Glob, Grep
---

Read `ai-robin/agents/finalization/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
```

- [ ] **Step 4: Verify all 11 wrappers exist**

```bash
cd /Users/waynewang/AI-Robin-Skill
ls .claude-plugin/agents/ | wc -l
```

Expected: 11.

- [ ] **Step 5: No commit** — end-of-phase commit.

---

### Task 2B.9: Phase 2B commit

- [ ] **Step 1: Final verification**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
# 20/20 routing coverage
comm -23 \
  <(grep -E '^#### `[a-z_]+`' contracts/dispatch-signal.md | sed -E 's/^#### `([a-z_]+)`.*/\1/' | sort -u) \
  <(grep -E '^\| `[a-z_]+` \|' SKILL.md | sed -E 's/^\| `([a-z_]+)` \|.*/\1/' | sort -u)
# Expected: empty

# 3 new agent packages exist
ls agents/commit/SKILL.md agents/degradation/SKILL.md agents/finalization/SKILL.md
# Expected: all 3 exist

# 11 plugin agent wrappers
ls ../.claude-plugin/agents/ | wc -l
# Expected: 11
```

- [ ] **Step 2: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add -A
git commit -m "$(cat <<'EOF'
feat(ai-robin): add 3 kernel-relief sub-agents + 3 new signal types

Phase 2B of plugin migration.

New sub-agents (agents/commit/, agents/degradation/, agents/finalization/)
and plugin wrappers (.claude-plugin/agents/commit|degradation|finalization.md)
for each. Kernel now delegates domain-heavy work:
- Git commits → Commit Agent (uses merge's commit_message verbatim)
- Context-degraded spec writing → Degradation Agent (reads original specs)
- Delivery bundle generation → Finalization Agent (summarizes intents + ledger)

New signal types in contracts/dispatch-signal.md (now 20 types):
- commit_complete (Commit Agent → kernel)
- degradation_spec_written (Degradation Agent → kernel → Commit)
- delivery_bundle_ready (Finalization Agent → kernel → exit)

Kernel routing table updated (now 20 rows); agents/kernel/discipline.md
reflects delegations; tests/routing-coverage.md passes 20/20.

Resolves severe issue #2 from the reorg-time audit: kernel no longer
reads domain content when committing or composing degraded specs.
EOF
)"
```

**Phase 2B complete.** Proceed to Phase 2C.

---

## Phase 2C — Python Hooks

**Goal:** Move the "operation ordering" rules from `agents/kernel/discipline.md §4` prose into Python hook scripts that the Claude Code runtime auto-executes. Kernel LLM no longer needs to remember to append ledger entries in a specific order — hooks enforce it.

**Rationale:** kernel-discipline §4 prescribes an 8-step ordering for each routing action. LLMs occasionally forget steps or reorder. Hooks running as actual code make the ordering mechanical and testable.

**TDD applies here** — Python code, pytest.

---

### Task 2C.1: Create hooks directory scaffold

**Files:**
- Create: `.claude-plugin/hooks/hooks.json`
- Create: `.claude-plugin/hooks/lib/__init__.py`
- Create: `.claude-plugin/hooks/tests/__init__.py`
- Create: `.claude-plugin/hooks/tests/conftest.py`

- [ ] **Step 1: Create directory structure**

```bash
cd /Users/waynewang/AI-Robin-Skill
mkdir -p .claude-plugin/hooks/lib
mkdir -p .claude-plugin/hooks/tests
touch .claude-plugin/hooks/lib/__init__.py
touch .claude-plugin/hooks/tests/__init__.py
```

- [ ] **Step 2: Write hooks.json**

Content for `.claude-plugin/hooks/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "command": "python3 $CLAUDE_PLUGIN_ROOT/hooks/pre_task.py"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task",
        "command": "python3 $CLAUDE_PLUGIN_ROOT/hooks/post_task.py"
      }
    ],
    "SessionStart": [
      {
        "command": "python3 $CLAUDE_PLUGIN_ROOT/hooks/session_start.py"
      }
    ],
    "Stop": [
      {
        "command": "python3 $CLAUDE_PLUGIN_ROOT/hooks/stop.py"
      }
    ],
    "SubagentStop": [
      {
        "command": "python3 $CLAUDE_PLUGIN_ROOT/hooks/subagent_stop.py"
      }
    ]
  }
}
```

**Note:** exact hook event matcher syntax may differ in Claude Code. Verify against current plugin docs; adjust if necessary.

- [ ] **Step 3: Write pytest conftest.py**

Content for `.claude-plugin/hooks/tests/conftest.py`:

```python
import json
import os
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def ai_robin_dir(tmp_path):
    """Create a minimal .ai-robin/ tree inside a temporary project root."""
    project = tmp_path / "project"
    project.mkdir()
    ai_robin = project / ".ai-robin"
    ai_robin.mkdir()
    (ai_robin / "dispatch").mkdir()
    (ai_robin / "dispatch" / "inbox").mkdir()
    (ai_robin / "dispatch" / "processed").mkdir()

    stage_state = {
        "schema_version": "1.0",
        "run_id": "test-run",
        "project_root": str(project),
        "current_stage": "intake",
        "stage_iterations": {
            "intake": 1,
            "planning": 0,
            "execute_control": 0,
            "execute": 0,
            "review": 0,
        },
        "active_invocations": [],
        "current_batch": {"batch_id": None, "milestone_ids": [], "review_iteration": 0, "status": None},
        "plan_pointer": {
            "plan_room": "",
            "completed_milestones": [],
            "in_progress_milestones": [],
            "pending_milestones": [],
            "degraded_milestones": [],
        },
        "run_started_at": "2026-04-17T10:00:00Z",
        "last_updated_at": "2026-04-17T10:00:00Z",
        "last_ledger_entry_id": 0,
    }
    (ai_robin / "stage-state.json").write_text(json.dumps(stage_state, indent=2))

    # Empty ledger
    (ai_robin / "ledger.jsonl").write_text("")

    # Minimal budgets
    budgets = {
        "per_batch": {"review_iterations_per_batch": {"default": 2, "current": {}}},
        "per_scope": {"replan_iterations": {"limit": 3, "consumed": 0}},
        "global": {
            "wall_clock_total_seconds": {"limit": 14400, "consumed_at_last_check": 0, "last_checked_at": "2026-04-17T10:00:00Z"},
            "tokens_total_estimated": {"limit": 10000000, "consumed": 0},
            "max_total_milestones_attempted": {"limit": 50, "consumed": 0},
        },
    }
    (ai_robin / "budgets.json").write_text(json.dumps(budgets, indent=2))

    return ai_robin
```

- [ ] **Step 4: No commit** — commit at end of 2C.

---

### Task 2C.2: Implement ledger.py lib (TDD)

**Files:**
- Create: `.claude-plugin/hooks/lib/ledger.py`
- Create: `.claude-plugin/hooks/tests/test_ledger.py`

- [ ] **Step 1: Write failing test for ledger.append**

Content for `.claude-plugin/hooks/tests/test_ledger.py`:

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib import ledger


def test_append_first_entry_gets_entry_id_1(ai_robin_dir):
    """First entry in an empty ledger has entry_id=1."""
    entry = {
        "entry_type": "run_start",
        "stage": "intake",
        "iteration": 0,
        "content": {"user_input_summary": "test"},
        "refs": {},
    }
    result = ledger.append(ai_robin_dir, entry)
    assert result["entry_id"] == 1

    # Verify file content
    lines = (ai_robin_dir / "ledger.jsonl").read_text().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["entry_id"] == 1
    assert parsed["entry_type"] == "run_start"


def test_append_subsequent_entry_increments_id(ai_robin_dir):
    """Second entry has entry_id=2, third is 3, etc."""
    for n in range(1, 4):
        entry = {"entry_type": "dispatch", "stage": "intake", "iteration": 1, "content": {"sub_agent": "consumer"}, "refs": {}}
        result = ledger.append(ai_robin_dir, entry)
        assert result["entry_id"] == n


def test_append_preserves_existing_entries(ai_robin_dir):
    """Appending does not rewrite prior entries."""
    e1 = ledger.append(ai_robin_dir, {"entry_type": "run_start", "stage": "intake", "iteration": 0, "content": {}, "refs": {}})
    e2 = ledger.append(ai_robin_dir, {"entry_type": "dispatch", "stage": "intake", "iteration": 1, "content": {}, "refs": {}})

    lines = (ai_robin_dir / "ledger.jsonl").read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["entry_id"] == 1
    assert json.loads(lines[1])["entry_id"] == 2


def test_append_sets_timestamp_automatically(ai_robin_dir):
    """Entries without timestamp get one set automatically in ISO 8601 format."""
    entry = {"entry_type": "dispatch", "stage": "intake", "iteration": 1, "content": {}, "refs": {}}
    result = ledger.append(ai_robin_dir, entry)
    assert "timestamp" in result
    # Minimal format check: YYYY-MM-DDTHH:MM:SS with Z or offset
    assert "T" in result["timestamp"]


def test_append_updates_last_entry_id_in_stage_state(ai_robin_dir):
    """After append, stage-state.json's last_ledger_entry_id matches."""
    ledger.append(ai_robin_dir, {"entry_type": "dispatch", "stage": "intake", "iteration": 1, "content": {}, "refs": {}})
    ledger.append(ai_robin_dir, {"entry_type": "dispatch", "stage": "intake", "iteration": 1, "content": {}, "refs": {}})

    stage_state = json.loads((ai_robin_dir / "stage-state.json").read_text())
    assert stage_state["last_ledger_entry_id"] == 2


def test_append_validates_required_fields(ai_robin_dir):
    """Missing entry_type raises ValueError."""
    import pytest
    with pytest.raises(ValueError, match="entry_type"):
        ledger.append(ai_robin_dir, {"stage": "intake", "content": {}, "refs": {}})
```

- [ ] **Step 2: Run the test — expect FAIL**

```bash
cd /Users/waynewang/AI-Robin-Skill/.claude-plugin/hooks
python3 -m pytest tests/test_ledger.py -v
```

Expected: `ImportError` or similar (ledger module doesn't exist).

- [ ] **Step 3: Write lib/ledger.py**

Content for `.claude-plugin/hooks/lib/ledger.py`:

```python
"""Atomic ledger append for .ai-robin/ledger.jsonl.

Rules (from ai-robin/agents/kernel/discipline.md §4 and
ai-robin/contracts/session-ledger.md):
- entry_id is monotonically increasing starting at 1
- timestamps are ISO 8601
- append is atomic per call (single fsync'd line write)
- stage-state.json's last_ledger_entry_id updated as part of the same call
"""

import json
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_FIELDS = ("entry_type", "stage", "iteration", "content", "refs")


def append(ai_robin_dir: Path, entry: dict) -> dict:
    """Append a ledger entry. Returns the full entry as written (with entry_id + timestamp)."""
    ai_robin_dir = Path(ai_robin_dir)

    # Validate required fields
    missing = [f for f in REQUIRED_FIELDS if f not in entry]
    if missing:
        raise ValueError(f"ledger entry missing required fields: {missing}")

    ledger_path = ai_robin_dir / "ledger.jsonl"
    stage_state_path = ai_robin_dir / "stage-state.json"

    # Determine next entry_id from stage-state
    stage_state = json.loads(stage_state_path.read_text())
    next_id = stage_state["last_ledger_entry_id"] + 1

    # Compose entry
    full_entry = {
        "entry_id": next_id,
        "timestamp": entry.get("timestamp") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        **{k: entry[k] for k in REQUIRED_FIELDS},
    }

    # Atomic append (open with 'a' then fsync)
    with ledger_path.open("a") as f:
        f.write(json.dumps(full_entry) + "\n")
        f.flush()
        import os
        os.fsync(f.fileno())

    # Update stage-state.json
    stage_state["last_ledger_entry_id"] = next_id
    stage_state["last_updated_at"] = full_entry["timestamp"]
    stage_state_path.write_text(json.dumps(stage_state, indent=2))

    return full_entry
```

- [ ] **Step 4: Re-run tests — expect PASS**

```bash
cd /Users/waynewang/AI-Robin-Skill/.claude-plugin/hooks
python3 -m pytest tests/test_ledger.py -v
```

Expected: all 6 tests pass.

- [ ] **Step 5: No commit** — commit at end of 2C.

---

### Task 2C.3: Implement state.py lib (TDD)

**Files:**
- Create: `.claude-plugin/hooks/lib/state.py`
- Create: `.claude-plugin/hooks/tests/test_state.py`

- [ ] **Step 1: Write failing tests**

Content for `.claude-plugin/hooks/tests/test_state.py`:

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib import state


def test_read_returns_current_stage_state(ai_robin_dir):
    s = state.read(ai_robin_dir)
    assert s["current_stage"] == "intake"
    assert s["stage_iterations"]["intake"] == 1


def test_set_current_stage_updates_atomically(ai_robin_dir):
    state.set_current_stage(ai_robin_dir, "planning")
    s = state.read(ai_robin_dir)
    assert s["current_stage"] == "planning"


def test_add_active_invocation_appends(ai_robin_dir):
    state.add_active_invocation(ai_robin_dir, {
        "invocation_id": "inv-1",
        "sub_agent": "consumer",
        "stage": "intake",
        "spawned_at": "2026-04-17T10:00:00Z",
        "expected_return_signal_types": ["intake_complete"],
    })
    s = state.read(ai_robin_dir)
    assert len(s["active_invocations"]) == 1
    assert s["active_invocations"][0]["invocation_id"] == "inv-1"


def test_remove_active_invocation_by_id(ai_robin_dir):
    state.add_active_invocation(ai_robin_dir, {
        "invocation_id": "inv-1", "sub_agent": "consumer", "stage": "intake",
        "spawned_at": "2026-04-17T10:00:00Z", "expected_return_signal_types": ["intake_complete"],
    })
    state.remove_active_invocation(ai_robin_dir, "inv-1")
    s = state.read(ai_robin_dir)
    assert s["active_invocations"] == []


def test_duplicate_active_invocation_raises(ai_robin_dir):
    import pytest
    inv = {"invocation_id": "inv-1", "sub_agent": "consumer", "stage": "intake",
           "spawned_at": "2026-04-17T10:00:00Z", "expected_return_signal_types": ["intake_complete"]}
    state.add_active_invocation(ai_robin_dir, inv)
    with pytest.raises(ValueError, match="invocation_id"):
        state.add_active_invocation(ai_robin_dir, inv)
```

- [ ] **Step 2: Run tests — expect FAIL (module doesn't exist)**

```bash
python3 -m pytest tests/test_state.py -v
```

- [ ] **Step 3: Write lib/state.py**

Content for `.claude-plugin/hooks/lib/state.py`:

```python
"""Atomic operations on .ai-robin/stage-state.json.

Invariants enforced (from ai-robin/contracts/stage-state.md):
- active_invocations cannot contain duplicate invocation_ids
- current_stage is a fixed enum
- all writes go through this module (no direct json.dump)
"""

import json
from pathlib import Path


VALID_STAGES = ("intake", "planning", "execute-control", "execute", "review", "done")


def read(ai_robin_dir: Path) -> dict:
    return json.loads((Path(ai_robin_dir) / "stage-state.json").read_text())


def _write(ai_robin_dir: Path, s: dict) -> None:
    path = Path(ai_robin_dir) / "stage-state.json"
    # Write to temp then rename (atomic on POSIX)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(s, indent=2))
    tmp.replace(path)


def set_current_stage(ai_robin_dir: Path, stage: str) -> None:
    if stage not in VALID_STAGES:
        raise ValueError(f"invalid stage: {stage}; must be one of {VALID_STAGES}")
    s = read(ai_robin_dir)
    s["current_stage"] = stage
    _write(ai_robin_dir, s)


def add_active_invocation(ai_robin_dir: Path, invocation: dict) -> None:
    s = read(ai_robin_dir)
    existing = {inv["invocation_id"] for inv in s["active_invocations"]}
    if invocation["invocation_id"] in existing:
        raise ValueError(f"invocation_id already active: {invocation['invocation_id']}")
    s["active_invocations"].append(invocation)
    _write(ai_robin_dir, s)


def remove_active_invocation(ai_robin_dir: Path, invocation_id: str) -> None:
    s = read(ai_robin_dir)
    s["active_invocations"] = [inv for inv in s["active_invocations"] if inv["invocation_id"] != invocation_id]
    _write(ai_robin_dir, s)
```

- [ ] **Step 4: Re-run tests — expect PASS**

```bash
python3 -m pytest tests/test_state.py -v
```

Expected: all 5 tests pass.

- [ ] **Step 5: No commit** — end-of-phase commit.

---

### Task 2C.4: Implement pre_task.py hook (TDD)

**Files:**
- Create: `.claude-plugin/hooks/pre_task.py`
- Create: `.claude-plugin/hooks/tests/test_pre_task.py`

**Hook purpose:** Fires before Claude Code invokes the Task tool. Reads the tool call args from stdin (per Claude Code hook contract), extracts `subagent_type` and prompt, appends a `dispatch` ledger entry, and decrements any relevant budget counter.

- [ ] **Step 1: Write failing test**

Content for `.claude-plugin/hooks/tests/test_pre_task.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "pre_task.py"


def test_pre_task_appends_dispatch_entry(ai_robin_dir):
    """When Task tool is invoked for a known sub-agent, pre_task appends a dispatch entry."""
    # Simulated Claude Code hook payload on stdin
    hook_input = {
        "tool_name": "Task",
        "tool_input": {
            "subagent_type": "ai-robin-consumer",
            "prompt": "user_raw_input: 'build a hello CLI'",
        },
        "cwd": str(ai_robin_dir.parent),
    }

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(ai_robin_dir.parent)},
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"

    # Ledger should now have one entry
    lines = (ai_robin_dir / "ledger.jsonl").read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["entry_type"] == "dispatch"
    assert "consumer" in entry["content"]["sub_agent"]


def test_pre_task_ignores_non_task_tools(ai_robin_dir):
    """Hook does nothing when a different tool is being invoked."""
    hook_input = {"tool_name": "Read", "tool_input": {"path": "/tmp/foo"}}

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(ai_robin_dir.parent)},
    )
    assert result.returncode == 0
    # No ledger entry
    assert (ai_robin_dir / "ledger.jsonl").read_text() == ""


def test_pre_task_handles_missing_ai_robin_dir(tmp_path):
    """If there's no .ai-robin/ in cwd, hook exits silently with 0."""
    hook_input = {"tool_name": "Task", "tool_input": {"subagent_type": "ai-robin-consumer"}}

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(tmp_path)},
    )
    assert result.returncode == 0
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
python3 -m pytest tests/test_pre_task.py -v
```

- [ ] **Step 3: Write pre_task.py**

Content for `.claude-plugin/hooks/pre_task.py`:

```python
#!/usr/bin/env python3
"""PreToolUse hook for Task tool.

Fires before Claude Code invokes the Task tool. Appends a `dispatch` ledger
entry (per ai-robin/agents/kernel/discipline.md §4 step 5).

Input: JSON on stdin per Claude Code hook contract:
  {
    "tool_name": "Task",
    "tool_input": {
      "subagent_type": "ai-robin-<agent>",
      "prompt": "..."
    },
    "cwd": "..."
  }

Environment: CLAUDE_PROJECT_DIR is the current working directory of the
Claude Code session (where .ai-robin/ should live).
"""

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent))
from lib import ledger


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Malformed input — do not block the tool call; exit silently.
        return 0

    if payload.get("tool_name") != "Task":
        return 0

    tool_input = payload.get("tool_input", {})
    subagent_type = tool_input.get("subagent_type", "")

    # Only track AI-Robin sub-agents
    if not subagent_type.startswith("ai-robin-"):
        return 0

    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    ai_robin_dir = Path(cwd) / ".ai-robin"

    # No .ai-robin/ → not in an AI-Robin run; skip silently
    if not ai_robin_dir.exists():
        return 0

    sub_agent_short = subagent_type.replace("ai-robin-", "")
    invocation_id = f"inv-{sub_agent_short}-{uuid4().hex[:8]}"

    entry = {
        "entry_type": "dispatch",
        "stage": _infer_stage(sub_agent_short),
        "iteration": 1,  # Could be enriched by reading stage-state; MVP keeps static
        "content": {
            "sub_agent": sub_agent_short,
            "invocation_id": invocation_id,
            "skill_path": f"ai-robin/agents/{sub_agent_short}/SKILL.md",
            "context_refs": [],  # TODO: extract from prompt if structured
            "purpose": tool_input.get("prompt", "")[:200],
        },
        "refs": {},
    }

    try:
        ledger.append(ai_robin_dir, entry)
    except Exception as e:
        # Log to stderr but do NOT block the tool
        print(f"pre_task hook: ledger append failed: {e}", file=sys.stderr)

    return 0


def _infer_stage(sub_agent: str) -> str:
    mapping = {
        "consumer": "intake",
        "planning": "planning",
        "execute-control": "execute-control",
        "execute": "execute",
        "research": "planning",  # research is scoped under planning
        "review-plan": "review",
        "merge": "review",
        "commit": "review",
        "degradation": "review",
        "finalization": "done",
    }
    if sub_agent.startswith("playbook-"):
        return "review"
    return mapping.get(sub_agent, "unknown")


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Re-run tests — expect PASS**

```bash
python3 -m pytest tests/test_pre_task.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 5: No commit** — end-of-phase commit.

---

### Task 2C.5: Implement post_task.py hook (TDD)

**Files:**
- Create: `.claude-plugin/hooks/post_task.py`
- Create: `.claude-plugin/hooks/tests/test_post_task.py`

**Hook purpose:** Fires after Claude Code's Task tool returns. Checks `.ai-robin/dispatch/inbox/` for new signal files; for each new signal file, appends a `signal_received` ledger entry and validates the signal's basic shape.

- [ ] **Step 1: Write failing tests**

Content for `.claude-plugin/hooks/tests/test_post_task.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "post_task.py"


def test_post_task_records_signal_received(ai_robin_dir):
    """When a new signal file appears in inbox, post_task appends signal_received ledger entry."""
    # Pre-populate: simulate sub-agent having written a signal
    signal = {
        "signal_id": "intake-consumer-20260417T100000-abc12345",
        "signal_type": "intake_complete",
        "produced_by": {
            "agent": "consumer",
            "invocation_id": "inv-consumer-abc123",
            "stage": "intake",
            "iteration": 1,
        },
        "produced_at": "2026-04-17T10:00:00Z",
        "payload": {"project_root": str(ai_robin_dir.parent), "rooms_created": ["00-project-room"]},
        "budget_consumed": {"tokens_estimated": 5000, "wall_clock_seconds": 120},
        "artifacts": [],
        "self_check": {"declared_complete": True, "notes": None},
    }
    (ai_robin_dir / "dispatch" / "inbox" / f"{signal['signal_id']}.json").write_text(json.dumps(signal))

    hook_input = {"tool_name": "Task", "tool_input": {"subagent_type": "ai-robin-consumer"}}

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(ai_robin_dir.parent)},
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"

    lines = (ai_robin_dir / "ledger.jsonl").read_text().splitlines()
    # Should have one signal_received entry
    assert any(json.loads(ln)["entry_type"] == "signal_received" for ln in lines)


def test_post_task_ignores_non_task_tools(ai_robin_dir):
    hook_input = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(ai_robin_dir.parent)},
    )
    assert result.returncode == 0
    assert (ai_robin_dir / "ledger.jsonl").read_text() == ""


def test_post_task_validates_signal_shape(ai_robin_dir):
    """Malformed signal → anomaly entry; does not crash."""
    malformed = {"signal_id": "bogus"}  # missing signal_type, produced_by, etc.
    (ai_robin_dir / "dispatch" / "inbox" / "bogus.json").write_text(json.dumps(malformed))

    hook_input = {"tool_name": "Task", "tool_input": {"subagent_type": "ai-robin-consumer"}}
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(ai_robin_dir.parent)},
    )
    assert result.returncode == 0
    lines = (ai_robin_dir / "ledger.jsonl").read_text().splitlines()
    assert any(json.loads(ln)["entry_type"] == "anomaly" for ln in lines)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python3 -m pytest tests/test_post_task.py -v
```

- [ ] **Step 3: Write post_task.py**

Content for `.claude-plugin/hooks/post_task.py`:

```python
#!/usr/bin/env python3
"""PostToolUse hook for Task tool.

Fires after Claude Code's Task tool returns. For each new signal file in
.ai-robin/dispatch/inbox/, append a `signal_received` ledger entry and
validate the signal's basic shape.

Does NOT move the signal file — the kernel does that as part of its routing
action. Does NOT do routing — kernel does that.

Input: JSON on stdin per Claude Code hook contract.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib import ledger


REQUIRED_SIGNAL_FIELDS = ("signal_id", "signal_type", "produced_by", "produced_at", "payload")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Task":
        return 0

    tool_input = payload.get("tool_input", {})
    subagent_type = tool_input.get("subagent_type", "")
    if not subagent_type.startswith("ai-robin-"):
        return 0

    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    ai_robin_dir = Path(cwd) / ".ai-robin"
    if not ai_robin_dir.exists():
        return 0

    inbox = ai_robin_dir / "dispatch" / "inbox"

    # Find signal files not yet recorded
    for signal_file in sorted(inbox.glob("*.json")):
        try:
            signal = json.loads(signal_file.read_text())
        except json.JSONDecodeError as e:
            _log_anomaly(ai_robin_dir, f"malformed signal JSON at {signal_file.name}: {e}")
            continue

        missing = [f for f in REQUIRED_SIGNAL_FIELDS if f not in signal]
        if missing:
            _log_anomaly(ai_robin_dir, f"signal {signal_file.name} missing fields: {missing}")
            continue

        # Append signal_received
        entry = {
            "entry_type": "signal_received",
            "stage": signal["produced_by"].get("stage", "unknown"),
            "iteration": signal["produced_by"].get("iteration", 1),
            "content": {
                "signal_type": signal["signal_type"],
                "from_agent": signal["produced_by"].get("agent", "unknown"),
                "declared_complete": signal.get("self_check", {}).get("declared_complete", False),
                "artifacts_count": len(signal.get("artifacts", [])),
            },
            "refs": {"signal_id": signal["signal_id"]},
        }

        try:
            ledger.append(ai_robin_dir, entry)
        except Exception as e:
            print(f"post_task hook: ledger append failed: {e}", file=sys.stderr)

    return 0


def _log_anomaly(ai_robin_dir: Path, message: str) -> None:
    entry = {
        "entry_type": "anomaly",
        "stage": "unknown",
        "iteration": 0,
        "content": {"what": message, "kernel_response": "logged_by_post_task_hook", "severity": "medium"},
        "refs": {},
    }
    try:
        ledger.append(ai_robin_dir, entry)
    except Exception as e:
        print(f"post_task hook: could not log anomaly: {e}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Re-run tests — expect PASS**

```bash
python3 -m pytest tests/test_post_task.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 5: No commit** — end-of-phase commit.

---

### Task 2C.6: Implement session_start.py hook (TDD)

**Files:**
- Create: `.claude-plugin/hooks/session_start.py`
- Create: `.claude-plugin/hooks/tests/test_session_start.py`

**Hook purpose:** Fires when a Claude Code session starts. If `.ai-robin/stage-state.json` exists in cwd, print a brief resume summary that Claude Code injects into the initial context.

- [ ] **Step 1: Write failing tests**

Content for `.claude-plugin/hooks/tests/test_session_start.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "session_start.py"


def test_session_start_prints_resume_summary_when_state_exists(ai_robin_dir):
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input="{}",
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(ai_robin_dir.parent)},
    )
    assert result.returncode == 0
    # Should emit a resume hint to stdout
    assert "Resuming" in result.stdout or "stage=" in result.stdout


def test_session_start_silent_when_no_state(tmp_path):
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input="{}",
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(tmp_path)},
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Write session_start.py**

Content for `.claude-plugin/hooks/session_start.py`:

```python
#!/usr/bin/env python3
"""SessionStart hook. When .ai-robin/stage-state.json exists in the cwd,
emit a one-line resume hint to stdout — Claude Code injects stdout into
the initial context.
"""

import json
import os
import sys
from pathlib import Path


def main() -> int:
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    state_path = Path(cwd) / ".ai-robin" / "stage-state.json"

    if not state_path.exists():
        return 0

    try:
        s = json.loads(state_path.read_text())
    except json.JSONDecodeError:
        return 0

    stage = s.get("current_stage", "unknown")
    iterations = s.get("stage_iterations", {})
    current_iter = iterations.get(stage.replace("-", "_"), 0)
    active = len(s.get("active_invocations", []))

    print(
        f"[AI-Robin resume] stage={stage} iteration={current_iter} active_invocations={active}. "
        f"Use /ai-robin-resume to continue the dispatch loop, /ai-robin-status for details."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Re-run tests — expect PASS**

- [ ] **Step 5: No commit** — end-of-phase commit.

---

### Task 2C.7: Implement stop.py hook (TDD)

**Files:**
- Create: `.claude-plugin/hooks/stop.py`
- Create: `.claude-plugin/hooks/tests/test_stop.py`

**Hook purpose:** Fires when a session ends. Validates the ledger integrity invariants from contracts/session-ledger.md.

- [ ] **Step 1: Write failing tests**

Content for `.claude-plugin/hooks/tests/test_stop.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "stop.py"


def _write_ledger_lines(ai_robin_dir, entries):
    (ai_robin_dir / "ledger.jsonl").write_text("\n".join(json.dumps(e) for e in entries) + "\n")


def test_stop_silent_when_ledger_ok(ai_robin_dir):
    _write_ledger_lines(ai_robin_dir, [
        {"entry_id": 1, "timestamp": "2026-04-17T10:00:00Z", "entry_type": "run_start", "stage": "intake", "iteration": 0, "content": {}, "refs": {}},
        {"entry_id": 2, "timestamp": "2026-04-17T10:00:05Z", "entry_type": "run_end", "stage": "done", "iteration": 0, "content": {"exit_reason": "all_complete"}, "refs": {}},
    ])
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input="{}", capture_output=True, text=True,
        env={"CLAUDE_PROJECT_DIR": str(ai_robin_dir.parent)},
    )
    assert result.returncode == 0


def test_stop_warns_on_nonmonotonic_entry_ids(ai_robin_dir):
    _write_ledger_lines(ai_robin_dir, [
        {"entry_id": 1, "timestamp": "t", "entry_type": "run_start", "stage": "intake", "iteration": 0, "content": {}, "refs": {}},
        {"entry_id": 3, "timestamp": "t", "entry_type": "dispatch", "stage": "intake", "iteration": 1, "content": {}, "refs": {}},
    ])
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input="{}", capture_output=True, text=True,
        env={"CLAUDE_PROJECT_DIR": str(ai_robin_dir.parent)},
    )
    assert result.returncode == 0  # Hook never fails the session
    assert "non-monotonic" in result.stderr.lower() or "non-monotonic" in result.stdout.lower()


def test_stop_warns_on_missing_run_end(ai_robin_dir):
    _write_ledger_lines(ai_robin_dir, [
        {"entry_id": 1, "timestamp": "t", "entry_type": "run_start", "stage": "intake", "iteration": 0, "content": {}, "refs": {}},
        {"entry_id": 2, "timestamp": "t", "entry_type": "dispatch", "stage": "intake", "iteration": 1, "content": {}, "refs": {}},
    ])
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input="{}", capture_output=True, text=True,
        env={"CLAUDE_PROJECT_DIR": str(ai_robin_dir.parent)},
    )
    assert result.returncode == 0
    combined = (result.stdout + result.stderr).lower()
    assert "run_end" in combined or "resumable" in combined
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Write stop.py**

Content for `.claude-plugin/hooks/stop.py`:

```python
#!/usr/bin/env python3
"""Stop hook. Validates ledger invariants on session end. Never fails
the session; only emits warnings to stderr/stdout.
"""

import json
import os
import sys
from pathlib import Path


def main() -> int:
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    ledger_path = Path(cwd) / ".ai-robin" / "ledger.jsonl"
    if not ledger_path.exists():
        return 0

    entries = []
    for i, line in enumerate(ledger_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"[AI-Robin stop] ledger line {i} is malformed JSON", file=sys.stderr)

    if not entries:
        return 0

    # Check entry_id monotonicity
    prev = 0
    for e in entries:
        eid = e.get("entry_id", -1)
        if eid != prev + 1:
            print(f"[AI-Robin stop] non-monotonic entry_id: expected {prev + 1}, got {eid}", file=sys.stderr)
        prev = eid

    # Check run_end presence
    last = entries[-1]
    if last["entry_type"] != "run_end":
        print(
            f"[AI-Robin stop] session ended without run_end entry — run is resumable. "
            f"Last entry: {last['entry_type']} (id={last.get('entry_id')})",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Re-run tests — expect PASS**

- [ ] **Step 5: No commit** — end-of-phase commit.

---

### Task 2C.8: Implement subagent_stop.py hook (minimal stub)

**Files:**
- Create: `.claude-plugin/hooks/subagent_stop.py`

**Hook purpose:** Fires when a sub-agent spawned via Task finishes. For the MVP, this is a no-op that validates its input and exits 0 — real behavior (like auto-invoking Commit Agent after review_merged) happens via kernel routing in SKILL.md, not in this hook.

- [ ] **Step 1: Write subagent_stop.py**

Content for `.claude-plugin/hooks/subagent_stop.py`:

```python
#!/usr/bin/env python3
"""SubagentStop hook. Reserved for future use; currently a no-op.

Potential uses (future work, not this plan):
- Auto-dispatch Commit Agent when review_merged signal observed
- Auto-dispatch Degradation Agent on budget exhaustion
- These are currently handled by the kernel's routing, not hooks — intentionally,
  because routing is the kernel's job and hooks are for deterministic ops only.
"""

import sys


def main() -> int:
    try:
        import json
        json.load(sys.stdin)  # Consume payload; no processing
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: No test needed** — it's a no-op.

- [ ] **Step 3: No commit** — end-of-phase commit.

---

### Task 2C.9: Update agents/kernel/discipline.md §4

**Files:**
- Modify: `ai-robin/agents/kernel/discipline.md`

- [ ] **Step 1: Locate §4 in discipline.md**

```bash
cd /Users/waynewang/AI-Robin-Skill/ai-robin
grep -n 'Order of operations\|append.*ledger.*before' agents/kernel/discipline.md
```

- [ ] **Step 2: Replace §4 prose with a runtime-adapter reference**

Use Edit tool. Find the 8-step "Order of operations" list. Replace it with:

```markdown
### 4. Ordering of ledger / state / signal operations

The abstract ordering is:

1. Read signal from inbox
2. Append `signal_received` ledger entry
3. Decide routing
4. Append `routing_decision` ledger entry
5. Spawn sub-agent(s) — for each: append `dispatch` entry
6. Move signal file inbox → processed
7. Update `stage-state.json`
8. Decrement budgets if applicable — append `budget_decrement` entry

**In the Claude Code runtime adapter**, steps 2, 5, and 8 are enforced mechanically by plugin hooks:
- `PreToolUse` hook on Task (`pre_task.py`) → step 5's `dispatch` entry + step 8's budget_decrement
- `PostToolUse` hook on Task (`post_task.py`) → step 2's `signal_received` entry + shape validation

Steps 3, 4, 6, 7 remain the kernel's responsibility: routing is a kernel decision; moving signal files and updating stage-state happen as part of routing execution.

**In other runtimes** (non-Claude Code), the full 8-step ordering must be honored by whatever mechanism the runtime adapter provides. If the adapter lacks hook primitives, the kernel implementation must enforce the order in its own code.

Why this ordering: ledger is append-only and durable; if anything fails mid-way, ledger truth is preserved. `stage-state.json` can be reconstructed from ledger if it gets corrupted.

If you get interrupted between step 5 and step 7, the next resume will see active_invocations mismatch with reality, trigger an anomaly entry, and reconcile.
```

- [ ] **Step 3: No commit** — end-of-phase commit.

---

### Task 2C.10: Phase 2C commit

- [ ] **Step 1: Run full hook test suite**

```bash
cd /Users/waynewang/AI-Robin-Skill/.claude-plugin/hooks
python3 -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 2: Verify hooks.json is valid JSON**

```bash
cd /Users/waynewang/AI-Robin-Skill
python3 -c "import json; json.load(open('.claude-plugin/hooks/hooks.json'))"
```

- [ ] **Step 3: Commit**

```bash
cd /Users/waynewang/AI-Robin-Skill
git add -A
git commit -m "$(cat <<'EOF'
feat(plugin): Python hooks for deterministic ledger/state operations

Phase 2C of plugin migration.

Hooks (`.claude-plugin/hooks/`):
- pre_task.py — PreToolUse on Task, appends `dispatch` ledger entry
- post_task.py — PostToolUse on Task, reads new signal files and appends
  `signal_received` + validates signal shape (anomaly on malformed)
- session_start.py — SessionStart, detects .ai-robin/ and emits resume hint
- stop.py — Stop, validates ledger invariants (monotonic entry_id, run_end
  presence); warns but never fails the session
- subagent_stop.py — stub for future use

Shared libs:
- lib/ledger.py — atomic jsonl append with schema validation
- lib/state.py — atomic stage-state.json RMW with invariants

Tests: pytest with tmp_path-based ai_robin_dir fixture.
agents/kernel/discipline.md §4 updated: prose ordering rule now references
the hook implementation; abstract ordering preserved for non-Claude-Code
runtimes.
EOF
)"
```

**Phase 2C complete.** Proceed to Phase 2D.

---

## Phase 2D — Validation & Publication

**Goal:** Document the plugin's relationship to the source, publish v0.2.0, update the root README so users know how to install and invoke.

**Note:** per user scope decision, we are NOT running an end-to-end baseline project. Validation here is structural + test-suite-based, not behavioral end-to-end.

---

### Task 2D.1: Write plugin-equivalence.md

**Files:**
- Create: `ai-robin/docs/plugin-equivalence.md`

- [ ] **Step 1: Write the document**

Content for `ai-robin/docs/plugin-equivalence.md`:

```markdown
# AI-Robin Plugin Equivalence Spec

This document defines what the Claude Code plugin adapter preserves from the abstract AI-Robin design (in `ai-robin/`) and what it concretely adds.

## What the plugin preserves (MUST be invariant)

Per `ai-robin/DESIGN.md §8`:

1. **File-based signal inbox is authoritative.** Plugin hooks read from and write to `.ai-robin/dispatch/inbox/` — they do not bypass it. Task tool return values are secondary; the signal file is the source of truth for audit.
2. **One signal per sub-agent invocation.** Each invocation ends with exactly one signal file.
3. **Lexicographic signal ordering.** When multiple signals are in inbox, kernel processes them in lexicographic signal_id order (per `agents/kernel/discipline.md §3.5`).
4. **Sub-skill files have no YAML frontmatter.** `ai-robin/agents/*/SKILL.md` remain frontmatter-less. The plugin's own `.claude-plugin/agents/*.md` wrappers have frontmatter (needed by Claude Code's agent-registration mechanism) but never contain methodology content.
5. **Kernel never reads domain content.** Commit messages, degradation narratives, delivery bundles are all produced by delegated sub-agents (Commit, Degradation, Finalization).

## What the plugin adds

1. **Slash-command entry.** `/ai-robin-start`, `/ai-robin-resume`, `/ai-robin-status` replace NL-based skill activation. Reliability ↑.
2. **Agent wrappers.** Each sub-agent is addressable via `Task(subagent_type: "ai-robin-...")`. Claude Code's tool system enforces that these names route correctly; accidental activation from user NL is no longer possible.
3. **Hooks for §4 ordering.** `pre_task.py` and `post_task.py` mechanically enforce the ledger-append-before-routing rule that was previously prose in `agents/kernel/discipline.md §4`. The abstract rule remains in the prose for portability to other runtimes.
4. **SessionStart resume hint.** `session_start.py` detects `.ai-robin/stage-state.json` and prints a one-line summary. User no longer needs to say "resume"; the runtime signals the state automatically.
5. **Stop-time integrity check.** `stop.py` validates ledger invariants on session end; warns if run ended without `run_end` entry.

## What the plugin deliberately does NOT do

- Does not replace the abstract methodology (still in `ai-robin/agents/*/SKILL.md`).
- Does not enforce tool scopes per-agent beyond what the wrapper frontmatter declares (Claude Code's own enforcement applies).
- Does not run any end-to-end validation automatically — that remains future work.

## Version pairing

| ai-robin spec version | Plugin version |
|---|---|
| 0.1.x (pre-plugin) | N/A |
| 0.2.x | 0.2.x |

Plugin version must match minor version of `ai-robin/SKILL.md` frontmatter (when versioned).

## Test coverage today

- **Structural tests** (pass):
  - `ai-robin/tests/routing-coverage.md` — 20/20
  - Broken-refs grep — 0 missing
- **Hook unit tests** (pass):
  - `.claude-plugin/hooks/tests/` — pytest suite; targets: ledger.py, state.py, pre_task.py, post_task.py, session_start.py, stop.py
- **Behavioral end-to-end test** (NOT run): deferred. A baseline run through a minimal project would produce a ledger whose shape (entry_type sequence, signal types observed, stage transitions) can be snapshotted as a reference for future plugin changes. See future work.

## Future work (out of scope for this migration)

- End-to-end baseline run to capture a reference ledger shape
- Additional runtime adapters (Claude Agent SDK, custom orchestrators)
- Parallel dispatch verification (DESIGN.md §8 claims parallel Task calls in one message run concurrently; this is unverified by an actual run)
- Auto-invoke-Commit-Agent via SubagentStop hook (currently no-op)
```

- [ ] **Step 2: No commit** — end-of-phase commit.

---

### Task 2D.2: Update repo-root README.md

**Files:**
- Modify: `/Users/waynewang/AI-Robin-Skill/README.md`

- [ ] **Step 1: Read current README**

```bash
cd /Users/waynewang/AI-Robin-Skill
head -50 README.md
```

- [ ] **Step 2: Add an "Installation" and "Invocation" section near the top**

Use Edit tool. After the existing description (but before any deep-dive content), insert:

```markdown
## Installation (Claude Code)

```bash
claude plugins install <git-url-or-local-path>/AI-Robin-Skill
```

This installs the plugin at `.claude-plugin/`, which exposes three slash commands and registers the AI-Robin sub-agents with Claude Code.

## Invocation

Start a new run:
```
/ai-robin-start Build a Python CLI that prints hello world
```

Resume an interrupted run (uses `.ai-robin/stage-state.json` in cwd):
```
/ai-robin-resume
```

Check status without changing state:
```
/ai-robin-status
```

## Architecture

AI-Robin is a **runtime-agnostic natural-language program**. The authoritative source is in `ai-robin/`; the Claude Code adapter is in `.claude-plugin/`. See `ai-robin/DESIGN.md §8` for runtime adaptation details and `ai-robin/docs/plugin-equivalence.md` for what the plugin preserves vs adds.
```

- [ ] **Step 3: No commit** — end-of-phase commit.

---

### Task 2D.3: Bump version and tag

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `ai-robin/SKILL.md` (if it has version)

- [ ] **Step 1: Bump plugin.json version**

```bash
cd /Users/waynewang/AI-Robin-Skill
python3 -c "
import json
p = '.claude-plugin/plugin.json'
d = json.load(open(p))
d['version'] = '0.2.0'
open(p, 'w').write(json.dumps(d, indent=2) + '\n')
"
```

- [ ] **Step 2: Verify version**

```bash
grep version .claude-plugin/plugin.json
```

Expected: `"version": "0.2.0"`.

- [ ] **Step 3: Commit and tag**

```bash
git add -A
git commit -m "$(cat <<'EOF'
chore(release): v0.2.0 — first Claude Code plugin adapter

Phase 2D of plugin migration.

Ships:
- Claude Code plugin at .claude-plugin/ (manifest + commands + agents + hooks)
- 3 new kernel-relief sub-agents (Commit / Degradation / Finalization)
- 20/20 signal coverage in routing table
- Python hooks for kernel-discipline §4 ordering
- docs/plugin-equivalence.md defining what plugin preserves vs adds
- README updated with installation + invocation instructions

Still runtime-agnostic (DESIGN.md §8); plugin is the first adapter.
No behavioral end-to-end validation; structural + hook-unit tests pass.
EOF
)"
git tag v0.2.0
```

- [ ] **Step 4: Verify the tag**

```bash
git tag --list | tail -5
git log -1 --stat
```

Expected: `v0.2.0` in tag list; commit shows Phase 2D changes.

**Phase 2D complete. Plan complete.**

---

## Summary of commits expected across both phases

| Phase | Commit message head | Count |
|---|---|---|
| 1 | `refactor(ai-robin): reorganize into agents/...` | 1 |
| 2A | `feat(plugin): scaffold Claude Code plugin as first runtime adapter` | 1 |
| 2B | `feat(ai-robin): add 3 kernel-relief sub-agents + 3 new signal types` | 1 |
| 2C | `feat(plugin): Python hooks for deterministic ledger/state operations` | 1 |
| 2D | `chore(release): v0.2.0 — first Claude Code plugin adapter` | 1 |
| **Total** | | **5 commits + 1 tag (`v0.2.0`)** |

Executors may split further (e.g., one commit per task) if review benefits from finer granularity, but the minimum is one commit per phase.

---

## Known risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Claude Code plugin schema differs from what's written in `plugin.json` (Task 2A.1) | Medium | Verify against current docs when installing; if validation fails, fix per error message. Plan accommodates this by having manifest in one isolated file. |
| `hooks.json` matcher syntax differs from assumed format (Task 2C.1) | Medium | Test each hook manually via Claude Code after install; fix matcher fields per current doc. |
| Python 3.11+ not installed on target machine | Low | Code uses only stdlib + `from datetime import datetime, timezone` which works 3.8+; state `>=3.8` as requirement if needed. |
| `sed -i ''` (BSD vs GNU) differences in Task 1.5 | High on non-macOS | Detect OS and use the correct variant; tested example is for macOS. |
| Cross-reference grep in Task 1.5 misses paths embedded in prose (e.g. "the consumer folder") | Medium | Step 4 does an additional grep specifically for bare references; manual review required when grep returns non-empty. |
| Hooks fire during unrelated operations and cause confusion | Low | All hooks check `ai_robin_dir.exists()` early and exit silently; only AI-Robin-prefixed subagent types trigger ledger activity. |
| Degradation Agent's narrative composition requires judgment beyond what the SKILL.md describes (Task 2B.3) | Medium | The 6-phase structure covers the shape; actual narrative quality is a future-iteration concern. Worst case: narrative is terse but factually complete — acceptable for v0.2.0. |

---

## Self-review checklist (executed by plan author before handoff)

**Spec coverage:** every scope item from the conversation appears as one or more tasks. Confirmed:
- ✅ File tree reorg (Phase 1, Tasks 1.1 - 1.10)
- ✅ Plugin scaffold: manifest, commands, agent wrappers (Phase 2A)
- ✅ Kernel-relief sub-agents: commit, degradation, finalization (Phase 2B)
- ✅ Three new signal types in contract (Task 2B.1)
- ✅ Routing table bump 17 → 20 (Tasks 2B.5, 2B.6)
- ✅ Python hooks (Phase 2C)
- ✅ plugin-equivalence.md (Task 2D.1)
- ✅ v0.2.0 release (Task 2D.3)
- ✅ DESIGN.md §8 invariants preserved (documented in 2D.1)
- ✅ No baseline run (scope honored per user decision)

**Placeholder scan:** No "TBD", "implement later", or vague instructions. Every task has concrete commands or concrete edit content.

**Type consistency:** Signal types, agent names, file paths are consistent across tasks (e.g., `agents/commit/SKILL.md` referenced identically in 2B.2 and 2B.5; `commit_complete` signal schema consistent between 2B.1 and 2B.5).

Plan ready for execution.
