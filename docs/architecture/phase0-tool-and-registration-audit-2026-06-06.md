# Phase 0 审计：工具能力与插件注册名（2026-06-06）

> 只读审计。本文件只「记录证据」，不修改任何 skill / agent / plugin.json / 测试文件。
> 目的：为 `context-minimal-writing-flow-plan` 提供可信的运行基线，复核计划中假设的
> `webnovel-writer:<agent>` 注册名、agent/skill frontmatter、以及计划依赖的官方工具行为结论。
>
> 工作目录（git 仓库根 = worktree）：`D:/wk/novel skill/webnovel-writer/.worktrees/context-minimal-flow`
> 插件目录（嵌套）：仓库根下的 `webnovel-writer/` 子目录。

---

## 1. Claude Code 版本与环境

| 项 | 值 | 证据 |
|----|----|------|
| 宿主 | Claude Code（固定，本插件唯一目标宿主） | — |
| `claude --version` | `2.1.161 (Claude Code)` | Bash 直接执行成功（非「subagent 不可用」） |
| 平台 | Windows（win32），PowerShell + Bash 双可用 | 环境说明 |
| 本审计执行体 | subagent（Task 1）；本机 `claude --version` 可正常返回 | — |

结论：版本/环境均可确认，无降级记录。

---

## 2. 插件注册（真实名）

### 2.1 plugin.json

文件：`webnovel-writer/.claude-plugin/plugin.json`（全文 18 行）。

```json
{
  "name": "webnovel-writer",
  "version": "6.1.0",
  "description": "长篇网文创作系统（skills + agents + data chain + RAG）",
  "author": { "name": "lingfengQAQ" },
  "homepage": "https://github.com/lingfengQAQ/webnovel-writer",
  "repository": "https://github.com/lingfengQAQ/webnovel-writer",
  "license": "GPL-3.0",
  "keywords": ["webnovel", "claude-code", "skills", "agents", "rag"]
}
```

- 插件名（namespace 前缀来源）：**`webnovel-writer`**。
- manifest **没有**显式 `agents` / `skills` / `commands` 路径数组。
  → 因此 agents 与 skills **全部走约定式 auto-discovery**：
  - 官方 `plugin-structure/SKILL.md:11` —「automatic component discovery」；
  - 同文件第 28-32 行：`agents/`（`.md` 文件）与 `skills/`（子目录，每个含 `SKILL.md`）。
  - 官方 `skill-development/SKILL.md:271-273` —「Claude Code automatically discovers skills: Scans `skills/` directory; Finds subdirectories containing `SKILL.md`」。

### 2.2 真实 on-disk agent 名（4 个）

每个 agent 是单一 `.md` 文件，frontmatter `name:` 与文件名（去 `.md`）一致：

| 文件 | frontmatter `name:` (行 2) | 一致？ |
|------|---------------------------|--------|
| `webnovel-writer/agents/context-agent.md` | `context-agent` | ✅ |
| `webnovel-writer/agents/data-agent.md` | `data-agent` | ✅ |
| `webnovel-writer/agents/deconstruction-agent.md` | `deconstruction-agent` | ✅ |
| `webnovel-writer/agents/reviewer.md` | `reviewer` | ✅ |

另有 `webnovel-writer/agents/evals/`（含 `evals.json` + `files/`）——非 agent 定义，是评测夹具，auto-discovery 不会把它当 agent（不是顶层 `.md`）。无 `agents/references/` 目录。

### 2.3 真实 on-disk skill 名（8 个）

每个 skill 是含 `SKILL.md` 的子目录，frontmatter `name:`（均在行 2）与目录名一致：

