# Feature Room ↔ AI-Robin 映射

AI-Robin 的数据层复用了 Feature Room 的格式。这个文档说明**哪些东西是复用的、哪些是 AI-Robin 扩展的、哪些是明确不复用的**。目的是让熟悉 Feature Room 的人能快速上手 AI-Robin，也让两个系统的 Room 数据能互相读。

---

## 复用（数据格式兼容）

### Spec type

AI-Robin 的 spec 用 Feature Room 的 7 种 type：

| Type | 含义 |
|---|---|
| intent | 目标、要做成什么 |
| decision | 技术选择 |
| constraint | 硬限制 |
| contract | 对外接口 |
| convention | 跨模块约定 |
| context | 背景信息 |
| change | 某次修改的记录 |

AI-Robin 不新增 type。degradation 用 `type: context` 加 tag 表示。

### Spec 字段

`spec_id` / `type` / `state` / `intent` / `indexing` / `provenance` / `relations` / `anchors` —— 字段名和结构与 Feature Room 一致。

### Spec state

AI-Robin 用 Feature Room 的 5 种 state：

- draft / active / stale / deprecated / superseded

并**新增 1 种**：

- **degraded** —— 该 scope 尝试过但未完成，budget 耗尽；保留为历史记录但不 load 给 Execute。

详见 `stdlib/state-lifecycle.md`。

### Room 目录结构

```
META/
├── 00-project-room/
│   ├── room.yaml
│   ├── spec.md
│   ├── progress.yaml
│   ├── _tree.yaml
│   └── specs/
├── 00-ai-robin-plan/          # AI-Robin 特有：Planning workspace
│   ├── room.yaml
│   ├── progress.yaml
│   └── specs/
├── 01-<feature>/
│   ├── room.yaml
│   ├── spec.md
│   ├── progress.yaml
│   └── specs/
└── ...
```

Room 文件结构、`spec.md` 的 Human Projection 渲染、`progress.yaml` 的 milestones / commits 字段 —— 都沿用 Feature Room。

### Anchor

`anchors[]` 的 file / symbols / line_range / hash 字段和 Feature Room 一致。Anchor tracking 的语义（file 移动 / symbol 改名 / stale 判定）也复用。详见 `stdlib/anchor-tracking.md`。

### Confidence

`provenance.confidence` 0.0-1.0 scalar 复用 Feature Room 的 random-contexts confidence 机制。AI-Robin 的 `stdlib/confidence-scoring.md` 扩展了几个 AI-Robin 特有的 source_type（planning_derived、research_derived、degradation_trigger）。

---

## AI-Robin 扩展

### 新 state：`degraded`

Feature Room 没这个概念（因为假设 human 在 loop 里，不会把 scope 扔掉）。AI-Robin 加这个 state 给 graceful degradation 用。不在原系统 read 这个 state 的路径上，所以不会 break 兼容。

### 新 source_type

`provenance.source_type` 扩展了几个值：
- `planning_derived` —— Planning Agent 的技术决策
- `research_derived` —— Research Agent 的发现
- `degradation_trigger` —— 记录 degradation 事件

原 Feature Room 的 source_type（`user_input` / `user_implied` / `agent_proxy` / `prd_extraction` / `chat_extraction` / `anchor_tracking`）都保留。

### 新 relations 类型

Feature Room 的 `relations[].type` 有 `depends_on` / `relates_to` / `supersedes` / `conflicts_with`。AI-Robin 不新增，但用得更严格——Planning 在 replan 时用 `supersedes` 链记录 decision 的演化。

### ai_robin_context 字段

`progress.yaml` 的 commits 条目可以有一个可选的 `ai_robin_context` 字段：

```yaml
ai_robin_context:
  batch_id: batch-3
  stage: execute
  review_status: pass | pass_with_warnings | fail
```

Feature Room 原系统不读这个字段，忽略即可；AI-Robin 用它关联 git commit 到 batch / review。

### 特殊 room：`00-ai-robin-plan/`

Consumer 产出阶段就创建这个 room，作为 Planning 和 Execute-Control 的 workspace。里面放全局 plan 的 progress.yaml、planning 产出的 decision / contract spec 等。

这个 room 在 Feature Room 原系统里不存在，但它只是一个普通 Room，符合 Feature Room 的目录结构规约，所以原系统读它也不会 break——只是看到"一个额外的 room"。

---

## 明确不复用的

这些 Feature Room 的 skill / 流程 AI-Robin **不调用**，而是用 `nlp-creator` flavor 重新写：

| Feature Room skill | AI-Robin 对应 |
|---|---|
| `room-init` | Consumer Phase 7（init-rooms）从零重写 |
| `timeline-init` | 不用；AI-Robin 不跑 timeline |
| `room` | 不用；AI-Robin 不跑 room-level 更新循环 |
| `random-contexts` | 方法论抽到 `stdlib/confidence-scoring.md` |
| `prompt-gen` | 方法论抽到 `execute/context-pulling.md` |
| `commit-sync` | 方法论抽到 `execute/commit-preparation.md` + `stdlib/anchor-tracking.md`；git commit 本身由 kernel 做 |
| `room-status` | 不用；audit 用 ledger + git log |

**为什么不直接 import 这些 skill**：原 skill 的每一步都假设 human 在 loop 里做决策（确认、选择、提问）。AI-Robin 的核心约束是 "no human after Consumer"，所以每个 skill 的交互循环都要拆掉，只留方法论。直接 import 会把 human-in-loop 假设带进来，违背核心设计。

---

## 兼容性保证

你可以在 AI-Robin 跑完后，用 Feature Room 的原 skill（比如 `room` 或 `room-status`）去读 AI-Robin 产出的 Room。原 skill 会看到：

- 标准 spec yaml（7 type，5 state 原系统认识的，1 degraded 不认识但不 break）
- 标准 `spec.md` / `progress.yaml` / `_tree.yaml`
- 额外的 `00-ai-robin-plan/` room（作为普通 Room 被读到）
- commits 里额外的 `ai_robin_context` 字段（原 skill 忽略）

**反向不保证**：AI-Robin 不会从 Feature Room 手动 run 的历史 Room 里 resume。如果要接管一个已有项目，推荐先走一次 AI-Robin Consumer stage 让它建立自己的 `00-ai-robin-plan/`。

---

## 命名风格差异（小心）

- Feature Room 用 "epic room" / "feature room" / "task"
- AI-Robin 用 "room" / "milestone" / "task"

AI-Robin 的 milestone ≈ Feature Room 的 feature-level 计划单元；AI-Robin 的 task ≈ Feature Room 的 task spec（执行层面的单次工作）。

写 spec 的时候，AI-Robin 的 decision / contract / constraint 落在哪个 Room 的判断规则和 Feature Room 一致：
- 跨模块、跨 Room 的 → `00-project-room/specs/`
- 单 Room 内的 → 该 Room 的 `specs/`
- AI-Robin plan 相关的 → `00-ai-robin-plan/specs/`

---

## 版本

当前对齐到：

- Feature Room skills：nlp-creator 里描述的那一版
- AI-Robin：第一版（本次设计）

后续 Feature Room 如果演化了 spec format（例如加新 state 或新 type），AI-Robin 需要同步更新 `stdlib/feature-room-spec.md` 和相关的 state-lifecycle。
