# 审查输出 Schema（v7）

> **主服务 skill**: `webnovel-write` Step 3、`webnovel-review` Step 4
> **内容层级**: 流程闸门 / schema 定义
> **关键原则**: reviewer 输出 JSON 是审查唯一事实源；`review-pipeline` 负责 report + metrics 落库；主 skill 不应伪造 `overall_score`。

统一审查 Agent 输出格式。替代原 checker-output-schema.md 的评分制。

## 核心变化

- **无总分**：不再输出 overall_score，改为结构化问题清单
- **blocking 语义**：替代原 timeline_gate，severity=critical 默认阻断
- **单 agent**：不再区分 6 个 checker，统一由 reviewer agent 输出
- **七维审查**：事实五维之外，增加 readability 与 ai_flavor
- **问题代码**：用稳定 code 区分语义省略、对白承接、模板聚集等可复用缺陷

## Issue Schema

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | ✅ | 稳定问题类型，如 `CAUSAL_BRIDGE_MISSING` |
| severity | critical/high/medium/low | ✅ | 严重度 |
| category | continuity/setting/character/timeline/readability/ai_flavor/logic/pacing/other | ✅ | 问题分类 |
| location | string | ✅ | 位置（如"第3段"） |
| description | string | ✅ | 问题描述 |
| evidence | string | ❌ | 原文引用或记忆对比 |
| fix_hint | string | ❌ | 修复建议 |
| blocking | bool | ❌ | 是否阻断（critical 默认 true） |

## 阻断规则

- 存在任何 `blocking=true` 的 issue → Step 4 不得开始
- `severity=critical` 自动 `blocking=true`
- 其余 severity 由审查 agent 根据上下文判断
- 单纯 `ai_flavor` 不得设为 critical 或 blocking
- `readability` 只有在关键请求、对象、因果或人物立场无法可靠理解时才可 blocking

## Dimension Results

reviewer 必须逐项输出：

`setting / timeline / continuity / character / logic / readability / ai_flavor`

`review-pipeline` 会保留合法、非重复的 `dimension_results`，而不是在标准化 artifact 时丢弃。

## 指标沉淀

统一审查 agent 的原始输出保存为 `review_results.json`，保留完整 `issues` 列表。

随后由 `review-pipeline` 生成 `review_metrics.json`，用于写入 `index.db.review_metrics`。
该文件同时包含两类信息：

- **落库兼容字段**：
  - `start_chapter`
  - `end_chapter`
  - `overall_score`（由问题严重度推导的兼容分）
  - `dimension_scores`
  - `severity_counts`
  - `critical_issues`
  - `report_file`
  - `notes`
- **v6 观测字段**：
  - `chapter`
  - `issues_count`
  - `blocking_count`
  - `categories`
  - `timestamp`

说明：
- `review_metrics` 表仍沿用现有 dashboard / trend / context 消费的兼容 schema。
- `overall_score` 仅用于趋势观测与排序，不替代原始 issue 清单。
- gate 决策仍以 `blocking=true` 和 issue 明细为准。

## 反馈沉淀

`medium` 以上的 `readability` / `ai_flavor` issue 会追加到 `.story-system/anti_patterns.json`，保存：

- 可跨章节复用的现象规则 `text`（稳定 issue code 优先映射为通用规则，不把案例原句当作未来写作指令）
- 本章证据 `evidence`
- 稳定问题类型 `issue_code`
- 可复用规则 `rule`
- 修复方向 `fix_hint`

后续 context-agent 应消费规则与修复方向，而不是只机械避开某一句原文。
