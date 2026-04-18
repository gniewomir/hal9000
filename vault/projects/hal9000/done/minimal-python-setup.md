
# Minimal Python setup (vault tooling)

**Superseded (2026)** as a YAML-front-matter implementation guide. The vault tooling still uses **Python 3.14+** under [`.scripts/vault_fm`](.scripts/vault_fm/__init__.py), but it **no longer** parses or writes `id` / `references` in YAML. Link validation parses Markdown with **mistune** (see [`ast-based-markdown-parsing-for-links.md`](vault/projects/hal9000/done/ast-based-markdown-parsing-for-links.md)); other pieces remain mostly stdlib. Responsibilities today: UTF-8 reads, repo-root link validation (see [`relative-links-to-other-md-files.md`](vault/projects/hal9000/done/relative-links-to-other-md-files.md)), and repair of link targets after **git-detected** renames/copies (`git diff --cached --name-status`).

For environment/version gating, see [`.scripts/ensure_python.sh`](.scripts/ensure_python.sh) and [`send.sh`](send.sh).

The previous hand-rolled YAML subset spec and `ensure_front_matter` plan applied only to the old FM model; see git history of this file if needed.
