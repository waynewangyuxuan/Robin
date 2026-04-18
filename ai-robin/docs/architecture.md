# Architecture Reference

一页纸的 AI-Robin 架构图。详细设计见 `DESIGN.md`。

---

## 核心思想

**Human 极度前置，AI 长时间自主 run，human 最后 verify。** Consumer 是唯一 human 交互点；之后所有 stage 都 headless，按 budget 自 run 到完成或 degrade。

类比：P vs NP。Generate 难，verify 便宜。把所有需要 judgment 的事前置到 Consumer，让后面几个小时的 execution 只需要 verify。

---

## 五阶段流水线

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAIN AGENT (Kernel)                          │
│               只做 dispatch、route、commit、degrade                │
│                   context 永远 light                             │
└────┬────────┬─────────┬──────────┬──────────┬───────────────────┘
     │        │         │          │          │
     ▼        ▼         ▼          ▼          ▼
  ┌──────┐ ┌──────┐ ┌────────┐ ┌───────┐ ┌──────────────┐
  │ Con- │ │ Plan-│ │Execute │ │Execute│ │ Review Stage │
  │sumer │ │ning  │ │Control │ │ × N   │ │              │
  └──┬───┘ └──┬───┘ └───┬────┘ └───┬───┘ │ Review-Plan  │
     │        │         │          │     │     │        │
     │        │         │          │     │     ▼        │
     │        │         │          │     │ Playbooks×N  │
     │        │         │          │     │     │        │
     │        │         │          │     │     ▼        │
     │        │         │          │     │   Merge      │
     │        │         │          │     └──────┬───────┘
     ▼        ▼         ▼          ▼            ▼
    Feature Room (on disk, shared substrate)
```

---

## Stage 职责速查

| Stage | 输入 | 输出 | 关键特征 |
|---|---|---|---|
| Consumer | 用户原始 brief | intent / constraint / decision / convention / context 等 spec；完整 Feature Room 骨架 | 唯一和 human 交互的 stage；≤15 轮问答 budget |
| Planning | Consumer 的 specs | 更多 decision spec、contract spec、带 gate 的 milestone 列表 | 最重要的产出是 contract spec（决定并行度） |
| Execute-Control | plan + progress | `dispatch_batch` 信号（这批跑哪些 milestone、并发模式） | 纯 scheduler，无领域判断 |
| Execute × N | 单个 milestone 的 task spec | 代码文件 + anchor 更新 + `change-*.yaml` | 不 commit（kernel 做）；互相不可见 |
| Review | 批次的 change artifacts | merged verdict（pass / pass_with_warnings / fail） | plan-fan-out-merge；main agent 无论结果都 commit |

---

## Main Agent (Kernel) 规则

**做的事**：
- spawn sub-agent
- 读 return signal
- route 到下一个 stage
- 做 git commit（Review 后）
- 写 ledger 条目
- 触发 degradation

**不做的事**：
- 读代码
- 评判 spec 质量
- 决定技术方案
- 任何领域判断

Context 永远保持 light——只保留 stage-state.json 里的极少信息（当前 stage、active sub-agents、剩余 budget）。每次 spawn 都把详细信息放进 dispatch-signal 里传下去，不留在 kernel 的 working memory。

---

## 通信协议：Dispatch Signal

每个 sub-agent return 时写一个 json 到 `.ai-robin/dispatch/inbox/`，main agent 在下一轮读。Signal 的 shape 见 `contracts/dispatch-signal.md`。主要 signal：

| Sub-agent | Return signals |
|---|---|
| Consumer | `intake_complete` / `intake_blocked` |
| Planning | `planning_complete` / `planning_needs_research` / `planning_needs_sub_planning` / `planning_replan_exhausted` |
| Execute-Control | `dispatch_batch` / `all_complete` / `dispatch_exhausted` |
| Execute | `execute_complete` / `execute_failed` |
| Research | `research_complete` / `research_inconclusive` |
| Review-Plan | `review_dispatch` |
| Review playbook | `review_sub_verdict` |
| Merge | `review_merged` |

---

## Budget & Degradation

| 维度 | 默认上限 |
|---|---|
| Consumer 交互轮数 | 15 |
| Review 迭代 per batch | 2 |
| Replan 迭代 per plan | 3 |
| Research 深度 per question | 2 |
| 总 milestone 尝试数 | 50 |

Budget 耗尽时**不 escalate to human**（没 human）：
1. 标该 scope `state: degraded`
2. 写 `context-degraded-*.yaml` 记录为什么
3. 加一条到 `ESCALATIONS.md`
4. 继续其他 scope
5. 最终 delivery 时 human 从 ESCALATIONS.md 看到哪些 scope 没完成

详见 `stdlib/degradation-policy.md`。

---

## 数据持久层：Feature Room

所有 spec 都落盘到 Feature Room 格式的目录。这个格式是从原 Feature Room skill 复用的，不是 AI-Robin 自造的。详见 `stdlib/feature-room-spec.md` 和 `docs/feature-room-mapping.md`。

Spec 7 种类型：intent / decision / constraint / contract / convention / context / change

Spec 6 种 state：draft / active / stale / deprecated / superseded / degraded（最后一个是 AI-Robin 扩展）

每个 spec 有 anchor 指向代码位置，保证 spec 和代码不漂移。

---

## 审计

整个 run 结束后，human verify 时有三个主要工具：

1. **Git log**：每个 batch 一个 commit，commit message 含 batch/stage/review-status
2. **`.ai-robin/ledger.jsonl`**：append-only，记录每个 kernel 决策
3. **Feature Room specs**：每个决策 / contract / change 都有可查 spec，provenance field 说明是谁产出、confidence 多少

Proxy decisions（Consumer 替用户填的）特别标出来，在 intake_complete signal 的 `agent_proxy_decisions` 列表里，每条都有五段式 proxy note 说明 gap / 选择 / 理由 / hint / 什么会改变它。

---

## 要了解更多

| 想了解 | 读 |
|---|---|
| 整体设计思路、thesis、trade-off | `DESIGN.md` |
| 如何作为 user 发起 run | `README.md` |
| Kernel 的行为规范 | `agents/kernel/discipline.md` |
| Spec 数据格式 | `stdlib/feature-room-spec.md` |
| 某个 stage 具体做什么 | `<stage>/SKILL.md` |
| Stage 内某一步的细节 | `<stage>/phases/phase-N-*.md` |
| Stage 的方法论 depth | `<stage>/<topic>.md`（例如 `agents/planning/contract-design.md`） |
