# Whole-document Critic evaluation (synthetic example only)

The editorial Critic is not validated by passing a sentence-level style benchmark. The
next evaluation uses **whole documents** in a blind pass, followed by review-issue-level
adjudication. These public examples are entirely fictional. **Never commit internal
drafts, real reviewer comments, revision exports, or adjudications of private work.**

## Why the earlier totals were misleading

A binary FAIL can happen for a reason unrelated to the human review. A quote that merely
overlaps an entire submitted passage is not evidence that the same issue was found.
Counting any material finding as a match also inflates apparent recall. The original
real-world holdout was read during development, so it is no longer independent.

## Full-document protocol

1. **Freeze the contract** at a known commit or local file. Record its SHA-256.
2. In a **private local directory**, put one full original document (before the human
   review) per case in the `candidate` field. Include the original brief, audience,
   relevant inputs, and source excerpts actually available to the author. Keep document
   headings, section order, and CTA intact. Avoid isolated snippets.
3. Store every human review issue in `expected.issues`, each with an opaque `id`,
   `kind: "problem"`, optional `quote`, `source_comment`, and a reason/category.
   Use `kind: "praise"` for positive evidence, but **do not** treat praise for one
   paragraph as approval of the whole document. Only use
   `document_approved: true` when the whole piece was explicitly approved.
4. Run `pack` to create a **blind input packet**. The package uses an explicit
   allowlist; `expected`, `source_comment`, `reviewer`, `adjudication` and any
   other unknown top-level keys do not reach the Critic. Inspect the packet manually
   before invoking external evaluation. Do not put human comments inside allowed
   `inputs` or `context` fields.
5. Run **one document per isolated Critic invocation**, using the frozen contract;
   no human comment, answer label, or earlier judgment is available to that invocation.
   Do not instruct the Critic to assume the facts are true or to assess style alone.
   Save its exact structured output, not a reconstruction.
6. A human or an independently isolated judge maps **each human issue** to at most
   one specific predicted finding. `finding_index` is zero-based over `findings()`,
   flattening gates and evidence in the order emitted. The mapping must indicate
   `diagnosis: aligned | partial | different` with adjudicated booleans
   `category_ok` and `severity_ok`. An undetected issue uses
   `finding_index: null, diagnosis: missed`. Unanchored document-level comments
   still count as issues, and can match a global finding if it expresses the same
   editorial defect.
7. Score **per human issue** and report aligned, partial, missed and different
   separately. Count unmatched model findings separately; these are **not automatically
   false positives** until independently adjudicated. The document-level rejection
   rate is a different measure. Explicitly approved content and factual objections
   need separate human review.
8. **Do not tune against the holdout after reading its comments.** After examining
   the results, this document becomes diagnostic material. New contract changes require
   another independent holdout, plus an end-to-end multi-round test.

A reviewer may criticize timing assumptions, argument structure, vague pronouns,
unanswered headings, or excess advertising. A generic claim about hallucinated
statistics is not equivalent to the specific critique merely because both lead to FAIL.

## Commands

```bash
python scripts/eval_critic.py pack \
  --cases tests/critic/fixtures/doc-cases-synthetic.json \
  --out /tmp/critic-doc-pack \
  --contract agents/critic.md

# The synthetic verdict file below is manually authored for testing the scorer.
# It is NOT an LLM result or evidence of Critic performance.
python scripts/eval_critic.py score-doc \
  --cases tests/critic/fixtures/doc-cases-synthetic.json \
  --verdicts tests/critic/fixtures/doc-verdicts-synthetic.json \
  --adjudications tests/critic/fixtures/doc-adjudications-synthetic.json

python -m unittest discover -s tests
```

The `pack` output includes `manifest.json` containing the contract hash and case
IDs. Never use synthetic-fixture alignment as evidence of model quality.

## Decision boundary

This evaluation tooling does not change `agents/critic.md`, the number of loop
rounds, severity rules, or any previous verdict. It cannot independently run an LLM
Critic or judge the commercial quality of writing; those require actual isolated
invocations and human adjudication. It only prevents blind-input leakage and
misleading arithmetic in subsequent experiments.
