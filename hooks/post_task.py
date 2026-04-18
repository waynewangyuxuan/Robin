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


def _log_anomaly(ai_robin_dir, message):
    entry = {
        "entry_type": "anomaly",
        "stage": "unknown",
        "iteration": 0,
        "content": {
            "what": message,
            "kernel_response": "logged_by_post_task_hook",
            "severity": "medium",
        },
        "refs": {},
    }
    try:
        ledger.append(ai_robin_dir, entry)
    except Exception as e:
        print(f"post_task hook: could not log anomaly: {e}", file=sys.stderr)


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Task":
        return 0

    tool_input = payload.get("tool_input", {})
    subagent_type = tool_input.get("subagent_type", "")
    if not subagent_type.startswith("robin-"):
        return 0

    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    ai_robin_dir = Path(cwd) / ".ai-robin"
    if not ai_robin_dir.exists():
        return 0

    inbox = ai_robin_dir / "dispatch" / "inbox"

    for signal_file in sorted(inbox.glob("*.json")):
        try:
            signal = json.loads(signal_file.read_text())
        except json.JSONDecodeError as e:
            _log_anomaly(ai_robin_dir, f"malformed signal JSON at {signal_file.name}: {e}")
            continue

        missing = [f for f in REQUIRED_SIGNAL_FIELDS if f not in signal]
        if missing:
            _log_anomaly(
                ai_robin_dir,
                f"signal {signal_file.name} missing required fields: {missing}",
            )
            continue

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


if __name__ == "__main__":
    sys.exit(main())
