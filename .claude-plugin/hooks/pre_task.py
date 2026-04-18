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

This hook MUST NOT block the tool call on any failure. All errors are
logged to stderr but the hook exits 0 so the tool proceeds.
"""

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent))
from lib import ledger


def _infer_stage(sub_agent):
    mapping = {
        "consumer": "intake",
        "planning": "planning",
        "execute-control": "execute-control",
        "execute": "execute",
        "research": "planning",
        "review-plan": "review",
        "merge": "review",
        "commit": "review",
        "degradation": "review",
        "finalization": "done",
    }
    if sub_agent.startswith("playbook-"):
        return "review"
    return mapping.get(sub_agent, "unknown")


def main():
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

    sub_agent_short = subagent_type.replace("ai-robin-", "")
    invocation_id = f"inv-{sub_agent_short}-{uuid4().hex[:8]}"

    entry = {
        "entry_type": "dispatch",
        "stage": _infer_stage(sub_agent_short),
        "iteration": 1,
        "content": {
            "sub_agent": sub_agent_short,
            "invocation_id": invocation_id,
            "skill_path": f"ai-robin/agents/{sub_agent_short}/SKILL.md",
            "context_refs": [],
            "purpose": tool_input.get("prompt", "")[:200],
        },
        "refs": {},
    }

    try:
        ledger.append(ai_robin_dir, entry)
    except Exception as e:
        print(f"pre_task hook: ledger append failed: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
