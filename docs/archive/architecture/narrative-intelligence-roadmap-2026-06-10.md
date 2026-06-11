# 叙事智能升级路线图（2026-06-10）

> **状态（2026-06-11 归档）：** 本路线图已被 v7 story repo 规格吸收，作为独立计划取消。条目归宿：M1-1 被否决（v7 spec §13，信息差/+时间线在场列取代 witnesses 投影）；M1-2 → 承诺派生指标（§5）+ 句式体检；M1-3 → 风格宪法否决入宪（§6.1）；M1-4 → 记忆层卷摘要（§4.6）；M2-1 → 体检事务（§9）；M2-2 → 三镜头评审（§8）；M3-1 → 卷复盘伏笔机会扫描（§9）；M2-3/M3-2/M3-3 随冻结令搁置。本文"不做清单"中的"禁全自动"已被 spec 0.5 撤销（§8.1），以 spec 为准。见 `docs/architecture/story-repo-spec-2026-06-10.md`。

> 来源：2026-06-10 全项目审查 + 「AI 写长篇网文系统」架构讨论。
> 前置依赖：`docs/superpowers/plans/2026-06-10-audit-fix-plan.md`（修复计划）完成 Phase 0/1 后启动本路线图；两者改同一批模块，不要并行。

## 设计原则（讨论共识）

1. **状态分三层**：事实状态（已有：event log + projection + contract）、叙事状态（张力/信息差/爽点节奏——当前最大空白）、文体状态（口癖/声音/漂移——第二空白）。本路线图主攻后两层。
2. **能机检的不用模型**：节奏规则做成"写完后的度量"而非"写作时的指导"；确定性脚本量出指标，超阈值才打回。
3. **重脚本、轻模型**：每次模型调用前由确定性代码把上下文压到最小最准；token 成本是真实作者的硬约束。
4. **作者品味是唯一不可再生资源**：高杠杆决策点（大纲拍板、弧光转折、伏笔埋收）永远留给人；系统从否决中学习而不是要求作者重复纠正。

---

## M1 近期（修复计划完成后立即可做，纯增量）

### M1-1 角色知识边界（信息差管理）

**动机**：悬念 = 作者已知/读者已知/角色已知三个集合的差。AI 两类隐蔽错误——泄密（角色说出不该知道的事）和废笔（向读者复述已知信息）——现有 review 维度抓不住。

**设计**：
- event log 已是事件事实源，为 `story_event_schema` 增加可选字段 `witnesses: [entity_id]`（哪些角色在场/得知）。data-agent 提取事件时顺带标注，无标注默认"仅在场角色"。
- 新增投影 `knowledge_projection_writer`：按角色累积"已知事件集"，落 `index.db` 新表 `entity_knowledge(entity_id, event_id, learned_chapter)`。
- prewrite 阶段（`write_gates/prewrite.py` 或 context pack 新 section `knowledge_boundaries`）注入：本章在场角色各自**不知道**的关键事件 top-N（按与本章大纲的实体重叠筛选）。
- review 新增机检维度 `info_leak`：扫描本章对白/内心戏中出现的实体与事件关键词，比对说话角色的已知集，疑似泄密列为 warning（不自动 blocking——误报率先观察一个月）。

**落点**：`story_event_schema.py`、新 `knowledge_projection_writer.py`、`event_projection_router.py` 注册、`context_manager.py` 新 section、`review_pipeline.py` 新检查器。
**验收**：构造"角色 A 不在场的密谋事件"测试项目，A 的对白引用该事件时 review 报 info_leak。

### M1-2 叙事节奏度量脚本化（写后量化，不是写前说教）

**动机**：爽点密度/钩子强度目前是 SKILL 里的指导性文字，模型打折执行；`chapter_reading_power` 表已有 hook_type/hook_strength 数据但没人消费成硬门禁。

