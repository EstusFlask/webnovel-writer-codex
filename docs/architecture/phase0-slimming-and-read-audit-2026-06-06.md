# Phase 0 审计：瘦身与读取方式清单（2026-06-06）

> 只读审计 + 实测。本文件只「记录可追踪结论」，不修改任何 skill / agent / reference / 测试文件。
> 目的：把 `context-minimal-writing-flow-plan-2026-06-05.md`（下称 Plan）第 4 节四条裁剪判据、§4.2 职责表、§6.2 读取方式，落成各瘦身 Phase 可直接照做的操作清单。
> 不复述 Plan，只给「文件 → 读取方式 / 归属 / 处理 Task」的可执行行。
>
> 工作目录（git 仓库根 = worktree）：`D:/wk/novel skill/webnovel-writer/.worktrees/context-minimal-flow`
> 插件目录（嵌套）：仓库根下 `webnovel-writer/` 子目录。下表路径均相对插件目录。
> 行数列为 `wc -l` 实测（2026-06-06，本机 Bash），不沿用 Plan 任何预填数字。

---

## 用法

- **Section A** 覆盖 Plan §6.2.1 reference-loading-map「直接 Read 的 md」全部条目，逐条定读取方式；Phase 4（Task #13/#14）按此改读取、清死文件。
- **Section B** 覆盖 8 Skill + 4 Agent，按 §4.2 职责表给保留要点与可压缩项；Phase 1–5（Task #5–#16）按此瘦身。
- 读取方式四分类（判据四 + §6.2.2）：**全文读** / **区段读** / **检索读**（CSV，单列于 A.3） / **不读**（清理候选）。
- 区段读锚点列给的是**文件里的真实标题原文**（已 Grep `^#{1,4} ` 核实）。Plan 正文锚点用了简写（去掉「、」、缩短标题），与真实标题**不逐字相等**；区段读时必须按本表真实锚点匹配，否则 `Grep ^## 一 ` 会匹配不到 `## 一、`。差异见 A.4「锚点校验与 FLAG」。

---

## Section A — 读取方式审计（逐个「直接 Read 的 md」）

行数 = 实测。「处理 Task」：靶心大文件区段读 = #13；死文件清理 = #14；其余「按需 / 全文」随其消费 Skill 的瘦身 Task 走（见 Section B），读取方式本身不单独占 Task，但 Phase 4 登记 loading-map 时一并写入（#13）。

### A.1 七个靶心大文件（区段读 → Task #13）

`always` / 高频触发的大 md，是 init / plan / write 每跑必吞的常驻成本。锚点已逐个 Grep 核实存在。

| 文件 | 实测行数 | 读取方式 | 区段：真实稳定标题锚点（原文） | 处理 Task |
|---|---|---|---|---|
| `references/genre-profiles.md` | 696 | 区段读 | 当前 genre 的**单个** `### 2.x`（`### 2.1`…`### 2.13`，13 题材各约 44 行）；按需加 `## 一、Profile 字段说明`。单本书只用 1 题材 → 省约 90% | #13 |
| `skills/webnovel-init/references/creativity/selling-points.md` | 687 | 区段读 | `## 9. 核心卖点定位模板`（骨架）；按需补 `### 1.3 核心卖点黄金公式`、`## 7. 实战检查清单` | #13 |
| `references/reading-power-taxonomy.md` | 361 | 区段读 | 按需取 `## 一、钩子类型` / `## 二、爽点模式` / `## 三、即时满足/微兑现` | #13 |
| `skills/webnovel-plan/references/outlining/chapter-planning.md` | 322 | 区段读 | `## 10. 结构化节点规范（CBN/CPNs/CEN）`（L299，至文件末）；需模板时加 `## 7. 章节规划模板` | #13 |
| `skills/webnovel-init/references/creativity/creativity-constraints.md` | 327 | 区段读 | 展示评分取 `### 8.1 五维评分`（L262，约 10 行）；创意采集读 `## 一、创意包 Schema (Idea Package)` / `## 六、硬约束驱动创意 (Hard Constraints)` / `## 八、评分系统 (Scoring System)` | #13 |
| `skills/webnovel-write/references/polish-guide.md` | 351 | 区段读 | 主路径 `## 2. 执行顺序（必须按序）`；Anti-AI 词库单独区段 `## 98:Phase 1 增补：Anti-AI 规范`（另有 `## 2A. Anti-AI 检测细则`）。**不可条目化进 CSV（csv/README 硬边界）** | #13 |
| `references/shared/cool-points-guide.md` | 313 | 区段读 | 所需爽点维度段；题材适配取 `## 九、题材适配`（L194）下对应题材 | #13 |

