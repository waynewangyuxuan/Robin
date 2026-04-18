# Dispatch Signal

The structured return object that every sub-agent produces when its work is done.
This is the only mechanism by which sub-agents communicate with the main agent.

One signal per sub-agent invocation. One file per signal. Written to
`.ai-robin/dispatch/inbox/{signal-id}.json`. Main agent picks it up, routes,
then moves to `processed/`.

---

## Schema

```json
{
  "signal_id": "string — unique id: {stage}-{agent-name}-{timestamp}-{shortuuid}",
  "signal_type": "one of the enumerated types below",
  "produced_by": {
    "agent": "string — which sub-agent produced this (e.g. 'consumer', 'planning', 'review-playbook:frontend-component')",
    "invocation_id": "string — matches the invocation id main agent assigned when spawning",
    "stage": "string — which stage this sub-agent was part of",
    "iteration": "integer — which iteration of that stage"
  },
  "produced_at": "ISO 8601 timestamp",
  "payload": {
    "// payload shape depends on signal_type; see per-type sections below": null
  },
  "budget_consumed": {
    "tokens_estimated": "integer — rough token count this sub-agent used",
    "wall_clock_seconds": "integer — how long the sub-agent ran"
  },
  "artifacts": [
    {
      "kind": "'spec' | 'code' | 'document' | 'verdict' | 'findings' | 'plan'",
      "path": "string — filesystem path relative to project root",
      "spec_id": "string — if kind='spec', the spec_id written/updated"
    }
  ],
  "self_check": {
    "declared_complete": "boolean — did the sub-agent believe it finished successfully",
    "notes": "string — optional, the sub-agent's own caveats"
  }
}
```

---

## Signal types

### Stage 0: Intake

#### `intake_complete`
Intake Agent successfully produced a planning-ready spec.

Payload:
```json
{
  "project_root": "string — path where Feature Room was initialized",
  "rooms_created": ["string — list of room ids created or updated"],
  "specs_count": {
    "intent": "integer",
    "constraint": "integer",
    "context": "integer",
    "convention": "integer",
    "decision": "integer"
  },
  "agent_proxy_decisions": [
    {
      "decision_spec_id": "string",
      "reason": "string — why Intake had to decide this on behalf of user"
    }
  ],
  "unresolved_but_deferred": [
    "string — list of things explicitly deferred to later stages with justification"
  ]
}
```

Main agent action: update stage-state to `planning`, spawn Planning Agent.

#### `intake_blocked`
Intake Agent cannot complete intake. This is the only pre-degradation signal
that can occur before intake ends. It means: user is unresponsive or input is
so incomplete that even Intake's decision-proxy rules can't resolve it.

Payload:
```json
{
  "reason": "'user_unresponsive' | 'input_fundamentally_incomplete' | 'conflicting_requirements'",
  "details": "string — what blocked it",
  "partial_spec_path": "string — where the partial work was saved"
}
```

Main agent action: this is the one case where AI-Robin exits without doing work.
Surface the partial spec + reason to user. Do not spawn anything further.

---

### Stage 1: Planning

#### `planning_complete`
Planning Agent produced a plan ready for execution.

Payload:
```json
{
  "plan_room": "string — room id where plan specs live",
  "milestones": [
    {
      "milestone_id": "string",
      "depends_on": ["string — other milestone_ids"],
      "rooms_affected": ["string"],
      "contract_spec_ids": ["string — api contracts defined for this milestone"]
    }
  ],
  "next_batch_suggestion": "string — which milestone(s) to execute first"
}
```

Main agent action: update stage-state to `execute-control`, spawn Scheduler.

#### `planning_needs_research`
Planning is blocked on a question that needs research.

Payload:
```json
{
  "question": "string — what needs to be researched",
  "context": "string — why this matters for planning",
  "depth_hint": "integer — suggested research depth, bounded by research budget"
}
```

Main agent action: spawn Research Agent. When research returns, re-spawn Planning
with findings attached. Keep stage at `planning`.

#### `planning_needs_sub_planning`
Planning scope is too large; a sub-section needs its own planning pass.

Payload:
```json
{
  "sub_scope_description": "string",
  "parent_plan_refs": ["string — spec_ids in parent plan that this sub-plan must honor"]
}
```

Main agent action: spawn a nested Planning Agent with sub-scope. Result merges
back into parent plan.

#### `planning_replan_exhausted`
Planning has been re-invoked too many times on the same issues.