**设计**：
- 新增 `pacing_metrics.py`：输入章号，输出确定性指标——距上次主线推进章数（strand_tracker）、距上次 strong hook 章数、本章爽点事件数（event log 中 payoff 类事件）、连续过渡章计数。
- `write_gates/postcommit.py` 增加软门禁：连续 N 章（默认 3）无 strong hook 或主线停滞超过配置阈值 → commit 通过但输出醒目"节奏债"警告并写入 `chase_debt`（表已存在，复用）。
- `webnovel-review` SKILL 把"节奏检查"从模型评审项改为：先读 pacing_metrics 输出，模型只解释数字、不重新估计数字。

**落点**：新 `data_modules/pacing_metrics.py`、`write_gates/postcommit.py`、review SKILL Step 调整、dashboard PacingPage 直接展示该指标（前端已有页面骨架）。
**验收**：构造连续 4 章 weak hook 的测试数据，postcommit 输出节奏债警告。

### M1-3 Override 泛化（从否决中学规则）

**动机**：作者连续改掉同类表达，系统应学到风格规则，而不是等第四次。override ledger 与 `project-memory add-pattern` 机制都已存在，缺的是连接。

**设计**：
- `override_ledger_service.py` 新增 `summarize_recurring(min_count=3)`：按 override 的 category/target 聚类，输出"同类否决 ≥3 次"的候选规则。
- `webnovel-review` SKILL 收尾步骤加一条指令：调用上述命令，存在候选时向作者展示"检测到你多次否决 X，是否固化为风格规则？"，确认后写入 `project_memory.json` 的 patterns（已有 add-pattern 命令），后续 context pack 的 preferences section 自动携带。

**落点**：`override_ledger_service.py`、review SKILL、无新存储。
**验收**：3 条同类 override 后 `summarize_recurring` 返回聚类项。

### M1-4 分层摘要（卷级中间层）

**动机**：现有 recent_summaries（近 3 章全文摘要）+ story_skeleton（间隔采样）之间缺"卷级摘要"，写 800 章时中距离剧情（50-200 章前）的召回靠 RAG 撞运气。

**设计**：
- 卷完结时（update_master_outline 或 plan skill 的卷复盘步骤）生成 `.webnovel/summaries/volume_NN.md`（500 字内：主线推进、关系变化、未回收伏笔清单）。
- `context_manager._build_pack` 的 core 增加 `volume_summaries`：当前卷之前的全部卷摘要（每卷 500 字，30 卷也只有 1.5 万字，且随距离可再截断）。

**落点**：plan SKILL 卷复盘步骤、`context_manager.py`、`summary_projection_writer.py` 不动（卷摘要由 skill 流程产出而非投影）。
**验收**：构造含 volume_01.md 的项目，context pack 出现 volume_summaries section。

---

## M2 中期（M1 验证后）

### M2-1 文体指纹与漂移检测

**动机**：千章尺度的声音漂移无法靠上下文策略根治（逐章累积、每步都在容差内），只能靠周期性度量校准。`style_sampler.py` 已有采样底子。

**设计**：
- `style_sampler` 扩展 `fingerprint` 子命令：对指定章节区间计算——句长分布（均值/方差/分位）、对白占比、高频口癖词 top-20（按角色分组）、段落长度分布、标点密度。结果存 `index.db` 新表 `style_fingerprints(range_start, range_end, metrics_json)`。
- 基线 = 第 1-30 章（或作者指定的"手感最好的区间"）；每 50 章自动对比最新窗口 vs 基线，KL 散度/简单百分比偏移超阈值 → doctor 与 dashboard 报警，并输出具体漂移项（"主角对白平均句长 +40%"）。
- 主角/核心配角的口癖词表进 context pack 的 `voice_contract` section（写前注入），漂移报警时由作者决定校准方向（回拉 or 接受演化并更新基线）。

**验收**：人工构造前后文风差异明显的两批章节，fingerprint diff 报告捕捉到句长与口癖偏移。

### M2-2 评审人格拆分

**动机**：同一模型写+评共享盲区；单一 reviewer 的注意力平均分配等于都不深。

