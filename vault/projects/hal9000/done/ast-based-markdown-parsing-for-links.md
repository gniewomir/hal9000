
# AST-based Markdown parsing for link validation (vault_fm)

## Context

[`vault_fm`](.scripts/vault_fm/__init__.py) checks and rewrites **in-repo link targets** in Markdown bodies (see policy in [`relative-links-to-other-md-files.md`](vault/projects/hal9000/done/relative-links-to-other-md-files.md)). Implementation used to approximate CommonMark with **line-based scanning**: skip fenced blocks, detect inline code spans, then regular expressions for inline `](dest)`, reference uses, and reference definitions.

That approach duplicated parts of a real Markdown grammar (nested emphasis, edge cases, reference resolution) and was easy to drift from what authors and renderers actually parse.

## Change (2026)

Link **discovery** for validation and rewrite now goes through **[mistune](https://pypi.org/project/mistune/)** in AST mode: parse the full body, walk **`link`** and **`image`** tokens, read destinations from each token’s **`attrs["url"]`**, and use the parser’s **`BlockState`** (notably **`env["ref_links"]`**) for reference-definition URLs.

**Unchanged:** repo-root path rules, tracked-file checks, symlink rejection, and the higher-level repair loops in [`rename_links.py`](.scripts/vault_fm/rename_links.py) / send / health. Those still call into [`links.py`](.scripts/vault_fm/links.py); only how destinations are **found** and **rewritten** moved to the AST pipeline.

## Behaviour notes

- **Fenced code and inline code** are not scanned as links by construction (they are `block_code` / `codespan` nodes, not link text), so the old hand-rolled fence scanner is no longer the source of truth for “what is a link.”
- **Undefined reference links** (`[text][missing]` with no `[missing]: …` definition) do not produce a link node under CommonMark; mistune leaves them as plain text. The tooling still reports **undefined reference** issues with a small supplementary line pass so behaviour stays visible to authors.
- **Rewrite path:** after mutating URLs on tokens and in **`ref_links`**, bodies are serialized with mistune’s **`MarkdownRenderer`**. That can **reformat** whitespace and where reference-definition lines appear; semantics and link targets should match policy, but diffs may be noisier than the old in-place string edits.

## Dependency

Parsing requires **mistune** (pinned in [`.scripts/requirements.txt`](.scripts/requirements.txt)). Install into the same interpreter used for [`send.sh`](send.sh) / [`check.sh`](check.sh) / [`fix.sh`](fix.sh); see the **Python dependencies** section in the root [`README.md`](README.md).

## Related

- Policy (what counts as a valid in-repo link): [`relative-links-to-other-md-files.md`](vault/projects/hal9000/done/relative-links-to-other-md-files.md)
- Implementation: [`.scripts/vault_fm/links.py`](.scripts/vault_fm/links.py)
