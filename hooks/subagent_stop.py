#!/usr/bin/env python3
"""SubagentStop hook.

Reserved for future use; currently a no-op.

Potential uses (future work, not this plan):
- Auto-dispatch Commit Agent when review_merged signal observed
- Auto-dispatch Degradation Agent on budget exhaustion

These are currently handled by the kernel's routing (SKILL.md routing
table), not hooks — intentionally, because routing is the kernel's job
and hooks are for deterministic ops only.
"""

import json
import sys


def main():
    try:
        json.load(sys.stdin)  # Consume payload; no processing
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
