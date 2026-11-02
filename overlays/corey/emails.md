---
overlay_for: emails
source: corey
upstream_version: 2.1.4
host_mentions_sha256: 18fa6c4ba10310fd82d6d302e8ccca435f57c7fee7d6729546ed666b48c101e0
---

<!-- op: vincular-contexto -->
<!-- trecho -->
**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Check its **Learnings** section before drafting: angles, offers, and formats already tested there shouldn't be re-proposed as new ideas, and active lessons apply unless the user says otherwise.
<!-- /trecho -->
<!-- /op -->

<!-- op: acrescentar-após | ## Output Format -->
**Studio:** timing, triggers and segments are a plan for the operator. Nothing is sent from the Studio (Studio rule 5).
<!-- /op -->

<!-- op: desativar | ## Tool Integrations -->
email platforms, MCP servers and sending tools are out of scope for the Studio (ADR-02).
<!-- /op -->
