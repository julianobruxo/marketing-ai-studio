---
overlay_common: bytedance
---

<!-- snippet: operating-rules -->
## Studio operating rules (read first)

This skill runs inside Marketing Content Studio. These rules override anything below that conflicts with them. The full precedence order is ADR-16 in `DECISIONS.md`.

1. **Your role.** The orchestrator's task message tells you your role (Strategist, Writer or Critic) and every path you may use. Stay inside that role.
2. **Context.** Brand, persona and the operator's writing instructions come only from the job context file named in your task message.
3. **Asking.** You cannot ask the user anything. Wherever this skill says to ask, offer or confirm, list what is missing as `[NEED: ...]` in your output and continue with what you have.
4. **Date.** Use the date and the period given in your task message wherever this skill says `<current_date>`. Never infer the date.
5. **Research.** Only the Strategist has web tools, and only when the task message says research was requested. The operator's data and sources come first. `web_search` means WebSearch and `web_fetch` means WebFetch.
6. **Files.** Write only where your task message allows. Ignore `/mnt/user-data/outputs` and `present_files`: the Writer saves to `runs/<job>/drafts/` and the orchestrator delivers.
7. **Facts.** Use only facts from the operator's inputs, the job context and the research notes, each with its source. Never invent statistics, quotes, examples or links. A section without real material is dropped, not filled.
8. **No self-approval.** Checklists in this skill are drafting discipline for the Writer. The Critic applies them independently, returns verdicts with evidence, and never rewrites the text.
9. **Defaults.** Structures, tones, emoji use and closing lines in this skill are defaults. The persona and the operator's instructions decide.
<!-- /snippet -->

<!-- snippet: context-binding -->
**Job context (Studio):** read the job context file at the path given in your task message. It is read-only.
<!-- /snippet -->
