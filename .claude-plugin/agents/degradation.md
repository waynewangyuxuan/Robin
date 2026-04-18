---
name: ai-robin-degradation
description: AI-Robin Degradation Agent. Writes the context-degraded-*.yaml spec with narrative and updates escalation-notice.md. Invoked only by the AI-Robin kernel when a scope is degraded.
tools: Read, Write, Edit, Glob, Grep
---

Read `ai-robin/agents/degradation/SKILL.md` and follow its instructions. The task specification is in the invocation prompt.