Payload:
```json
{
  "exhausted_budget": "'replan_iterations'",
  "unresolvable_issues": ["string — what planning couldn't fix"],
  "partial_plan_ref": "string — what was achievable gets preserved"
}
```

Main agent action: trigger degradation for these issues, continue with partial
plan for the rest.

---

### Research

#### `research_complete`
Research Agent produced findings.

Payload:
```json
{
  "question_answered": "string — the original question",
  "findings_path": "string — path to findings markdown",
  "confidence": "number 0.0-1.0",
  "follow_up_questions": ["string — questions research surfaced but didn't answer"]
}
```

Main agent action: hand findings back to whichever stage requested the research
(usually Planning). Typically by re-spawning that stage with findings attached.

#### `research_inconclusive`
Research could not produce a confident answer within its budget.

Payload:
```json
{
  "question_answered": "string",
  "best_guess": "string — what the agent thinks is most likely",
  "confidence": "number — below 0.5",
  "reasoning": "string — why confident answer isn't possible"
}
```

Main agent action: pass best_guess to requesting stage, flag in ledger. Requesting
stage decides how to proceed (typically: make decision with best_guess, mark
relevant spec as having low confidence).

---

### Stage 2: Scheduler

#### `dispatch_batch`
Scheduler Agent has decided what to spawn next.

Payload:
```json
{
  "batch_id": "string",
  "tasks": [
    {
      "task_id": "string",
      "scope": {
        "room": "string",
        "milestone": "string",
        "files_or_specs": ["string"]
      },
      "context_refs": ["string — spec_ids the execute agent should load"],
      "depends_on_tasks": ["string — other task_ids that must finish first"]
    }
  ],
  "concurrency_mode": "'parallel' | 'sequential' | 'mixed'",
  "rationale": "string — why this concurrency choice (for ledger)"
}
```

Main agent action: spawn N Execute Agents per the `tasks` list, respecting
`concurrency_mode` and `depends_on_tasks`.

#### `dispatch_exhausted`
Scheduler cannot form a valid batch — typically because plan is inconsistent
or all remaining milestones are blocked.

Payload:
```json
{
  "reason": "'circular_dependencies' | 'blocked_milestones' | 'plan_inconsistent'",
  "details": "string"
}
```

Main agent action: feed back to Planning as a replan trigger (consuming replan
budget).

---

### Stage 3: Execute

#### `execute_complete`
Execute Agent finished its task and produced artifacts.

Payload:
```json
{
  "task_id": "string — matches the task in dispatch_batch",
  "artifacts_summary": {
    "files_created": ["string"],
    "files_modified": ["string"],
    "specs_created": ["string — spec_ids"],
    "specs_updated": ["string — spec_ids"],
    "change_spec_id": "string — the change-*.yaml recording this execution"
  },
  "self_assessment": {
    "declared_complete": "boolean",
    "known_issues": ["string — what the execute agent itself noticed is off"]
  }
}
```

Main agent action: wait until all tasks in this batch return. When all in, spawn
Review-Plan with the batch's combined artifacts.

#### `execute_failed`
Execute Agent could not complete its task (e.g., fundamental ambiguity in the
task spec, or technical blocker).

Payload:
```json
{
  "task_id": "string",
  "reason": "string",
  "partial_artifacts": ["string — anything salvageable"]
}
```

Main agent action: treat as a failed batch, route to Planning for replan
(consumes replan budget). Do not skip review — even a failed task's partial
output may need verdict logging.

---

### Stage 4: Review

#### `review_dispatch`
Review-Plan Agent has determined which playbooks to run.

Payload:
```json
{
  "batch_id": "string — matches the batch being reviewed",
  "playbooks": [
    {
      "playbook_name": "string — e.g. 'code-quality', 'frontend-component'",
      "scope": {
        "files": ["string"],
        "specs": ["string"]
      },
      "severity_focus": "'blocking' | 'quality' | 'advisory'"
    }
  ],
  "rationale": "string — why these playbooks were chosen"
}
```

Main agent action: spawn N review sub-agents per the playbooks list, in parallel.

#### `review_sub_verdict`
One review sub-agent produced its verdict.

Payload:
```json
{
  "playbook_name": "string",
  "batch_id": "string",
  "verdict": {
    "status": "'pass' | 'pass_with_warnings' | 'fail'",
    "issues": [
      {
        "severity": "'blocking' | 'quality' | 'advisory'",
        "location": "string — file:line or spec_id",
        "description": "string",
        "suggested_action": "string"
      }
    ]
  }
}
```

