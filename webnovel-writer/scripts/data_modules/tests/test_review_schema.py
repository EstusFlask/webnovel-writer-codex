#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""审查 schema 测试"""
import json

import pytest
from data_modules.review_schema import (
    REVIEW_DIMENSIONS,
    ReviewIssue,
    ReviewResult,
    append_ai_flavor_anti_patterns,
    parse_review_output,
)


def test_review_issue_blocking_defaults():
    """critical severity 默认 blocking=True"""
    issue = ReviewIssue(
        severity="critical",
        category="continuity",
        location="第3段",
        description="主角使用了已失去的能力",
    )
    assert issue.blocking is True


def test_review_issue_non_critical_not_blocking():
    """非 critical 默认 blocking=False"""
    issue = ReviewIssue(
        severity="high",
        category="setting",
        location="第7段",
        description="时间线矛盾",
    )
    assert issue.blocking is False


def test_review_result_counts():
    """blocking_count 自动计算"""
    result = ReviewResult(
        chapter=10,
        issues=[
            ReviewIssue(severity="critical", category="continuity", location="p1", description="d1"),
            ReviewIssue(severity="high", category="setting", location="p2", description="d2"),
            ReviewIssue(severity="high", category="timeline", location="p3", description="d3", blocking=True),
        ],
        summary="测试",
    )
    assert result.blocking_count == 2
    assert result.issues_count == 3
    assert result.has_blocking is True


def test_review_result_no_issues():
    result = ReviewResult(chapter=10, issues=[], summary="无问题")
    assert result.blocking_count == 0
    assert result.has_blocking is False


def test_review_result_to_dict_roundtrip():
    result = ReviewResult(
        chapter=10,
        issues=[
            ReviewIssue(severity="medium", code="TELEGRAPHIC_CLUSTER",
                        category="ai_flavor", location="p5", description="AI味重",
                        evidence="'稳住心神'出现3次", fix_hint="替换为具体动作描写"),
        ],
        summary="1个AI味问题",
    )
    d = result.to_dict()
    assert d["chapter"] == 10
    assert d["blocking_count"] == 0
    assert len(d["issues"]) == 1
    assert d["issues"][0]["category"] == "ai_flavor"
    assert d["issues"][0]["code"] == "TELEGRAPHIC_CLUSTER"
    assert d["issues"][0]["fix_hint"] == "替换为具体动作描写"


def test_parse_review_output_from_dict():
    raw = {
        "issues": [
            {"severity": "critical", "category": "continuity", "location": "p1",
             "description": "矛盾", "evidence": "证据", "fix_hint": "修复"},
        ],
        "summary": "1个严重问题",
    }
    result = parse_review_output(chapter=5, raw=raw)
    assert result.chapter == 5
    assert result.blocking_count == 1


def test_parse_review_output_preserves_seven_dimension_results():
    raw = {
        "issues": [],
        "dimension_results": [
            {"dimension": dimension, "conclusion": "pass"}
            for dimension in REVIEW_DIMENSIONS
        ],
        "summary": "无问题",
    }

    result = parse_review_output(chapter=5, raw=raw)

    assert [item["dimension"] for item in result.dimension_results] == list(REVIEW_DIMENSIONS)
    assert result.to_dict()["dimension_results"] == raw["dimension_results"]


def test_parse_review_output_tolerates_missing_fields():
    raw = {
        "issues": [
            {"severity": "low", "description": "小问题"},
        ],
        "summary": "轻微",
    }
    result = parse_review_output(chapter=1, raw=raw)
    assert result.issues[0].category == "other"
    assert result.issues[0].location == ""


def test_review_result_to_metrics_dict():
    result = ReviewResult(
        chapter=10,
        issues=[
            ReviewIssue(severity="critical", category="continuity", location="p1", description="d1"),
            ReviewIssue(severity="high", category="ai_flavor", location="p2", description="d2"),
        ],
        summary="测试",
    )
    metrics = result.to_metrics_dict()
    assert metrics["chapter"] == 10
    assert metrics["start_chapter"] == 10
    assert metrics["end_chapter"] == 10
    assert metrics["issues_count"] == 2
    assert metrics["blocking_count"] == 1
    assert "continuity" in metrics["categories"]
    assert "ai_flavor" in metrics["categories"]
    assert metrics["severity_counts"]["critical"] == 1
    assert metrics["severity_counts"]["high"] == 1
    assert metrics["critical_issues"] == ["d1"]
    assert metrics["report_file"] == ""
    assert metrics["overall_score"] < 100
    assert metrics["dimension_scores"]["continuity"] < 100
    assert metrics["dimension_scores"]["ai_flavor"] < 100
    assert metrics["dimension_scores"]["readability"] == 100


def test_ai_flavor_review_issue_added_to_anti_patterns(tmp_path):
    result = ReviewResult(
        chapter=2,
        issues=[
            ReviewIssue(
                severity="medium",
                category="ai_flavor",
                evidence="唯一一个知道复利公式的人。唯一一个知道账本秘密的人。",
            ),
            ReviewIssue(severity="low", category="ai_flavor", evidence="低风险句式"),
            ReviewIssue(severity="high", category="logic", evidence="逻辑问题"),
        ],
    )

    added = append_ai_flavor_anti_patterns(tmp_path, result)

    patterns = json.loads((tmp_path / ".story-system" / "anti_patterns.json").read_text(encoding="utf-8"))
    assert added == 1
    assert any("唯一一个知道" in item["text"] for item in patterns)
    assert patterns[0]["source_id"].startswith("ch0002_issue_")


def test_readability_review_issue_added_with_reusable_rule(tmp_path):
    result = ReviewResult(
        chapter=1,
        issues=[
            ReviewIssue(
                severity="high",
                code="IMPLICIT_SPEECH_ACT",
                category="readability",
                description="回应依赖前句未说出的开门请求",
                evidence="“开业了。” / “你开。”",
                fix_hint="补回明确请求，让相邻对白字面可承接",
            )
        ],
    )

    added = append_ai_flavor_anti_patterns(tmp_path, result)

    patterns = json.loads((tmp_path / ".story-system" / "anti_patterns.json").read_text(encoding="utf-8"))
    assert added == 1
    assert patterns[0]["category"] == "readability"
    assert patterns[0]["issue_code"] == "IMPLICIT_SPEECH_ACT"
    assert "字面可承接" in patterns[0]["fix_hint"]


def test_ai_flavor_review_feedback_dedupes_evidence(tmp_path):
    existing = tmp_path / ".story-system" / "anti_patterns.json"
    existing.parent.mkdir(parents=True)
    existing.write_text(
        json.dumps([{"text": "第一片 / 第二片 / 第三片", "source_table": "review_extracted"}], ensure_ascii=False),
        encoding="utf-8",
    )
    result = ReviewResult(
        chapter=3,
        issues=[
            ReviewIssue(
                severity="high",
                category="ai_flavor",
                evidence="第一片 / 第二片 / 第三片",
            )
        ],
    )

    added = append_ai_flavor_anti_patterns(tmp_path, result)

    patterns = json.loads(existing.read_text(encoding="utf-8"))
    assert added == 0
    assert len(patterns) == 1
