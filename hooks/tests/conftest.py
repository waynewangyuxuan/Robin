"""Shared pytest fixtures for AI-Robin plugin hook tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def ai_robin_dir(tmp_path):
    """Create a minimal .ai-robin/ tree inside a temporary project root.

    Returns the Path to the .ai-robin/ directory. The project root is at
    `ai_robin_dir.parent` — hooks expect CLAUDE_PROJECT_DIR to point there.
    """
    project = tmp_path / "project"
    project.mkdir()
    ai_robin = project / ".ai-robin"
    ai_robin.mkdir()
    (ai_robin / "dispatch").mkdir()
    (ai_robin / "dispatch" / "inbox").mkdir()
    (ai_robin / "dispatch" / "processed").mkdir()

    stage_state = {
        "schema_version": "1.0",
        "run_id": "test-run",
        "project_root": str(project),
        "current_stage": "intake",
        "stage_iterations": {
            "intake": 1,
            "planning": 0,
            "execute_control": 0,
            "execute": 0,
            "review": 0,
        },
        "active_invocations": [],
        "current_batch": {
            "batch_id": None,
            "milestone_ids": [],
            "review_iteration": 0,
            "status": None,
        },
        "plan_pointer": {
            "plan_room": "",
            "completed_milestones": [],
            "in_progress_milestones": [],
            "pending_milestones": [],
            "degraded_milestones": [],
        },
        "run_started_at": "2026-04-17T10:00:00Z",
        "last_updated_at": "2026-04-17T10:00:00Z",
        "last_ledger_entry_id": 0,
    }
    (ai_robin / "stage-state.json").write_text(json.dumps(stage_state, indent=2))

    # Empty ledger
    (ai_robin / "ledger.jsonl").write_text("")

    # Minimal budgets
    budgets = {
        "per_batch": {
            "review_iterations_per_batch": {"default": 2, "current": {}}
        },
        "per_scope": {"replan_iterations": {"limit": 3, "consumed": 0}},
        "global": {
            "wall_clock_total_seconds": {
                "limit": 14400,
                "consumed_at_last_check": 0,
                "last_checked_at": "2026-04-17T10:00:00Z",
            },
            "tokens_total_estimated": {"limit": 10000000, "consumed": 0},
            "max_total_milestones_attempted": {"limit": 50, "consumed": 0},
        },
    }
    (ai_robin / "budgets.json").write_text(json.dumps(budgets, indent=2))

    return ai_robin
