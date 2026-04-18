# AI-Robin Plugin (Claude Code adapter)

This directory is the **Claude Code runtime adapter** for AI-Robin. The authoritative source of the AI-Robin NLP is in `../ai-robin/` — this plugin is a thin wrapper that adapts the abstract design to Claude Code's specific primitives (slash commands, subagents, hooks).

## Relationship to source

- **Source of truth:** `../ai-robin/` — runtime-agnostic natural-language program
- **This plugin:** the FIRST runtime adapter (Claude Code). Other adapters (Claude Agent SDK, custom orchestrators) may be added later without changing the source.

Per `../ai-robin/DESIGN.md §8`, the file-based signal inbox at `.ai-robin/dispatch/inbox/` remains the authoritative communication channel even in Claude Code. Plugin hooks enforce ordering rules but do NOT replace the inbox.

## What the plugin provides

1. **Slash commands** (`commands/`): `/robin-start`, `/robin-resume`, `/robin-status`
2. **Agent wrappers** (`agents/`): thin adapters that let Claude Code's Task tool address each AI-Robin sub-agent by name
3. **Hooks** (`hooks/`): Python scripts that automatically append to ledger, move signal files, and validate state — enforcing `kernel-discipline §4` rules so the kernel LLM doesn't have to remember them

## What the plugin does NOT do

- Does not replace the abstract methodology (lives in `../skills/robin-*/SKILL.md`)
- Does not replace the file-based inbox
- Does not enable new capabilities — it only enforces and simplifies the existing design
