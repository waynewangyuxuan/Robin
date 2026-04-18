"""Tests for .claude-plugin/hooks/pre_task.py"""

import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "pre_task.py"
PYTHON = sys.executable


def _run(payload, cwd):
    return subprocess.run(
        [PYTHON, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(cwd), "PATH": "/usr/bin:/bin"},
    )


def test_pre_task_appends_dispatch_entry(ai_robin_dir):
    """When Task tool is invoked for an AI-Robin sub-agent, pre_task appends a dispatch entry."""
    payload = {
        "tool_name": "Task",
        "tool_input": {
            "subagent_type": "ai-robin-consumer",
            "prompt": "user_raw_input: 'build a hello CLI'",
        },
        "cwd": str(ai_robin_dir.parent),
    }
    result = _run(payload, ai_robin_dir.parent)
    assert result.returncode == 0, f"stderr: {result.stderr}"

    lines = (ai_robin_dir / "ledger.jsonl").read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["entry_type"] == "dispatch"
    assert entry["content"]["sub_agent"] == "consumer"


def test_pre_task_ignores_non_task_tools(ai_robin_dir):
    """Hook does nothing when a different tool is being invoked."""
    payload = {"tool_name": "Read", "tool_input": {"path": "/tmp/foo"}}
    result = _run(payload, ai_robin_dir.parent)
    assert result.returncode == 0
    assert (ai_robin_dir / "ledger.jsonl").read_text() == ""


def test_pre_task_ignores_non_ai_robin_subagents(ai_robin_dir):
    """Hook does nothing for non-AI-Robin subagent types."""
    payload = {
        "tool_name": "Task",
        "tool_input": {"subagent_type": "general-purpose", "prompt": "do something"},
    }
    result = _run(payload, ai_robin_dir.parent)
    assert result.returncode == 0
    assert (ai_robin_dir / "ledger.jsonl").read_text() == ""


def test_pre_task_handles_missing_ai_robin_dir(tmp_path):
    """If there's no .ai-robin/ in cwd, hook exits silently with 0."""
    payload = {
        "tool_name": "Task",
        "tool_input": {"subagent_type": "ai-robin-consumer", "prompt": "x"},
    }
    result = subprocess.run(
        [PYTHON, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(tmp_path), "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0


def test_pre_task_handles_malformed_stdin(ai_robin_dir):
    """Hook does not crash on malformed JSON input."""
    result = subprocess.run(
        [PYTHON, str(HOOK_PATH)],
        input="not-json",
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(ai_robin_dir.parent), "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0
    assert (ai_robin_dir / "ledger.jsonl").read_text() == ""
