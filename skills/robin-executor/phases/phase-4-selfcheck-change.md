# Execute Phase 4: Self-check and write change spec

**Autonomy: guided** (self-check); **explicit** (change spec format)

## Self-check first

Before writing the change spec, review your own output:

### Structural checks

1. **Does it compile / parse?** Run the appropriate check for the
   language:
   - TypeScript: `tsc --noEmit`
   - Python: `python -m py_compile` or `mypy` if configured
   - Go: `go build ./...`
   - Rust: `cargo check`
   - JS: parse test via Node or linter

2. **Does it match the contracts?** For each contract in your
   `context_refs`, verify your code implements its declared shape. If
   a contract says an endpoint returns `{ id, email }`, your code
   actually returns that.

3. **Did you stay in scope?** Did you modify files outside
   `scope.files_or_specs`? If so, either revert them or return
   `execute_failed` per Phase 2's rules.

### Behavioral checks

4. **Do your tests pass?** Run the test suite you wrote (if any).

5. **Known issues identified?** Surface anything that works but is
   incomplete or suboptimal. These go in `self_assessment.known_issues`
   in the return signal.

### If self-check catches significant issues

Fix them now rather than surfacing through Review. Review is slower
and more expensive than iteration in Execute.

Exception: if the issue requires changes outside your scope or
capability, put in `known_issues` and let Review decide. Don't fake a
fix.

## Write the change spec

Load `skills/robin-executor/commit-preparation.md`. Produce a `change-*.yaml` spec:

```yaml
spec_id: "change-{YYYYMMDD-HHMMSS}-{batch_id}-{task_id}"
type: change
state: active

intent:
  summary: "{one-line description of what was done}"
  detail: |
    Batch: {batch_id}
    Task: {task_id}
    Milestone: {milestone_id}

    Files created:
    - {path}

    Files modified:
    - {path}: {summary of change}

    Specs updated (anchors):
    - {spec_id}: {anchor change summary}

    Known issues: {self-assessment notes}

indexing:
  type: change
  priority: P1
  layer: task
  domain: "{inferred from scope}"
  tags: ["change", "batch-{batch_id}", "milestone-{milestone_id}"]

provenance:
  source_type: manual_input
  confidence: 1.0
  source_ref: "Execute invocation {invocation_id}"
  produced_by_agent: "execute-{task_id}"
  produced_at: "{timestamp}"

relations:
  - type: relates_to
    ref: "{milestone spec_id or intent spec_id}"

anchors: []
```

Write it to `{scope.room}/specs/`.

## Update progress (partial)

Update the milestone's status in `{scope.room}/progress.yaml`:

- Status: `pending` → `in_progress`

**Do not mark the milestone `completed`.** Only Review can do that. The
milestone stays `in_progress` until Review passes it. If Review fails
and replan happens, it may go back to `pending`.

Add a commit placeholder entry (the actual git hash is added by kernel
post-commit).

## Output

- Change spec written to disk
- Progress.yaml updated with `in_progress` status
- Ready for Phase 5 (emit)
