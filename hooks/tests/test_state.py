"""Tests for .claude-plugin/hooks/lib/state.py"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib import state


def test_read_returns_current_stage_state(ai_robin_dir):
    s = state.read(ai_robin_dir)
    assert s["current_stage"] == "intake"
    assert s["stage_iterations"]["intake"] == 1


def test_set_current_stage_updates_atomically(ai_robin_dir):
    state.set_current_stage(ai_robin_dir, "planning")
    s = state.read(ai_robin_dir)
    assert s["current_stage"] == "planning"


def test_set_current_stage_rejects_invalid_stage(ai_robin_dir):
    with pytest.raises(ValueError, match="invalid stage"):
        state.set_current_stage(ai_robin_dir, "bogus")


def test_add_active_invocation_appends(ai_robin_dir):
    state.add_active_invocation(
        ai_robin_dir,
        {
            "invocation_id": "inv-1",
            "sub_agent": "intake",
            "stage": "intake",
            "spawned_at": "2026-04-17T10:00:00Z",
            "expected_return_signal_types": ["intake_complete"],
        },
    )
    s = state.read(ai_robin_dir)
    assert len(s["active_invocations"]) == 1
    assert s["active_invocations"][0]["invocation_id"] == "inv-1"


def test_remove_active_invocation_by_id(ai_robin_dir):
    state.add_active_invocation(
        ai_robin_dir,
        {
            "invocation_id": "inv-1",
            "sub_agent": "intake",
            "stage": "intake",
            "spawned_at": "2026-04-17T10:00:00Z",
            "expected_return_signal_types": ["intake_complete"],
        },
    )
    state.remove_active_invocation(ai_robin_dir, "inv-1")
    s = state.read(ai_robin_dir)
    assert s["active_invocations"] == []


def test_duplicate_active_invocation_raises(ai_robin_dir):
    inv = {
        "invocation_id": "inv-1",
        "sub_agent": "intake",
        "stage": "intake",
        "spawned_at": "2026-04-17T10:00:00Z",
        "expected_return_signal_types": ["intake_complete"],
    }
    state.add_active_invocation(ai_robin_dir, inv)
    with pytest.raises(ValueError, match="invocation_id"):
        state.add_active_invocation(ai_robin_dir, inv)
