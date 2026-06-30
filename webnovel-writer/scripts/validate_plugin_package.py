#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import sync_plugin_version
from runtime_compat import enable_windows_utf8_stdio


SCHEMA_VERSION = "webnovel-plugin-package-validator/v1"
PLUGIN_NAME = "webnovel-writer"
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = sync_plugin_version.VERSION_PATTERN
LOCAL_ABSOLUTE_RE = re.compile(r"(?i)(?:[a-z]:\\users\\|/users/[^/\s]+/|/home/[^/\s]+/)")
TEXT_SUFFIXES = {".csv", ".json", ".md", ".py", ".sh", ".yaml", ".yml"}
MOJIBAKE_MARKERS = ("\ufffd", "\u9225", "\u9239", "\u951f\u65a4\u62f7")


def _issue(
    code: str,
    *,
    message: str,
    severity: str = "error",
    path: str = "",
    repair: str = "",
) -> dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "path": path,
        "repair": repair,
    }


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "missing"
    except UnicodeDecodeError as exc:
        return {}, f"invalid_utf8:{exc}"
    except json.JSONDecodeError as exc:
        return {}, f"invalid_json:{exc}"
    except OSError as exc:
        return {}, f"read_error:{exc}"
    if not isinstance(payload, dict):
        return {}, "not_object"
    return payload, ""


def _frontmatter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {}
    except OSError:
        return {}
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


def _marketplace_plugin(payload: dict[str, Any]) -> dict[str, Any] | None:
    plugins = payload.get("plugins")
    if not isinstance(plugins, list):
        return None
    for item in plugins:
        if isinstance(item, dict) and item.get("name") == PLUGIN_NAME:
            return item
    return None


def _is_plugin_root(root: Path) -> bool:
    return (
        (root / ".claude-plugin" / "plugin.json").is_file()
        or (root / ".codex-plugin" / "plugin.json").is_file()
    )


def _plugin_root(root: Path) -> Path:
    return root if _is_plugin_root(root) else root / PLUGIN_NAME


def _repo_root(root: Path) -> Path:
    if _is_plugin_root(root) and (root.parent / ".claude-plugin" / "marketplace.json").is_file():
        return root.parent
    return root


def _check_manifest(root: Path, issues: list[dict[str, str]]) -> tuple[str, str]:
    plugin_json = _plugin_root(root) / ".claude-plugin" / "plugin.json"
    payload, error = _load_json(plugin_json)
    if error:
        issues.append(_issue("manifest.plugin_json", message=error, path=str(plugin_json), repair="恢复 .claude-plugin/plugin.json。"))
        return "", ""
    name = str(payload.get("name") or "")
    version = str(payload.get("version") or "")
    if not KEBAB_RE.fullmatch(name):
        issues.append(_issue("manifest.name", message=f"invalid plugin name: {name}", path=str(plugin_json), repair="使用 kebab-case 插件名。"))
    if not SEMVER_RE.fullmatch(version):
        issues.append(_issue("manifest.version", message=f"invalid semver: {version}", path=str(plugin_json), repair="使用 X.Y.Z 版本号。"))
    if not str(payload.get("description") or "").strip():
        issues.append(_issue("manifest.description", message="plugin description missing", path=str(plugin_json), repair="补齐 description。"))
    return name, version


def _check_codex_manifest(root: Path, claude_version: str, issues: list[dict[str, str]]) -> None:
    plugin_json = _plugin_root(root) / ".codex-plugin" / "plugin.json"
    payload, error = _load_json(plugin_json)
    if error:
        issues.append(
            _issue(
                "manifest.codex_plugin_json",
                message=error,
                path=str(plugin_json),
                repair="恢复 .codex-plugin/plugin.json，Codex 兼容入口依赖该 manifest。",
            )
        )
        return

    name = str(payload.get("name") or "")
    version = str(payload.get("version") or "")
    if name != PLUGIN_NAME:
        issues.append(
            _issue(
                "manifest.codex_name",
                message=f"unexpected Codex plugin name: {name}",
                path=str(plugin_json),
                repair=f"Codex manifest name 应为 {PLUGIN_NAME}。",
            )
        )
    if claude_version and version != claude_version:
        issues.append(
            _issue(
                "version.codex_manifest",
                message=f"claude plugin.json={claude_version}, codex plugin.json={version}",
                path=str(plugin_json),
                repair="运行 sync_plugin_version.py --version X.Y.Z --release-notes ...。",
            )
        )
    if payload.get("skills") != "./skills/":
        issues.append(
            _issue(
                "manifest.codex_skills",
                message=f"unexpected Codex skills path: {payload.get('skills')}",
                path=str(plugin_json),
                repair='Codex manifest 应声明 "skills": "./skills/"。',
            )
        )
    if "agents" in payload:
        issues.append(
            _issue(
                "manifest.codex_agents_unsupported",
                message="Codex plugin manifest does not support an agents field",
                path=str(plugin_json),
                repair="不要在 .codex-plugin/plugin.json 中伪注册 agents；通过 skills 内的兼容模式读取 agents/*.md。",
            )
        )