Main agent action: collect. When all review sub-agents for this batch report in,
spawn Merger Agent.

#### `review_merged`
Merger Agent has synthesized all sub-verdicts into one overall decision.

Payload:
```json
{
  "batch_id": "string",
  "overall_status": "'pass' | 'pass_with_warnings' | 'fail'",
  "consolidated_issues": [
    {
      "severity": "string",
      "source_playbooks": ["string"],
      "description": "string"
    }
  ],
  "review_iteration": "integer — 1 or 2 or 3",
  "commit_ready": "boolean — always true; kernel commits regardless",
  "summary": "string — one-paragraph narrative of what was reviewed and the outcome; written by Merger Agent's Phase 4",
  "commit_message": "string — the exact git commit message the kernel uses; Conventional Commits-style header + body; see skills/robin-merger/phases/phase-4-emit.md for format"
}
```

Main agent action:
1. **Spawn Commit Agent** with `trigger_signal_type: 'review_merged'`, passing
   `payload.commit_message` verbatim and the list of files to stage (batch
   artifacts + the verdict record). Do NOT commit directly — Commit Agent does
   that. Wait for `commit_complete`.
2. After `commit_complete` returns: route based on `overall_status`:
   - `pass` or `pass_with_warnings` → signal Scheduler for next batch
   - `fail` + iteration < budget → signal Planning for replan with issues
   - `fail` + iteration >= budget → spawn Degradation Agent

#### `commit_complete`
Commit Agent finished executing a git commit (triggered by either `review_merged`
or `degradation_spec_written`).

Payload:
```json
{
  "batch_id": "string | null — present when commit was triggered by review_merged; null when triggered by degradation",
  "trigger_signal_type": "'review_merged' | 'degradation_spec_written'",
  "trigger_signal_id": "string — the signal_id of the signal whose commit this is",
  "git_hash": "string | null — the SHA of the new commit; null if commit failed",
  "success": "boolean",
  "error": "string | null — error message if success is false",
  "files_committed": "integer",
  "commit_message": "string — verbatim echo of the message actually used, for audit"
}
```

Main agent action: append `commit` ledger entry using the fields in this payload.
Then route per the trigger:
- If `trigger_signal_type == 'review_merged'`: continue the `review_merged`
  routing (next stage per the original verdict — Scheduler on pass,
  Planning on fail-with-budget, Degradation Agent on fail-without-budget).
- If `trigger_signal_type == 'degradation_spec_written'`: continue the dispatch
  loop (typically back to Scheduler to attempt next batch).
- If `success == false`: log `anomaly` entry severity high; continue with the
  routing path as if the commit had happened (commit failure is recorded but
  does not halt the run — kernel never retries commits).

---

### Completion / termination signals

#### `all_complete`
Scheduler or main agent itself determines all plan milestones have been
addressed (passed review, degraded, or explicitly skipped).

Payload:
```json
{
  "summary": {
    "milestones_passed": "integer",
    "milestones_degraded": "integer",
    "total_commits": "integer",
    "wall_clock_total_seconds": "integer"
  },
  "delivery_bundle_path": "string — where to find the final deliverable"
}
```

Main agent action: spawn Finalization Agent with the plan summary. Wait for
`delivery_bundle_ready`. Then append `run_end` ledger entry with
`exit_reason: "all_complete"` and exit the dispatch loop.

#### `delivery_bundle_ready`
Finalization Agent finished generating the delivery bundle.

Payload:
```json
{
  "bundle_path": "string — where the delivery bundle lives on disk (typically .ai-robin/DELIVERY.md)",
  "summary": {
    "milestones_passed": "integer",
    "milestones_degraded": "integer",
    "total_commits": "integer",
    "wall_clock_total_seconds": "integer"
  }
}
```

Main agent action: append `run_end` ledger entry with
`exit_reason: "all_complete"`. Surface `bundle_path` and summary to user on
their next turn. Exit dispatch loop.

#### `degradation_spec_written`
Degradation Agent finished writing the `context-degraded-*.yaml` spec and
updating `escalation-notice.md`.

Payload:
```json
{
  "scope_type": "'batch' | 'milestone' | 'research_question' | 'plan_scope' | 'global'",
  "scope_id": "string — batch_id / milestone_id / question_id / etc.",
  "degraded_spec_id": "string — the context-degraded-*.yaml spec id written",
  "files_to_commit": ["string — absolute paths of files to be staged for the degradation commit"],
  "commit_message": "string — verbatim commit message for Commit Agent to use"
}
```

