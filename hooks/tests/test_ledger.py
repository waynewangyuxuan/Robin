"""Tests for .claude-plugin/hooks/lib/ledger.py"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib import ledger


def test_append_first_entry_gets_entry_id_1(ai_robin_dir):
    """First entry in an empty ledger has entry_id=1."""
    entry = {
        "entry_type": "run_start",
        "stage": "intake",
        "iteration": 0,
        "content": {"user_input_summary": "test"},
        "refs": {},
    }
    result = ledger.append(ai_robin_dir, entry)
    assert result["entry_id"] == 1

    lines = (ai_robin_dir / "ledger.jsonl").read_text().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["entry_id"] == 1
    assert parsed["entry_type"] == "run_start"


def test_append_subsequent_entry_increments_id(ai_robin_dir):
    """Second entry has entry_id=2, third is 3, etc."""
    for n in range(1, 4):
        entry = {
            "entry_type": "dispatch",
            "stage": "intake",
            "iteration": 1,
            "content": {"sub_agent": "intake"},
            "refs": {},
        }
        result = ledger.append(ai_robin_dir, entry)
        assert result["entry_id"] == n


def test_append_preserves_existing_entries(ai_robin_dir):
    """Appending does not rewrite prior entries."""
    ledger.append(
        ai_robin_dir,
        {"entry_type": "run_start", "stage": "intake", "iteration": 0, "content": {}, "refs": {}},
    )
    ledger.append(
        ai_robin_dir,
        {"entry_type": "dispatch", "stage": "intake", "iteration": 1, "content": {}, "refs": {}},
    )

    lines = (ai_robin_dir / "ledger.jsonl").read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["entry_id"] == 1
    assert json.loads(lines[1])["entry_id"] == 2


def test_append_sets_timestamp_automatically(ai_robin_dir):
    """Entries without timestamp get one set automatically in ISO 8601 format."""
    entry = {
        "entry_type": "dispatch",
        "stage": "intake",
        "iteration": 1,
        "content": {},
        "refs": {},
    }
    result = ledger.append(ai_robin_dir, entry)
    assert "timestamp" in result
    assert "T" in result["timestamp"]


def test_append_updates_last_entry_id_in_stage_state(ai_robin_dir):
    """After append, stage-state.json's last_ledger_entry_id matches."""
    ledger.append(
        ai_robin_dir,
        {"entry_type": "dispatch", "stage": "intake", "iteration": 1, "content": {}, "refs": {}},
    )
    ledger.append(
        ai_robin_dir,
        {"entry_type": "dispatch", "stage": "intake", "iteration": 1, "content": {}, "refs": {}},
    )

    stage_state = json.loads((ai_robin_dir / "stage-state.json").read_text())
    assert stage_state["last_ledger_entry_id"] == 2


def test_append_validates_required_fields(ai_robin_dir):
    """Missing entry_type raises ValueError."""
    with pytest.raises(ValueError, match="entry_type"):
        ledger.append(
            ai_robin_dir,
            {"stage": "intake", "iteration": 0, "content": {}, "refs": {}},
        )
