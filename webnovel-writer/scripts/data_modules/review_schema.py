#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审查结果 schema（v7）。

在结构化问题清单中保留事实审查、可读性与 AI 痕迹维度。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from security_utils import atomic_write_json
except ImportError:  # pragma: no cover
    from scripts.security_utils import atomic_write_json

VALID_SEVERITIES = {"critical", "high", "medium", "low"}
VALID_CATEGORIES = {
    "continuity", "setting", "character", "timeline",
    "readability", "ai_flavor", "logic", "pacing", "other",
}
REVIEW_DIMENSIONS = (
    "setting",
    "timeline",
    "continuity",
    "character",
    "logic",
    "readability",
    "ai_flavor",
)
SCORE_CATEGORIES = (
    "continuity",
    "setting",
    "character",
    "timeline",
    "readability",
    "ai_flavor",
    "logic",
    "pacing",
    "other",
)
SEVERITY_PENALTIES = {
    "critical": 35.0,
    "high": 15.0,
    "medium": 6.0,
    "low": 2.0,
}


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def _issue_penalty(issue: "ReviewIssue") -> float:
    return float(SEVERITY_PENALTIES.get(issue.severity, SEVERITY_PENALTIES["medium"]))


@dataclass
class ReviewIssue:
    severity: str
    code: str = ""
    category: str = "other"
    location: str = ""
    description: str = ""
    evidence: str = ""
    fix_hint: str = ""
    blocking: Optional[bool] = None

    def __post_init__(self):
        if self.severity not in VALID_SEVERITIES:
            self.severity = "medium"
        if self.category not in VALID_CATEGORIES:
            self.category = "other"
        if self.blocking is None:
            self.blocking = self.severity == "critical"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewResult:
    chapter: int
    issues: List[ReviewIssue] = field(default_factory=list)
    dimension_results: List[Dict[str, str]] = field(default_factory=list)
    summary: str = ""

    @property
    def issues_count(self) -> int:
        return len(self.issues)

    @property
    def blocking_count(self) -> int:
        return sum(1 for i in self.issues if i.blocking)

    @property
    def has_blocking(self) -> bool:
        return self.blocking_count > 0

    @property
    def severity_counts(self) -> Dict[str, int]:
        counts = {level: 0 for level in ("critical", "high", "medium", "low")}
        for issue in self.issues:
            severity = issue.severity if issue.severity in counts else "medium"
            counts[severity] += 1
        return counts

    @property
    def categories(self) -> List[str]:
        return sorted(set(i.category for i in self.issues))

    @property
    def critical_issues(self) -> List[str]:
        return [
            issue.description
            for issue in self.issues
            if issue.severity == "critical" and issue.description
        ]

    def _build_dimension_scores(self) -> Dict[str, float]:
        scores = {category: 100.0 for category in SCORE_CATEGORIES}
        for issue in self.issues:
            category = issue.category if issue.category in scores else "other"
            scores[category] = _clamp_score(scores[category] - _issue_penalty(issue))
        return scores

    def _build_notes(self, categories: List[str]) -> str:
        parts: List[str] = []
        if self.summary:
            parts.append(self.summary)
        parts.append(f"issues={self.issues_count}")
        parts.append(f"blocking={self.blocking_count}")
        if categories:
            parts.append("categories=" + ",".join(categories))
        return " | ".join(parts)

    def _calculate_overall_score(self) -> float:
        score = 100.0
        for issue in self.issues:
            score -= _issue_penalty(issue)
        return _clamp_score(score)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter": self.chapter,
            "issues": [i.to_dict() for i in self.issues],
            "issues_count": self.issues_count,
            "blocking_count": self.blocking_count,
            "has_blocking": self.has_blocking,
            "dimension_results": list(self.dimension_results),
            "summary": self.summary,
        }

    def to_metrics_dict(self, report_file: str = "") -> Dict[str, Any]:
        categories = self.categories
        severity_counts = self.severity_counts
        return {
            "chapter": self.chapter,
            "start_chapter": self.chapter,
            "end_chapter": self.chapter,
            "overall_score": self._calculate_overall_score(),
            "dimension_scores": self._build_dimension_scores(),
            "severity_counts": severity_counts,
            "critical_issues": self.critical_issues,
            "report_file": report_file,
            "notes": self._build_notes(categories),
            "issues_count": self.issues_count,
            "blocking_count": self.blocking_count,
            "categories": categories,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }


