# AI-Robin

> Drop a brief in, get a project out. One human touchpoint (intake), then
> multi-hour autonomous run, then verify.

AI-Robin 是一个 Natural Language Program（NLP），跑在 Claude Code 或类似
的 agentic runtime 上。它把软件项目当作 **batch job** 来执行：你一次性
把需求讲清楚，它自主跑完 planning / execute / review 全流程，结束后你
来 verify。

**源码是 runtime-agnostic 的**（在 `ai-robin/`），第一个 runtime adapter
是 Claude Code plugin（在 `.claude-plugin/`）。其他 runtime 可以增加 adapter
而不改源码。

---

## 安装（Claude Code）

```bash
claude plugins install /path/to/AI-Robin-Skill
```

这会激活 `.claude-plugin/` 下的 plugin manifest，注册 3 个 slash commands、
11 个 sub-agent，和 5 个 hook 脚本（Python 3.11+ 自带库即可）。

## 调用

```
/ai-robin-start Build a Python CLI that prints fibonacci(10)
```

也可以：
- `/ai-robin-resume` — 接着上次被打断的 run（会自动检测 `.ai-robin/stage-state.json`）
- `/ai-robin-status` — 只看当前状态、不改 state

## 架构

- **抽象源**：`ai-robin/DESIGN.md` + `ai-robin/SKILL.md` + `ai-robin/agents/`
- **Claude Code adapter**：`.claude-plugin/` 下的 commands / agents / hooks
- **运行时状态**：每个项目下的 `.ai-robin/`（ledger、stage-state、dispatch inbox）

详见 [`ai-robin/DESIGN.md §8 Runtime adaptation`](ai-robin/DESIGN.md) 和
[`ai-robin/docs/plugin-equivalence.md`](ai-robin/docs/plugin-equivalence.md)
(plugin 保留什么、新加什么)。

---

## 这是为了解决什么问题

传统 AI-assisted 开发里，human 参与是持续的——每个决策、每个 review、
每次 rework 都需要你在场。这个模式 cognitively expensive。

AI-Robin 的赌注是：

- **生成一个解答很难**（AI 长时间 run，用 token 换结果）
- **验证一个解答便宜**（human 最后看 diff + ledger）

如果前置 input 足够好，后面几个小时的 execution 不需要你在。你把脑子
的高带宽时间留给 Consumer intake 和 final verify 两端，中间去做别的。

---

## 它做什么 / 不做什么

### 适合

- 从 0 到 1 建立一个中等复杂度项目（web app、CLI、API service、agent app 等）
- 需求可以在 15 轮对话内讲清楚的范畴
- 你愿意接受"跑完可能有 degraded scope"，而不是要求 100% 完成
- 有明确的 acceptance criteria（通过 gate criteria 表达）

### 不适合

- 需求极度模糊、需要探索式迭代的项目（那种本来就需要 human in loop）
- 对最终产物的风格 / 细节有强偏好且难以言传（proxy decisions 会让你不满意）
- 代码库本身巨大、需要深度上下文理解才能改动（scope 太大 degrade 风险高）
- 关乎生命 / 金融 / 法律的 production 代码（这种 AI 自主 run 不建议）

---

## 怎么用

### Prerequisite

1. Claude Code 或兼容的 agent runtime
2. 项目 repo 初始化完毕（`git init` 做过）
3. `ai-robin/` 这个 skill 目录放在 runtime 能 load 到的位置
4. 一个干净的分支或者 worktree（AI-Robin 会往里面频繁 commit）

### Run

在 Claude Code 里唤起 ai-robin skill，简单描述你要做什么：

```
Use ai-robin skill: I want to build [...]
```

然后 **Consumer stage 会开始问你问题**——大约 4-8 个核心问题，最多 15 轮
对话。典型问题包括：

- 技术栈（框架、数据库、部署目标）
- 核心功能边界（in-scope / out-of-scope）
- 硬约束（performance、兼容性、deployment target）
- 用户模型（single-user、multi-user、权限）

