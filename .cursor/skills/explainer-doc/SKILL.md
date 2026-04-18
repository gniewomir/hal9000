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

Deliver a **single markdown document** (new or revised) with **exactly these top-level sections**, in order. The reader should finish with **enough depth to act** (choose tools, spot pitfalls, debug) — not a glossary entry or a thin outline.

**Practical focus (throughout):** Tie abstract ideas to **what you do** day to day: decisions, workflows, APIs, commands, or repo-specific patterns. When you state a rule, show **how it shows up in practice** (before/after, concrete criteria, or a short walkthrough). Surface-level one-liners are not enough.

1. **Short explanation (layman terms)** — Plain language for someone unfamiliar with the topic; no jargon unless defined. Enough substance that a reader gets the *shape* of the idea (not a single vague paragraph). If the topic needs a quick analogy or contrast with something familiar, include it.
2. **Theory (precise)** — Formal or technical account: definitions, invariants, how it fits in a broader model, limits and assumptions. Use precise terminology. **Bridge to practice:** after the core definitions, add a short subsection or paragraph on **how practitioners use this theory** (e.g. what to measure, what to configure, what to watch in logs) so theory is not isolated from use.
3. **Where it applies (examples)** — This section carries most of the **practical weight**. Give **several** concrete scenarios (aim for roughly **4–8** bullets unless the topic is extremely narrow) where the concept is the right tool. For each bullet, include **Context**, **What you actually do** (steps, options, or patterns — not just “use X”), **Why this concept**, and **Tradeoffs or when to pick something else**. Prefer realistic combinations (e.g. stack + constraint) over generic “web apps.”
4. **Common gotchas (examples)** — Misunderstandings, edge cases, footguns, and how to recognize or avoid them. Prefer real patterns over generic warnings. Aim for **at least 3** gotchas when the topic allows; each should read like **symptom → likely cause → fix or verification step** with enough detail to reproduce or diagnose.
5. **Related concepts** — Neighboring ideas worth exploring next: for each, **one or two sentences** (what it is and why it matters relative to the main topic). Prefer a small bullet list (roughly **5–9** items); optional short links if helpful. Keep these short, but list enough neighbors that the reader can **continue learning with a practical path** (what to learn next to ship or debug).
6. **References** — Bulleted links: official docs, specs, authoritative articles, and **paths to relevant files in this repo**.

   **In-repo link targets (this repository):** Use the **path from the git repository root**, **POSIX slashes**, **no leading `/`** — e.g. `vault/topics/node/event-loop.md`, `.scripts/vault_fm/links.py`. That matches `vault_fm` validation and rename repair (see [`vault/projects/hal9000/done/relative-links-to-other-md-files.md`](vault/projects/hal9000/done/relative-links-to-other-md-files.md)). **Do not** use per-file relative navigation between notes (`../sibling.md`, `./note.md`) or a **leading slash** (`/vault/...`) for in-repo targets. You may append `#fragment` or `?query` when needed. External URLs use normal `https://...` links. Do **not** use absolute filesystem paths (`/home/...`), `file://` URLs, or other machine-specific roots.

Use `##` headings with those section titles (adjust parenthetical bits to match, but keep the six-part structure).

Optional: a single `#` title line at the top for the concept name. **Do not add YAML front matter** to generated or reworked vault markdown unless the user explicitly asks; the vault does not use front matter for identity or relations.

## Reworking existing documents

When the user points at existing markdown (paste, path, or open file):

1. Read the full source; preserve factual correctness and intent.
2. Map content into the six sections; **move and rewrite** for clarity rather than duplicating rambling blocks.
3. If material is missing for a section, add a brief honest gap note *or* research from repo/docs (with references) — do not invent citations. Prefer **expanding** thin sections with practical detail over leaving them skeletal.
4. Keep the user's examples if they are good; tighten wording; merge duplicates.
5. If the original used a different heading hierarchy, normalize to this structure without losing information.

## Quality bar

- **Depth:** The document should feel **substantial** — multiple paragraphs where needed, not a slide deck. If the draft reads like a summary of summaries, **add** scenarios, steps, criteria, or diagnostic detail until it meets the section guidance above.
- Layman section must stand alone for a quick read but still **ground** the reader; theory section must satisfy someone who already knows adjacent concepts **and** connect to what people do with the idea.
- **Practical applications first:** “Where it applies” and “Common gotchas” should together answer “**When do I reach for this? What do I do? What breaks?**” Default assumption: the reader wants to **use** the concept, not only recognize its name.
- Related concepts must stay **short per item** (one–two sentences each); they are pointers, not mini explainers — but the **list** should be rich enough to suggest a learning path.
- Gotchas must be **specific** (symptom → cause → fix or avoidance), not vague "be careful" advice.
- References must include at least one **in-repo** link when the concept touches this codebase (search if needed). Links to other markdown or tracked files in this repo must use the **repo-root path form** (see References section above), not `../`-style paths between siblings.

## Document template

```markdown
# [Concept name]

## Short explanation (layman terms)

[Plain-language overview: enough paragraphs that the “what and why” is clear. Optional: analogy or contrast.]

## Theory (precise)

[Definitions, formal account, assumptions, limits.]

**In practice:** [How this theory maps to decisions, tooling, observability, or typical workflows — not a second theory lecture.]

## Where it applies (examples)

- **Context:** … **What you do:** … (concrete steps/patterns) **Why this concept:** … **Tradeoffs / alternatives:** …
- **Context:** … **What you do:** … **Why this concept:** … **Tradeoffs / alternatives:** …
- … (several bullets; vary constraints and stacks where it helps)

## Common gotchas (examples)

- **Gotcha:** … **What goes wrong:** … **What to do instead / how to verify:** …
- … (enough entries to cover realistic failure modes)

## Related concepts

- **Concept A** — … (one or two sentences: what it is, why explore it next).
- **Concept B** — …
- … (enough pointers for a practical next-learning path)

## References

- [Title](https://example.com) — …
- [Other topic](vault/topics/example/other-topic.md) — … (in-repo: **repo-root** path from git root, no leading `/`)
```
