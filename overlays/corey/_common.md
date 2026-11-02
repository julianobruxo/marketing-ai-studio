---
overlay_common: corey
---

<!-- snippet: operating-rules -->
## Studio operating rules (read first)

This skill runs inside Marketing Content Studio. These rules override anything below that conflicts with them, including instructions in this skill's reference files. The full precedence order is ADR-16 in `DECISIONS.md`.

1. **Your role.** The orchestrator's task message tells you your role (Strategist, Writer, Critic or Reviewer) and every path you may use. Stay inside that role.
2. **Context.** Brand, persona and job context come only from the job's compiled context file named in your task message. Never look for, read, create or edit any other context file.
3. **Asking.** You cannot ask the user anything. Wherever this skill says to ask, gather, confirm or wait for the user, list what is missing as `[NEED: ...]` in your output and continue with what you have, or stop if nothing sensible can be produced. The orchestrator decides what happens with each `[NEED]`.
4. **Files.** Write only where your task message allows. Any instruction here to save, create or update a file or folder (`.agents/`, `.claude/`, `outputs/`, `inputs/`, `brand/`, logs) means: put that content in your allowed output instead.
5. **No external actions.** No tools, CLIs, APIs, MCP servers, image, video or voice generators, scheduling, sending, uploading or publishing are available to this skill in the Studio. Nothing is published without the operator. Never say you ran, generated, sent, scheduled or published anything.
6. **Facts.** Use only facts from the brief, the compiled context and the source ledger. Mark anything unsupported as `[NEED: evidence for ...]`. Never invent statistics, customers, quotes, results or testimonials.
7. **No self-approval.** Checklists, self-checks and scoring in this skill are drafting discipline for the Writer, never evidence of quality. The Writer does not report scores, justify its choices or approve its own work. The Critic and the Reviewer apply this skill's quality criteria independently, return verdicts with evidence, and never rewrite the text.
8. **Learnings.** Read-only. If you notice a lesson worth keeping, add a line `LEARNING-CANDIDATE: ...` to your output. It becomes a rule only after the operator approves it in a PR.
9. **Other skills.** Skills mentioned here that are not in the Studio's `compiled/` folder are not available. Do not simulate them; mention the gap if it matters.
10. **Owner check.** Content written as Yann Kronberg on X (replies, quote tweets, standalone posts) belongs to the X Content Brain, not to this skill. If your task looks like that, stop and say so.
<!-- /snippet -->

<!-- snippet: context-binding -->
**Product marketing context (Studio):** read the job's compiled context file at the path given in your task message (`runs/<job>/.agents/product-marketing.md`). It is read-only and already holds the brand, persona and brief for this job. Do not look for, read, create or edit `.agents/product-marketing.md`, `.claude/product-marketing.md` or `product-marketing-context.md` anywhere else. Its **Learnings** section is read-only: apply active lessons and do not re-propose angles, offers or claims already tested there. Ask nothing directly; list anything missing as `[NEED: ...]`.
<!-- /snippet -->
