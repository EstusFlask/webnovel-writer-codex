#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path


def _ensure_scripts_on_path() -> None:
    scripts_dir = Path(__file__).resolve().parents[2]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


_ensure_scripts_on_path()

from data_modules.run_logger import redact_payload, redact_text, write_run_log  # noqa: E402


def test_run_log_redacts_env_values(tmp_path: Path) -> None:
    result = write_run_log(
        tmp_path,
        event="failure",
        payload={
            "EMBED_API_KEY": "sk-real-key",
            "nested": {"authorization": "Bearer token-value"},
            "message": "RERANK_TOKEN=abc123 normal=value",
        },
    )

    log_text = Path(result["path"]).read_text(encoding="utf-8")
    assert "sk-real-key" not in log_text
    assert "token-value" not in log_text
    assert "abc123" not in log_text
    assert "<redacted>" in log_text
    record = json.loads(log_text)
    assert record["payload"]["EMBED_API_KEY"] == "<redacted>"
    assert record["payload"]["nested"]["authorization"] == "<redacted>"


def test_redact_helpers_keep_non_sensitive_content() -> None:
    assert redact_text("foo=bar") == "foo=bar"
    payload = redact_payload({"title": "测试书", "api_key": "secret"})
    assert payload == {"title": "测试书", "api_key": "<redacted>"}