| 目录 | frontmatter `name:` | 一致？ |
|------|--------------------|--------|
| `skills/webnovel-write/` | `webnovel-write` | ✅ |
| `skills/webnovel-init/` | `webnovel-init` | ✅ |
| `skills/webnovel-plan/` | `webnovel-plan` | ✅ |
| `skills/webnovel-review/` | `webnovel-review` | ✅ |
| `skills/webnovel-query/` | `webnovel-query` | ✅ |
| `skills/webnovel-learn/` | `webnovel-learn` | ✅ |
| `skills/webnovel-dashboard/` | `webnovel-dashboard` | ✅ |
| `skills/webnovel-doctor/` | `webnovel-doctor` | ✅ |

（路径前缀省略 `webnovel-writer/`。）

### 2.4 注册名 ↔ 计划引用名 复核（关键）

计划 `docs/architecture/context-minimal-writing-flow-plan-2026-06-05.md` 在多处用
`webnovel-writer:<agent>` 形式引用 4 个 agent，例如：

- L181 `必须调用 webnovel-writer:context-agent`
- L195 `... webnovel-writer:reviewer`
- L228 `... webnovel-writer:data-agent`
- L97 `... webnovel-writer:deconstruction-agent`
- L463/L698/L713/L728 `Use the Agent tool to run webnovel-writer:context-agent` 等
- L430 计划自带告警：「plugin scoped agent 的真实注册名必须在 Phase 0 复核」（即本节）。

复核结论：

- **on-disk agent 名 = `context-agent` / `data-agent` / `deconstruction-agent` / `reviewer`**，
  与计划里冒号后半段完全一致，**无错名**。
- 关于前缀：官方 `agent-development/SKILL.md:281-285`「Namespacing」原文：
  - 「Agents are namespaced automatically: Single plugin: `agent-name`; With subdirectories: `plugin:subdir:agent-name`」。
  - 即官方文档把「单插件、无子目录」的 agent 标识写作**裸名 `agent-name`**，把带前缀的形态留给「子目录」场景（`plugin:subdir:agent`）。
  - 命令侧旁证：`command-development` 与 `plugin-features-reference.md:30` 显示插件组件在 `/help` 里带 `(plugin:plugin-name)` 标签，说明「插件名:组件名」是 marketplace 场景下的实际可见限定形态。
  - ⚠️ **轻微风险（命名形态，非错名）**：官方 agent-development 文档对「单插件无子目录」给出的范式是裸 `agent-name`，并未把 `plugin:agent`（无 subdir）列为 canonical 形态。计划统一用 `webnovel-writer:context-agent` 这类**带插件前缀、无 subdir** 的写法，是合理且更显式的（在多插件并存时消歧），但官方文档**没有把这一形态写成单插件的标准范式**。
  - 建议：Phase 1 真正接线时，以**运行时实测**（`Agent`/Task 工具能否用 `webnovel-writer:context-agent` 解析到该 agent）为准；若实测裸名 `context-agent` 才解析得到、带前缀失败，则按裸名修正计划。本审计无法在 subagent 内实跑 Agent 工具来终判，故标注为「待运行时验证」。

---

## 3. Agent frontmatter 审计（4 个）

逐项抄录 frontmatter（行号以各文件为准；所有 4 个 agent 的 frontmatter 块均为第 1-7 行）：

| agent | name | description（摘） | model | color | tools |
|-------|------|------------------|-------|-------|-------|
| context-agent | `context-agent` | 写前 research，输出写作任务书。 | `inherit` | `blue` | `Read, Grep, Bash` |
| data-agent | `data-agent` | 从正文提取事实，生成 commit artifacts。 | `inherit` | `green` | `Read, Write, Bash` |
| deconstruction-agent | `deconstruction-agent` | /webnovel-init 的参考书拆解子代理…… | `inherit` | `purple` | `Read, Grep, Bash` |
| reviewer | `reviewer` | 统一审查 agent。逐维度检查…… | `inherit` | `yellow` | `Read, Grep, Bash` |

对照 agent-development 规则：

