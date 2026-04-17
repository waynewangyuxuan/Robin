# Anchor Tracking

How specs stay aligned with code as code evolves. The mechanism that
keeps the Feature Room from becoming stale documentation.

Used by: Execute Agent (during and after code changes), Review
sub-agents (to verify anchor correctness).

Adapted from Feature Room's `commit-sync` skill Phase 2.

---

## What an anchor is

A spec's `anchors[]` field links the spec to specific code:

```yaml
anchors:
  - file: "src/routes/users/create.ts"
    symbols: ["handleCreateUser"]
    line_range: [45, 134]
    hash: "sha256:abc123..."  # optional; content hash of the anchored region
```

An anchor says: "The claim in this spec is implemented / embodied by
this code location." Without anchors, specs drift into abstract
aspirations. With anchors, the system knows when a spec is about to
become wrong because the code it anchors to has changed.

---

## When to update anchors

### During Execute (Phase 3)

Execute Agent maintains anchors as part of its work. For each spec in
`context_refs`:

#### Scenario 1: File rename or move

Old: `anchors[].file = "src/routes/users.ts"`
Code change: renamed to `src/routes/users/create.ts`

**Action**: update `anchors[].file` to the new path. Keep the anchor;
the spec's claim still holds.

#### Scenario 2: Symbol signature change

Old: `anchors[].symbols = ["handleCreate"]`
Code change: renamed function to `handleCreateUser`

**Action**: update `anchors[].symbols`. Claim still holds if function
does the same thing.

#### Scenario 3: Line range shift

Anchored region's line numbers have shifted because code above it
changed.

**Action**: update `anchors[].line_range`. No semantic change.

#### Scenario 4: Hash changes but behavior intact

Anchor has `hash: "abc123"`; code at that location is the same
function but with different formatting / minor refactor.

**Action**: update `anchors[].hash`. Spec claim still accurate.

#### Scenario 5: Actual behavior change

Code at the anchored location now does something materially different
than what the spec claims.

**Action**: mark the spec `state: stale`. Do NOT update anchors to
pretend alignment. A stale flag tells Review to evaluate whether the
spec needs revision or the code does.

#### Scenario 6: New code, no existing spec anchor

Execute Agent wrote new code that relates to a spec in context_refs,
but the spec had no anchor pointing to this code.

**Action**: add a new anchor to the spec pointing at the new code.

### During Review (verification)

Review sub-agents (especially `spec-anchors` playbook) verify:

- Every spec's anchors point to files that exist
- Symbols referenced in anchors exist in the anchored files
- Line ranges are valid (within file bounds)
- Claims match actual code behavior (when feasible to check)

Failures here are flagged as review issues — typically `quality`
severity, `blocking` if the spec is a contract that downstream code
depends on.

---

## When NOT to update

- **Unchanged spec, unchanged code**: no action.
- **Unrelated file change elsewhere in project**: don't touch this
  spec's anchors.
- **Hash-based drift detection with no structural change**: if you
  compute a new hash but the symbol and line range are stable, update
  the hash; don't mark stale.

---

## Creating anchors

When Planning writes a new contract spec that references code that
doesn't exist yet (Execute will create it), anchor the spec to the
expected file path:

```yaml
anchors:
  - file: "src/routes/users/create.ts"  # doesn't exist yet
    symbols: []  # unknown until Execute writes it
    line_range: null
```

Execute's Phase 3 will fill in symbols and line_range once the file
exists.

---

## Stale detection

A spec is `stale` when its claim is no longer supported by the anchored
code. Three ways to detect:

1. **Explicit Execute-time detection**: Execute knows it changed the
   behavior at that location, marks stale.
2. **Hash mismatch**: if hash was recorded and code at location has
   different content, it's a candidate for stale. Review may verify
   semantic impact.
3. **Review-time detection**: Review sub-agent reads both spec claim
   and code, finds mismatch.

Stale specs are NOT ignored — they're surfaced to the next Planning
iteration (via Review's verdict) for revision or retirement.

---

## What anchors enable

- **Context pulling** (Execute, prompt-gen equivalent): when Execute
  needs to know what specs constrain a given file, it searches for
  specs whose anchors match that file.
- **Drift detection**: automated check for specs pointing to deleted
  files, missing symbols, etc.
- **Cross-room conflict detection** (Review): contracts whose
  anchored files are being modified by unrelated agents trigger
  conflict warnings.
- **Change propagation**: when file X is renamed, all specs with
  anchors to file X can be updated in one sweep.

---

## Anti-patterns

- **Lazy anchor updates**: leaving stale anchors around because "it
  still kind of points the right way". This is how Feature Room
  systems decay — if anchors don't stay accurate, stale detection
  becomes unreliable.
- **Deleting anchors instead of marking stale**: removing an anchor
  to avoid "flagging" the spec is dishonest. The system's integrity
  depends on accurate state.
- **Adding too many anchors**: a spec with 20 anchors is usually
  claiming too much or anchoring at too fine granularity. Prefer 1-3
  anchors per spec, at the right granularity (function or section,
  not individual lines).
- **Anchoring to test files** (usually): anchors should point to the
  production code that embodies the spec, not its tests. Exception:
  test-coverage specs or specs about testing infrastructure.

---

## Format reminder

```yaml
anchors:
  - file: "src/routes/users/create.ts"
    symbols: ["handleCreateUser", "validateCreatePayload"]
    line_range: [45, 134]
    hash: "sha256:abc123..."   # optional
```

Multiple anchors per spec if the spec's claim spans multiple locations.
Most specs have 1-2 anchors.
