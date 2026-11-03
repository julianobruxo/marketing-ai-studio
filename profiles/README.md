# Brand context and editorial calibration (local only)

This folder is intentionally documentation-only in the public repository. The Studio reads an operator-supplied brand profile from `profiles/<brand>.md` **only when it exists locally**. A missing file never means the model may invent a brand voice or positioning.

Suggested fields for a private profile:

- `identity`: brand name and supported public/first-party facts, each with a source
- `audience`: ICP/reader, business pain, objections and desired outcome
- `positioning`: a defensible point of view, benefits, differentiators and forbidden claims
- `voice`: approved cadence/degree of formality, allowable style devices, and contextual anti-patterns
- `channels`: channel-specific conventions and deliverable distinctions, e.g. LinkedIn caption vs infographic text
- `goldens`: references to **exact** operator-approved, same-format samples, with date/approval and why each works; do not copy a single template into every post
- `last_reviewed`: operator approval date and source provenance

Use Corey Product Marketing (`compiled/corey/product-marketing.md`) as the structure when assembling this context from **provided evidence**. It is not a source of facts. Keep actual client profiles, copy and goldens in operator-controlled local files or `runs/<job>/inputs/calibration.md`; never commit them to this public repository without explicit authorization. This README itself contains no customer details.

Precedence for **style only**: explicit operator brief and approved same-brand, same-format guidance > general Corey/ByteDance template preferences. Factual provenance, safety and `strict-source` fidelity are never overridden by stylistic examples.
