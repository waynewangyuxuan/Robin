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
