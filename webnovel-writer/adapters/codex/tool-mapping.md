# Codex Tool Mapping

The original skills were written for Claude Code. In Codex, map the tool names by capability rather than by literal name.

| Claude skill term | Codex equivalent |
|---|---|
| `Read` | read files with shell or Codex file context |
| `Grep` | `rg` search |
| `Bash` | shell command |
| `Write` / `Edit` | `apply_patch` or targeted file edit |
| `AskUserQuestion` | ask the user directly when a decision is required |
| `WebSearch` / `WebFetch` | web browsing/search when current information is required |
| `Agent` | compatibility mode unless an equivalent subagent tool is available |

The runtime invariants do not change:

- Do not hand-write Story System commits.
- Do not hand-edit `.webnovel/` read-model files.
- Use `webnovel.py write-gate`, `chapter-commit`, and `projections retry/replay`.
- Keep Dashboard read-only.