def parse_review_output(chapter: int, raw: Dict[str, Any]) -> ReviewResult:
    issues = []
    for item in raw.get("issues", []):
        if not isinstance(item, dict):
            continue
        issues.append(ReviewIssue(
            severity=str(item.get("severity", "medium")),
            code=str(item.get("code", "")),
            category=str(item.get("category", "other")),
            location=str(item.get("location", "")),
            description=str(item.get("description", "")),
            evidence=str(item.get("evidence", "")),
            fix_hint=str(item.get("fix_hint", "")),
            blocking=item.get("blocking"),
        ))
    dimension_results: List[Dict[str, str]] = []
    seen_dimensions = set()
    for item in raw.get("dimension_results", []):
        if not isinstance(item, dict):
            continue
        dimension = str(item.get("dimension", "")).strip()
        conclusion = str(item.get("conclusion", "")).strip()
        if dimension not in REVIEW_DIMENSIONS or dimension in seen_dimensions or not conclusion:
            continue
        seen_dimensions.add(dimension)
        dimension_results.append({
            "dimension": dimension,
            "conclusion": conclusion,
        })

    return ReviewResult(
        chapter=chapter,
        issues=issues,
        dimension_results=dimension_results,
        summary=str(raw.get("summary", "")),
    )


def _read_json_if_exists(path: Path) -> Any | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Bad JSON in {path}") from exc


def _write_json(path: Path, payload: Any) -> None:
    atomic_write_json(path, payload, backup=True)


_REUSABLE_ANTI_PATTERN_RULES = {
    "IMPLICIT_SPEECH_ACT": "相邻对白不得让后一轮回答前一轮未提出、且无法从紧邻动作恢复的请求。",
    "MISSING_ARGUMENT": "动作或指令存在多个候选对象时，不得省略关键宾语。",
    "CAUSAL_BRIDGE_MISSING": "会影响判断的关键动作必须保留目的或因果桥梁。",
    "POV_CERTAINTY_JUMP": "人物推断不得脱离现场证据写成无来源的绝对事实。",
    "INFORMATION_PACKING": "不要把观察、反驳、风险和命令压成互不连接的报告短句。",
    "UNANCHORED_REFERENCE": "代词、序数、真假判断和代动词必须在前一两段有唯一指代对象。",
    "PSEUDO_SHARED_CONTEXT": "不得用前文未建立的暗号、编号、惯例或默契回应省略关键信息。",
    "ABSTRACT_DIALOGUE": "现场对白不要连续堆叠分类、定性和流程名词。",
    "REGISTER_MISMATCH": "对白正式程度必须符合人物身份、关系、场景压力和情绪。",
    "TELEGRAPHIC_CLUSTER": "不要连续使用只陈述事实、没有强调作用的残句或单句段。",
    "BINARY_CORRECTION_CLUSTER": "不要成组重复“不是X，是Y / 没有A，只是B”等纠正式模板。",
    "NARRATOR_VERDICT": "不要用整齐总结替人物或群体统一裁定现场意义。",
    "GENERIC_REACTION": "不同角色不得反复共用同一套神态、动作和反应模板。",
    "TRANSLATIONESE_DIALOGUE": "对白先还原中文言语行为，不得逐词沿用英文 pro-form、系词判断、抽象分类问句或字幕语序。",
    "SLOGANIZED_DIALOGUE": "对白不得为了金句、对称或预告片效果删去主体、对象和实际行动。",
}


def append_ai_flavor_anti_patterns(project_root: str | Path, result: ReviewResult) -> int:
    """Persist reusable readability/AI-flavor failures as future writing anti-patterns.

    The legacy function name is retained for callers and compatibility.
    """
    root = Path(project_root).expanduser().resolve()
    path = root / ".story-system" / "anti_patterns.json"
    existing = _read_json_if_exists(path) or []
    if not isinstance(existing, list):
        existing = []

    seen_texts = {str(item.get("text") or "").strip() for item in existing if isinstance(item, dict)}
    additions: List[Dict[str, Any]] = []
    for index, issue in enumerate(result.issues, start=1):
        if issue.category not in {"readability", "ai_flavor"} or issue.severity not in {"medium", "high", "critical"}:
            continue
        code = str(issue.code or "").strip()
        text = (
            _REUSABLE_ANTI_PATTERN_RULES.get(code)
            or issue.description
            or issue.evidence
            or ""
        ).strip()[:240]
        if not text or text in seen_texts:
            continue
        seen_texts.add(text)
        additions.append(
            {
                "text": text,
                "source_table": "review_extracted",
                "source_id": f"ch{int(result.chapter):04d}_issue_{index}",
                "category": issue.category,
                "issue_code": issue.code,
                "rule": issue.description,
                "evidence": issue.evidence,
                "fix_hint": issue.fix_hint,
                "added_at": datetime.now().isoformat(timespec="seconds"),
            }
        )

    if additions:
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, [*existing, *additions])
    return len(additions)