- **单一 `.md` 文件**：✅ 全部满足。
- **必备字段 name/description/model/color**：✅ 4 个全齐。
  - `model: inherit` 符合官方推荐（`agent-development/SKILL.md:100,105`）。
  - `color` 取值：`blue/green/purple/yellow`。⚠️ 官方 `agent-development/SKILL.md:111` 列出的合法色为
    `blue, cyan, green, yellow, magenta, red`，**未列 `purple`**。`deconstruction-agent` 的
    `color: purple` 不在官方枚举内（应为 `magenta`）。属**轻微规范偏差**，不影响功能/注册（color 仅 UI 着色）。
- **`tools` 最小集**：✅ 都是 3 个工具的小集合（least privilege，符合 `SKILL.md:134`）。
- **FLAG：`tools` 含 `Agent` 或 `AskUserQuestion`？** → ❌ **均不含**。
  4 个 agent 的 tools 仅为 `{Read, Grep/Write, Bash}` 组合，**没有任何一个**带 `Agent`/`AskUserQuestion`/`Task`。
  → 与计划「subagent 不得用 `Agent`/`AskUserQuestion`」一致，**无违例**。
- **FLAG：缺必备 frontmatter 字段？** → 无。4 个 agent 字段齐全。
- **FLAG：依赖外部 `agents/references/*` 当隐藏手册？** → 无。`agents/references/` 目录不存在；
  4 个 agent 正文未引用 `agents/references/...`。（注：正文大量引用 `${SCRIPTS_DIR}/webnovel.py` 子命令，
  那是运行时脚本调用，不是「隐藏 manual 文件」。）
- **`skills:` frontmatter 字段？** → 4 个 agent **均无** `skills:` 字段（Grep `^(name|skills):` 仅命中
  `name:`）。即当前没有任何 agent 预载 Skill 内容。

---

## 4. Skill frontmatter 审计（8 个）

逐项抄录（`name`/`allowed-tools` 行号见下；所有 skill `name:` 均在行 2）：

| skill | name | description 触发型 | allowed-tools |
|-------|------|-------------------|---------------|
| webnovel-write | `webnovel-write` | 产出可发布章节，完整执行上下文→起草→审查→润色→提交→备份。 | `Read Write Edit Grep Bash Agent AskUserQuestion` |
| webnovel-init | `webnovel-init` | 深度初始化网文项目。分阶段交互收集…… | `Read Write Edit Grep Bash Agent AskUserQuestion WebSearch WebFetch` |
| webnovel-plan | `webnovel-plan` | 基于总纲生成卷纲、时间线和章纲…… | `Read Write Edit Bash AskUserQuestion` |
| webnovel-review | `webnovel-review` | 使用审查 Agent 评估章节质量…… | `Read Grep Write Edit Bash Agent AskUserQuestion` |
| webnovel-query | `webnovel-query` | 查询项目设定、角色、力量体系、势力、伏笔…… | `Read Grep Bash` |
| webnovel-learn | `webnovel-learn` | 从当前会话提取成功模式并写入 project_memory.json | `Read Bash` |
| webnovel-dashboard | `webnovel-dashboard` | 启动只读小说管理面板…… | `Bash Read` |
| webnovel-doctor | `webnovel-doctor` | This skill should be used when the user asks to "/webnovel-doctor", "检查项目环境"…… | `Read Bash` |

对照 skill-development 规则：

- **目录 + SKILL.md 结构**：✅ 8 个目录均含 `SKILL.md`（逐一 `test -f` 通过）。
- **frontmatter 含 `name` + 触发型 `description`**：✅ 全部有 `name` + `description`。
  - 官方只强制 `name` + `description`（`skill-development/SKILL.md:33-34`）。
  - 触发表述：7 个用中文动作/场景式触发短语（计划偏好），`webnovel-doctor` 用英文官方范式
    「This skill should be used when…」并把中文触发词内嵌其中——两类都满足「具体触发」要求。
  - `webnovel-doctor` 还带 `version: 0.1.0`（额外字段，无害）。
