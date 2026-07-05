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
| `Agent` | named Claude agent when available; otherwise Codex generic subagent with the matching `agents/*.md` contract; otherwise compatibility mode |

When Codex uses a generic subagent, pass the relevant agent file as the role and output contract:

- `agents/context-agent.md` for writing briefs.
- `agents/reviewer.md` for review JSON.
- `agents/data-agent.md` for chapter-commit artifacts.
- `agents/deconstruction-agent.md` for reference-work analysis.

The generic subagent is a Codex host capability, not a plugin-native `webnovel-writer:*` named agent. Final reports must distinguish these cases:

- Named host agent used: say the corresponding `webnovel-writer:*` agent was called.
- Codex generic subagent used: say a Codex generic subagent was called with the matching agent contract.
- No subagent used: say no subagent was called and compatibility mode was used.

The runtime invariants do not change:

- Do not hand-write Story System commits.
- Do not hand-edit `.webnovel/` read-model files.
- Use `webnovel.py write-gate`, `chapter-commit`, and `projections retry/replay`.
- Keep Dashboard read-only.
