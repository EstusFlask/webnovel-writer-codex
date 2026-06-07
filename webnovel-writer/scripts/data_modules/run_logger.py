#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "webnovel-run-log/v1"
LOG_REL = Path(".webnovel") / "logs" / "run_last.log"
SENSITIVE_KEY_RE = re.compile(r"(api[_-]?key|secret|token|authorization|password|passwd|credential)", re.IGNORECASE)
ASSIGNMENT_RE = re.compile(
    r"(?P<key>[A-Za-z0-9_.-]*(?:api[_-]?key|secret|token|authorization|password|passwd|credential)[A-Za-z0-9_.-]*)"
    r"(?P<sep>\s*[:=]\s*)"
    r"(?P<value>\"[^\"]*\"|'[^']*'|[^\s,;]+)",
    re.IGNORECASE,
)


def log_path(project_root: str | Path) -> Path:
    return Path(project_root) / LOG_REL


def redact_text(text: str) -> str:
    raw = str(text)
    return ASSIGNMENT_RE.sub(lambda match: f"{match.group('key')}{match.group('sep')}<redacted>", raw)


def redact_payload(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                result[str(key)] = "<redacted>"
            else:
                result[str(key)] = redact_payload(item)
        return result
    if isinstance(value, list):
        return [redact_payload(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_run_log(
    project_root: str | Path,
    *,
    event: str,
    payload: dict[str, Any] | None = None,
    append: bool = False,
) -> dict[str, Any]:
    path = log_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now_iso(),
        "event": str(event),
        "payload": redact_payload(payload or {}),
    }
    line = json.dumps(record, ensure_ascii=False, sort_keys=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as handle:
        handle.write(line)
        handle.write("\n")
    return {"schema_version": SCHEMA_VERSION, "path": str(path), "record": record}


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a redacted webnovel run log entry")
    parser.add_argument("--project-root", required=True, help="书项目根目录")
    parser.add_argument("--event", required=True, help="事件名")
    parser.add_argument("--payload-json", default="{}", help="要写入日志的 JSON 对象")
    parser.add_argument("--append", action="store_true", help="追加而不是覆盖 run_last.log")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    try:
        payload = json.loads(args.payload_json)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"payload-json 不是合法 JSON: {exc}")
    if not isinstance(payload, dict):
        raise SystemExit("payload-json 必须是 JSON object")
    result = write_run_log(args.project_root, event=args.event, payload=payload, append=args.append)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["path"])


if __name__ == "__main__":
    main()
