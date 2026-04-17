# Feature Room Spec Format

AI-Robin's data persistence reuses the Feature Room specification format. This
module defines the format as it applies to AI-Robin. For the original
Feature Room system this was extracted from, see `references/feature-room-mapping.md`.

Used by: all sub-agents that produce specs (Consumer, Planning, Research,
Execute, Review sub-agents). Main agent does not produce specs; it only
coordinates agents that do.

---

## Why we reuse this format

Feature Room already provides a well-designed structured representation of
project state: typed spec objects, state lifecycle, anchors to code, provenance
tracking. AI-Robin inherits this format so that:

1. Artifacts produced by AI-Robin are compatible with Feature Room tooling
   (a human using Feature Room can inspect AI-Robin's output natively).
2. We don't reinvent a data model when an existing one is sound.
3. Sub-agents can use existing methodology (anchor tracking, confidence
   scoring, state transitions) that has been tested in practice.

We reuse the **data format**, not the **execution logic**. AI-Robin does not
invoke Feature Room's `commit-sync`, `prompt-gen`, `random-contexts`, etc.
skill implementations. Instead, AI-Robin's stdlib re-implements the relevant
parts of those skills' methodology in AI-Robin's own style (see
`anchor-tracking.md`, `confidence-scoring.md`, etc. — to be written).

---

## Directory structure

AI-Robin expects the project under development to have a Feature Room
structure at `{project_root}/META/` (or similar conventional location). If
the project doesn't have this, Consumer Agent creates it during intake.

```
META/
├── project.yaml                     # Project-level metadata
├── 00-project-room/                 # Root room for project-wide specs
│   ├── _tree.yaml                   # Index of all rooms
│   ├── room.yaml
│   ├── spec.md
│   ├── progress.yaml
│   └── specs/
│       ├── intent-project-001.yaml
│       ├── convention-project-001.yaml
│       └── ...
├── 01-{feature-name}/
│   ├── room.yaml
│   ├── spec.md
│   ├── progress.yaml
│   └── specs/
│       ├── intent-*.yaml
│       ├── contract-*.yaml
│       └── ...
└── ...
```

Additionally, AI-Robin uses a dedicated Room for planning artifacts:

```
META/
└── 00-ai-robin-plan/                # Planning Agent's workspace
    ├── room.yaml
    ├── progress.yaml
    └── specs/
        ├── decision-plan-001.yaml
        ├── contract-api-*.yaml
        └── ...
```

---

## Spec types (the 7)

Every spec has a `type` from this enumeration:

| Type | Semantic | Who produces (in AI-Robin) |
|---|---|---|
| `intent` | "Why are we doing this" / functional goal | Consumer Agent (extracts from user input); Planning may refine |
| `decision` | "We chose A over B because ..." | Planning Agent (technical decisions); Consumer (occasionally, for proxy decisions) |
| `constraint` | "Must / must not / upper bound / lower bound" | Consumer (from user requirements); Planning (derived from architecture) |
| `contract` | "Interface between components" | Planning Agent (primary producer; most important spec for AI-Robin) |
| `convention` | "Team/project-wide rules" | Consumer (if user specifies); Planning (if derived) |
| `context` | "Background information" | Consumer; Research Agent; Planning (as context-degraded) |
| `change` | "A specific change record" | Execute Agent (one per execute completion); Main agent (for degradation commits) |

---

## Spec states

```
draft  ->  active  ->  stale  ->  deprecated
             |
             +----->  superseded (replaced by another spec)
             |
             +----->  degraded (AI-Robin extension: scope was attempted but abandoned)
```

State meanings:

- `draft`: Just created, not yet validated. In original Feature Room, drafts
  await human review. **In AI-Robin, drafts are auto-promoted to active by
  the producing agent when its self-check passes.** This is the key adaptation
  to "no human in the loop after intake". Consumer is the only agent that
  can leave specs in draft state for human review (because Consumer is the
  stage where human IS in the loop).
- `active`: Current, authoritative, used by prompt-gen equivalents.
- `stale`: Linked code has changed in a way that may have invalidated the
  spec. Anchor Tracking module flags this automatically.
- `deprecated`: No longer applicable but kept for history.
- `superseded`: Replaced by a newer spec (referenced in `relations[]`).
- `degraded`: AI-Robin-specific — represents a scope that was attempted but
  could not be completed. See `degradation-policy.md`.

---

## Full spec schema

```yaml
spec_id: "{type}-{scope-slug}-{NNN}"
# Examples:
#   intent-distillation-001
#   contract-api-auth-003
#   context-degraded-batch3-001
# Rules: type must match the `type:` field; scope-slug is short (3-20 chars);
# NNN is zero-padded 3-digit serial within (scope, type).

type: {intent|decision|constraint|contract|convention|change|context}

state: {draft|active|stale|deprecated|superseded|degraded}

intent:
  summary: "{one sentence — the proposition}"
  detail: |
    {multi-line detail: rationale, examples, background.
    Use markdown freely. Cite sources where applicable.}

# Optional — mainly for intents. Lists sub-constraints that narrow this intent.
constraints: []

indexing:
  type: {same as top-level type field}
  priority: {P0|P1|P2}
  layer: {project|epic|feature|task}
  domain: "{short string — e.g. 'auth', 'db', 'api', 'frontend'}"
  tags: ["{short tags for cross-cutting retrieval}"]

provenance:
  source_type: {user_input|prd_extraction|chat_extraction|manual_input|
                agent_proxy|research_derived|planning_derived|anchor_tracking|
                degradation_trigger}
  confidence: {0.0 to 1.0 — see confidence-scoring.md}
  source_ref: "{description of source: 'user message @ 14:32', 'research findings
              research-auth-providers.md', 'planning iter 2 decision', etc.}"
  produced_by_agent: "{agent name, e.g. 'consumer', 'planning-iter2',
                     'research-depth-2'}"
  produced_at: "{ISO 8601 timestamp}"

# Relationships to other specs. Multiple relations allowed.
relations:
  - type: {depends_on|conflicts_with|supersedes|superseded_by|relates_to|
           derived_from}
    ref: "{spec_id of related spec}"
    note: "{optional clarification}"

# Anchors tie specs to code. See anchor-tracking.md.
anchors:
  - file: "{path relative to project root}"
    # Optional:
    symbols: ["{function/class/var name}"]
    line_range: [{start_line}, {end_line}]
    hash: "{content hash for stale detection}"
```

---

## `agent_proxy` source_type (AI-Robin specific)

Original Feature Room does not have `agent_proxy` as a source type. AI-Robin
adds this for a specific case: **Consumer Agent had to make a decision on
behalf of the user because the user's input did not cover it and the gap
couldn't be filled with a reasonable default**.

When this happens:
- Spec's `provenance.source_type: agent_proxy`
- Spec's `provenance.confidence` is moderate (typically 0.6-0.8, representing
  "I'm reasonably sure this is what user would want, but they didn't confirm")
