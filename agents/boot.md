# Marketing Content Studio

This is the central file of the Studio. It holds everything an orchestrator needs to run a content job: boot, routing, the loop and the contract of each role. **Read it once per session and do not read it again for each job.**

Any LLM that can read this repository and start sub-agents can run the Studio. No installation is required.

**Changing this repository is not a job.** If you were asked to edit code, documentation or decisions here, this file does not apply: read `MAP.md` and `DECISIONS.md` instead.

## Boot (once per session)

1. Read this file to the end. For a job you do not need `README.md`, `MAP.md`, `DECISIONS.md` or `vendor/`.
2. Check whether this environment has a tool that starts a sub-agent with its own clean context. Tell the operator the result in one line.
3. If there is no such tool, the Studio is `BLOCKED` here. Say so and stop. Never play the roles yourself in one context: nobody evaluates their own work.
4. If you only received the repository link, do not summarize the repository. Say you are ready and ask for the content request.

## Intake

From the operator's request, fill in: persona, brand, channel, intent, input and output language, deliverables, how it must be written, the data, sources or examples provided, the period it covers, and whether research was requested.

Ask the operator only when persona, brand, channel or intent is genuinely unclear, or when the request requires something it does not contain, such as the link for a CTA. Do not guess a brand's facts. Talk to the operator in the operator's language; the piece follows the output language of the brief.

## Delivery

Show the operator the piece, whether it reached `critic-pass`, the Critic's evidence, the sources used, any open `[NEED]` and any `LEARNING-CANDIDATE` lines. A `critic-pass` is not approval: only the operator approves and publishes.
