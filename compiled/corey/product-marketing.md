---
name: product-marketing
description: "When the user wants to create or update their product marketing context document. Also use when the user mentions 'product context,' 'marketing context,' 'set up context,' 'positioning,' 'who is my target audience,' 'describe my product,' 'ICP,' 'ideal customer profile,' 'brand voice,' 'tone of voice,' 'brand guidelines,' 'what have we learned,' 'log this learning,' or wants to avoid repeating foundational information across marketing tasks. Use this at the start of any new project before using other marketing skills — it creates `.agents/product-marketing.md` that all other skills reference for product, audience, and positioning context."
metadata:
  version: 2.2.0
---
<!-- STUDIO-COMPILED — gerado por scripts/vendor.py compile; não editar.
source: https://github.com/coreyhaines31/marketingskills
commit: 88c79f6528a9347420e57ceb1fff9a60de651768
upstream_path: skills/product-marketing/SKILL.md
upstream_version: 2.2.0
overlay: overlays/corey/product-marketing.md sha256=04ab5e69b430dce57bd7d7f756934c89473526317b865ec319d7c6f82ef847e9
common: overlays/corey/_common.md sha256=9c9942012447de70c821872c4551a37da5af2c2495b9d799993963ab0f0eca2c
Copyright (c) 2025 Corey Haines. MIT License — see vendor/corey/LICENSE.
-->

# Product Marketing Context

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

You help users create and maintain a product marketing context document. This captures foundational positioning and messaging information that other marketing skills reference, so users don't repeat themselves.

The document is stored at `.agents/product-marketing.md`.

## Workflow

### Step 1: Check for Existing Context

**Studio:** the canonical brand and persona live in `profiles/` in the Studio repository. This skill helps the operator draft a new profile or propose changes to an existing one; it never maintains a context file of its own.

**If the task message includes the current compiled context:** read it, summarize what it covers (document version and recent changelog entries), and only work on the sections the task asks for.

**If there is no profile yet, use one of two modes:**

1. **Draft from the operator's materials** (recommended): study only the files the operator provided for this job in `runs/<job>/inputs/` and draft all sections from them.
2. **Section by section**: work through the sections below one at a time from what the brief provides.

Whatever needs the operator's correction or is missing goes in your output as `[NEED: ...]` (Studio rule 3).

### Step 2: Gather Information

**If auto-drafting:**
1. Read the codebase: README, landing pages, marketing copy, about pages, meta descriptions, package.json, any existing docs
2. Draft all sections based on what you find
3. Present the draft and ask what needs correcting or is missing
4. Iterate until the user is satisfied

**If starting from scratch:**
Walk through each section below conversationally, one at a time. Don't dump all questions at once.

For each section:
1. Briefly explain what you're capturing
2. Ask relevant questions
3. Confirm accuracy
4. Move to the next

Push for verbatim customer language — exact phrases are more valuable than polished descriptions because they reflect how customers actually think and speak, which makes copy more resonant.

**Studio:** "the codebase" means the materials in `runs/<job>/inputs/`. Never read other repositories or folders. Verbatim customer language must come from those materials, with the file it came from.

---

## Sections to Capture

### 1. Product Overview
- One-line description
- What it does (2-3 sentences)
- Product category (what "shelf" you sit on—how customers search for you)
- Product type (SaaS, marketplace, e-commerce, service, etc.)
- Business model and pricing

### 2. Target Audience
- Target company type (industry, size, stage)
- Target decision-makers (roles, departments)
- Primary use case (the main problem you solve)
- Jobs to be done (2-3 things customers "hire" you for)
- Specific use cases or scenarios

### 3. Personas (B2B only)
If multiple stakeholders are involved in buying, capture for each:
- User, Champion, Decision Maker, Financial Buyer, Technical Influencer
- What each cares about, their challenge, and the value you promise them

### 4. Problems & Pain Points
- Core challenge customers face before finding you
- Why current solutions fall short
- What it costs them (time, money, opportunities)
- Emotional tension (stress, fear, doubt)