- Spec's `intent.detail` contains a clear "Agent proxy note:" section
  explaining: what gap was filled, what reasoning led to this default, what
  user hints in the input suggested this direction
- All `agent_proxy` specs are listed in the `intake_complete` signal's
  `agent_proxy_decisions` field, so human verifier can quickly audit them

---

## Confidence values

See `confidence-scoring.md` for the complete table. Quick reference:

| Situation | Confidence |
|---|---|
| User directly stated this | 1.0 |
| User stated clearly but with a hint of uncertainty ("I think", "probably") | 0.85 |
| Derived from user statements via clear logical inference | 0.75 |
| Agent proxy decision with strong signal in intake | 0.7 |
| Agent proxy decision with weak signal (filled sensible default) | 0.55-0.65 |
| Research result with clear consensus | 0.85 |
| Research result with partial consensus | 0.65-0.75 |
| Research inconclusive (best guess) | 0.4-0.55 |
| Any spec below 0.5 should be reviewed carefully; sub-agents may choose to
  degrade rather than persist | — |

---

## `change-*.yaml` specs (Execute Agent output)

Change specs record a single execute invocation's output. They're nearly
immutable (rarely edited after creation).

```yaml
spec_id: "change-{YYYYMMDD-HHMMSS}-{batch_id}-{task_id}"
type: change
state: active

intent:
  summary: "{one-line description of what was changed}"
  detail: |
    **Batch**: {batch_id}
    **Task**: {task_id}
    **Milestone**: {milestone_id}
    **Produced by**: execute agent {invocation_id}

    **Files changed**:
    - Created: {list}
    - Modified: {list}
    - Deleted: {list}

    **Specs updated**:
    - {spec_id}: {old_state} -> {new_state}
    - ...

    **Anchors updated**:
    - {spec_id}: {summary of anchor change}
    - ...

    **Execute agent self-assessment**:
    {verbatim from execute_complete.self_assessment}

indexing:
  type: change
  priority: P1
  layer: task
  domain: "{inferred from scope}"
  tags: ["change", "batch-{batch_id}"]

provenance:
  source_type: manual_input
  confidence: 1.0
  source_ref: "Execute agent invocation {invocation_id}"
  produced_by_agent: "execute-{task_id}"
  produced_at: "{timestamp}"

relations:
  - type: relates_to
    ref: "{milestone spec_id}"

anchors: []  # change specs don't have their own anchors; they describe anchor
             # changes in other specs
```

