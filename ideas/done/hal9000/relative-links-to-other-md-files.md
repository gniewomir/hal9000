---
id: 019d7a30-17ff-77f9-abb1-cd6f7e5d2a2f
references: []
---
# Relative links (validation)

## Problem

Tools and authors add **relative** Markdown links to notes and assets, e.g. `[title](sibling.md)`, `[title](../folder/note.md)`, or `![fig](../assets/diagram.png)`. Those links are useful in editors and on GitHub. When files are **moved or renamed**, path-based links that still use the old location **break silently** until someone opens the target or runs a link checker.

The vault already encodes **stable identity** in YAML (`id`, `references`), but **body links are separate**: they are not updated by front-matter tooling and can drift after renames.

## Reasoning

- Catching broken links **at send time** and in a **health** pass fails fast: bad changes do not land without an explicit fix.
- Validation is **mechanical**: resolve each in-scope relative target from the source file (or repo root for leading `/`), normalize, and check policy (tracked file, correct casing, no symlink-as-target).
- This complements UUID-based `references:`: front matter stays canonical for graph semantics; body links stay human-readable, with integrity enforced by resolution checks.

## Specification (decisions)

### What to scan

- **Sources:** Same **in-scope** path rules as the rest of `vault_fm` (`is_in_scope`)—same set as send/health for markdown bodies.
- **Skip regions:** Do not treat link-like text inside **fenced code blocks** or **inline code** as links.
- **HTML:** Do not validate `<a href="...">`; repository rules ask authors to use **`[text](url)`** only for navigation links in Markdown.

### Link syntax to validate

- **Inline:** `[label](destination)` and `![alt](destination)` (same rules for both).
- **Reference-style:** Resolve `[label][ref]` / `[ref][]` using per-file **`[ref]: url`** definitions (strip optional title after the URL; validate the URL path).
- **Skip:** Fragment-only or empty destinations, e.g. `[text](#heading)` or `[text]()`.

### Destinations to check

- **Include:** Scheme-free relative paths and repo-root paths **`/path/from/repo-root`** (resolve from **git repository root**).
- **Exclude schemes** (do not validate as repo paths): e.g. `https:`, `mailto:`, `file:`, and other non-filesystem URL schemes.
- **Normalization:** Strip **`#fragment`** and **`?query`** before existence checks. Apply **URI percent-decoding** on the path (e.g. `%20`), then normalize `.` / `..` and reject unsafe path behavior.
- **Targets:** Any **git-tracked file** (not only `.md`)—images and other assets count the same as notes.

### Valid target rule

- Resolved path must exist in the **git index as tracked**, with **strict path casing** (portable with Linux/CI, not only case-insensitive local FS).
- **Symlinks:** **Error** if the path produced by the link resolves to a **symlink**—authors must link to the **canonical tracked regular file**, not a symlink path. (Implementation may use a single “invalid target” message; distinct reasons optional if cheap.)

### `send` and `health`

- **`vault_fm send`:** Run link validation **after** front-matter / ensure steps have been written for the send plan, **before** commit/push. Staging is expected to happen so the working tree matches what you commit; validation uses the **current working tree** against **tracked** targets.
- **`vault_fm health`:** Same validation rules over in-scope files (full pass as appropriate).

### Errors and exit code

- **Collect all** broken links in one run, print them (source file, location, bad destination), then **exit non-zero** if any failures—one fix pass can clear the list.
- Parser implementation can stay **stdlib-only** (no mandatory external Markdown parser): pragmatic extraction after skipping code regions, plus reference-definition handling, with tests grounded in real notes.

## Stretch (automatic repair after moves)

See [auto-fix-relative-links-to-md.md](auto-fix-relative-links-to-md.md).
