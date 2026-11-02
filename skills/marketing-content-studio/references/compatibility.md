# Host compatibility

The Studio runs on capabilities, not on a list of products (ADR-20). A job needs one thing: a tool that starts sub-agents with their own clean context. Without it, the job is BLOCKED.

| Capability | With it | Without it |
|---|---|---|
| Sub-agents | Job runs | BLOCKED, never simulated |
| Read this repository | Reads `AGENTS.md` and the compiled skills | The operator attaches `AGENTS.md` and the skills the intent needs |
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
