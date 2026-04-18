# AI-Robin — Design Document

> An NLP (Natural Language Program) that takes a one-shot human intake and runs
> an autonomous multi-agent workflow to deliver a software project end to end.

---

## 1. Thesis

AI-Robin is built on a single bet:

> **Human思考前置 + AI 长时间 running + Human 后置 verification** 比
> **Human 在每一步做 tactical 决策** 更高产。

这是一个 P-vs-NP 式的直觉：verification 比 generation 便宜。只要前期 intake 做得
足够好，agent framework 在 human 不在场的情况下，是可以把一个项目从 spec 推到
deliverable 的。

AI-Robin 不是一个 helper、不是一个 copilot。它是一个 **batch job**：扔进去一个
需求，几个小时后拿出一个项目。中间没有人。

---

## 2. 核心约束

整套设计由四个硬约束撑起来：

### 约束 1: 只有一次 human 交互

整个 project 的 lifecycle 里，human 只在 **Consumer Agent** 这一个 stage 里出现。
Consumer Agent 结束后，human 就走了，直到最终 verify 项目产出。

这个约束的含义：
- **Consumer Agent 是生死线**。所有可能的决策点、所有可能的 gap、所有模糊性，必须在
  Consumer 阶段被识别、被问清楚、或被 Consumer Agent 代为钉死。
- **后续 agent 没有"停下来问"的 affordance**。它们只有三个出路：自己做决策 / 回到
  前面的 stage re-plan / 触发 graceful degradation（把这部分标为未完成，继续别的）。
- **Planning/Execute/Review 都是自主的**。它们依赖的所有信息必须已经在 Consumer 阶段
  固化到 spec 里。

### 约束 2: Main agent 是 kernel，永远 light

Main agent 只做三件事：
1. **Parse stage transitions**（当前是哪个 stage、下一个是什么）
2. **Spawn sub-agents**（按照 dispatch signal 创建 sub-agent，注入最小必要 context）
3. **Route return signals**（读 sub-agent 的 return，决定下一步）

Main agent **不做领域判断**——不评估代码好不好、不决定研究方向、不合成文档内容。
所有实质工作在 sub-agent 里，main agent 的 context window 永远有余量处理意外。

这个约束的实现方式：
- Sub-agent 不能自己 spawn sub-agent。Sub-agent 通过 **return signal** 告诉 main
  agent "我需要 X"，main agent 负责真正 spawn。
- 所有 state 都在 disk 上（spec yaml、session ledger、progress.yaml）。Main agent
  每次 turn 开始只 load 必要的 state 切片。

### 约束 3: 文档系统复用 Feature Room 的数据格式

AI-Robin 写到 disk 的所有东西，**格式上兼容 Feature Room**：
- Spec 用 Feature Room 的 7 种 type（intent/decision/constraint/contract/convention/
  context/change）+ state 机制（draft/active/stale/deprecated/superseded）+ anchor
  + provenance/confidence。
- Room 目录结构：`room.yaml`、`specs/`、`progress.yaml`、`spec.md`。

但 AI-Robin **不调用** Feature Room 的现有 skill（room-init, commit-sync, prompt-gen
等）。它自己的 stdlib 里抽取了这些 skill 的方法论（anchor tracking、confidence
scoring、state lifecycle 等），用自己的 flavor 重写。

**为什么**：Feature Room 的 skill 假设了 "human 每一步都在线"（比如 commit-sync
Phase 5 "等待用户确认"），这和 AI-Robin 的约束 1 直接冲突。但 Feature Room 的
**数据模型**是优秀的、可复用的，所以格式兼容、执行独立。

### 约束 4: Review 是 domain-specific 的

"Code review" 不是单一 agent 的单一任务。它是 **按 change 性质动态组合**的一组
领域特定 review：
- 前端组件 review（component API、props、a11y、styling convention）
- 后端 API review（endpoint design、error handling、auth）
- DB schema review（索引、约束、迁移策略）
- Agent integration review（prompt quality、tool contract、error recovery）
- Code quality review（可读性、测试、文档）

AI-Robin 的 Review 层是 **plan-then-fan-out** 的结构：
1. **Review-Plan Agent** 看这次 change，决定要 spawn 哪些 review sub-agent
2. Main agent 并行 spawn N 个 review sub-agent，每个带自己的 **playbook**
3. 每个 sub-agent 产出结构化 verdict
4. Merge verdicts，决定 pass / fail