---

## `room.yaml` format

Unchanged from Feature Room:

```yaml
room:
  id: "{room-id}"
  name: "{human-readable name}"
  parent: "{parent room id or null}"
  lifecycle: {planning|backlog|in-dev|done|archived}
  created_at: "{ISO 8601}"
  updated_at: "{ISO 8601}"
  owner: "{string — in AI-Robin, often just 'ai-robin'}"
  contributors: []
  prompt_test:
    passable: {boolean}
    last_tested: "{timestamp or null}"
    token_count: {integer or null}
  depends_on: ["{other room_ids this room depends on}"]
```

---

## `progress.yaml` format

Unchanged from Feature Room. Main additions in AI-Robin:

- `commits[]` includes kernel-generated commits (degradation commits, review
  commits) in addition to feature commits.
- AI-Robin-specific commit messages use the `[ai-robin:{stage}]` prefix so
  they're distinguishable in git log.

```yaml
progress:
  completion: {0.0-1.0}
  milestones:
    - id: "{milestone-id}"
      name: "{name}"
      status: {pending|in_progress|completed|degraded|blocked}
      completed_at: "{timestamp or null}"
      gate: {true|false}
      gate_criteria: "{description if gate=true}"
      evidence: []
  commits:
    - hash: "{git hash}"
      date: "{ISO 8601}"
      message: "{commit message}"
      files_changed: {integer}
      specs_affected: []
      milestones_affected: []
      ai_robin_context:  # optional AI-Robin extension
        batch_id: "{if applicable}"
        stage: "{stage that produced this commit}"
        review_status: "{if this is a review commit}"
```

---

## `spec.md` (the Human Projection)

Feature Room maintains a Markdown aggregation of all spec yamls in a Room.
AI-Robin sub-agents update this file after creating or modifying specs, to
keep human-readable view in sync.

See original Feature Room `room` skill's "spec.md 同步规则" for the format.
AI-Robin inherits the format but automates the sync (no human confirmation
step).

---

## Validation

Sub-agents producing specs should self-check:

1. `spec_id` is unique across the project
2. `type` matches the filename convention (`{type}-*.yaml`)
3. `state` is one of the enum values
4. `anchors[].file` paths exist (or are about-to-exist as declared by
   Execute Agent's plan)
5. `relations[].ref` point to specs that exist
6. `confidence` is in [0.0, 1.0]

Invalid specs are a malformed output and should not be committed. The
producing sub-agent's self-check catches this before returning. If an
invalid spec somehow reaches disk, Review will flag it (code-quality
playbook includes spec validity checks).