def _check_marketplace(root: Path, plugin_version: str, issues: list[dict[str, str]]) -> None:
    marketplace = _repo_root(root) / ".claude-plugin" / "marketplace.json"
    payload, error = _load_json(marketplace)
    if error:
        severity = "warning" if _is_plugin_root(root) else "error"
        issues.append(
            _issue(
                "marketplace.json",
                message=error,
                severity=severity,
                path=str(marketplace),
                repair="在仓库根运行可校验 marketplace；插件根安装包可忽略该项。",
            )
        )
        return
    plugin = _marketplace_plugin(payload)
    if plugin is None:
        issues.append(_issue("marketplace.plugin", message=f"{PLUGIN_NAME} missing from marketplace", path=str(marketplace), repair="在 plugins[] 中加入 webnovel-writer。"))
        return
    if plugin.get("source") != "./webnovel-writer":
        issues.append(_issue("marketplace.source", message=f"unexpected source: {plugin.get('source')}", path=str(marketplace), repair="source 应为 ./webnovel-writer。"))
    marketplace_version = str(plugin.get("version") or "")
    if plugin_version and marketplace_version != plugin_version:
        issues.append(
            _issue(
                "version.marketplace",
                message=f"plugin.json={plugin_version}, marketplace.json={marketplace_version}",
                path=str(marketplace),
                repair="运行 sync_plugin_version.py --version X.Y.Z --release-notes ...。",
            )
        )


def _check_readme_version(root: Path, plugin_version: str, issues: list[dict[str, str]]) -> None:
    if _is_plugin_root(root):
        candidates = [_repo_root(root) / "README.md", root / "README.md"]
    else:
        candidates = [root / "README.md", _plugin_root(root) / "README.md"]
    readme = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    try:
        content = readme.read_text(encoding="utf-8")
        readme_version = sync_plugin_version.get_readme_current_version(content)
        readme_badge_version = sync_plugin_version.get_readme_badge_version(content)
    except Exception as exc:
        issues.append(_issue("version.readme.parse", message=str(exc), path=str(readme), repair="保持 README 版本表格式与 sync_plugin_version.py 一致。"))
        return
    if plugin_version and readme_version != plugin_version:
        issues.append(
            _issue(
                "version.readme",
                message=f"plugin.json={plugin_version}, README.md={readme_version}",
                path=str(readme),
                repair="运行 sync_plugin_version.py --version X.Y.Z --release-notes ...。",
            )
        )
    if plugin_version and readme_badge_version != plugin_version:
        issues.append(
            _issue(
                "version.readme_badge",
                message=f"plugin.json={plugin_version}, README badge={readme_badge_version}",
                path=str(readme),
                repair="运行 sync_plugin_version.py --version X.Y.Z --release-notes ...。",
            )
        )


def _iter_plugin_text_files(root: Path) -> list[Path]:
    plugin_root = _plugin_root(root)
    roots = [
        plugin_root / ".claude-plugin",
        plugin_root / ".codex-plugin",
        plugin_root / "adapters",
        plugin_root / "agents",
        plugin_root / "hooks",
        plugin_root / "references",
        plugin_root / "scripts",
        plugin_root / "skills",
        plugin_root / "templates",
    ]
    files = [plugin_root / "README.md", plugin_root / "LICENSE"]
    marketplace = _repo_root(root) / ".claude-plugin" / "marketplace.json"
    if marketplace.is_file():
        files.append(marketplace)
    for base in roots:
        if base.is_dir():
            files.extend(path for path in base.rglob("*") if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES)
    return sorted({path for path in files if path.is_file()})


