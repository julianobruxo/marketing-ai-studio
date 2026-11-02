---
overlay_for: newsletter-generation
source: bytedance
upstream_version: 12c304f12ce5c0bf66d8927386e5dd18ea84f685
host_mentions_sha256: 89f6a8488179aa2222237ea068e67ec9236afb11ef0b4c378fb2bd52592dc193
---

<!-- op: acrescentar-após | #### Step 1.1: Understand Newsletter Requirements -->
**Studio:** the brief gives the topic, period, audience, tone, length and the operator's data. The defaults in this table apply only where the brief is silent. A period in the brief (for example "October 2026") replaces the 7-30 day recency default everywhere in this skill.
<!-- /op -->

<!-- op: acrescentar-após | #### Step 2.1: Multi-Source Research -->
**Studio:** search only when the task message says research was requested, and only for what the operator's data does not cover (Studio rule 5). Build queries from the brief's period, not from the current month.
<!-- /op -->

<!-- op: acrescentar-após | #### Step 4.3: Quality Checklist -->
**Studio:** the Writer uses this checklist while drafting; the Critic applies it independently (Studio rule 8). Every link must come from the operator's sources or the research notes.
<!-- /op -->

<!-- op: substituir-seção | ## Output Handling -->
**Studio:** the Writer saves the newsletter as Markdown to the draft path given in the task message, in `runs/<job>/drafts/`. The orchestrator delivers it to the operator. HTML conversion only if the brief asks for it.
<!-- /op -->

<!-- op: acrescentar-após | ## Notes -->
**Studio:** "load deep-research" means the Strategist uses the compiled `deep-research` skill, and only when research was requested.
<!-- /op -->