Consumer 尽量给你多选项和默认值，不让你写长文。

Consumer 完成后会告诉你：**"Intake complete. Starting autonomous run. 
Expect ~X hours. I'll ping you when done."**

然后你就可以走了。

### 期间

AI-Robin 会持续在 repo 里 commit。每个 commit message 包含 batch / stage
/ review-status 信息。如果你好奇可以看 `git log`。

关键文件：

- `META/` —— Feature Room，所有 spec 落盘在这里
- `.ai-robin/ledger.jsonl` —— append-only audit log
- `.ai-robin/dispatch/` —— sub-agent 间通信
- `ESCALATIONS.md` —— 如果发生 degradation，会在这里记录

你**不需要**在 run 期间操作任何东西。如果你 interrupt 了 run，下次重启
可能会从中断点 resume，也可能会重做最近一个 batch（取决于 runtime 行为）。

### Run 结束后

AI-Robin 会告诉你：

- 总共 commits 数、passed milestones 数、degraded scope 数（如果有）
- Verify checklist 建议的 review 路径

**Verify 步骤**（建议 30-60 min，取决于项目大小）：

1. **读 `ESCALATIONS.md` 先**：如果有 degraded scope，看是什么、是否能接受
2. **读 `META/00-project-room/spec.md`**：这是整个项目的 Human Projection，
   等于 Consumer + Planning 产出的 intent / decision / contract 的渲染版
3. **跑 `git log --oneline`**：扫一遍 commits，感知整体的演化
4. **跑一次**：`npm test` / `pytest` / 你的项目的 sanity command
5. **开一个主要 feature 路径**：手动试用核心流程
6. **抽查 review verdicts**：去 `META/*/progress.yaml` 看每个 milestone
   的 review_status

如果发现问题：

- Small fix → 自己改，commit，move on
- Big miss → 重新 invoke AI-Robin，在 Consumer stage 把原来的 miss 作为
  新需求讲进去。它会建立新 plan 处理（本质是"换一个角度再 run 一次"）

---

## 代价和上限

### Token 消耗

一次 full run 可能消耗 5M-50M tokens，取决于项目规模和 review 迭代次数。
大头在：

- Execute × N 的代码生成（最大头）
- Review playbooks 的 verdict 产出
- Planning 在 replan 循环里的决策

### 时间

典型 run 0.5-6 小时。取决于：

- 项目复杂度
- Runtime 并发能力（能否真并行 spawn sub-agent）
- Review 失败率（每次失败要 replan + re-execute）

### Degradation 频率

平均每个 run 有 0-3 个 degraded scope。最常见的原因：

- Review 迭代 2 次还没 pass → 该 milestone 被标 degraded，continue 其他
- Replan 3 次还没产出可用 plan → 该 scope 被 degraded
- Research 深度 2 层还没找到答案 → Planning 拿 best-guess 继续

Degraded scope 不等于 "没做"——已有的代码还在，只是没达到 review 的 bar。
Human 在 verify 时需要决定：接受 / 自己补 / 下次 run 重新 scope。

---

## 调参

### 项目规模预估过大时

如果 Consumer 之后估算的 milestone 数超过 50（hard cap），Planning 会
suggest sub-planning 或 degrade 部分 scope。这是系统在保护你——如果一
开始就 50+ milestone，run 会跑很久、review 失败概率也更高。建议先砍
scope，分多次 run。

### 想改 budget

编辑 `stdlib/iteration-budgets.md` 里的数值：

- `review_max_iterations_per_batch`（默认 2）
- `replan_max_iterations`（默认 3）
- `research_max_depth_per_question`（默认 2）
- `consumer_max_turns`（默认 15）
- `max_total_milestones_attempted`（默认 50）

收紧 budget → 更容易 degrade 但 run 更快、token 更省。
放宽 budget → 更少 degrade 但可能卡在同一个 review 不停 retry。

### 想改 review 严格度

编辑 `ai-robin/agents/review/playbooks/code-quality/SKILL.md` 把某些 rule 的 severity
从 `quality` 提升到 `blocking`，或降到 `advisory`。

