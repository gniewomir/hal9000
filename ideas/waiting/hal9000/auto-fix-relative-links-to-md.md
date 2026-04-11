---
id: 019d7a30-17ff-77f9-abb1-cd6eeac594d0
references: []
---

# Auto-fix relative Markdown links after renames (stretch)

## Problem

Even with [validation of relative links to other Markdown files](../../done/hal9000/relative-links-to-other-md-files.md), every **rename or move** can leave many notes with outdated paths. Fixing them by hand is tedious and error-prone. A checker alone tells you what broke; it does not **rewrite** links to follow the new layout.

## Reasoning

- **Git records renames** (exact renames or similarity-based) in diffs and history. That gives a mapping **old path → new path** for files touched in a change set, which is strong signal for automatic updates.
- **Automatic edits** are safe only when **unambiguous**: one clear new target for each old path. When several files could match (e.g. duplicate basenames), the tool must **stop and ask** rather than guess wrong.
- This step **builds on** path validation: after rewriting, the same resolver should pass; the user is involved only when automation cannot choose safely.

## Proposed solution

1. **Inputs:** Git change information for the current commit or working tree (e.g. `git diff --name-status`, rename pairs from index vs HEAD). Build a map **former relative path → current relative path** for moved/renamed `.md` files under the vault.
2. **Scan** notes (at least those that reference old paths or that are staged) for Markdown links whose targets match **keys** in that map or whose **basename** matches a unique new location.
3. **Rewrite** link targets in the working tree (or as part of a `send` / `fix` pass) when exactly one **new** path is determined; skip or flag when **zero or many** candidates exist.
4. **Re-run** relative-link existence validation; surface remaining failures for manual edit.
5. **Policy:** Never rewrite inside fenced code blocks if those are excluded from link parsing; respect the same URL rules as the validator.

Optional later enhancement: resolve links via **note `id`** in the body (custom scheme or convention) so renames do not require rewrites—but that is a separate design from path-based auto-fix.
