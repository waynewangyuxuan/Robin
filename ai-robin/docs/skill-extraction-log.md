# Skill Extraction Log

记录 AI-Robin 的哪些文件是从现有外部 skill 抽取 / 改写的，哪些是全新写的。目的是：

1. 后面维护时知道该跟哪个源头对齐
2. 看到 AI-Robin 某个方法论时能回溯到原出处
3. 判断源 skill 更新了之后 AI-Robin 哪里需要跟进

---

## 抽取映射

### 从 Feature Room skills 抽取

Feature Room 不被调用，但方法论抽到 AI-Robin 的 stdlib 和 depth 文件里。

| AI-Robin 文件 | 抽取自 | 抽取内容 |
|---|---|---|
| `stdlib/feature-room-spec.md` | Feature Room 通用 spec 格式 | 7 种 spec type、6 种 state、`spec_id` / `type` / `state` / `intent` / `indexing` / `provenance` / `relations` / `anchors` 字段 |
| `stdlib/confidence-scoring.md` | `random-contexts` skill 的 confidence 表 | 0.0-1.0 scale；per source_type 的 default；低于 0.5 的 filter 规则 |
| `stdlib/anchor-tracking.md` | `commit-sync` skill Phase 2 | anchor 的 file/symbols/line_range/hash；rename/move/stale 检测；stale state 的触发 |
| `agents/execute/context-pulling.md` | `prompt-gen` skill | context 加载规则；state-aware filtering；relations 遍历；什么该 / 不该加载 |
| `agents/execute/commit-preparation.md` | `commit-sync` skill Phase 1-4 | change spec 格式；progress.yaml 更新；commit message 模板 |

**重要**：AI-Robin 不 import 这些 skill。所有上述方法论都用 `nlp-creator` flavor 重写，并适配 "no human after Consumer" 的执行循环——原 skill 里每次询问用户的步骤都拆掉，替换成 agent 的 self-check 或 return signal。

### 从 gstack / 外部 review skills 抽取（future）

Review playbook 计划 build-time 从外部 skill 抽取。当前只有一个：

| AI-Robin 文件 | 抽取自 | 状态 |
|---|---|---|
| `agents/review/playbooks/code-quality/SKILL.md` | 2025 业界 code review checklist（Google、Microsoft、OWASP 的公开 practice，综合多篇 2025 年 blog 文章） | ✅ 已写 |

Planned for future（尚未抽取）：
- frontend-component —— 将从 gstack 前端规则抽取
- frontend-a11y —— 将从 accessibility guidelines（WCAG / ARIA）抽取
- backend-api —— 将从 REST API design + backend conventions 抽取
- db-schema —— 将从 database migration + schema design practice 抽取
- agent-integration —— 将从 LLM application patterns 抽取
- test-coverage —— 将从 testing practice（TDD + test-pyramid）抽取
- spec-anchors —— 会用 AI-Robin 自己的 `stdlib/anchor-tracking.md` 作为 source；专注于 anchor 对齐的审查

### 全新写的（没有明确外部源）

这些内容是 AI-Robin 特有的设计，没有直接的外部 skill 作参考：

| 文件 | 原因 |
|---|---|
| `DESIGN.md` | AI-Robin 整体思路 |
| `SKILL.md` (main agent kernel) | Kernel 模式是 AI-Robin 特有 |
| `agents/kernel/discipline.md` | Main agent 永远 light 的规则 |
| `stdlib/iteration-budgets.md` | Budget 数值和边界 |
| `stdlib/degradation-policy.md` | No-human degradation 是 AI-Robin 特有 |
| `stdlib/state-lifecycle.md` | 扩展了 Feature Room 的 state，加了 `degraded` |
| `contracts/*.md` | 所有 signal / ledger / verdict / stage-state 格式 |
| `agents/consumer/*.md` | Consumer 是 AI-Robin 特有的 stage |
| `agents/planning/*.md` | Planning 是 AI-Robin 特有的 stage（Feature Room 没有单独的 Planning agent） |
| `agents/execute-control/*.md` | 调度层是 AI-Robin 特有 |
| `agents/review/*.md` | Plan-fan-out-merge review 结构是 AI-Robin 特有 |
| `agents/research/SKILL.md` | Research agent 是 AI-Robin 特有；简版，用户自定义 |

### 部分借鉴（不是直接抽取）

- Consumer 的 gap analysis + 替决策填默认的方法（`agents/consumer/phase-2-gap-analysis.md`、`agents/consumer/phase-6-proxy.md`）借鉴了 Feature Room 里 Q&A 穷举 gap 的思路，但具体的五段式 proxy note 和 15 轮交互 budget 是新的。
- Planning 的 contract design 方法论（`agents/planning/contract-design.md`）参考了一般软件工程里"设计 API 契约"的 best practice（exposed / invariants / preconditions 三段式），但作为 AI-Robin 特有的 depth file 写成。
- Execute-Control 的并发规则（`agents/execute-control/concurrency-rules.md`）是在 Feature Room 的 cross-room-conflict-detection 思路基础上扩展了"single-writer rule"、"schema/migration implicit serial"等 AI-Robin 特有的规则。

---

## 源 skill 更新时怎么办

**情况 A：Feature Room 的 spec 格式演化**
例如 Feature Room 加了一个新 spec type 或新 state。
→ 更新 `stdlib/feature-room-spec.md` 和 `stdlib/state-lifecycle.md`。
→ 评估 Consumer / Planning / Execute 是否需要知道新类型。
→ 如果是 state 变化，check 是否影响 context-pulling 的 filter 规则。

**情况 B：commit-sync 的流程变了**
→ 重新 review `agents/execute/commit-preparation.md` 和 `stdlib/anchor-tracking.md`。
→ 注意 AI-Robin 把 git commit 放在 kernel 做、不是 Execute 做，所以流程后半段故意不对齐——不要把 commit-sync 的 Phase 5/6 搬过来。

**情况 C：confidence 标准变了**
→ 更新 `stdlib/confidence-scoring.md`。
→ AI-Robin 加了几个 source_type（planning_derived 等），这些不在原表里，要单独维护。

**情况 D：gstack 里某个 review rule 演化了**
→ 更新对应的 `agents/review/playbooks/*/SKILL.md`。
→ Playbook 之间相对独立，可以单独更。

---

## 为什么不直接 import / call

一个自然的问题：既然方法论是一样的，为什么不让 AI-Robin 直接调 Feature Room 的 skill？

原因：

1. **Human-in-loop 假设冲突**。Feature Room 的每个 skill 都在某一步假设 human 会确认 / 选择 / 回答。AI-Robin 的核心约束是 Consumer 之后没有 human。直接 import 会把 "需要 human" 这个假设带进来，破坏整个设计。

2. **Context 粒度不同**。Feature Room skill 是 session-level（run 一次 room skill 持续整个 feature 的生命周期）。AI-Robin 的 sub-agent 是 invocation-level（一次 spawn 做一件事就结束）。Context 结构、state-holding 方式完全不同。

3. **NLP-creator flavor**。你明确要求 AI-Robin 以 nlp-creator 的风格重写（有 entrypoint、contract、stdlib、per-step autonomy），而不是延续 Feature Room 的叙事性 skill 文档风格。重写是必要的。

所以复用的是**数据格式 + 方法论**，不是可执行 skill。

---

## 更新这个 log

每次从外部 skill 抽取新内容（或者改了现有 mapping），在这个文件里加一条记录。

格式：

```
### YYYY-MM-DD
- 抽取：<新文件> 来自 <源 skill / 文档>
- 内容：<抽取了什么>
- 动机：<为什么抽取>
```