Playbooks 是 **build-time 从外部 skill packages 抽取**的。比如前端 review 的
playbook 是从 gstack 的前端 review skill 抽取、改写成符合 AI-Robin flavor 的
sub-skill。Runtime 不动态加载外部 skill。

---

## 3. 整体架构

### 3.1 Agent 拓扑

```
                    ┌─────────────────┐
                    │   Main Agent    │  Kernel: dispatch + spawn + route
                    │   (永远 light)   │
                    └────────┬────────┘
                             │
        ┌────────┬───────────┼───────────────┬─────────────┐
        │        │           │               │             │
        ▼        ▼           ▼               ▼             ▼
   Consumer  Planning   Execute-Control  Execute Agents  Review Stage
   (一次)     (可多次)    (每个 stage)    (N 个并行)      (plan + fan-out)
                │
                ├──► Research (辅助 sub-agent)
                │
                └──► Sub-Planning (更细粒度 planning)
```

### 3.2 Stage lifecycle

```
[Stage 0: Intake]
  User 扔 raw input
    ↓
  Main agent spawn Consumer Agent
    ↓
  Consumer Agent:
    - 主动穷举决策点
    - 识别 gap、问 user、钉死 decisions
    - 写 spec 到 Room 结构
    - self-review 完整性
    ↓
  return: "intake_complete" + spec-ready-for-planning
    ↓
  Human 此时退出，后续不再 involve

[Stage 1: Planning]
  Main agent spawn Planning Agent
    ↓
  Planning Agent:
    - 读 intake 的 spec
    - 产出 decision/contract/constraint spec
    - 识别模块边界 + API 契约
    - 定义 milestones
    ↓
  return 可能是:
    - "planning_complete" → 进入 Execute-Control
    - "need_research" → main agent spawn Research Agent
    - "need_sub_planning" → main agent spawn sub-planning for specific part
    - "replan_budget_exhausted" → graceful degradation

[Stage 2: Execute-Control]
  Main agent spawn Execute-Control Agent
    ↓
  Execute-Control Agent:
    - 读 plan + 当前 progress
    - 决定这一批要 spawn 几个 Execute Agent、各自 scope
    - 判断并发度（按 depends_on 和 contract 约束）
    ↓
  return: "dispatch_batch" + [task specs for N execute agents]

[Stage 3: Execute]
  Main agent spawn N × Execute Agent (并行或串行，按 Execute-Control 指令)
    ↓
  每个 Execute Agent:
    - 拉自己 scope 内的 context
    - 执行代码任务
    - 产出代码 + spec updates + change record
    ↓
  return: "execute_complete" + artifacts reference

[Stage 4: Review]
  所有 Execute Agent 都结束后，main agent spawn Review-Plan Agent
    ↓
  Review-Plan Agent:
    - 看 change 性质
    - 决定 spawn 哪些 review sub-agent
    ↓
  return: "review_dispatch" + [review playbook names]
    ↓
  Main agent spawn N × Review Sub-Agent (并行)
    ↓
  每个 Review Sub-Agent 读自己的 playbook + 相关 change，产出 verdict
    ↓
  Main agent 调用 Review-Merge 合并 verdicts
    ↓
  【强制 commit】无论 pass/fail，这次 review 的结果都写入 ledger
    ↓
  return 可能是:
    - "all_pass" → 回 Stage 2 继续下一个 batch
    - "has_issues" + 第 1 次 → 整理 issues，回 Stage 1 re-plan
    - "has_issues" + 第 2 次 → 再 re-plan + execute + review 一次
    - "has_issues" + 第 3 次 → 降级，标为 known issue，继续其他 batch

[Stage Done]
  所有 milestone 完成（或超 budget）
    ↓
  生成交付包: 代码 + spec 完整状态 + session ledger + 未完成说明(如有)
    ↓
  Human 回来做 final verification
```

### 3.3 Return signals

每个 sub-agent 只能通过 **return 一个结构化 signal** 和 main agent 通信。Main
agent 根据 signal type 决定下一步。

Sub-agent **不能**：
- 自己 spawn 其他 sub-agent
- 读其他 sub-agent 的 in-progress 输出
- 直接修改 session ledger（main agent 负责 append）

Sub-agent **必须**：
- 产出一个符合 `contracts/dispatch-signal.md` 的 return object
- 把所有 artifacts 写到约定路径（符合 Feature Room 的 Room 结构）
- 在 return 前写一个 session-ledger entry

---

## 4. 目录结构

