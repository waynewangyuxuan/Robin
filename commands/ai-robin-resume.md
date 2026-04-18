---
description: Resume an interrupted AI-Robin run
---

You are resuming an AI-Robin run.

**Pre-flight check:**
1. If `.ai-robin/stage-state.json` does not exist: STOP. Tell the user there's no run to resume; suggest `/ai-robin-start` instead.

**If the check passes:**

Load `ai-robin/SKILL.md` and follow its resume protocol from the "Initialization: the first turn" section — read stage-state, identify where the run was when it stopped, handle any active invocations, and continue the dispatch loop.
