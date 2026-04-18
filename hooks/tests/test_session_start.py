"""Tests for .claude-plugin/hooks/session_start.py"""

import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "session_start.py"
PYTHON = sys.executable


def _run(cwd):
    return subprocess.run(
        [PYTHON, str(HOOK_PATH)],
        input="{}",
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(cwd), "PATH": "/usr/bin:/bin"},
    )


def test_session_start_prints_resume_summary_when_state_exists(ai_robin_dir):
    result = _run(ai_robin_dir.parent)
    assert result.returncode == 0
    assert "AI-Robin resume" in result.stdout or "stage=" in result.stdout


def test_session_start_silent_when_no_state(tmp_path):
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_session_start_silent_when_state_is_malformed(tmp_path):
    ai_robin = tmp_path / ".ai-robin"
    ai_robin.mkdir()
    (ai_robin / "stage-state.json").write_text("not-json{")
    result = _run(tmp_path)
    assert result.returncode == 0