```
ai-robin/
├── SKILL.md                              # kernel entrypoint (routing table)
├── DESIGN.md                             # 本文档
├── SUMMARY.md
├── contracts/                            # 数据契约
│   ├── dispatch-signal.md                # Sub-agent return 给 main agent 的 signal
│   ├── session-ledger.md                 # Append-only 决策日志的格式
│   ├── stage-state.md                    # 当前 stage 的状态表示
│   ├── review-verdict.md                 # Review sub-agent 的统一输出
│   └── escalation-notice.md              # 降级时写入交付包的"未完成说明"
├── agents/                               # 所有 agent 的 package
│   ├── kernel/                           # Main agent 的内部资源
│   │   └── discipline.md                 # Main agent 作为 kernel 的行为规范
│   ├── consumer/                         # Stage 0
│   │   ├── SKILL.md
│   │   ├── decision-taxonomy.md          # 项目类型 → 必须决策点
│   │   ├── question-prioritization.md    # 交互预算 + 问题排序
│   │   ├── completeness-check.md         # Return 前的 self-review
│   │   └── phases/
│   ├── planning/                         # Stage 1
│   │   ├── SKILL.md
│   │   ├── contract-design.md            # 怎么设计模块间 API 契约
│   │   ├── parallelism-identification.md # 识别可并行边界
│   │   ├── replan-protocol.md            # 收到 Review fail 怎么 incremental re-plan
│   │   └── phases/
│   ├── research/                         # Planning 辅助
│   │   └── SKILL.md
│   ├── execute-control/                  # Stage 2
│   │   ├── SKILL.md
│   │   ├── concurrency-rules.md
│   │   └── phases/
│   ├── execute/                          # Stage 3
│   │   ├── SKILL.md
│   │   ├── context-pulling.md            # (build-time from prompt-gen)
│   │   ├── commit-preparation.md         # (build-time from commit-sync Phase 1-4)
│   │   └── phases/
│   └── review/                           # Stage 4
│       ├── SKILL.md                      # 入口（就是 review-plan）
│       ├── review-plan/
│       │   └── SKILL.md                  # Review-Plan Agent
│       ├── merge/
│       │   └── SKILL.md                  # Verdict merge
│       └── playbooks/                    # 各领域 review sub-skills
│           ├── code-quality/SKILL.md     # 总是 spawn
│           ├── frontend-component/SKILL.md
│           ├── frontend-a11y/SKILL.md
│           ├── backend-api/SKILL.md
│           ├── db-schema/SKILL.md
│           ├── agent-integration/SKILL.md
│           └── test-coverage/SKILL.md
├── stdlib/                               # 共享方法论（kernel-discipline.md 已移走）
│   ├── feature-room-spec.md              # Spec yaml 格式 (从 Feature Room 复用)
│   ├── anchor-tracking.md                # (build-time from commit-sync)
│   ├── confidence-scoring.md             # (build-time from random-contexts)
│   ├── state-lifecycle.md                # Spec state 转换规则
│   ├── iteration-budgets.md              # Review 2 次、re-plan 3 次等 budget
│   └── degradation-policy.md             # 超 budget 后怎么降级
├── docs/                                 # 架构参考和 migration plans
│   ├── architecture.md                   # 本文档的可视化/简化版
│   ├── feature-room-mapping.md           # 和 Feature Room 的数据兼容说明
│   ├── skill-extraction-log.md           # 哪些 stdlib 是从哪个 external skill 抽取的
│   └── plan-2-plugin-migration.md        # Plugin migration plan (Phase 1 + Phase 2)
└── tests/                                # routing audit + end-to-end traces
    ├── routing-coverage.md
    └── end-to-end-trace.md
```

---

## 5. 关键机制

### 5.1 Session Ledger

所有 agent 的行为都留痕。Session ledger 是 append-only 的 jsonl 文件，放在
项目的 `.ai-robin/ledger.jsonl`。

每条 entry 记录：
- 时间戳
- 哪个 agent / stage / iteration
- 产生了什么 artifacts（reference 到 spec id 或文件路径）
- 关键决策（what / why）

Human final verification 时，读 ledger 可以快速定位任何一个决策点。这把
verification 的成本从 O(deliverable 大小) 降到 O(决策数量)。

### 5.2 Budget & iteration

几个 hard budget，写进 `stdlib/iteration-budgets.md`：

