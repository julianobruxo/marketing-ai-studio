# Host compatibility

What each host can actually do with the Marketing Content Studio. A job runs only where independent subagents really exist.

| Host | Status | Notes |
|---|---|---|
| Claude Code | supported (first host) | Named subagents with their own context and model, PreToolUse hooks with `onFailure: "block"` (v2.1.295+). Tested on v2.1.303. Install with `scripts/install_host.py` in a run clone, never in the development clone. |
| claude.ai chat | planning only | No subagent tool. Jobs are BLOCKED; use it for planning, review and building datasets. |
| ChatGPT | planning only | Not set up as a Studio host. |
| Other hosts | not supported yet | Need their own entry in `hosts/` and an ADR. |

## Requirements on Claude Code

- Installed with `python scripts/install_host.py --host claude-code --target <run clone>`.
- The hook is installed with absolute paths: reinstall after moving the run clone.
- The three `studio-*` subagents must appear in the host. If they do not, the job is BLOCKED.
- `CLAUDE_CODE_FORK_SUBAGENT=0` and `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` come from the installed settings.
