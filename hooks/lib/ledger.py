"""Atomic ledger append for .ai-robin/ledger.jsonl.

Rules (from ai-robin/agents/kernel/discipline.md §4 and
ai-robin/contracts/session-ledger.md):
- entry_id is monotonically increasing starting at 1
- timestamps are ISO 8601
- append is atomic per call (single fsync'd line write)
- stage-state.json's last_ledger_entry_id updated as part of the same call
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_FIELDS = ("entry_type", "stage", "iteration", "content", "refs")


def append(ai_robin_dir, entry):
    """Append a ledger entry. Returns the full entry as written (with entry_id + timestamp)."""
    ai_robin_dir = Path(ai_robin_dir)

    missing = [f for f in REQUIRED_FIELDS if f not in entry]
    if missing:
        raise ValueError(f"ledger entry missing required fields: {missing}")

    ledger_path = ai_robin_dir / "ledger.jsonl"
    stage_state_path = ai_robin_dir / "stage-state.json"

    stage_state = json.loads(stage_state_path.read_text())
    next_id = stage_state["last_ledger_entry_id"] + 1

    full_entry = {
        "entry_id": next_id,
        "timestamp": entry.get("timestamp") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        **{k: entry[k] for k in REQUIRED_FIELDS},
    }

    with ledger_path.open("a") as f:
        f.write(json.dumps(full_entry) + "\n")
        f.flush()
        os.fsync(f.fileno())

    stage_state["last_ledger_entry_id"] = next_id
    stage_state["last_updated_at"] = full_entry["timestamp"]
    stage_state_path.write_text(json.dumps(stage_state, indent=2))

    return full_entry