### 5. Competitive Landscape
- **Direct competitors**: Same solution, same problem (e.g., Calendly vs SavvyCal)
- **Secondary competitors**: Different solution, same problem (e.g., Calendly vs Superhuman scheduling)
- **Indirect competitors**: Conflicting approach (e.g., Calendly vs personal assistant)
- How each falls short for customers

### 6. Differentiation
- Key differentiators (capabilities alternatives lack)
- How you solve it differently
- Why that's better (benefits)
- Why customers choose you over alternatives

### 7. Objections & Anti-Personas
- Top 3 objections heard in sales and how to address them
- Who is NOT a good fit (anti-persona)

### 8. Switching Dynamics
The JTBD Four Forces:
- **Push**: What frustrations drive them away from current solution
- **Pull**: What attracts them to you
- **Habit**: What keeps them stuck with current approach
- **Anxiety**: What worries them about switching

### 9. Customer Language
- How customers describe the problem (verbatim)
- How they describe your solution (verbatim)
- Words/phrases to use
- Words/phrases to avoid
- Glossary of product-specific terms

### 10. Brand Voice
- 3-5 voice attributes, each with what it means, what it doesn't mean, and a real line from existing copy
- Tone by context: how the voice shifts for support, launches, errors, sales, and social
- Brand words: terms you own, words you never use (with the reason)

Build this from copy that already performed and from the founder's own writing, rather than from adjectives picked in a meeting. See [references/brand-voice.md](../../vendor/corey/skills/product-marketing/references/brand-voice.md) for the extraction steps, a worked profile, before/after examples, and per-person voice guides.

### 11. Proof Points
- Key metrics or results to cite
- Notable customers/logos
- Testimonial snippets
- Main value themes and supporting evidence

### 12. Goals
- Primary business goal
- Key conversion action (what you want people to do)
- Current metrics (if known)

### 13. Paid Ads (optional, only if they run ads)
The **ads** skill reads this so the user doesn't re-explain the account every session.
- Margin reality: the target CPA or ROAS that keeps the business profitable, and the hard floor (the ROAS below which, or CPA above which, to flag immediately)
- Budget and pacing: monthly budget and acceptable daily variance
- Conversion truth: which conversion actions count and what each is worth, known tracking weaknesses (lag, double counting, offline gaps), and what separates a good lead from a form fill
- Campaign naming convention and what each campaign is for, one line each
- What the agent may do (read, compare, flag, draft, recommend) and may not do without approval (change budgets or bids, pause or launch, edit tracking, publish ads)

### 14. Learnings
Start this empty. It fills up as work ships (see "Maintaining Learnings" below).

---

## Step 3: Create the Document

After gathering information, create `.agents/product-marketing.md` with this structure:

```markdown
# Product Marketing Context

**Document version:** v1
**Last updated:** [date]

## Product Overview
**One-liner:**
**What it does:**
**Product category:**
**Product type:**
**Business model:**

## Target Audience
**Target companies:**
**Decision-makers:**
**Primary use case:**
**Jobs to be done:**
-
**Use cases:**
-

## Personas
| Persona | Cares about | Challenge | Value we promise |
|---------|-------------|-----------|------------------|
| | | | |

## Problems & Pain Points
**Core problem:**
**Why alternatives fall short:**
-
**What it costs them:**
**Emotional tension:**

## Competitive Landscape
**Direct:** [Competitor] — falls short because...
**Secondary:** [Approach] — falls short because...
**Indirect:** [Alternative] — falls short because...

## Differentiation
**Key differentiators:**
-
**How we do it differently:**
**Why that's better:**
**Why customers choose us:**

## Objections
| Objection | Response |
|-----------|----------|
| | |

**Anti-persona:**

## Switching Dynamics
**Push:**
**Pull:**
**Habit:**
**Anxiety:**

## Customer Language
**How they describe the problem:**
- "[verbatim]"
**How they describe us:**
- "[verbatim]"
**Words to use:**
**Words to avoid:**
**Glossary:**
| Term | Meaning |
|------|---------|
| | |

## Brand Voice
| Attribute | Means | Doesn't mean | Example line |
|-----------|-------|--------------|--------------|
| | | | |

**Tone by context:**
- Support:
- Launch:
- Errors:
- Sales:
- Social:
**Terms we own:**
**Never use (and why):**

## Proof Points
**Metrics:**
**Customers:**
**Testimonials:**
> "[quote]" — [who]
**Value themes:**
| Theme | Proof |
|-------|-------|
| | |

## Goals
**Business goal:**
**Conversion action:**
**Current metrics:**

## Paid Ads (optional)
**Target CPA / ROAS:**
**Hard floor:**
**Monthly budget and daily variance:**
**Conversions that count:**
| Action | Means | Value | Feeds bidding? |
|--------|-------|-------|----------------|
| | | | |
**Known tracking weaknesses:**
**Good lead vs. form fill:**
**Campaigns:** [name] — [what it's for]
**Agent may:** read, compare, flag, draft, recommend
**Agent may not (without approval):** change budgets or bids, pause or launch, edit tracking, publish ads

## Learnings
*Decisions and tested lessons. Newest first. Keep it to about 20 active entries.*
| Date | Learning | Evidence | Applies to | Status |
|------|----------|----------|------------|--------|
| | | | | |

## Changelog
*Newest first. One line per revision: what changed and why.*
- v1 ([date]) — Initial context.
```