改完之后 AI-Robin 会按新规则 review。

### 想加 review playbook

在 `ai-robin/agents/review/playbooks/` 下新建一个目录，写个 `SKILL.md`，描述触发条件
（文件 pattern / spec 类型 / content）。Review-Plan 会自动发现它并在
条件匹配时 dispatch。

---

## 常见问题

### AI-Robin 卡住了 / 不动了

看 `.ai-robin/ledger.jsonl` 最后几条。正常运行时每 1-5 分钟会有新的
ledger entry。如果 30 分钟没动静，可能是 runtime 崩了。

重启方式：重新 invoke ai-robin skill，告诉它 "resume from the last
committed state"。Kernel 会读现有 progress.yaml 判断在哪一步。

### 结果很烂 / 不是我想要的

先看 **proxy decisions**（在 Consumer 的 intake_complete signal 里，
也在 ledger 开头的 entries 里）。很多时候"结果不对"的根源是 Consumer 替
你填的默认不符合你的真实偏好。

下次 run 的时候，在 Consumer 那里主动把这些 proxy 点讲清楚。

### 我中途想改需求

AI-Robin 的核心约束是 intake 之后 no human。中途改需求的设计代价很高。

推荐方式：让这次 run 跑完（即使结果是你不要的），然后重新 invoke 讲清
楚新需求。第二次 run 会很多东西重做，但对 AI-Robin 来说这比"中途接受
新信号"要 robust。

### Run 完成后想做少量调整

直接自己改。AI-Robin 的产出就是普通代码和普通 git history，你可以在
任何时候接管。改完之后以后要再 invoke，它会从当前状态继续，不会擦掉
你的改动。

### 我想 dry-run 一下看看它大概会做什么

Consumer 完成后、在 Planning 开始前，你可以 kill 这次 run。Consumer 的
产出（intent / decision / constraint / convention specs）已经落盘。
读 `META/00-ai-robin-plan/specs/` 就知道 AI-Robin 理解到了什么。

不满意就重新 invoke 改 Consumer 的回答。满意就让它继续。

### Review 全 pass 但代码有 bug

这是可能的。Review playbook 只在它 check 的维度上给 verdict，bug 在那
些维度之外就会漏掉。

这是 human verify 阶段的职责。Review 是第一道筛，不是最终 gate。

---

## 当前实现状态

**已完整设计和实现（作为 NLP）**：

- Main agent kernel
- Consumer / Planning / Execute-Control / Execute / Research agents
- Review-Plan + Merge
- code-quality review playbook（always-on）

**尚未实现**（但架构已支持，可加）：

- 领域 review playbooks：frontend-component / frontend-a11y /
  backend-api / db-schema / agent-integration / test-coverage /
  spec-anchors
- 这些可以随着你用 AI-Robin 的经验逐步加，基于 gstack 或其他外部 rule 集

**实验性 / 边界情况还没验证**：

- Sub-planning 递归（Planning 发现某 scope 复杂度够大需要自己 decompose）
- 非常大的项目（100+ milestone 规模）
- 长时间 pause-and-resume

---

## 要了解更多

- `ai-robin/DESIGN.md` —— 完整设计文档、thesis、trade-off 分析
- `ai-robin/docs/architecture.md` —— 架构一页纸
- `ai-robin/SUMMARY.md` —— 当前文件清单
- `ai-robin/docs/feature-room-mapping.md` —— 数据格式和 Feature Room 的兼容性
- `ai-robin/docs/skill-extraction-log.md` —— 哪些方法论来自哪里

---

## Feedback

这是 AI-Robin 的 v1 设计。跑几次后你一定会发现：

- 某些 Consumer 问题问得不好
- 某些 planning decision 的默认不符合你习惯
- 某些 review rule 太严 / 太松
- 某些 budget 数值需要调

把这些观察记下来，回来改相应的 SKILL / phase / depth 文件。AI-Robin 是
为了长期维护的 NLP，每次迭代都会让它更贴合你的工作方式。
