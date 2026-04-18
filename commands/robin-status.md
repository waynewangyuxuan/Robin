---
description: Report status of the current AI-Robin run without changing state
---

Do not dispatch any sub-agents. Do not modify any file.

Read `.ai-robin/stage-state.json` and the last N lines of `.ai-robin/ledger.jsonl`. Report to the user:

1. Current stage and iteration number
2. Active invocations (if any)
3. Last ledger entry
4. Any active anomalies from the ledger
5. Current batch status (if `current_batch.batch_id` is not null)
6. Remaining budget snapshot from `.ai-robin/budgets.json`

Keep the report to under 15 lines. Do NOT read spec content or source code — report only kernel-level metadata.
