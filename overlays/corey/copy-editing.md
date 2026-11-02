---
overlay_for: copy-editing
source: corey
upstream_version: 2.2.1
host_mentions_sha256: 8faf1f08899d69484e7cb35a9b863946cf589fb4e24f708fb4d9bb6c03dd64cf
---

<!-- op: vincular-contexto -->
<!-- trecho -->
**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before editing. Use brand voice and customer language from that context to guide your edits.
<!-- /trecho -->
<!-- /op -->

<!-- op: substituir-seção | ### How It Works -->
1. **Only the Critic runs this panel.** The Writer never scores its own copy (Studio rule 7).
2. **Assemble 3-5 expert personas** relevant to the copy type (see the panels below).
3. **Each persona scores 1-10 and gives specific critiques**, quoting the line each critique refers to.
4. **Return the critiques and scores to the orchestrator.** Do not revise the copy. If a revision is needed, the orchestrator starts a new Writer round.
5. **Scores are signals, not gates.** A high average is never a PASS on its own; the Critic's verdict rests on the evidence.
<!-- /op -->
