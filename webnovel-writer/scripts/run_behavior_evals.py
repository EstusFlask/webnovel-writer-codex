#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

from runtime_compat import enable_windows_utf8_stdio


SCHEMA_VERSION = "webnovel-behavior-eval-report/v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _plugin_root(root: Path) -> Path:
    if (root / ".claude-plugin" / "plugin.json").is_file():
        return root
    return root / "webnovel-writer"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        result[key.strip()] = value.strip()
    return result


def _result(case: dict[str, Any], *, passed: bool, reason: str, evidence: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": case.get("id"),
        "type": case.get("type"),
        "passed": passed,
        "reason": reason,
        "evidence": evidence or [],
    }


def _eval_skill_frontmatter(root: Path, case: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    for skill in sorted((_plugin_root(root) / "skills").glob("*/SKILL.md")):
        fm = _frontmatter(_read(skill))
        if not fm.get("name") or not fm.get("description"):
            missing.append(str(skill.relative_to(root)))
    return _result(
        case,
        passed=not missing,
        reason="all skills have name and description" if not missing else "skill frontmatter missing",
        evidence=missing,
    )


def _eval_skill_contract(root: Path, case: dict[str, Any]) -> dict[str, Any]:
    skill_name = str(case.get("skill") or "").strip()
    path = _plugin_root(root) / "skills" / skill_name / "SKILL.md"
    if not path.is_file():
        return _result(case, passed=False, reason="skill missing", evidence=[str(path)])
    text = _read(path)
    missing = [str(item) for item in case.get("required") or [] if str(item) not in text]
    for group in case.get("required_any") or []:
        options = [str(item) for item in group]
        if options and not any(option in text for option in options):
            missing.append("one of: " + " | ".join(options))

    ordering_errors: list[str] = []
    for pair in case.get("ordered") or []:
        if not isinstance(pair, list) or len(pair) != 2:
            continue
        left, right = str(pair[0]), str(pair[1])
        left_pos = text.find(left)
        right_pos = text.find(right)
        if left_pos < 0 or right_pos < 0 or left_pos >= right_pos:
            ordering_errors.append(f"{left} before {right}")

    forbidden = [
        str(pattern)
        for pattern in case.get("forbidden_patterns") or []
        if re.search(str(pattern), text)
    ]
    passed = not missing and not ordering_errors and not forbidden
    return _result(
        case,
        passed=passed,
        reason=f"{skill_name} contract holds" if passed else f"{skill_name} contract drifted",
        evidence=missing + ordering_errors + forbidden or [str(path.relative_to(root))],
    )


def _eval_write_blocking_gate(root: Path, case: dict[str, Any]) -> dict[str, Any]:
    path = _plugin_root(root) / "skills" / "webnovel-write" / "SKILL.md"
    text = _read(path)
    required = [
        "blocking=true",
        "write-gate --chapter {chapter_num} --stage prewrite",
        "write-gate --chapter {chapter_num} --stage precommit",
        "write-gate --chapter {chapter_num} --stage postcommit",
        "chapter-commit",
    ]
    missing = [item for item in required if item not in text]
    precommit_pos = text.find("write-gate --chapter {chapter_num} --stage precommit")
    commit_pos = text.find("chapter-commit")
    ordering_ok = precommit_pos >= 0 and commit_pos >= 0 and precommit_pos < commit_pos
    if not ordering_ok:
        missing.append("precommit gate must appear before chapter-commit")
    return _result(
        case,
        passed=not missing,
        reason="write flow keeps blocking and runtime gates" if not missing else "write flow contract missing",
        evidence=missing or [str(path.relative_to(root))],
    )


def _eval_data_agent_boundary(root: Path, case: dict[str, Any]) -> dict[str, Any]:
    path = _plugin_root(root) / "agents" / "data-agent.md"
    text = _read(path)
    required = [
        "产出三份 JSON 到 `.webnovel/tmp/`",
        "不直接写 state/index/summaries/memory",
        "chapter-commit",
    ]
    missing = [item for item in required if item not in text]
    forbidden_patterns = [
        r"webnovel\.py[^\n]+state\s+process",
        r"webnovel\.py[^\n]+memory\s+update",
        r"webnovel\.py[^\n]+rag\s+index-chapter",
    ]
    forbidden = [pattern for pattern in forbidden_patterns if re.search(pattern, text)]
    return _result(
        case,
        passed=not missing and not forbidden,
        reason="data-agent boundary is artifact-only" if not missing and not forbidden else "data-agent boundary drifted",
        evidence=missing + forbidden or [str(path.relative_to(root))],
    )


def _eval_artifact_ownership(root: Path, case: dict[str, Any]) -> dict[str, Any]:
    plugin_root = _plugin_root(root)
    write_text = _read(plugin_root / "skills" / "webnovel-write" / "SKILL.md")
    review_text = _read(plugin_root / "skills" / "webnovel-review" / "SKILL.md")
    reviewer_tools = _frontmatter(_read(plugin_root / "agents" / "reviewer.md")).get("tools", "")
    data_tools = _frontmatter(_read(plugin_root / "agents" / "data-agent.md")).get("tools", "")
    missing: list[str] = []
    if "Write" in reviewer_tools:
        missing.append("reviewer 不应持 Write（review_results.json 由主流程落盘）")
    if "Write" not in data_tools:
        missing.append("data-agent 应持 Write（它是 tmp artifact 的唯一写入者）")
    for text, owner in ((write_text, "webnovel-write"), (review_text, "webnovel-review")):
        if "主流程" not in text or ".webnovel/tmp/review_results.json" not in text:
            missing.append(f"{owner}: 缺 reviewer→主流程落盘 review_results.json 的所有权说明")
    for item in (
        "唯一写入者",
        "主流程只检查文件存在与 schema",
        "不直接写 state/index/summaries/memory/vectors/projection",
    ):
        if item not in write_text:
            missing.append(f"webnovel-write 缺写入所有权红线：{item}")
    return _result(
        case,
        passed=not missing,
        reason="artifact ownership matches tools and prompts" if not missing else "artifact ownership drifted",
        evidence=missing or ["reviewer→主流程 review_results.json；data-agent→tmp artifacts"],
    )


def _eval_commit_projection_runtime(root: Path, case: dict[str, Any]) -> dict[str, Any]:
    scripts_dir = _plugin_root(root) / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from data_modules.chapter_commit_service import ChapterCommitService

    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
        (project_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")
        service = ChapterCommitService(project_root)
        payload = service.build_commit(
            chapter=1,
            review_result={"blocking_count": 1},
            fulfillment_result={"planned_nodes": [], "covered_nodes": [], "missed_nodes": [], "extra_nodes": []},
            disambiguation_result={"pending": []},
            extraction_result={"accepted_events": [], "state_deltas": [], "entity_deltas": []},
        )
        projected = service.apply_projections(payload)
        state_path = project_root / ".webnovel" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
    ok = (
        projected.get("projection_status", {}).get("state") == "done"
        and state.get("progress", {}).get("chapter_status", {}).get("1") == "chapter_rejected"
    )
    return _result(
        case,
        passed=ok,
        reason="chapter commit drives state projection" if ok else "chapter commit projection failed",
        evidence=[str(projected.get("projection_status"))],
    )


def _eval_dashboard_read_only(root: Path, case: dict[str, Any]) -> dict[str, Any]:
    path = _plugin_root(root) / "dashboard" / "app.py"
    text = _read(path)
    forbidden = re.findall(r"@app\.(post|put|delete|patch)\b", text)
    get_only = 'allow_methods=["GET"]' in text or 'allow_methods=[\n        "GET"' in text
    ok = not forbidden and get_only and "strictly read" not in text.lower()
    # The module's Chinese docstring is the authoritative local signal.
    ok = ok or (not forbidden and "仅提供 GET 接口" in text)
    return _result(
        case,
        passed=ok,
        reason="dashboard is GET-only" if ok else "dashboard write endpoint detected",
        evidence=forbidden or [str(path.relative_to(root))],
    )


EVALUATORS = {
    "skill_frontmatter": _eval_skill_frontmatter,
    "skill_contract": _eval_skill_contract,
    "write_blocking_gate": _eval_write_blocking_gate,
    "data_agent_boundary": _eval_data_agent_boundary,
    "artifact_ownership": _eval_artifact_ownership,
    "commit_projection_runtime": _eval_commit_projection_runtime,
    "dashboard_read_only": _eval_dashboard_read_only,
}


def load_suite(root: Path, suite: str) -> dict[str, Any]:
    path = _plugin_root(root) / "evals" / "fixtures" / "behavior" / f"{suite}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run_behavior_evals(root: str | Path | None = None, *, suite: str = "fast") -> dict[str, Any]:
    repo_root = Path(root) if root is not None else _repo_root()
    payload = load_suite(repo_root, suite)
    results: list[dict[str, Any]] = []
    for case in payload.get("cases") or []:
        evaluator = EVALUATORS.get(str(case.get("type") or ""))
        if evaluator is None:
            results.append(_result(case, passed=False, reason="unknown eval type"))
            continue
        try:
            results.append(evaluator(repo_root, case))
        except Exception as exc:
            results.append(_result(case, passed=False, reason=f"exception: {exc}"))
    failed = [item for item in results if not item.get("passed")]
    return {
        "schema_version": SCHEMA_VERSION,
        "suite": suite,
        "ok": not failed,
        "root": str(repo_root),
        "total": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": results,
    }


def format_report(report: dict[str, Any], output_format: str = "text") -> str:
    if output_format == "json":
        return json.dumps(report, ensure_ascii=False, indent=2)
    status = "OK" if report.get("ok") else "ERROR"
    lines = [f"{status} behavior evals {report.get('suite')}: {report.get('passed')}/{report.get('total')} passed"]
    for item in report.get("results") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"{marker} {item.get('id')}: {item.get('reason')}")
    return "\n".join(lines)


def main() -> int:
    if sys.platform == "win32":
        enable_windows_utf8_stdio()
    parser = argparse.ArgumentParser(description="Run deterministic webnovel-writer behavior evals")
    parser.add_argument("--root", default="", help="仓库根目录，默认自动推断")
    parser.add_argument("--suite", default="fast", choices=["fast"])
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    report = run_behavior_evals(args.root or None, suite=args.suite)
    print(format_report(report, args.format))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
