
# Stable identities for files in the vault

**Superseded (2026).** The vault **no longer** uses YAML front matter with UUID `id` and `references:`. Identity is the **normalized repo-relative path** to each note; relations between notes are **only** expressed as resolvable **links in the markdown body**. Tooling lives under [`.scripts/vault_fm`](.scripts/vault_fm/__init__.py) (`send`, `health`, link validation, rename-based link repair). Rationale and migration notes: [`drop-frontmatter-as-dead-end.md`](vault/projects/hal9000/done/drop-frontmatter-as-dead-end.md).

The archived specification that described UUID7 in front matter, append-only references, and the send/health FM contract is **not** current; see git history of this file if you need that text.
