# Codex Adapter Support

Status: initial local adapter

Verified against local Codex plugin manifest validation on this machine.

## Supported

- `.codex-plugin/plugin.json` exposes the plugin to Codex.
- `skills/` are shared with the Claude Code plugin.
- `WEBNOVEL_PLUGIN_ROOT` is the cross-host plugin root variable used by Codex instructions.
- The Python runtime remains `scripts/webnovel.py`.
- Read-only flows (`webnovel-doctor`, `webnovel-query`, `webnovel-dashboard`) use the same runtime commands as Claude Code.

## Compatibility Mode

Codex does not use the Claude Code hook manifest in `hooks/hooks.json`.

When a business skill asks for the Claude `Agent` tool and that tool is not available, Codex must use compatibility mode:

1. Read the corresponding `agents/*.md` file.
2. Perform the same bounded task in the main flow.
3. Preserve the declared output schema.
4. State in the final report that no subagent was called and compatibility mode was used.

Do not claim that `webnovel-writer:context-agent`, `webnovel-writer:reviewer`, `webnovel-writer:data-agent`, or `webnovel-writer:deconstruction-agent` was invoked unless the host actually provides such a tool.

## Smoke Checks

From the repository root:

```bash
python -X utf8 C:/Users/x-ray/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py webnovel-writer
python -X utf8 webnovel-writer/scripts/validate_plugin_package.py --format json
```

For a real book project:

```bash
export WEBNOVEL_PLUGIN_ROOT="<plugin root>"
python -X utf8 "${WEBNOVEL_PLUGIN_ROOT}/scripts/webnovel.py" --project-root "<project root>" project-status --format summary
python -X utf8 "${WEBNOVEL_PLUGIN_ROOT}/scripts/webnovel.py" --project-root "<project root>" doctor --format text
```
