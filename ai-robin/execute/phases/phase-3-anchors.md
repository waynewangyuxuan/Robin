# Execute Phase 3: Anchor maintenance

**Autonomy: guided** (per `stdlib/anchor-tracking.md`)

Specs stay useful only if their anchors stay aligned with code. Skipping
this is how spec-code drift starts.

## For each spec you touched

For each spec in your `context_refs` that has `anchors[]`:

- **File path changed (rename/move)** → update the anchor's `file`
  field
- **Anchored symbol's signature changed** → update the anchor's
  `symbols` field
- **Anchored logic changed meaningfully** (different behavior, not just
  refactor) → consider whether the spec is now stale; update
  `state: stale` if the spec's claim is no longer accurate
- **Anchored content hash** (if present) → recompute

## For new code you wrote

- Spec referenced your scope but had no anchor → add one pointing to
  your new code
- Spec had an anchor but your new code is a better match → update to
  point to yours

## Which specs get touched

Typically:

- The milestone's **intent** spec — may gain an anchor to the new code
- **Contract** specs — may need anchor updates if you refactored the
  contract's implementation
- Relevant **decision** specs — if the decision's rationale references
  code that moved

Don't touch unrelated specs — that's out-of-scope.

## When in doubt

If a spec's current anchor no longer matches your code and you're
unsure whether to update or mark stale, default to **update**. The
spec's claim is probably still true; the code just moved.

Mark stale only if you changed the actual behavior the spec claimed
(e.g., an endpoint that used to return X now returns Y). Stale specs
are flagged for Review to evaluate.

## Output

Spec yamls updated with accurate anchors. Feeds Phase 4 (self-check).
