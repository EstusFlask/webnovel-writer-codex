#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path


def _ensure_scripts_on_path() -> None:
    scripts_dir = Path(__file__).resolve().parents[1]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


_ensure_scripts_on_path()

from validate_plugin_package import validate_package  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_minimal_package(root: Path, *, plugin_version: str = "1.2.3", marketplace_version: str = "1.2.3") -> None:
    _write_json(
        root / "webnovel-writer" / ".claude-plugin" / "plugin.json",
        {"name": "webnovel-writer", "version": plugin_version, "description": "desc"},
    )
    _write_json(
        root / "webnovel-writer" / ".codex-plugin" / "plugin.json",
        {
            "name": "webnovel-writer",
            "version": plugin_version,
            "description": "desc",
            "skills": "./skills/",
        },
    )
    _write_json(
        root / ".claude-plugin" / "marketplace.json",
        {
            "plugins": [
                {
                    "name": "webnovel-writer",
                    "version": marketplace_version,
                    "source": "./webnovel-writer",
                }
            ]
        },
    )
    (root / "README.md").write_text(
        "\n".join(
            [
                "# Test",
                "",
                f"[![Version](https://img.shields.io/badge/version-{plugin_version}-brightgreen.svg)](.claude-plugin/marketplace.json)",
                "",
                "| 版本 | 说明 |",
                "|------|------|",
                f"| **v{plugin_version} (当前)** | test |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "webnovel-writer" / "LICENSE").parent.mkdir(parents=True, exist_ok=True)
    (root / "webnovel-writer" / "LICENSE").write_text("license\n", encoding="utf-8")
    skill = root / "webnovel-writer" / "skills" / "demo" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text("---\nname: demo\ndescription: demo\n---\n\n# Demo\n", encoding="utf-8")
    compat = "Codex 兼容模式：未调用 subagent，使用兼容模式。"
    for skill_name in ("webnovel-init", "webnovel-write", "webnovel-review"):
        path = root / "webnovel-writer" / "skills" / skill_name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\nname: {skill_name}\ndescription: demo\n---\n\n# Demo\n\n{compat}\n",
            encoding="utf-8",
        )
    using = root / "webnovel-writer" / "skills" / "using-webnovel-writer" / "SKILL.md"
    using.parent.mkdir(parents=True, exist_ok=True)
    using.write_text(
        "---\nname: using-webnovel-writer\ndescription: demo\n---\n\n"
        "Use compatibility mode with agents/*.md and say no subagent was called.\n",
        encoding="utf-8",
    )
    support = root / "webnovel-writer" / "adapters" / "codex" / "support.md"
    support.parent.mkdir(parents=True, exist_ok=True)
    support.write_text(
        "compatibility mode; no subagent was called; agents/*.md; "
        "webnovel-writer:context-agent; webnovel-writer:reviewer; "
        "webnovel-writer:data-agent; webnovel-writer:deconstruction-agent\n",
        encoding="utf-8",
    )
    agents_dir = root / "webnovel-writer" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for agent_name in ("demo", "context-agent", "reviewer", "data-agent", "deconstruction-agent"):
        agent = agents_dir / f"{agent_name}.md"
        agent.write_text(
            f"---\nname: {agent_name}\ndescription: demo\ntools: Read\n---\n\n# Demo\n",
            encoding="utf-8",
        )


def test_validate_plugin_package_passes_minimal_package(tmp_path):
    _write_minimal_package(tmp_path)

    report = validate_package(tmp_path)

    assert report["ok"] is True
    assert report["error_count"] == 0


def test_validate_plugin_package_accepts_plugin_root(tmp_path):
    _write_minimal_package(tmp_path)

    report = validate_package(tmp_path / "webnovel-writer")

    assert report["ok"] is True
    assert report["error_count"] == 0


def test_validate_plugin_package_detects_version_mismatch(tmp_path):
    _write_minimal_package(tmp_path, plugin_version="1.2.3", marketplace_version="1.2.4")

    report = validate_package(tmp_path)

    assert report["ok"] is False
    assert any(item["code"] == "version.marketplace" for item in report["issues"])


def test_validate_plugin_package_detects_codex_version_mismatch(tmp_path):
    _write_minimal_package(tmp_path)
    codex_manifest = tmp_path / "webnovel-writer" / ".codex-plugin" / "plugin.json"
    payload = json.loads(codex_manifest.read_text(encoding="utf-8"))
    payload["version"] = "1.2.4"
    _write_json(codex_manifest, payload)

    report = validate_package(tmp_path)

    assert report["ok"] is False
    assert any(item["code"] == "version.codex_manifest" for item in report["issues"])


def test_validate_plugin_package_rejects_codex_agents_field(tmp_path):
    _write_minimal_package(tmp_path)
    codex_manifest = tmp_path / "webnovel-writer" / ".codex-plugin" / "plugin.json"
    payload = json.loads(codex_manifest.read_text(encoding="utf-8"))
    payload["agents"] = "./agents/"
    _write_json(codex_manifest, payload)

    report = validate_package(tmp_path)

    assert report["ok"] is False
    assert any(item["code"] == "manifest.codex_agents_unsupported" for item in report["issues"])


def test_validate_plugin_package_detects_readme_badge_mismatch(tmp_path):
    _write_minimal_package(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8").replace("version-1.2.3", "version-1.2.2"), encoding="utf-8")

    report = validate_package(tmp_path)

    assert report["ok"] is False
    assert any(item["code"] == "version.readme_badge" for item in report["issues"])


def test_validate_plugin_package_detects_missing_skill_frontmatter(tmp_path):
    _write_minimal_package(tmp_path)
    skill = tmp_path / "webnovel-writer" / "skills" / "demo" / "SKILL.md"
    skill.write_text("---\nname: demo\n---\n\n# Demo\n", encoding="utf-8")

    report = validate_package(tmp_path)

    assert report["ok"] is False
    assert any(item["code"] == "skill.frontmatter" for item in report["issues"])


def test_validate_plugin_package_detects_non_utf8_skill_text(tmp_path):
    _write_minimal_package(tmp_path)
    skill = tmp_path / "webnovel-writer" / "skills" / "demo" / "SKILL.md"
    skill.write_bytes("---\nname: demo\ndescription: 写章\n---\n".encode("gbk"))

    report = validate_package(tmp_path)

    assert report["ok"] is False
    assert any(item["code"] == "text.encoding" and str(skill) == item["path"] for item in report["issues"])


def test_validate_plugin_package_detects_mojibake_skill_text(tmp_path):
    _write_minimal_package(tmp_path)
    skill = tmp_path / "webnovel-writer" / "skills" / "demo" / "SKILL.md"
    skill.write_text("---\nname: demo\ndescription: demo\n---\n\n# Demo\n\nUse domains\u9225\u6516asks.\n", encoding="utf-8")

    report = validate_package(tmp_path)

    assert report["ok"] is False
    assert any(item["code"] == "text.mojibake" and str(skill) == item["path"] for item in report["issues"])