| Budget | 默认值 | 触发时的行为 |
|---|---|---|
| Review on same content | 2 次 | 第 3 次 fail → degrade to known issue |
| Re-plan on same stage | 3 次 | 第 4 次 → degrade to known issue |
| Research depth | 2 层（research 可以触发 sub-research） | 第 3 层 → 用已有信息做决策 |
| Total wall-clock | 由 Consumer 阶段确定 | 超时 → 暂停，等 human |
| Total token budget | 由 Consumer 阶段确定 | 超时 → 暂停，等 human |

Budget 不是软约束，是硬 kill switch。任何 agent 在 return 前要 check budget。

### 5.3 Graceful degradation

当 budget 被 exhaust 时，系统**不 crash、不 escalate to human**（因为 human 不在），
而是 **degrade gracefully**：

- 这部分工作标记为 `state: degraded`
- 写一个 `context-degraded-*.yaml` spec 说明：目标是什么、尝试过什么、最后为什么
  放弃、当前状态是什么
- 继续剩下的工作
- 最终交付包里有一份 `escalation-notice.md`，列出所有降级项

Human final verify 时，看到降级清单，决定是自己接手修、还是再跑一轮 AI-Robin、
还是改需求。

### 5.4 Review Stage 的 plan-fan-out-merge

这是整个架构里最复杂的一层，单独展开：

```
Execute Stage 结束
  ↓
Main agent 读取这一批 Execute Agent 产出的 change（通过 session ledger）
  ↓
Spawn Review-Plan Agent
  读 change 性质: 涉及哪些文件类型、哪些 anchor、哪些 contract spec
  决策 autonomy: autonomous
  产出 dispatch list: [
    "code-quality",           # always
    "frontend-component",     # 因为改了 .tsx 文件
    "backend-api",            # 因为改了 /api/ 下的文件
    "agent-integration"       # 因为改了 prompt 或 tool 定义
  ]
  return to main agent
  ↓
Main agent 并行 spawn 4 × Review Sub-Agent
  每个 sub-agent 独立:
    - load 自己的 playbook (agents/review/playbooks/{name}/SKILL.md)
    - load change 相关的代码和 spec
    - 运行 playbook 的 checklist
    - 产出 verdict: { status: pass/fail, issues: [...], severity: ... }
  ↓
所有 sub-agent 结束，main agent spawn Merge
  Merge Agent:
    - 合并所有 verdict
    - any critical fail → overall fail
    - only minor warnings → overall pass with warnings
    - all clean → overall pass
  ↓
【强制 commit】
  不管 pass/fail，这次 review 产出的 verdict 包写到 Room 的 specs/ 下
  作为一个 change-review-{timestamp}-*.yaml spec
  commit 到 git
  session ledger append entry
  ↓
根据 verdict 决定下一步:
  pass → return "ready_for_next_batch" to Execute-Control
  fail + within iteration budget → return "needs_rework" + issues → Planning
  fail + budget exhausted → return "degraded" + reason → continue with known issue
```

---

## 6. Build strategy

这个 NLP 本身规模不小（25-40 个 markdown files）。开发顺序：

### 阶段 A: 骨架（最先写）
1. `SKILL.md`（main dispatch）
2. `contracts/` 下所有 contract 定义
3. `agents/kernel/discipline.md`
4. `stdlib/feature-room-spec.md`
5. `stdlib/iteration-budgets.md`
6. `stdlib/degradation-policy.md`

### 阶段 B: 五个 agent 的骨架
7. 每个 stage 目录下的 `SKILL.md` 骨架，定义 return signal 和核心流程

### 阶段 C: 每个 agent 的 stdlib depth
8. Consumer 的 decision-taxonomy / question-prioritization / completeness-check
9. Planning 的 contract-design / parallelism-identification / replan-protocol
10. Execute 的 context-pulling（从 prompt-gen 抽取）/ commit-preparation（从
    commit-sync 抽取）

### 阶段 D: Review playbooks（渐进）
11. `agents/review/playbooks/code-quality/SKILL.md`（总是 spawn，必须先有）
12. 其他 playbook 按需添加——每接触一个新领域加一个

每个阶段跑完，可以 **dog-food** 在一个真实 mini project 上，发现问题、补 gap。

---

## 7. 开放问题

这些问题在开发过程中会被逐步收紧：

1. **Consumer Agent 的交互预算到底是多少？** 3 轮 Q&A？10 个问题？需要实测。
2. **Research Agent 的输出格式**——是 structured findings（JSON），还是 markdown？
   倾向 markdown + 一个 summary spec。
