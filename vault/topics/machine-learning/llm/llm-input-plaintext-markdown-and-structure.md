
# LLM input: plain text vs Markdown, implicit structure, and job-offer extraction

Notes from an internal discussion (April 2026), expanded with examples and pointers to standard references.

## Executive summary

- **Plain text and Markdown are both just token sequences** to the model. There is no separate “Markdown mode” in the weights; structure is inferred from **tokens and statistical patterns** learned during training (documentation, forums, READMEs, etc.).
- **Markdown** tends to help when headings, lists, and fenced code blocks are **clean and faithful** to the source. It hurts when HTML→Markdown conversion introduces **false structure** (broken lists, mangled tables).
- For **structured extraction from scraped job posts**, reliability usually depends more on **denoising**, **explicit output schemas**, and **stable section boundaries** than on Markdown per se.
- **Headings without `#`** are often recoverable from **context** (short isolated lines, capitalization, numbering, semantics), but that inference is **probabilistic**—explicit markers or real headings improve consistency.

---

## Plain text vs Markdown: tradeoffs

### Similarities

- Both are fed through **tokenization** (subword BPE/SentencePiece–style units are typical in modern LLMs).
- The model’s job is still **next-token prediction** (possibly conditioned on instructions); formatting does not switch on a different “parser.”

### Where Markdown helps

1. **Explicit hierarchy** — `#` / `##` give cheap, repeatable cues for section boundaries versus body text.
2. **Code vs prose** — fenced blocks with a language tag signal *verbatim, syntactic content*; useful when extraction must not paraphrase snippets.
3. **Lists and tables** — bullets and pipe tables chunk content into **regular units** (when the conversion is correct).
4. **Training overlap** — models see lots of Markdown-shaped technical text, so common patterns often align with prior learning.

### Where Markdown costs