> 区段读手法：先 `Grep` content 输出匹配 `^#{1,4} ` 拿锚点行号，再 `Read` offset/limit 取段。两者均 Claude Code 内置，平台无关。

### A.2 其余「直接 Read 的 md」（全文 / 区段 / 不读）

判据：≤ ~150 行且需整体理解 → 全文读；明显大且只取某节、且 Plan 标了「按需 / 需X」触发 → 区段读；当前非直接调用 → 不读。

| 文件 | 实测行数 | 读取方式 | 区段：真实锚点（若区段读） | 处理 Task |
|---|---|---|---|---|
| **webnovel-init** | | | | |
| `skills/webnovel-init/references/system-data-flow.md` | 43 | 全文读 | — | #10 |
| `skills/webnovel-init/references/genre-tropes.md` | 183 | 区段读 | 当前题材段（题材套路库，按 genre 取对应小节） | #10 |
| `skills/webnovel-init/references/worldbuilding/world-rules.md` | 86 | 全文读 | — | #10 |
| `skills/webnovel-init/references/worldbuilding/faction-systems.md` | 179 | 区段读（按需） | always 触发但偏长；按当前世界观需要的小节取 | #10 |
| `skills/webnovel-init/references/worldbuilding/power-systems.md` | 160 | 区段读（按需） | 仅「力量体系」相关项触发；取对应小节 | #10 |
| `skills/webnovel-init/references/worldbuilding/character-design.md` | 111 | 全文读 | — | #10 |
| `skills/webnovel-init/references/worldbuilding/setting-consistency.md` | 215 | 区段读 | always 触发但偏长；取一致性校验小节 | #10 |
| `skills/webnovel-init/references/creativity/creative-combination.md` | 510 | 区段读 | **非 7 靶心但 510 行**：仅「需创意组合」触发，按当前混搭轴取小节，禁止全文 | #10 |
| `skills/webnovel-init/references/creativity/inspiration-collection.md` | 298 | 区段读 | 仅 Step1.5 灵感来源询问触发；取所需采集小节 | #10 |
| `skills/webnovel-init/references/creativity/anti-trope-game.md` | 170 | 区段读（按需） | 仅 game 题材 + 「需反套路」触发；取对应反套路项 | #10 |
| `skills/webnovel-init/references/creativity/anti-trope-rules-mystery.md` | 214 | 区段读（按需） | 仅 rules-mystery 题材触发 | #10 |
| `skills/webnovel-init/references/creativity/anti-trope-urban.md` | 169 | 区段读（按需） | 仅 urban 题材触发 | #10 |
| `skills/webnovel-init/references/creativity/anti-trope-xianxia.md` | 159 | 区段读（按需） | 仅 xianxia 题材触发 | #10 |
| **webnovel-plan** | | | | |
| `templates/output/大纲-卷节拍表.md` | 38 | 全文读 | — 模板，须整体套用 | #11 |
| `templates/output/大纲-卷时间线.md` | 51 | 全文读 | — 模板，须整体套用 | #11 |
| `references/shared/strand-weave-pattern.md` | 111 | 全文读 | — Plan §6.2.2 明示短文件维持全文 | #11 |
| `references/outlining/plot-signal-vs-spoiler.md` | 53 | 全文读 | — | #11 |
| `skills/webnovel-plan/references/outlining/conflict-design.md` | 277 | 区段读 | 仅「需冲突」触发；取对应冲突类型小节 | #11 |
| `skills/webnovel-plan/references/outlining/genre-volume-pacing.md` | 84 | 全文读 | — 短，卷级节奏整体读 | #11 |
| **webnovel-write** | | | | |
| `skills/webnovel-write/references/writing/typesetting.md` | 60 | 全文读 | — Step4 always，短 | #5 |
| `skills/webnovel-write/references/style-adapter.md` | 71 | 全文读 | — Step4 always，短 | #5 |
| **webnovel-review** | | | | |
| `references/shared/core-constraints.md` | 111 | 全文读 | — always 铁律，须整体 | #8/#12 |
| `references/review-schema.md` | 59 | 全文读 | — schema，须整体 | #8/#12 |
| `references/review/blocking-override-guidelines.md` | 47 | 全文读 | — 按需，短 | #12 |
| **webnovel-query** | | | | |
| `skills/webnovel-query/references/system-data-flow.md` | 343 | 区段读 | 偏长，按查询类型取数据源优先级小节 | #15 |
| `skills/webnovel-query/references/advanced/foreshadowing.md` | 120 | 全文读 | — 按需，伏笔查询整体读 | #15 |
| `skills/webnovel-query/references/tag-specification.md` | 154 | 全文读（边界） | — 154 行、tag 规范须整体；如证明只用单段可降区段读 | #15 |

