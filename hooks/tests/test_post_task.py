"""Tests for .claude-plugin/hooks/post_task.py"""

import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "post_task.py"
PYTHON = sys.executable


def _valid_signal(signal_type="intake_complete"):
    return {
        "signal_id": f"intake-consumer-20260417T100000-abc12345",
        "signal_type": signal_type,
        "produced_by": {
            "agent": "intake",
            "invocation_id": "inv-consumer-abc123",
            "stage": "intake",
            "iteration": 1,
        },
        "produced_at": "2026-04-17T10:00:00Z",
        "payload": {"project_root": "/tmp/project"},
        "budget_consumed": {"tokens_estimated": 5000, "wall_clock_seconds": 120},
        "artifacts": [],
        "self_check": {"declared_complete": True, "notes": None},
    }


def _run(payload, cwd):
    return subprocess.run(
        [PYTHON, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(cwd), "PATH": "/usr/bin:/bin"},
    )


def test_post_task_records_signal_received(ai_robin_dir):
    """When a new signal file appears in inbox, post_task appends signal_received ledger entry."""
    signal = _valid_signal()
    (ai_robin_dir / "dispatch" / "inbox" / f"{signal['signal_id']}.json").write_text(
        json.dumps(signal)
    )

    payload = {"tool_name": "Task", "tool_input": {"subagent_type": "robin-intake"}}
    result = _run(payload, ai_robin_dir.parent)
    assert result.returncode == 0, f"stderr: {result.stderr}"

    lines = (ai_robin_dir / "ledger.jsonl").read_text().splitlines()
    entries = [json.loads(ln) for ln in lines]
    assert any(e["entry_type"] == "signal_received" for e in entries)
    assert any(e["content"]["signal_type"] == "intake_complete" for e in entries)


def test_post_task_ignores_non_task_tools(ai_robin_dir):
    payload = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
    result = _run(payload, ai_robin_dir.parent)
    assert result.returncode == 0
    assert (ai_robin_dir / "ledger.jsonl").read_text() == ""


def test_post_task_ignores_non_ai_robin_subagents(ai_robin_dir):
    payload = {
        "tool_name": "Task",
        "tool_input": {"subagent_type": "general-purpose"},
    }
    result = _run(payload, ai_robin_dir.parent)
    assert result.returncode == 0
    assert (ai_robin_dir / "ledger.jsonl").read_text() == ""


def test_post_task_logs_anomaly_on_malformed_signal(ai_robin_dir):
    """Malformed signal → anomaly entry; does not crash."""
    malformed = {"signal_id": "bogus"}  # missing required fields
    (ai_robin_dir / "dispatch" / "inbox" / "bogus.json").write_text(json.dumps(malformed))

    payload = {"tool_name": "Task", "tool_input": {"subagent_type": "robin-intake"}}
    result = _run(payload, ai_robin_dir.parent)
    assert result.returncode == 0

    lines = (ai_robin_dir / "ledger.jsonl").read_text().splitlines()
    entries = [json.loads(ln) for ln in lines]
    assert any(e["entry_type"] == "anomaly" for e in entries)


def test_post_task_handles_missing_ai_robin_dir(tmp_path):
    payload = {"tool_name": "Task", "tool_input": {"subagent_type": "robin-intake"}}
    result = subprocess.run(
        [PYTHON, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(tmp_path), "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0


def test_post_task_handles_invalid_json_signal_file(ai_robin_dir):
    """Signal file with invalid JSON → anomaly entry."""
    (ai_robin_dir / "dispatch" / "inbox" / "bad.json").write_text("not-json{")
    payload = {"tool_name": "Task", "tool_input": {"subagent_type": "robin-intake"}}
    result = _run(payload, ai_robin_dir.parent)
    assert result.returncode == 0

    lines = (ai_robin_dir / "ledger.jsonl").read_text().splitlines()
    entries = [json.loads(ln) for ln in lines]
    assert any(e["entry_type"] == "anomaly" for e in entries)