1. **Token overhead** — punctuation (`#`, `*`, `` ` ``, `[]()`) consumes tokens; for very short prompts the overhead matters more than for long documents (where structure can *save* natural-language scaffolding).
2. **Noisy conversion** — bad HTML→Markdown can invent nesting, split columns wrong, or break tables; that noise competes with factual extraction.
3. **Ambiguity** — heavy or broken Markdown can be **echoed** or mistaken for content to reproduce; unclosed code fences are worse than plain text.

### When plain text is preferable

- **Narrative or linear** content where extra syntax adds little.
- **Messy scrapes** where Markdown would mostly encode **artifacts**, not semantics.
- Content full of **literal** backticks, asterisks, or brackets—plain text avoids fighting the tokenizer and the model’s “template” instincts.

---

## Use case: structured data from scraped job offers

Goals such as salary range, location, seniority, tech stack, employment type, and company name are sensitive to:

- **Denoising** — remove navigation, cookie banners, “similar jobs,” and repeated apply CTAs.
- **Verbatim numbers** — preserve currency symbols, separators, and ranges (`50–70k PLN gross / month`) without normalizing prematurely in a way that splits tokens badly.
- **Schema-first extraction** — define a **fixed JSON (or equivalent) schema** with nullable fields and enums so the model is not inventing structure twice.
- **Pipeline choice**:
  - Prefer **plain text + your own section labels** when HTML→Markdown is unreliable.
  - Prefer **Markdown** when your converter consistently yields **honest headings and lists**.

| Goal | Practical lean |
|------|----------------|
| Messy real-world HTML | Plain text + explicit `SECTION:` lines (or similar) + strict JSON schema |
| Clean, doc-like JD pages | Markdown *may* help sectioning |
| Tabular salary grids | Do not trust pipe tables from scrapes; preserve lines or handle tables separately |

---

## Can models tell headings from paragraphs without Markdown?

**Yes, often** — not because of a heading detector, but because **statistical cues** in plain text match patterns seen in training:

- Short line, **blank line**, then a long block → strong “title + body” feel.
- **Title Case**, **ALL CAPS**, or label-like phrases (“Requirements”, “Nice to have”).
- **Numbered sections** (`1.`, `A.`).
- **Semantic grouping** — a line looks like a topic label and the following lines elaborate.

**Limits:** one-line intros, legal boilerplate, broken newlines from scraping, or flattened multi-column layouts all increase confusion. For extraction pipelines, **explicit markers** or real Markdown headings (when clean) reduce variance.

---

## Practical examples

### 1. Plain text: heading-like line vs one-line paragraph

```text
We're excited to grow the team and hope you'll apply.

What you'll do
Ship features on our payments API, collaborate with product,
and participate in on-call rotation for the billing service.
```

Here **What you'll do** behaves like a heading because it is short, isolated, and followed by elaboration. A model will usually group the bullet-style sentence under it—but it is still **inference**, not a guaranteed parse.

```text
We're looking for someone who loves backend work and wants to shape our roadmap.
```

This is also a **short first line**, but it reads as **body** (full sentence, narrative). Heading detection is **more ambiguous** without surrounding structure.

### 2. Noisy Markdown from a bad scrape

```markdown
- Seniority: Mid#### Responsibilities- Build APIs- Mentor juniors#### Benefits
```

False `####`, run-together list items, and missing newlines create **fake hierarchy**. For extraction, **this is often worse** than stripped plain text with manual newlines.

### 3. Plain text + explicit sections (extraction-friendly)

```text
TITLE: Senior Backend Engineer
COMPANY: ExampleCorp
LOCATION: Remote (EU)

SECTION: Requirements
- 5+ years Python or Go
- Experience with PostgreSQL

SECTION: Nice to have
- Kubernetes

SECTION: Compensation
8000–11000 PLN gross monthly
```

You supply the structure the scrape failed to preserve; the model fills your schema instead of guessing section boundaries.

### 4. When Markdown helps

```markdown
## Requirements

- Python or Go (5+ years)
- PostgreSQL

## Salary

8000–11000 PLN gross / month
```

If this faithfully reflects the page, headings and lists **anchor** fields better than an unstructured wall of text.

---

## Theory (and sources you can cite)

### 1. Sequence of tokens, not a document layout tree

Transformer-based LLMs (decoder-only or encoder–decoder) consume **ordered token embeddings**. There is **no native DOM or page geometry** in the model input: anything that corresponds to “heading,” “caption,” or “footnote” must be **encoded in the token sequence** (markup, newlines, wording) or inferred from context. The original Transformer architecture is described in Vaswani et al. (2017).

**Reference:** Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin, *Attention Is All You Need*, 2017. [https://arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762)

### 2. Tokenization

Text is segmented into **subword** units (BPE, Unigram LM, SentencePiece, etc.). Punctuation and Markdown delimiters are often **separate tokens** or split across tokens, which slightly changes the budget and boundaries compared to “words only.” The **BPE** idea for NMT is commonly cited as:

**Reference:** Rico Sennrich, Barry Haddow, Alexandra Birch, *Neural Machine Translation of Rare Words with Subword Units*, 2016. [https://arxiv.org/abs/1508.07909](https://arxiv.org/abs/1508.07909)

(For SentencePiece as used in many production models, see Taku Kudo and John Richardson’s *SentencePiece* documentation and paper.)

### 3. What “understanding structure” means here

“Discerning a heading” is **not** a dedicated module running a heading classifier; it is **contextual prediction** over token sequences after training on diverse text where headings *correlate* with short lines, following newlines, section keywords, etc. **Explicit Markdown** reduces that statistical ambiguity by making section starts **cheaply identifiable** in token space—when the Markdown itself is trustworthy.

---

## Quick decision checklist

1. Is the **HTML→text** pipeline **high quality**? If no, avoid leaning on Markdown syntax; add **your own** section scaffolding.
2. Is there **code or tight verbatim** content? Fenced blocks help—if fences are reliable.
3. Is the task **schema extraction**? Define **JSON + nulls**; optionally **two-step** (locate salary block, then parse numbers).
4. Are headings **ambiguous** in plain text? Add `#` **or** explicit `SECTION:` lines—whichever survives your pipeline intact.

references:
  - [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
  - [Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909)
