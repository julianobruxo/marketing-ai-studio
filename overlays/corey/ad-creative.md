---
overlay_for: ad-creative
source: corey
upstream_version: 2.12.2
host_mentions_sha256: a4dd3f222e1ccfcc284887e8cc1a3b782155c281c520eae83f1dff9b660dd8fb
---

<!-- op: vincular-contexto -->
<!-- trecho -->
**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Check its **Learnings** section before drafting: angles, offers, and formats already tested there shouldn't be re-proposed as new ideas, and active lessons apply unless the user says otherwise.
<!-- /trecho -->
<!-- /op -->

<!-- op: acrescentar-após | ## Grounded Inputs -->
**Studio paths:** `inputs/` means `runs/<job>/inputs/` (material the operator provided for this job). `brand/` means the job's compiled context. `outputs/` means your allowed draft location, `runs/<job>/drafts/`. "Stop and ask the user" means: stop and return `[NEED: ...]` listing the missing inputs (Studio rule 3). The grounding rules above stay in force.
<!-- /op -->

<!-- op: acrescentar-após | ## Generating Ad Visuals -->
**Studio:** no image, video or voice generation tool is available in this version. Deliver formats, visual specs, scripts and image prompts as text. Never claim to have generated media (Studio rule 5).
<!-- /op -->

<!-- op: acrescentar-após | ### Creative Review Page (client / stakeholder approval) -->
**Studio:** a review page is a draft saved in `runs/<job>/drafts/`. The Studio does not host it or send it to anyone; the operator decides who sees it.
<!-- /op -->

<!-- op: desativar | ## Tool Integrations -->
ad platform CLIs, APIs and integrations are out of scope for the Studio (ADR-02); performance data is used only when the operator provides it for the job.
<!-- /op -->