**设计**：
- reviewer agent 改为按"镜头"多次调用（不增加 agent 数量，改 prompt 参数化）：`--lens reader`（毒舌白嫖读者：只回答爽不爽、第几段想划走、会不会弃）、`--lens editor`（结构与商业性）、`--lens fact`（只比对事实，输入为机检结果+contract）。
- 镜头裁决规则：fact 镜头由脚本结果主导（模型只解释）；reader 镜头产出不进 blocking，只进 reading_power/弃书风险标注；editor 镜头维持现有 blocking 语义。
- review SKILL 流程改为：机检 → 三镜头并行 → 汇总（明确"文笔好坏"不在任何镜头职责内，防止模型口味自我强化）。

**验收**：同一测试章三镜头输出可区分（reader 镜头不含结构术语，editor 镜头不含"这段不够爽"类表述）。

### M2-3 Token 成本预算线

**动机**：multi-agent 是拿 token 换确定性，写百万字的成本会劝退真实作者；context 减负重构（refactor/context-minimal-flow 分支）已在做单次调用瘦身，缺总量视角。

**设计**：
- `run_ledger` 已记录每次 SubagentRun，扩展记录 prompt/output 字符数（近似 token）；`quality_trend_report` 增加"每章成本"曲线。
- 设定每章字符预算（config 项，默认宽松），超预算章在报告中标黄并列出最大头的调用——给作者看见"钱花在哪"，不做硬限制。
- 对照实验钩子：同一章纲跑 `--profile minimal/full` 两种 context 模板（TEMPLATE_WEIGHTS 已支持多模板），review 分数与成本一起入库，用数据决定默认模板瘦到什么程度。

**验收**：quality_trend_report 输出含每章成本列与超预算标记。

---

## M3 实验（高风险高回报，单独立项验证）

### M3-1 长线伏笔机会扫描

**动机**：AI 不会自己起意"这里埋个 300 章后才响的雷"；目前伏笔全部依赖大纲显式声明。这是开放问题，谁解了谁有护城河。

**设计草图**：plan skill 的卷规划步骤新增"机会扫描"：输入 = 未回收伏笔清单 + 总纲远期节点 + 本卷章纲；让模型提议 3-5 个"本卷可顺手埋、N 卷后回收"的候选（必须引用总纲的具体远期节点作为回收点，防止悬空），作者勾选后写入 plot_threads.foreshadowing（带 target_chapter）。**人选 AI 提**，不全自动。

**验证标准**：连续两卷使用后，作者采纳率 ≥1/卷 才值得保留；否则砍掉。

### M3-2 读者模拟器（弃书点预测）

**设计草图**：reader 镜头（M2-2）的延伸——按"白嫖党/老书虫/女频读者"等画像参数化，对每章输出 0-100 弃书风险与触发段落。先只做趋势可视化（dashboard 已有 reading-power 页），积累 100+ 章人工对照后再决定是否进入门禁。明确定位：参考信号，永不 blocking。

### M3-3 review 评分与真实数据对齐（远期）

若作者发书，把章节追读/留存数据（手动导入 CSV 即可）与 review 分数、pacing_metrics 做相关性分析（`quality_trend_report` 扩展）。哪个内部指标与真实留存相关性最高，哪个就升权——让质量闭环最终锚定在读者行为而不是模型口味上。

---

## 不做清单（明确否决，避免回潮）

- ❌ 全文向量化作为事实召回主路径（语义相似 ≠ 叙事相关；向量只服务文风/场景参考）。
- ❌ 让模型自由评"文笔好坏"（口味自我强化，全书越来越 AI 味）。
- ❌ 全自动无人值守写作模式（作者品味流失 = 系统失去校准源）。
- ❌ 增加新的常驻 agent（现有 4 个职责已清晰；新能力优先做成脚本或现有 agent 的参数化镜头）。

## 里程碑顺序与依赖

```
修复计划 Phase 0/1 ──> M1-1 知识边界 ──> M2-2 评审人格(fact镜头吃M1-1产出)
                  ├──> M1-2 节奏度量 ──> M2-3 成本预算线(共用run_ledger/报告)
                  ├──> M1-3 Override泛化
                  └──> M1-4 卷级摘要 ──> M2-1 文体指纹(共用采样基建)
M3 全部独立立项，任一 M2 完成后可启动
```
