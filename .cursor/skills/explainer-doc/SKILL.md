---
name: explainer-doc
description: >-
  Manual skill only. Use only when the user explicitly invokes /explainer-doc, names explainer-doc, or asks for this
  exact section layout or explainer format.
---

# Explainer document (`/explainer-doc`)

## When to use this skill

- **Apply** when the user explicitly invokes `/explainer-doc`, names `explainer-doc`, or clearly asks for this document structure or "explainer format."
- **Do not apply** because a topic sounds educational, because the user is learning something, or because documentation might help — wait for an explicit request.

If unsure whether the user wanted this skill, ask once instead of assuming.

## Outputs

Deliver a **single markdown document** (new or revised) with **exactly these top-level sections**, in order:

1. **Short explanation (layman terms)** — Plain language for someone unfamiliar with the topic; no jargon unless defined; one tight subsection or a few short paragraphs.
2. **Theory (precise)** — Formal or technical account: definitions, invariants, how it fits in a broader model, limits and assumptions. Use precise terminology here.
3. **Where it applies (examples)** — Concrete scenarios where the concept is the right tool, with **why** it fits (criteria, tradeoffs).
4. **Common gotchas (examples)** — Misunderstandings, edge cases, footguns, and how to recognize or avoid them. Prefer real patterns over generic warnings.
5. **Related concepts** — Neighboring ideas worth exploring next: for each, **one or two sentences** (what it is and why it matters relative to the main topic). Prefer a small bullet list (roughly 3–7 items); optional short links if helpful.
6. **References** — Bulleted links: official docs, specs, authoritative articles, and **paths to relevant files in this repo** (use repo-relative paths like `vault/topics/...`). Prefer stable URLs and paths the user can follow offline.

Use `##` headings with those section titles (adjust parenthetical bits to match, but keep the six-part structure).

Optional: a single `#` title line at the top for the concept name. **Do not add YAML frontmatter** to generated or reworked files unless the user explicitly asks (this repo discourages unsolicited frontmatter changes).

## Reworking existing documents

When the user points at existing markdown (paste, path, or open file):

1. Read the full source; preserve factual correctness and intent.
2. Map content into the six sections; **move and rewrite** for clarity rather than duplicating rambling blocks.
3. If material is missing for a section, add a brief honest gap note *or* research from repo/docs (with references) — do not invent citations.
4. Keep the user's examples if they are good; tighten wording; merge duplicates.
5. If the original used a different heading hierarchy, normalize to this structure without losing information.

## Quality bar

- Layman section must stand alone for a quick read; theory section must satisfy someone who already knows adjacent concepts.
- Related concepts must stay **short** (one–two sentences each); they are pointers, not mini explainers.
- Gotchas must be **specific** (symptom → cause → fix or avoidance), not vague "be careful" advice.
- References must include at least one **in-repo** link when the concept touches this codebase (search if needed).

## Document template

```markdown
# [Concept name]

## Short explanation (layman terms)

[Plain-language overview.]

## Theory (precise)

[Definitions, formal account, assumptions, limits.]

## Where it applies (examples)

- **Context:** … **Why this concept:** …
- …

## Common gotchas (examples)

- **Gotcha:** … **What goes wrong:** … **What to do instead:** …
- …

## Related concepts

- **Concept A** — … (one or two sentences: what it is, why explore it next).
- **Concept B** — …

## References

- [Title](https://example.com) — …
- [`path/in/repo/file.md`](path/in/repo/file.md) — …
```
