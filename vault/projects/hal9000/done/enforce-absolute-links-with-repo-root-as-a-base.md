
# Enforce repo-root–absolute links (hard policy)

## Problem

**Relative** links (`../sibling.md`, `./note.md`) resolve differently depending on the **source file’s directory**. That is fine for humans and short URLs, but it complicates **automatic repair** after moves:

- A rename map from git is naturally keyed by **repo-relative paths** (`old → new`).
- To know whether a link “meant” the renamed file, tooling must **resolve** each relative target from each source path, then compare to the map.
- After a move, the **correct new relative string** differs for every linking file (different depth), so rewrites are **per-link recomputation**, not one global substitution.

So rename tracking is not enough for **simple, uniform** fixes when targets stay relative.

## Idea

**Require** Markdown link destinations that spell the target as the **git repo-relative path** (POSIX slashes), **without** a **leading `/`**.

Examples: `vault/projects/hal9000/done/relative-links-to-other-md-files.md`, `.scripts/vault_fm/__init__.py`.

**Why not `"/vault/…"`?** A leading slash is easy for humans to read as “from repo root,” but many renderers (e.g. GitHub pages) treat `/…` as **site**-absolute. Dropping the slash keeps the string aligned with `git` paths and avoids that class of host mismatch while staying unambiguous in `vault_fm` (paths are **not** resolved from the source file’s directory).

See [relative link validation](vault/projects/hal9000/done/relative-links-to-other-md-files.md).

Identity stays **path-based**; only the **spelling** of links in the body is canonical.

## Why it helps

- **One string per target:** every note that links to the same file uses the **same** destination text (modulo normalization), so matching link text to git’s `old_path` is direct.
- **Uniform rewrites:** when `old_path → new_path` is known unambiguously, replace that **one** path everywhere.
- **Aligns with the rename map:** keys are already repo-relative; link text matches that model without resolving from each source file first.

This does **not** make git’s rename **detection** more deterministic; it makes **applying** detected renames to Markdown **simpler and less ambiguous**.

## Hard policy (authoritative)

Enforcement is **strict**: violations fail `vault_fm send` (when it runs link validation) and `check.sh` / `vault_fm health`.

1. **Where it applies:** Same scan as today—in-scope tracked `.md` bodies, **outside** fenced code blocks and outside inline code spans; inline `[text](url)` / `![alt](url)` and reference-style destinations after resolving `[ref]: url`.
2. **Required form:** Any destination that is **not** skipped (fragments-only `#…`, empty, `https:`, `mailto:`, other `scheme:`, etc.) and that names a **repository path** after stripping `#` / `?` and percent-decoding must be the **full path from the repository root** with **no** leading `/`, e.g. `vault/topics/foo.md`. **`..` is not allowed** in the path; paths are **not** resolved from the source file’s directory.
3. **Rejected:** Leading `/` (use `vault/…` not `/vault/…`), bare relative paths (`note.md`, `./x`, `../y`), including in reference definitions.
4. **Unchanged:** External URLs, fragment-only anchors, and the symlink / casing / tracked-file rules in the done spec.

**Also applies** to images and other tracked assets: same spelling rules as for `.md` targets.

## Implementation (in tree)

- **Resolver / validation:** `.scripts/vault_fm/links.py` — `logical_target_rel` normalizes only repo-root spellings (no leading `/`, no `..`); `_check_one_path` errors on leading `/` or invalid paths.
- **Rename repair:** `.scripts/vault_fm/rename_links.py` — rewrites to `normalize_rel_path(new_target) + suffix` (no per-file relative paths).
- **Tests:** `.scripts/vault_fm/test_links.py`, `test_rename_links.py`.
- **Normative spec:** amend [relative-links-to-other-md-files.md](vault/projects/hal9000/done/relative-links-to-other-md-files.md) so it matches this policy (filename still says “relative” historically).

## Costs and risks

- **Verbosity:** paths are longer than `./note.md`.
- **Editors:** some previews assume link targets are relative to the current file; local validation is the source of truth.

## Relation to other work

- Complements [auto-fix after renames](vault/projects/hal9000/done/auto-fix-relative-links-to-md.md): rename repair emits full repo-relative targets, so updates align with git’s path map.
- [Stable ids in links](vault/projects/hal9000/ideas/ux/autofixing-links.md) remains a separate layer if you add id-based linking later.
