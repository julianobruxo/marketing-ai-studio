---
name: deep-research
description: Use this skill instead of WebSearch for ANY question requiring web research. Trigger on queries like "what is X", "explain X", "compare X and Y", "research X", or before content generation tasks. Provides systematic multi-angle research methodology instead of single superficial searches. Use this proactively when the user's question needs online information.
---
<!-- STUDIO-COMPILED — gerado por scripts/vendor.py compile; não editar.
source: https://github.com/bytedance/deer-flow
commit: 12c304f12ce5c0bf66d8927386e5dd18ea84f685
upstream_path: skills/public/deep-research/SKILL.md
upstream_version: 12c304f12ce5c0bf66d8927386e5dd18ea84f685
overlay: overlays/bytedance/deep-research.md sha256=89d5eea677f22f707f9b385c0a425c59111195178ccbf1693887af6ab321fb18
common: overlays/bytedance/_common.md sha256=5293183d2a62c1b9b34d7328dc6bfd8f8b6999ad8a59e41cc59275ec87021430
Copyright (c) 2025 Bytedance Ltd. and/or its affiliates; Copyright (c) 2025-2026 DeerFlow Authors. MIT License — see vendor/bytedance/LICENSE.
-->

# Deep Research Skill

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

## Overview

This skill provides a systematic methodology for conducting thorough web research. **Load this skill BEFORE starting any content generation task** to ensure you gather sufficient information from multiple angles, depths, and sources.

## When to Use This Skill

**Always load this skill when:**

### Research Questions
- User asks "what is X", "explain X", "research X", "investigate X"
- User wants to understand a concept, technology, or topic in depth
- The question requires current, comprehensive information from multiple sources
- A single web search would be insufficient to answer properly

### Content Generation (Pre-research)
- Creating presentations (PPT/slides)
- Creating frontend designs or UI mockups
- Writing articles, reports, or documentation
- Producing videos or multimedia content
- Any content that requires real-world information, examples, or current data

## Core Principle

**Never generate content based solely on general knowledge.** The quality of your output directly depends on the quality and quantity of research conducted beforehand. A single search query is NEVER enough.

**Studio:** in this Studio, research runs only when the operator asked for it, and every search has a cost. Start from the operator's data and sources, search only for the gaps the brief needs, and stop when every claim the piece needs has a source.

## Research Methodology

### Phase 1: Broad Exploration

Start with broad searches to understand the landscape:

1. **Initial Survey**: Search for the main topic to understand the overall context
2. **Identify Dimensions**: From initial results, identify key subtopics, themes, angles, or aspects that need deeper exploration
3. **Map the Territory**: Note different perspectives, stakeholders, or viewpoints that exist

Example:
```
Topic: "AI in healthcare"
Initial searches:
- "AI healthcare applications 2024"
- "artificial intelligence medical diagnosis"
- "healthcare AI market trends"

Identified dimensions:
- Diagnostic AI (radiology, pathology)
- Treatment recommendation systems
- Administrative automation
- Patient monitoring
- Regulatory landscape
- Ethical considerations
```

### Phase 2: Deep Dive

For each important dimension identified, conduct targeted research:

1. **Specific Queries**: Search with precise keywords for each subtopic
2. **Multiple Phrasings**: Try different keyword combinations and phrasings
3. **Fetch Full Content**: Use `web_fetch` to read important sources in full, not just snippets
4. **Follow References**: When sources mention other important resources, search for those too

Example:
```
Dimension: "Diagnostic AI in radiology"
Targeted searches:
- "AI radiology FDA approved systems"
- "chest X-ray AI detection accuracy"
- "radiology AI clinical trials results"

Then fetch and read:
- Key research papers or summaries
- Industry reports
- Real-world case studies
```

### Phase 3: Diversity & Validation

Ensure comprehensive coverage by seeking diverse information types:

| Information Type | Purpose | Example Searches |
|-----------------|---------|------------------|
| **Facts & Data** | Concrete evidence | "statistics", "data", "numbers", "market size" |
| **Examples & Cases** | Real-world applications | "case study", "example", "implementation" |
| **Expert Opinions** | Authority perspectives | "expert analysis", "interview", "commentary" |
| **Trends & Predictions** | Future direction | "trends 2024", "forecast", "future of" |
| **Comparisons** | Context and alternatives | "vs", "comparison", "alternatives" |
| **Challenges & Criticisms** | Balanced view | "challenges", "limitations", "criticism" |

