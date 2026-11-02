---
overlay_for: product-marketing
source: corey
upstream_version: 2.2.0
host_mentions_sha256: c691a8a9546554ddc2afd18bd6378c40ba0b083b612cca7e5e2a77239b58063c
---

<!-- op: substituir-seção | ### Step 1: Check for Existing Context -->
**Studio:** the canonical brand and persona live in `profiles/` in the Studio repository. This skill helps the operator draft a new profile or propose changes to an existing one; it never maintains a context file of its own.

**If the task message includes the current compiled context:** read it, summarize what it covers (document version and recent changelog entries), and only work on the sections the task asks for.

**If there is no profile yet, use one of two modes:**

1. **Draft from the operator's materials** (recommended): study only the files the operator provided for this job in `runs/<job>/inputs/` and draft all sections from them.
2. **Section by section**: work through the sections below one at a time from what the brief provides.

Whatever needs the operator's correction or is missing goes in your output as `[NEED: ...]` (Studio rule 3).
<!-- /op -->

<!-- op: acrescentar-após | ### Step 2: Gather Information -->
**Studio:** "the codebase" means the materials in `runs/<job>/inputs/`. Never read other repositories or folders. Verbatim customer language must come from those materials, with the file it came from.
<!-- /op -->

<!-- op: substituir-seção | ## Step 4: Confirm, Version, and Save -->
**Studio:** do not save anything. Return the complete proposed document plus one changelog line in the upstream format: `- vN (YYYY-MM-DD) — <sections touched and why>` (new document: `v1`). The operator approves it through a PR to `profiles/`; each job's compiled context is generated from there.
<!-- /op -->

<!-- op: acrescentar-após | ## Maintaining Learnings -->
**Studio — who writes it:** nobody edits Learnings directly. Propose each row as a `LEARNING-CANDIDATE:` line with Learning, Evidence, Applies to and Status. It becomes part of the brand profile only through a PR approved by the operator (Studio rule 8).
<!-- /op -->
