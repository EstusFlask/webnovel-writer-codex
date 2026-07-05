# Codex Adapter Support

Status: initial local adapter

Verified against local Codex plugin manifest validation on this machine.

## Supported

- `.codex-plugin/plugin.json` exposes the plugin to Codex.
- `skills/` are shared with the Claude Code plugin.
- `agents/*.md` are shared prompt contracts. Codex does not register them through `.codex-plugin/plugin.json`; business skills pass them to the Codex generic subagent when the generic multi-agent tool is available, and use compatibility mode only when no equivalent subagent capability is available.
- `WEBNOVEL_PLUGIN_ROOT` is the cross-host plugin root variable used by Codex instructions.
- The Python runtime remains `scripts/webnovel.py`.
- Read-only flows (`webnovel-doctor`, `webnovel-query`, `webnovel-dashboard`) use the same runtime commands as Claude Code.

## Agent Routing

Codex does not use the Claude Code hook manifest in `hooks/hooks.json`.

When a business skill asks for the Claude `Agent` tool, route in this order:

1. If the host provides the named Claude Code agent, call `webnovel-writer:context-agent`, `webnovel-writer:reviewer`, `webnovel-writer:data-agent`, or `webnovel-writer:deconstruction-agent` directly.
2. If Codex exposes its generic multi-agent tool, spawn a Codex generic subagent and include the corresponding `agents/*.md` file as that subagent's role, boundary, tool, and output-schema contract. The final report must say that a Codex generic subagent was called, and must not claim that the plugin-native `webnovel-writer:*` named agent was called.
3. If no subagent capability is available, use compatibility mode.

Compatibility mode means:

1. Read the corresponding `agents/*.md` file.
2. Perform the same bounded task in the main flow.
3. Preserve the declared output schema.
4. State in the final report that no subagent was called and compatibility mode was used.

Do not claim that `webnovel-writer:context-agent`, `webnovel-writer:reviewer`, `webnovel-writer:data-agent`, or `webnovel-writer:deconstruction-agent` was invoked unless the host actually provides such a tool.

For `data-agent`, preserve artifact ownership when using a Codex generic subagent. If the subagent's file writes are visible to the main flow, it may write `.webnovel/tmp/fulfillment_result.json`, `.webnovel/tmp/disambiguation_result.json`, and `.webnovel/tmp/extraction_result.json` directly. If the subagent runs in an isolated workspace, it must return the three JSON payloads; the main flow may only transport those exact payloads to the three artifact files without regenerating or semantically repairing them.

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