### Phase 4: Synthesis Check

Before proceeding to content generation, verify:

- [ ] Have I searched from at least 3-5 different angles?
- [ ] Have I fetched and read the most important sources in full?
- [ ] Do I have concrete data, examples, and expert perspectives?
- [ ] Have I explored both positive aspects and challenges/limitations?
- [ ] Is my information current and from authoritative sources?

**If any answer is NO, continue researching before generating content.**

**Studio:** answer these only for the claims the piece needs. If the operator's sources already cover them, no further search is needed. Expert perspectives are optional unless the brief asks for them.

## Search Strategy Tips

### Effective Query Patterns

```
# Be specific with context
❌ "AI trends"
✅ "enterprise AI adoption trends 2024"

# Include authoritative source hints
"[topic] research paper"
"[topic] McKinsey report"
"[topic] industry analysis"

# Search for specific content types
"[topic] case study"
"[topic] statistics"
"[topic] expert interview"

# Use temporal qualifiers — always use the ACTUAL current year from <current_date>
"[topic] 2026"   # ← replace with real current year, never hardcode a past year
"[topic] latest"
"[topic] recent developments"
```

### Temporal Awareness

**Always check `<current_date>` in your context before forming ANY search query.**

`<current_date>` gives you the full date: year, month, day, and weekday (e.g. `2026-02-28, Saturday`). Use the right level of precision depending on what the user is asking:

| User intent | Temporal precision needed | Example query |
|---|---|---|
| "today / this morning / just released" | **Month + Day** | `"tech news February 28 2026"` |
| "this week" | **Week range** | `"technology releases week of Feb 24 2026"` |
| "recently / latest / new" | **Month** | `"AI breakthroughs February 2026"` |
| "this year / trends" | **Year** | `"software trends 2026"` |

**Rules:**
- When the user asks about "today" or "just released", use **month + day + year** in your search queries to get same-day results
- Never drop to year-only when day-level precision is needed — `"tech news 2026"` will NOT surface today's news
- Try multiple phrasings: numeric form (`2026-02-28`), written form (`February 28 2026`), and relative terms (`today`, `this week`) across different queries

❌ User asks "what's new in tech today" → searching `"new technology 2026"` → misses today's news
✅ User asks "what's new in tech today" → searching `"new technology February 28 2026"` + `"tech news today Feb 28"` → gets today's results

**Studio:** use the date and period given in the task message instead of `<current_date>` (Studio rule 4).

### When to Use web_fetch

Use `web_fetch` to read full content when:
- A search result looks highly relevant and authoritative
- You need detailed information beyond the snippet
- The source contains data, case studies, or expert analysis
- You want to understand the full context of a finding

### Iterative Refinement

Research is iterative. After initial searches:
1. Review what you've learned
2. Identify gaps in your understanding
3. Formulate new, more targeted queries
4. Repeat until you have comprehensive coverage

## Quality Bar

Your research is sufficient when you can confidently answer:
- What are the key facts and data points?
- What are 2-3 concrete real-world examples?
- What do experts say about this topic?
- What are the current trends and future directions?
- What are the challenges or limitations?
- What makes this topic relevant or important now?

## Common Mistakes to Avoid

- ❌ Stopping after 1-2 searches
- ❌ Relying on search snippets without reading full sources
- ❌ Searching only one aspect of a multi-faceted topic
- ❌ Ignoring contradicting viewpoints or challenges
- ❌ Using outdated information when current data exists
- ❌ Starting content generation before research is complete

## Output

After completing research, you should have:
1. A comprehensive understanding of the topic from multiple angles
2. Specific facts, data points, and statistics
3. Real-world examples and case studies
4. Expert perspectives and authoritative sources
5. Current trends and relevant context

**Only then proceed to content generation**, using the gathered information to create high-quality, well-informed content.

**Studio:** return research notes to the orchestrator in the format of your role instructions: for each fact, the source (URL, publisher or author, date), whether you read it with WebFetch (`fetched`) or only saw a snippet (`snippet`), and the exact supporting excerpt. The Critic cannot open the web, so the excerpt is the evidence. You cannot write files.
