---
name: robin-intake
description: AI-Robin Intake Agent. Intake stage — the only sub-agent that interacts with the user. Do not invoke for general intake tasks; only invoke as part of an AI-Robin dispatch loop.
tools: Read, Write, Edit, Glob, Grep, Bash
---

Read `skills/robin-intake/SKILL.md` and follow its instructions. The task specification is in the invocation prompt — it conforms to the Input contract described in that file.

**Bash scope** (Axis 1, `pr_continuation` mode): Bash is granted so Intake can run read-only `git log` / `git diff` / `gh pr view` / `gh issue view` commands when loading existing repo context. Do NOT use Bash for writes — git commits, branch operations, and file edits stay out of scope. File modifications go through Write/Edit; commits are kernel-via-Committer.
