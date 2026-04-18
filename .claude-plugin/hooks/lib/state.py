"""Atomic operations on .ai-robin/stage-state.json.

Invariants enforced (from ai-robin/contracts/stage-state.md):
- active_invocations cannot contain duplicate invocation_ids
- current_stage is a fixed enum
- all writes go through this module (no direct json.dump)
- writes are atomic (write to tmp + rename)
"""

import json
from pathlib import Path


VALID_STAGES = ("intake", "planning", "execute-control", "execute", "review", "done")


def read(ai_robin_dir):
    return json.loads((Path(ai_robin_dir) / "stage-state.json").read_text())


def _write(ai_robin_dir, s):
    path = Path(ai_robin_dir) / "stage-state.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(s, indent=2))
    tmp.replace(path)


def set_current_stage(ai_robin_dir, stage):
    if stage not in VALID_STAGES:
        raise ValueError(f"invalid stage: {stage}; must be one of {VALID_STAGES}")
    s = read(ai_robin_dir)
    s["current_stage"] = stage
    _write(ai_robin_dir, s)


def add_active_invocation(ai_robin_dir, invocation):
    s = read(ai_robin_dir)
    existing = {inv["invocation_id"] for inv in s["active_invocations"]}
    if invocation["invocation_id"] in existing:
        raise ValueError(f"invocation_id already active: {invocation['invocation_id']}")
    s["active_invocations"].append(invocation)
    _write(ai_robin_dir, s)


def remove_active_invocation(ai_robin_dir, invocation_id):
    s = read(ai_robin_dir)
    s["active_invocations"] = [
        inv for inv in s["active_invocations"] if inv["invocation_id"] != invocation_id
    ]
    _write(ai_robin_dir, s)
