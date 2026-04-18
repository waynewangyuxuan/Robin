#!/usr/bin/env python3
"""SessionStart hook.

When .ai-robin/stage-state.json exists in the cwd, emit a one-line resume
hint to stdout — Claude Code injects stdout into the initial context so the
user sees "AI-Robin resume" automatically.

Silent (no output) when:
- No .ai-robin/ directory
- stage-state.json is missing
- stage-state.json is malformed (log to stderr, exit 0)
"""

import json
import os
import sys
from pathlib import Path


def main():
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
    # Handle both "execute-control" (hyphen) and "execute_control" (underscore) keys
    current_iter = iterations.get(stage) or iterations.get(stage.replace("-", "_"), 0)
    active = len(s.get("active_invocations", []))

    print(
        f"[AI-Robin resume] stage={stage} iteration={current_iter} "
        f"active_invocations={active}. Use /ai-robin-resume to continue, "
        f"/ai-robin-status for details."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
