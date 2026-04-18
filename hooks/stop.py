#!/usr/bin/env python3
"""Stop hook.

Validates ledger invariants on session end. Never fails the session; only
emits warnings to stderr/stdout.

Invariants (from contracts/session-ledger.md):
- entry_id is monotonic (+1 per line)
- last entry is either run_end (terminal) or an interruption (resumable)
"""

import json
import os
import sys
from pathlib import Path


def main():
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    ledger_path = Path(cwd) / ".ai-robin" / "ledger.jsonl"
    if not ledger_path.exists():
        return 0

    entries = []
    for i, line in enumerate(ledger_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            print(
                f"[AI-Robin stop] ledger line {i} is malformed JSON",
                file=sys.stderr,
            )

    if not entries:
        return 0

    prev = 0
    for e in entries:
        eid = e.get("entry_id", -1)
        if eid != prev + 1:
            print(
                f"[AI-Robin stop] non-monotonic entry_id: expected {prev + 1}, got {eid}",
                file=sys.stderr,
            )
        prev = eid

    last = entries[-1]
    if last.get("entry_type") != "run_end":
        print(
            f"[AI-Robin stop] session ended without run_end entry — run is resumable. "
            f"Last entry: {last.get('entry_type')} (id={last.get('entry_id')})",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