Main agent action: spawn Commit Agent with
`trigger_signal_type: 'degradation_spec_written'`, passing the `commit_message`
and `files_to_commit` verbatim. Wait for `commit_complete`. Then continue the
dispatch loop (typically back to Scheduler for the next batch).

#### `stage_exhausted`
Generic signal for "this scope's budget ran out and I couldn't do it". Any stage
can produce this as a last-resort signal.

Payload:
```json
{
  "stage": "string",
  "scope_description": "string — what this refers to",
  "budget_type": "'iterations' | 'tokens' | 'wall_clock'",
  "best_partial_state": "string — path or description of partial work preserved"
}
```

Main agent action: degrade this scope (add to escalation-notice), continue other
scopes. Only if ALL remaining scopes are exhausted does the whole run end.

---

## Validation rules

- `signal_id` must be unique within a run. Uniqueness is enforced by the
  producing sub-agent via the `{stage}-{agent}-{timestamp}-{shortuuid}` format.
- `signal_id` is the sort key the kernel uses to order multiple pending
  signals; see `skills/robin-kernel/discipline.md` § "Signal ordering when inbox
  has multiple files".
- `signal_type` must be one of the enumerated values in this document
- `produced_by.invocation_id` must match an invocation main agent actually
  spawned (prevents stray signals from rogue contexts)
- Payload shape must match the signal_type's spec exactly — extra fields are
  allowed, missing required fields are a malformed signal
- `artifacts[].path` must be inside the project root or inside `.ai-robin/`
- `budget_consumed` must be present; if unknown, use best-effort estimates

## When main agent receives a malformed signal

See `skills/robin-kernel/discipline.md` § "Malformed signal protocol". Summary: log to
ledger as anomaly, do not route, consider re-spawning the sub-agent once with
a clarification note. If second attempt also malformed, degrade that scope.

## Example

```json
{
  "signal_id": "review-code-quality-20260416T143022-a3f9",
  "signal_type": "review_sub_verdict",
  "produced_by": {
    "agent": "review-playbook:code-quality",
    "invocation_id": "inv-review-batch-3-cq",
    "stage": "review",
    "iteration": 1
  },
  "produced_at": "2026-04-16T14:30:22Z",
  "payload": {
    "playbook_name": "code-quality",
    "batch_id": "batch-3",
    "verdict": {
      "status": "pass_with_warnings",
      "issues": [
        {
          "severity": "quality",
          "location": "apps/api/src/routes/users.ts:45",
          "description": "Function handleCreate exceeds 80 lines; extractable helper suggested.",
          "suggested_action": "Split validation logic into validateCreatePayload()."
        }
      ]
    }
  },
  "budget_consumed": {
    "tokens_estimated": 4200,
    "wall_clock_seconds": 38
  },
  "artifacts": [
    {
      "kind": "verdict",
      "path": ".ai-robin/dispatch/inbox/review-code-quality-20260416T143022-a3f9.json"
    }
  ],
  "self_check": {
    "declared_complete": true,
    "notes": null
  }
}
```

### Example: `review_merged`

```json
{
  "signal_id": "review-merged-batch3-20260416T144530-c4e2",
  "signal_type": "review_merged",
  "produced_by": {
    "agent": "review-merge",
    "invocation_id": "inv-review-merge-batch-3",
    "stage": "review",
    "iteration": 1
  },
  "produced_at": "2026-04-16T14:45:30Z",
  "payload": {
    "batch_id": "batch-3",
    "review_iteration": 1,
    "overall_status": "pass_with_warnings",
    "consolidated_issues": [
      {
        "severity": "quality",
        "source_playbooks": ["code-quality"],
        "description": "handleCreate exceeds 80 lines; extractable helper suggested."
      }
    ],
    "summary": "Batch 3 reviewed by 3 playbooks. All passed with one quality warning on function length. Ready for commit.",
    "commit_message": "feat(api): implement user CRUD endpoints (batch-3)\n\nReview: pass_with_warnings (iteration 1)\n- 1 quality warning on function length, non-blocking\n\nMilestones: m2-api-endpoints, m3-auth-middleware\nPlaybooks run: code-quality, backend-api, test-coverage",
    "commit_ready": true
  },
  "budget_consumed": {"tokens_estimated": 2100, "wall_clock_seconds": 12},
  "artifacts": [
    {"kind": "verdict", "path": ".ai-robin/dispatch/inbox/review-merged-batch3-20260416T144530-c4e2.json"}
  ],
  "self_check": {"declared_complete": true, "notes": null}
}
```
