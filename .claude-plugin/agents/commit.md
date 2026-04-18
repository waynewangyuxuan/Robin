---
name: ai-robin-commit
description: AI-Robin Commit Agent. Executes a git commit using the exact message provided by the trigger signal. Invoked only by the AI-Robin kernel after review_merged or degradation_spec_written.
tools: Read, Bash, Write
---

Read `ai-robin/agents/commit/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