- **`allowed-tools` 是否存在及其值**：✅ **8 个 skill 全部声明了 `allowed-tools`**（值见上表）。
  - 4 个编排型 skill（write/init/plan/review）的 `allowed-tools` 含 **`Agent`**（write/init/review）
    与 **`AskUserQuestion`**（write/init/plan/review）——这是**顶层 skill / 命令层**用来「预批准」调度子代理
    与向用户提问的工具集，**不是 subagent 的 tools**。与计划角色分工（编排在 skill 层、执行在 agent 层）一致。
  - 只读型 skill（query/learn/dashboard/doctor）的 `allowed-tools` 收敛为 `Read/Bash(/Grep)`，无 `Agent`/`AskUserQuestion`。

> 说明：官方 `skill-development/SKILL.md` 通篇**未出现** `allowed-tools` 字段名（仅强制 `name`+`description`）。
> 因此「`allowed-tools` 是预批准而非限制」这一语义**无法从本地官方 skill 文档直接证实**，见 §5。

---

## 5. 计划依赖的官方工具行为结论（运行基线）

交叉核对源（实际使用路径）：
**`C:/Users/lcy/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/`**
（primary 路径存在；fallback `.tmp/plugin-dev-official/...` **不存在**，未使用）。
核对的三个 skill：`agent-development/`、`skill-development/`、`plugin-structure/`（含其 `references/`、`examples/`）。

逐条结论与本地可证实性：

| # | 计划依赖的结论 | 本地官方文档可证实？ | 证据 / 标注 |
|---|----------------|---------------------|-------------|
| (a) | **subagent 不能再生成另一个 subagent** | ❌ 未找到 | 在 plugin-dev 全树 Grep `spawn / another (sub)?agent / nested / recursi` 仅命中 MCP 进程「spawn」，**无 subagent 嵌套禁令**条文。→ **「计划断言，本地未证实」**。（与之相容的旁证：`command-development/SKILL.md:720`「Claude uses **Task tool** to launch agent」——launch agent 是上层/命令侧动作；官方未给出 subagent 自身可再调 Task 的任何示例，但「未给出」≠「明文禁止」。） |
| (b) | **`Agent` / `AskUserQuestion` 不作为 subagent 的 tools** | ⚠️ 部分（间接） | 官方 agent `tools` 文档（`agent-development/SKILL.md:122-140`）给的「常用 tool set」全是 `Read/Write/Grep/Glob/Bash`，**从不**把 `Agent`/`AskUserQuestion` 列进 agent 的 `tools`。`AskUserQuestion` 出现处均在**命令/skill 层**的 `allowed-tools`（`plugin-dev/commands/create-plugin.md:12`、`plugin-settings/examples/create-settings-command.md:3`），不在任何 agent frontmatter。→ 官方**惯例支持**该结论，但**无一句明文「禁止」**。标注为「官方惯例支持，无明文禁令」。本仓 4 个 agent 实测也无人含 `Agent`/`AskUserQuestion`（§3）。 |
| (c) | **`tools` / `disallowedTools` 控制 subagent 工具边界** | ⚠️ 一半 | `tools` 控制边界：✅ 明文——`agent-development/SKILL.md:124`「Restrict agent to specific tools」、`:132`「If omitted, agent has access to all tools」、`:134` least-privilege。`disallowedTools`：❌ 在 plugin-dev 全树 **Grep 无任何命中**。→ `tools` 部分「本地已证实」；`disallowedTools` 部分「计划断言，本地未证实」。 |
| (d) | **agent `skills:` frontmatter 会把整份 Skill 内容预载进 subagent** | ❌ 未找到 | 官方 agent frontmatter 文档只列 `name/description/model/color/tools`（`SKILL.md:122` 区段 + `:340-342` 表），**无 `skills:` 字段**说明；全树 Grep `skills:`（agent 语境）无命中。→ **「计划断言，本地未证实」**。当前本仓也无 agent 使用该字段（§3），故即便成立也属「未来才会用到」的能力。 |
| (e) | **Skill 的 `allowed-tools` 是预批准、不是限制** | ❌ 未找到 | `skill-development/SKILL.md` 全篇**无** `allowed-tools` 字样；官方只把 `allowed-tools` 用在**命令** frontmatter（`command-development` / `plugin-settings` 示例）。其「预批准/非限制」语义在本地官方文档中**无直接定义**。→ **「计划断言，本地未证实」**。（注：经验上 skill/command 的 `allowed-tools` 行为确为预批准，但本审计按要求不凭记忆造引用，仅据本地文档判定为「未证实」。） |