def _check_text_encoding(root: Path, issues: list[dict[str, str]]) -> None:
    for path in _iter_plugin_text_files(root):
        try:
            raw = path.read_bytes()
        except OSError as exc:
            issues.append(_issue("text.read", message=str(exc), path=str(path), repair="确认发布文件可读。"))
            continue
        if raw.startswith(b"\xef\xbb\xbf"):
            severity = "error" if path.name == "SKILL.md" or path.suffix.lower() == ".json" else "warning"
            issues.append(
                _issue(
                    "text.utf8_bom",
                    message="UTF-8 BOM found",
                    severity=severity,
                    path=str(path),
                    repair="以 UTF-8 无 BOM 保存插件文本文件，避免 frontmatter/manifest 解析漂移。",
                )
            )
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            issues.append(
                _issue(
                    "text.encoding",
                    message=f"file is not strict UTF-8: {exc}",
                    path=str(path),
                    repair="用 UTF-8 无 BOM 重新保存该文件；Windows PowerShell 读取时使用 Get-Content -Encoding UTF8。",
                )
            )
            continue
        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                issues.append(
                    _issue(
                        "text.mojibake",
                        message=f"possible mojibake marker found: {marker}",
                        path=str(path),
                        repair="检查是否曾被 ANSI/GBK/Windows-1252 错误解码后保存，并用原始中文 UTF-8 内容替换。",
                    )
                )
                break


def _check_frontmatter(root: Path, issues: list[dict[str, str]]) -> None:
    plugin_root = _plugin_root(root)
    for skill in sorted((plugin_root / "skills").glob("*/SKILL.md")):
        fm = _frontmatter(skill)
        for field in ("name", "description"):
            if not fm.get(field):
                issues.append(_issue("skill.frontmatter", message=f"skill missing {field}", path=str(skill), repair="按 plugin-dev skill-development 补齐 frontmatter。"))
    for agent in sorted((plugin_root / "agents").glob("*.md")):
        fm = _frontmatter(agent)
        for field in ("name", "description", "tools"):
            if not fm.get(field):
                issues.append(_issue("agent.frontmatter", message=f"agent missing {field}", path=str(agent), repair="按 plugin-dev agent-development 补齐 frontmatter。"))


def _check_optional_assets(root: Path, issues: list[dict[str, str]]) -> None:
    plugin_root = _plugin_root(root)
    if not (plugin_root / "LICENSE").is_file():
        issues.append(_issue("license", message="LICENSE missing", severity="error", path=str(plugin_root / "LICENSE"), repair="恢复插件 LICENSE。"))
    dashboard_dist = plugin_root / "dashboard" / "frontend" / "dist"
    if not dashboard_dist.is_dir():
        issues.append(_issue("dashboard.dist", message="dashboard frontend dist missing", severity="warning", path=str(dashboard_dist), repair="发布前运行 dashboard 前端 build 并包含 dist。"))
    hooks_json = plugin_root / "hooks" / "hooks.json"
    if hooks_json.exists():
        payload, error = _load_json(hooks_json)
        if error:
            issues.append(_issue("hooks.schema", message=error, path=str(hooks_json), repair="修复 hooks/hooks.json。"))
        elif "description" not in payload or "hooks" not in payload:
            issues.append(_issue("hooks.wrapper", message="hooks.json should use plugin-dev wrapper format", path=str(hooks_json), repair="外层包含 description 与 hooks。"))


def _check_portability(root: Path, issues: list[dict[str, str]]) -> None:
    plugin_root = _plugin_root(root)
    targets = list((plugin_root / "skills").glob("*/SKILL.md"))
    targets.extend((plugin_root / "agents").glob("*.md"))
    targets.extend((plugin_root / ".claude-plugin").glob("*.json"))
    targets.extend((plugin_root / ".codex-plugin").glob("*.json"))
    hooks_root = plugin_root / "hooks"
    if hooks_root.is_dir():
        targets.extend(path for path in hooks_root.rglob("*") if path.suffix in {".json", ".py", ".sh", ".md"})
    for path in targets:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        if LOCAL_ABSOLUTE_RE.search(text):
            issues.append(
                _issue(
                    "portability.local_absolute_path",
                    message="local absolute path found in plugin component",
                    severity="warning",
                    path=str(path),
                    repair="插件组件内使用 ${CLAUDE_PLUGIN_ROOT} 或相对路径。",
                )
            )