3. **Execute Agent 内部是不是也用 tree 递归？** 比如一个大 task 可以 decompose 成
   多个 sub-task？目前设计是不递归，由 Execute-Control 统一切分。
4. **Review playbook 怎么判断触发条件**——按文件扩展名？按 anchor 内容？需要一个
   明确的 trigger matcher 规范。
5. **跨项目的 learning**——不同项目之间有没有经验复用？目前不做，每个项目独立。

---

## 8. Runtime adaptation

AI-Robin is a **runtime-agnostic natural-language program (NLP)**. The
architecture assumes sub-agents communicate with the main agent via a
shared inbox (`.ai-robin/dispatch/inbox/{signal-id}.json`). What "communicate
via inbox" concretely means depends on the runtime.

### Reference model (abstract)

- Sub-agents run independently. When done, each writes a single JSON signal
  file to `.ai-robin/dispatch/inbox/`.
- The main agent's turn loop:
  1. Read `stage-state.json`.
  2. Check inbox for new signal files.
  3. Process **one** signal (lexicographic order; see
     `agents/kernel/discipline.md`).
  4. Move signal file to `processed/`, append ledger, update state.
- Parallel sub-agents means: N sub-agents each write one signal file; main
  agent processes them across N turns, one signal at a time.

### Claude Code mapping

Claude Code's `Task` tool is **synchronous**: invoking it runs the sub-agent
to completion and returns its result within the same parent turn. There is
no asynchronous "sub-agent is still running in the background" state.

In Claude Code, the reference model collapses cleanly:

- Sub-agent work: main agent invokes `Task`. The sub-agent's SKILL file
  instructs it to write its final signal to
  `.ai-robin/dispatch/inbox/{signal-id}.json` just before returning.
- "Checking inbox": main agent reads `.ai-robin/dispatch/inbox/` with
  `Glob`/`Read` **within the same turn** that the sub-agent returned.
- Parallel dispatch: main agent issues N `Task` tool calls in **one
  message** (Claude Code runs them concurrently). Each sub-agent writes its
  own signal file. After all N return, main agent sees N signals in inbox.
- Signal ordering: the signal files are all present when main agent reads
  them; lexicographic sort on signal_id gives deterministic processing
  order.

The file-based inbox is still the authoritative communication channel even
in Claude Code. Sub-agents must not return structured data "through the
Task return value" alone — the signal file is the source of truth for audit.

### Other runtimes

- **Truly async runtime (e.g., a custom orchestration loop)**: inbox polling
  fires between real asynchronous work. `active_invocations` tracks
  in-flight agents accurately. Signal ordering rule still applies.
- **Single-threaded runtime without parallelism**: spawn "N parallel
  agents" degrades gracefully to sequential execution. Same inbox, same
  routing, just slower.

### Invariants that hold across all runtimes

- One signal per sub-agent invocation.
- Signals are files in `.ai-robin/dispatch/inbox/` until processed.
- Main agent never reads sub-agent tool-return values as the authoritative
  source of signal content — only the inbox file.
- Main agent processes one signal per routing action (see
  `agents/kernel/discipline.md` § 3), regardless of how many are present.

If a runtime cannot satisfy these invariants (e.g., has no filesystem),
an adapter layer is required. AI-Robin does not ship such adapters — they
are out of scope for the v1 NLP.

### Sub-skill invocation and activation

AI-Robin's sub-skills (`agents/consumer/SKILL.md`, `agents/planning/SKILL.md`, etc.)
must **not** be registered as top-level user-invocable skills. Only the
root `ai-robin/SKILL.md` has YAML frontmatter; all sub-skill files omit
it so the main agent can load them via the `Read` tool without the
runtime treating them as independent skills discoverable from user intent.

If a runtime's skill-discovery mechanism does not recognize the
frontmatter-less convention, the sub-skill files should be renamed
(e.g., to `AGENT.md`) as a runtime-specific adaptation. The root
`ai-robin/SKILL.md`'s internal references can then be updated to the
new filename. This is purely a runtime-adapter concern, not a change to
the abstract design.

---

## 9. 一句话总结

> **AI-Robin 是一个 NLP runtime: Consumer Agent 是唯一的 human interface;
> Main agent 是永远 light 的 kernel; Planning/Execute-Control/Execute/Review
> 是按 stage 串起来的 stateless sub-agents; Session ledger 是 append-only 的
> audit log; Review 是按 change 性质动态 fan-out 的 domain-specific checks;
> 所有 state 以 Feature Room 格式写到 disk; Graceful degradation 替代 human
> escalation。**
