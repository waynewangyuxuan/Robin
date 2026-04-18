"""Tests for .claude-plugin/hooks/stop.py"""

import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "stop.py"
PYTHON = sys.executable


def _write_ledger_lines(ai_robin_dir, entries):
    (ai_robin_dir / "ledger.jsonl").write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n"
    )


def _run(cwd):
    return subprocess.run(
        [PYTHON, str(HOOK_PATH)],
        input="{}",
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(cwd), "PATH": "/usr/bin:/bin"},
    )


def test_stop_silent_when_ledger_ok(ai_robin_dir):
    _write_ledger_lines(
        ai_robin_dir,
        [
            {
                "entry_id": 1,
                "timestamp": "2026-04-17T10:00:00Z",
                "entry_type": "run_start",
                "stage": "intake",
                "iteration": 0,
                "content": {},
                "refs": {},
            },
            {
                "entry_id": 2,
                "timestamp": "2026-04-17T10:00:05Z",
                "entry_type": "run_end",
                "stage": "done",
                "iteration": 0,
                "content": {"exit_reason": "all_complete"},
                "refs": {},
            },
        ],
    )
    result = _run(ai_robin_dir.parent)
    assert result.returncode == 0
    # Well-formed ledger → no warnings
    combined = result.stdout + result.stderr
    assert "non-monotonic" not in combined.lower()


def test_stop_warns_on_nonmonotonic_entry_ids(ai_robin_dir):
    _write_ledger_lines(
        ai_robin_dir,
        [
            {
                "entry_id": 1,
                "timestamp": "t",
                "entry_type": "run_start",
                "stage": "intake",
                "iteration": 0,
                "content": {},
                "refs": {},
            },
            {
                "entry_id": 3,
                "timestamp": "t",
                "entry_type": "dispatch",
                "stage": "intake",
                "iteration": 1,
                "content": {},
                "refs": {},
            },
        ],
    )
    result = _run(ai_robin_dir.parent)
    assert result.returncode == 0
    combined = (result.stdout + result.stderr).lower()
    assert "non-monotonic" in combined


def test_stop_warns_on_missing_run_end(ai_robin_dir):
    _write_ledger_lines(
        ai_robin_dir,
        [
            {
                "entry_id": 1,
                "timestamp": "t",
                "entry_type": "run_start",
                "stage": "intake",
                "iteration": 0,
                "content": {},
                "refs": {},
            },
            {
                "entry_id": 2,
                "timestamp": "t",
                "entry_type": "dispatch",
                "stage": "intake",
                "iteration": 1,
                "content": {},
                "refs": {},
            },
        ],
    )
    result = _run(ai_robin_dir.parent)
    assert result.returncode == 0
    combined = (result.stdout + result.stderr).lower()
    assert "run_end" in combined or "resumable" in combined


def test_stop_silent_when_no_ai_robin_dir(tmp_path):
    result = _run(tmp_path)
    assert result.returncode == 0
    # Empty project → nothing to check
    assert result.stderr.strip() == ""
