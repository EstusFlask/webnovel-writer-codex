---
name: using-webnovel-writer
description: Codex 中使用 Webnovel Writer 的总入口说明：解析插件根、运行 doctor/status、理解无 Claude Agent/hook 时的兼容模式。
---

# Using Webnovel Writer In Codex

Use this skill when the user asks how to use Webnovel Writer from Codex, asks for a Codex compatibility check, or asks to run the webnovel runtime without naming one of the narrower `webnovel-*` skills.

## Host Setup

Webnovel Writer keeps one Python runtime and exposes host-specific entry points. In Codex, treat the plugin root as the directory that contains `.codex-plugin/plugin.json`.

Before running examples from the business skills, set:

```bash
export WEBNOVEL_PLUGIN_ROOT="<installed webnovel-writer plugin root>"
export WORKSPACE_ROOT="${CODEX_PROJECT_DIR:-$PWD}"
export SCRIPTS_DIR="${WEBNOVEL_PLUGIN_ROOT}/scripts"
```

If Codex loaded this skill from an installed plugin path, infer `WEBNOVEL_PLUGIN_ROOT` by walking upward from this `SKILL.md` path to the directory containing `.codex-plugin/plugin.json`. Do not use the book project directory as the plugin root.

Claude Code still uses `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PROJECT_DIR`; keep those variables working for Claude users.

## First Checks

Run short status first:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" project-status --format summary
```

If the status is unclear or unhealthy, run the read-only doctor:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" doctor --format text
```

Use `webnovel-doctor` for diagnosis, `webnovel-query` for read-only story questions, and `webnovel-dashboard` for the local dashboard.

## Codex Compatibility Mode

Some Claude Code plugin affordances do not exist as the same tool names in Codex:

- Claude slash commands map to Codex skills. The user can still say `/webnovel-write 12`, but route by the matching skill name.
- Claude `Agent` tool calls may not be available. If unavailable, do not claim a subagent was called. Run the same step in compatibility mode, following the referenced agent file's boundaries and output schema in the main Codex flow.
- Claude hooks are not registered through the Codex manifest. Keep guardrails explicit: run `project-status`, `doctor`, and `write-gate` rather than relying on hidden hook execution.
- Use Codex native file and shell tools. `Read`, `Grep`, `Bash`, `Write`, and `Edit` in the original Claude skills correspond to Codex file reads/search, shell commands, and patch edits.

Compatibility mode must preserve the runtime invariants:

1. Never hand-write `.story-system/commits/` or `.webnovel/` read-model files.
2. Use `webnovel.py write-gate` before and after chapter commits.
3. Use `webnovel.py chapter-commit` for chapter fact submission.
4. If projections fail, retry with `webnovel.py projections retry` instead of rewriting artifacts manually.

## Narrow Skill Routing

Use the narrower skill when possible:

| User intent | Skill |
|---|---|
| Initialize a new novel project | `webnovel-init` |
| Plan a volume or chapters | `webnovel-plan` |
| Write a chapter | `webnovel-write` |
| Review chapters | `webnovel-review` |
| Query story state or settings | `webnovel-query` |
| Save a successful writing pattern | `webnovel-learn` |
| Open the read-only dashboard | `webnovel-dashboard` |
| Diagnose project health | `webnovel-doctor` |

Keep this file as host guidance only; do not duplicate the full business workflows here.
