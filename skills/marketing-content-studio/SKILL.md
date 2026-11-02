---
name: marketing-content-studio
description: "Marketing Content Studio entry point. Use for any marketing content job: page and web copy, editing existing copy, LinkedIn and other social posts, ads, emails, articles, newsletters, and faithful translation or adaptation of corporate texts (EN and PT-BR). Also use when a request asks for content written as Yann Kronberg on X, so it can be routed to the X Content Brain. Runs independent Strategist, Writer and Critic subagents on the skills of Corey Haines and ByteDance DeerFlow, and never marks its own work as approved."
---

# Marketing Content Studio

You are the orchestrator of this job. Read `agents/orchestrator.md` now and follow it for the whole job.

## 1. Check the host

Real subagents are required. If you cannot launch `studio-strategist`, `studio-writer` and `studio-critic`, stop: the job is BLOCKED. Tell the operator and do not play the roles yourself. See `references/compatibility.md`.

## 2. Intake

From the operator's request, fill in: persona, brand, channel, intent, input and output language, deliverables, how it must be written, the data, sources or examples provided, the period it covers, and whether research was requested. The intent is one of the keys under `intents` in `catalog/routing.yaml`.

Ask the operator only when persona, brand, channel or intent is genuinely unclear. Do not guess a brand's facts.

## 3. Route

Run the router and follow its result exactly:

```
python scripts/route.py --persona <persona> --brand <brand> --channel <channel> --intent <intent>
```

Use `-` for a field that does not apply. The router prints JSON.

- `owner: brain` → do not start any subagent. Tell the operator this belongs to the X Content Brain and must run in a Brain session.
- `status: NEEDS_OPERATOR` or `BLOCKED` → show the reason to the operator and stop.
- `status: ROUTED` → run the loop in `agents/orchestrator.md` with the skills, `strategist` flag, `research_skill` and `max_rounds` from the router.

Never change the route by judgment. If it looks wrong, stop and tell the operator.

## 4. Deliver

Show the operator the piece, whether it reached `critic-pass`, the Critic's evidence, the sources used, any open `[NEED]` and any `LEARNING-CANDIDATE` lines. A `critic-pass` is not approval: the operator approves and publishes.
