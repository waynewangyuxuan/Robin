---
name: robin-degrader
description: AI-Robin Degrader Agent. Writes the context-degraded-*.yaml spec with narrative and updates escalation-notice.md. Invoked only by the AI-Robin kernel when a scope is degraded.
tools: Read, Write, Edit, Glob, Grep
---

Read `skills/robin-degrader/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