> `cool-points-guide.md`(313)、`strand-weave-pattern.md`(111) 同时被 plan/review 直接 Read：前者已入 A.1 靶心区段读；后者全文读，跨 Skill 共用同一结论。

### A.3 检索读（CSV-backed，不在「直接 Read md」清单，单列）

Plan §6.2.1 明示 CSV 那条线「已做对，本轮不重做」。这里只登记，**不改造**；Phase 4 登记 loading-map 时保持现状。

| 数据源 | 读取方式 | 调用 | 备注 |
|---|---|---|---|
| `references/csv/场景写法.csv` | 检索读 | `reference_search.py --table 场景写法 --query ... --genre ...` | write Step2 战斗/对峙/桥段；承接已下线的 combat-scenes 等 md |
| `references/csv/写作技法.csv` | 检索读 | `reference_search.py --table 写作技法 --query ...` | write Step2 对话/情感；承接 dialogue-writing / emotion-psychology |
| `references/csv/题材与调性推理.csv`、`裁决规则.csv` 等 8 表 | 检索读（间接） | `story-system` 内部 `_route()` / `_collect_tables()` / `_load_reasoning()` | init/write 经 story-system 间接消费，已按需 |

> 现存 CSV：`裁决规则 / 场景写法 / 金手指与设定 / 命名规则 / 桥段套路 / 人设与关系 / 爽点与节奏 / 题材与调性推理 / 写作技法`（9 表）+ `genre-canonical.md` + `README.md`。

### A.4 不读（Phase 4 清理候选 → Task #14）