补充已证实的注册/调度事实（支撑计划接线）：

- 自动发现：agents 扫 `agents/*.md`、skills 扫 `skills/*/SKILL.md`（`plugin-structure/SKILL.md:11,28-32`；`skill-development/SKILL.md:271-273`）。✅
- agent 命名空间：单插件裸名 `agent-name`，带子目录 `plugin:subdir:agent-name`（`agent-development/SKILL.md:283-285`）。✅
- 上层用 **Task 工具** 启动 agent（`command-development/SKILL.md:720`）。✅

---

## 6. 结论 / 风险清单

### 与计划假设一致的部分（无阻断）

1. 4 个 agent 的 on-disk 名（`context-agent` / `data-agent` / `deconstruction-agent` / `reviewer`）与计划
   `webnovel-writer:<agent>` 引用的冒号后半段**完全一致**，无错名、无缺失。
2. 8 个 skill 目录名与各自 `name:` 一致，结构合规（目录 + SKILL.md，name + 触发型 description）。
3. **没有任何 agent 的 `tools` 含 `Agent` / `AskUserQuestion` / `Task`** → 计划「subagent 不持调度工具」的红线
   在现状下**已天然满足**，无需先修。
4. 没有 agent 缺必备 frontmatter 字段；没有 agent 依赖 `agents/references/*` 隐藏手册（该目录不存在）。
5. 没有 agent 使用 `skills:` 预载字段（即 (d) 即便成立，也不会与现状冲突）。
6. 8 个 skill 均显式声明 `allowed-tools`，且编排型/只读型分工与计划角色划分吻合。

### 会动摇计划假设的风险点（需后续处理 / 实测）

- **R1（命名形态，待运行时验证）**：官方 agent-development 文档把「单插件无子目录」agent 的 canonical 标识写成
  **裸 `agent-name`**，未把 `plugin:agent`（无 subdir）列为标准范式。计划统一用 `webnovel-writer:context-agent`
  这类带前缀写法。**名字本身没错**，但前缀形态能否被 Agent/Task 工具解析到，需 Phase 1 **运行时实测**确认；
  若实测仅裸名可解析，应回改计划为裸名。本审计（subagent 内）无法实跑 Agent 工具终判。
- **R2（工具行为，本地未证实——见 §5）**：计划依赖的 (a) subagent 不能再开 subagent、(d) agent `skills:` 预载整份
  Skill、(e) skill `allowed-tools` 为预批准——这三条在本地官方 plugin-dev 文档中**找不到出处**；(c) 的
  `disallowedTools`、(b) 的「明文禁止」也**无出处**。这些应作为**「计划断言、本地未证实」**对待：
  计划据此设计无妨，但任何「以 `skills:` 预载替代 reference 大块文本」「靠 subagent 链式分发」的关键改动，
  应在实现期以小样例**实测**，不能仅以官方文档为据。
- **R3（轻微规范偏差，不阻断）**：`deconstruction-agent` 的 `color: purple` 不在官方合法色枚举
  （`blue/cyan/green/yellow/magenta/red`）内。仅 UI 着色，无功能影响；如要严格合规，应改 `magenta`。
  本审计为只读，不修改。

### 一句话总览

注册名与 frontmatter 现状**与计划高度一致、无错名、无 `Agent`/`AskUserQuestion` 违例**；唯一需在实现期落实的是
**R1 的 `webnovel-writer:<agent>` 前缀形态运行时实测** 与 **R2 中那几条「本地未证实」的工具行为以实测兜底**。