def _check_codex_agent_compatibility(root: Path, issues: list[dict[str, str]]) -> None:
    plugin_root = _plugin_root(root)
    support_doc = plugin_root / "adapters" / "codex" / "support.md"
    using_skill = plugin_root / "skills" / "using-webnovel-writer" / "SKILL.md"
    business_skills = (
        plugin_root / "skills" / "webnovel-init" / "SKILL.md",
        plugin_root / "skills" / "webnovel-write" / "SKILL.md",
        plugin_root / "skills" / "webnovel-review" / "SKILL.md",
    )

    for filename in (
        "context-agent.md",
        "reviewer.md",
        "data-agent.md",
        "deconstruction-agent.md",
    ):
        path = plugin_root / "agents" / filename
        if not path.is_file():
            issues.append(
                _issue(
                    "codex.agent_file",
                    message=f"agent file missing: {filename}",
                    path=str(path),
                    repair="恢复 agents/*.md；Codex 兼容模式按这些文件执行边界。",
                )
            )

    docs_text = ""
    for path in (support_doc, using_skill):
        try:
            docs_text += "\n" + path.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(
                _issue(
                    "codex.compat_doc",
                    message=str(exc),
                    path=str(path),
                    repair="恢复 Codex adapter 文档和 using-webnovel-writer skill。",
                )
            )
    for required in (
        "compatibility mode",
        "no subagent was called",
        "agents/*.md",
        "webnovel-writer:context-agent",
        "webnovel-writer:reviewer",
        "webnovel-writer:data-agent",
        "webnovel-writer:deconstruction-agent",
    ):
        if required not in docs_text:
            issues.append(
                _issue(
                    "codex.compat_doc",
                    message=f"missing compatibility wording: {required}",
                    path=str(support_doc),
                    repair="在 Codex adapter 文档中说明无 Agent 工具时的 agents/*.md 兼容模式。",
                )
            )

    for path in business_skills:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(
                _issue(
                    "codex.compat_skill",
                    message=str(exc),
                    path=str(path),
                    repair="恢复业务 Skill 的 Codex 兼容模式说明。",
                )
            )
            continue
        for required in ("Codex", "兼容模式", "未调用 subagent，使用兼容模式"):
            if required not in text:
                issues.append(
                    _issue(
                        "codex.compat_skill",
                        message=f"missing Codex agent compatibility wording: {required}",
                        path=str(path),
                        repair="业务 Skill 调用 Agent 的地方必须说明无 Agent 工具时按对应 agents/*.md 在主流程执行。",
                    )
                )


def validate_package(root: str | Path | None = None, *, strict: bool = False) -> dict[str, Any]:
    repo_root = Path(root) if root is not None else Path(__file__).resolve().parent.parent.parent
    issues: list[dict[str, str]] = []
    _, plugin_version = _check_manifest(repo_root, issues)
    _check_codex_manifest(repo_root, plugin_version, issues)
    _check_marketplace(repo_root, plugin_version, issues)
    _check_readme_version(repo_root, plugin_version, issues)
    _check_text_encoding(repo_root, issues)
    _check_frontmatter(repo_root, issues)
    _check_optional_assets(repo_root, issues)
    _check_portability(repo_root, issues)
    _check_codex_agent_compatibility(repo_root, issues)
    blocking = [
        item for item in issues if item["severity"] == "error" or (strict and item["severity"] == "warning")
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": not blocking,
        "strict": strict,
        "root": str(repo_root),
        "error_count": sum(1 for item in issues if item["severity"] == "error"),
        "warning_count": sum(1 for item in issues if item["severity"] == "warning"),
        "issues": issues,
    }


def format_report(report: dict[str, Any], output_format: str = "text") -> str:
    if output_format == "json":
        return json.dumps(report, ensure_ascii=False, indent=2)
    status = "OK" if report.get("ok") else "ERROR"
    lines = [
        f"{status} plugin package",
        f"errors: {report.get('error_count')} warnings: {report.get('warning_count')}",
    ]
    for item in report.get("issues") or []:
        lines.append(f"{item.get('severity', '').upper()} {item.get('code')}: {item.get('message')}")
        if item.get("path"):
            lines.append(f"  path: {item.get('path')}")
        if item.get("repair"):
            lines.append(f"  repair: {item.get('repair')}")
    return "\n".join(lines)


def main() -> int:
    enable_windows_utf8_stdio()
    parser = argparse.ArgumentParser(description="Validate webnovel-writer plugin package metadata and components")
    parser.add_argument("--root", default="", help="仓库根目录，默认自动推断")
    parser.add_argument("--strict", action="store_true", help="warning 也视为失败")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    report = validate_package(args.root or None, strict=args.strict)
    print(format_report(report, args.format))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