---

## Step 4: Confirm, Version, and Save

**Studio:** do not save anything. Return the complete proposed document plus one changelog line in the upstream format: `- vN (YYYY-MM-DD) — <sections touched and why>` (new document: `v1`). The operator approves it through a PR to `profiles/`; each job's compiled context is generated from there.

---

## Maintaining Learnings

The Changelog records how the document changed. **Learnings** records what the team found out by shipping: which angles won, which offers flopped, which decisions were made and why. Drafting skills (copywriting, emails, ads, ad-creative, social) read it before writing so the next brief starts from what's already known.

**Entry format:** one row per learning.
- **Learning:** one sentence, specific enough to change a draft. "Price-anchored headlines beat outcome headlines on the pricing page" works. "Be clearer" doesn't.
- **Evidence:** the test, campaign, or source, with the number and sample size. "Variant B +18% trial starts, 2,400 visitors per arm, 3 weeks."
- **Applies to:** the channels, segments, or skills it affects.
- **Status:** `active`, `watch` (one data point, worth retesting), or `retired`.

**What earns a place:**
- A test result that reached its planned sample, or the same pattern seen in two or more campaigns
- A decision the user made with a reason (positioning, pricing, a channel cut) that future drafts must respect
- A correction the user gave more than once ("never call it a platform")

**What doesn't:** single-run anecdotes (log those as `watch` or leave them out), task notes, and anything that belongs in another section. A new objection goes in Objections; a new customer phrase goes in Customer Language.

**When to retire an entry:** a later test contradicts it, the product or market changed underneath it (new pricing, new ICP), or it hasn't been relevant for two quarters. Change the status to `retired` and add a line saying why, rather than deleting it, so nobody re-tests a settled question. Move retired rows to the bottom, and archive them once the table passes about 20 active rows.

**Who writes it:** any skill that finishes a test, campaign, or postmortem may propose a row. Show the proposed row to the user and add it on approval, with a version bump and a Changelog line like any other substantive change. Loops that run on a schedule do this through their session-end step (see **marketing-loops**).

**Studio — who writes it:** nobody edits Learnings directly. Propose each row as a `LEARNING-CANDIDATE:` line with Learning, Evidence, Applies to and Status. It becomes part of the brand profile only through a PR approved by the operator (Studio rule 8).

---

## Tips

- **Be specific**: Ask "What's the #1 frustration that brings them to you?" not "What problem do they solve?"
- **Capture exact words**: Customer language beats polished descriptions
- **Ask for examples**: "Can you give me an example?" unlocks better answers
- **Validate as you go**: Summarize each section and confirm before moving on
- **Skip what doesn't apply**: Not every product needs all sections (e.g., Personas for B2C, Paid Ads if they don't run ads)
