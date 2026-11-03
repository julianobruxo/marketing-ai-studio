# Host compatibility

The Studio runs on capabilities, not on a list of products (ADR-20). A job needs one thing: a tool that starts sub-agents with their own clean context. Without it, the job is BLOCKED.

| Capability | With it | Without it |
|---|---|---|
| Sub-agents | Job runs | BLOCKED, never simulated |
| Read this repository | Reads `AGENTS.md` and the focused `compiled/` sections listed by the manifest | The orchestrator injects exact selected source sections into each role; if unavailable the job is BLOCKED before writing |
| Write files | Job record in `runs/<job>/` | Job record as labeled blocks in the conversation |
| Shell | `scripts/route.py` routes the job | The orchestrator applies the routing tables in `AGENTS.md` |
| Web tools | Strategist can research when asked | Research is unavailable; the piece uses the operator's sources |

## Two ways to run

| Mode | What separates the roles | Hosts |
|---|---|---|
| **Portable** | Clean contexts and the rule that the orchestrator gives each role only its material. Nothing blocks a sub-agent from reading a file it was not given | Any host with sub-agents |
| **Reinforced** | The same, plus a hook that blocks paths and tools by role | Claude Code, installed with `scripts/install_host.py` in a run clone |

Hosts to try in portable mode: the Claude app (Cowork), ChatGPT Work, Codex, Antigravity. Status of each one is in `README.md`.

## Reinforced mode on Claude Code

- Install with `python scripts/install_host.py --host claude-code --target <run clone>`, never in the development clone.
- Hooks with `onFailure: "block"` need v2.1.295 or later. Tested on v2.1.303.
- The hook is installed with absolute paths: reinstall after moving the run clone.
- The three `studio-*` sub-agents must appear in the host. If they do not, the job is BLOCKED.
- `CLAUDE_CODE_FORK_SUBAGENT=0` and `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` come from the installed settings.

## Skill evidence vs. editorial effectiveness

The role catalog provides the expected files and exact focus sections. The host's access mechanisms must deliver them to each fresh subagent. A Claude Code `PreToolUse` record can establish that a `Read` request was authorized for an agent and path, **not** that it completed or that the model used the text. `skill_checks` provide candidate-specific assessment traces but must be verified against real operator judgments. No host should claim that a file name in `AGENTS.md` alone proves a skill was loaded.