loading-map「当前非直接调用项」+ Plan §6.2.3 点名的 writing/* 迁移候选。合计约 1402 行死内容（实测）。处置：先核 CSV 覆盖，已覆盖则删或留空壳指向 CSV，未覆盖先补 CSV 再处置。

| 文件 | 实测行数 | 现状 / CSV 承接 | 处理 Task |
|---|---|---|---|
| `skills/webnovel-write/references/writing/combat-scenes.md` | 229 | 战斗触发已由 `场景写法.csv` 承接，不直接 Read | #14 |
| `skills/webnovel-write/references/writing/dialogue-writing.md` | 231 | 对话触发已由 `写作技法.csv` 承接 | #14 |
| `skills/webnovel-write/references/writing/emotion-psychology.md` | 265 | 情感触发已由 `写作技法.csv` 承接 | #14 |
| `skills/webnovel-write/references/writing/scene-description.md` | 263 | Plan §6.2.3 点名；不在直接 Read 清单，核 `场景写法.csv` 覆盖后处置 | #14 |
| `skills/webnovel-write/references/writing/desire-description.md` | 311 | 同上；核 CSV 覆盖后处置 | #14 |
| `skills/webnovel-write/references/writing/genre-hook-payoff-library.md` | 85 | Plan §6.2.3 点名；不在直接 Read 清单，核 CSV 覆盖后处置 | #14 |
| `skills/webnovel-write/references/style-variants.md` | 38 | 非直接调用项 | #14 |
| `skills/webnovel-review/references/common-mistakes.md` | 96 | 非直接调用项 | #14 |
| `skills/webnovel-review/references/pacing-control.md` | 129 | 非直接调用项 | #14 |

> `scene-description.md`(263)、`desire-description.md`(311)、`genre-hook-payoff-library.md`(85) 三者**存在且当前非直接 Read**，按 Plan 要求纳入清理核验。
> 其余存在但本轮无显式处置的 reference（不直接 Read、Plan 未点名）：`skills/webnovel-write/references/anti-ai-guide.md`(74，内容已并入 polish-guide §98/§2A，建议 #14 一并核验是否死)、`skills/webnovel-init/references/init-collection-schema.md`(74，Plan §6.2.4 指定 init 区段读真源，**保留**)、`skills/webnovel-init/references/creativity/market-positioning.md`(424，未登记直接 Read，建议 #14 核验)、`references/shared/naming-and-voice-gaps.md`(63)、`skills/webnovel-plan/references/outlining/outline-structure.md`、`plot-frameworks.md`（未登记直接 Read，建议 #13/#14 核验消费方）。

### A.5 锚点校验与 FLAG

所有 7 靶心锚点经 Grep `^#{1,4} ` 核实**真实存在**，无缺失锚点。需注意的「Plan 简写 vs 真实标题」差异（不是缺失，是匹配口径，区段读时必须用右列）：

| 文件 | Plan 正文写法 | 真实标题（区段读须匹配此） |
|---|---|---|
| genre-profiles | 「一、字段说明」 | `## 一、Profile 字段说明` |
| reading-power-taxonomy | 「## 一 钩子类型 / ## 二 爽点模式 / ## 三 微兑现」 | `## 一、钩子类型` / `## 二、爽点模式` / `## 三、即时满足/微兑现` |
| selling-points | 「### 1.3」「## 7」「## 9」 | `### 1.3 核心卖点黄金公式` / `## 7. 实战检查清单` / `## 9. 核心卖点定位模板` |
| chapter-planning | 「## 10 …」「## 7」 | `## 10. 结构化节点规范（CBN/CPNs/CEN）` / `## 7. 章节规划模板` |
| creativity-constraints | 「### 8.1」「一 Schema / 六 硬约束 / 八 评分」 | `### 8.1 五维评分` / `## 一、创意包 Schema (Idea Package)` / `## 六、硬约束驱动创意 (Hard Constraints)` / `## 八、评分系统 (Scoring System)` |
| polish-guide | 「## 2 执行顺序」「Anti-AI 词库段」 | `## 2. 执行顺序（必须按序）` / `## 98:Phase 1 增补：Anti-AI 规范`（另 `## 2A. Anti-AI 检测细则`） |
| cool-points-guide | 「## 九 题材适配」 | `## 九、题材适配` |

**FLAG：无缺失锚点。** 唯一注意点：Plan 锚点去掉了中文序号点「、」并缩短标题，按字面 `Grep` 会漏匹配——Phase 4 区段读与 loading-map 登记一律以本表右列真实标题为准。

---

## Section B — 逐组件归属（8 Skill + 4 Agent）

依 §4.2 职责表。「层」标主 agent 契约形状（Skill）/ subagent（Agent）/ runtime 边界。每格一句话，细节交叉引用 Plan，不复述。

| 组件 | 层 | 保留要点（一句话） | 主要可压缩 / 下沉项（一句话） | 处理 Task |
|---|---|---|---|---|
| `skills/webnovel-write/SKILL.md`（202） | Skill：主 agent 契约形状 | 三模式 + 准备链 + 三 Agent 调用合同 + 三道 gate/commit/postcommit/backup（§3.4、§8.2），新增提交前只读 `git diff`（§5.2 B） | context/reviewer/data 内部教程、data payload schema、长润色教程下沉 Agent/reference（§8.3） | #5 |
| `agents/context-agent.md`（181） | subagent | 五段写作任务书 + `memory-contract load-context` + 按需 query + `.story-system` 优先 + blocker（§9.1） | 长示例、过细推断说明、术语解释删（§9.1） | #6 |
| `agents/data-agent.md`（120） | subagent（含完整 artifact schema 真源） | 三份 artifact 顶层/子项最小字段 + 禁写 state/projection（§9.2、§4.3）；`tools` 含 `Write` | 各 event_type 长 payload 说明、长 JSON 示例、旧字段名解释压缩（§9.2） | #7 |
| `agents/reviewer.md`（135） | subagent | 五维 `dimension_results`(pass 也写) + evidence/fix_hint + 严格 JSON、不评分（§9.3）；不授 `Write`，只返 JSON | 删「思维链/ReAct」元叙述、删过长审查教程（§9.3、§12.2 松绑段号测试） | #8 |
| `agents/deconstruction-agent.md`（296） | subagent | quick/deep/auto 路由 + 不写文件 + 不造 canon + `init_reference_research`/quality/防污染（§9.4、§3.2） | 长质量门控表、超长 schema、深度分阶段长说明压缩（§9.4） | #9 |
| `skills/webnovel-init/SKILL.md`（402） | Skill：主 agent 契约形状 | §3.2 全链：Step1.5 灵感询问、deconstruction 调用边界、确认前不写 canon、root 安全化、idea_bank、patch 总纲、init 后 MASTER、验证回滚（§10.1） | 采集字段→`init-collection-schema.md` 区段读、题材列表收敛、CLI 长表收缩、创意/反套路/世界观按需读（§10.1、§6.2.4） | #10 |
| `skills/webnovel-plan/SKILL.md`（394） | Skill：主 agent 契约形状 | §3.3 全链：placeholder-scan、跨卷状态、设定基线、节拍表/时间线/卷纲/批量章纲、设定写回、总纲写回 JSON、master-outline-sync、update-state、真实 CHAPTER_GOAL 刷合同（§10.2） | CBN/CPN/CEN 细则→`chapter-planning.md`§10 区段读、长 reference 表改按阶段触发、节点示例下沉（§10.2、§6.2.4） | #11 |
| `skills/webnovel-review/SKILL.md`（170） | Skill：主 agent 契约形状 | §3.5 全链：合同缺失补 story-system、reviewer 调用、`review-pipeline --save-metrics`、`update-state --add-review`、blocking 用户裁决（§10.3） | reviewer 审查方法 / 证据查询过程不在 Skill 展开（§10.3） | #12 |
| `skills/webnovel-query/SKILL.md`（109） | Skill：主 agent 契约形状（只读） | 只读 + root 保护 + 数据源优先级(`.story-system`→accepted commit→memory-contract→projection) + 降级说明（§11.1、§3.6） | 默认全量 `load-context` 改按查询类型用最窄工具（entity-state/relationships/query-rules/open-loop）（§11.1） | #15 |
| `skills/webnovel-learn/SKILL.md`（82） | Skill：主 agent 契约形状 | root 保护 + 读当前章节号 + `project-memory add-pattern` + 不手写 JSON（§11.2） | 已极简，基本无可压缩；维持（§11.2） | #16 |
| `skills/webnovel-dashboard/SKILL.md`（101） | Skill：主 agent 契约形状（只读） | 只读边界 + `story-runtime/health` + root 解析 + dist 校验（§11.3） | 不默认装依赖（缺依赖提示命令）、启动前轻量检查（§11.3） | #16 |
| `skills/webnovel-doctor/SKILL.md`（70） | Skill：主 agent 契约形状（只读） | `project-status` 先行 + `doctor` 阶段感知 + 不修复/不装/不启 dashboard（§11.4、§3.6） | frontmatter description 改简洁中文触发型（§11.4） | #16 |

> Runtime 层（`webnovel.py` 各命令、artifact_validator、write-gate、chapter-commit、projection）承载 schema/gate/commit/projection/backup/状态推进，不在本轮 prompt 瘦身改动范围；各 Skill/Agent 只保留「调用形状」，校验留给 runtime（§4.2、§4.5 写入所有权矩阵）。
> Agent 单文件约束（§4.3）：4 个 Agent 均为 `agents/*.md` 单文件，不得新增 `agents/references/*`；其产物 schema 作为单文件唯一真源（data-agent 尤为关键）。

---

## 体量小结（实测）

- 8 Skill 合计 **1530 行**（write 202 / init 402 / plan 394 / review 170 / query 109 / learn 82 / dashboard 101 / doctor 70）；init、plan 最大，是 §10 主战场。
- 4 Agent 合计 **732 行**（context 181 / data 120 / reviewer 135 / deconstruction 296）；deconstruction 最大。
- 7 靶心 reference 合计 **3057 行**（区段读后单本书常驻锐减，genre-profiles 单题材约省 90%）。
- 不读清理候选合计 **约 1402 行**（A.4 九个核心候选，待核 CSV 覆盖后处置）。
- 读取方式分布：靶心区段读 7；A.2 区段读 11；全文读 15（含模板/schema/铁律/短文件）；检索读 CSV 3 类（不改造）；不读 9（+ 建议核验若干）。
