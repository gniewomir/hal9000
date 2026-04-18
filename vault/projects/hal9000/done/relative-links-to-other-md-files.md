
# Relative links (validation)

## Problem

Tools and authors historically used **per-file relative** Markdown links, e.g. `[title](sibling.md)` or `[title](../folder/note.md)`. **Policy today:** in-repo links must spell the target as the **full path from the git repository root** (POSIX slashes) **without** a leading `/` (e.g. `vault/topics/a.md`, not `/vault/topics/a.md`), so the same string matches `git` paths and rename repair. Leading `/` is rejected to avoid hosts that interpret `/…` as site-absolute URLs.

**Identity** for a note is its **repo-relative path**; the **graph** between notes is carried only by **links in the body**. Those links can still **drift after renames** unless validation (and optional rename-based repair) updates targets.

## Reasoning

- Catching broken links **at send time** and in a **health** pass fails fast: bad changes do not land without an explicit fix.
- Validation is **mechanical**: normalize each in-scope filesystem target to a **repo-relative path** (no leading `/`, no `..` segments; not resolved from the source file’s directory), then check policy (tracked file, correct casing, no symlink-as-target).
- Rename/copy detection (`index` vs `HEAD`) can **rewrite** link destinations to match moved files while preserving `#` / `?` suffixes; everything else stays a hard validation error until fixed manually.

## Specification (decisions)

### What to scan

- **Sources:** Same **in-scope** path rules as the rest of `vault_fm` (`is_in_scope`)—same set as send/health for markdown bodies.
- **Skip regions:** Link-like text inside **fenced code blocks** or **inline code** is not part of the link AST (same effect as “do not validate” for those regions). Details: [ast-based-markdown-parsing-for-links.md](vault/projects/hal9000/done/ast-based-markdown-parsing-for-links.md).
- **HTML:** Do not validate `<a href="...">`; repository rules ask authors to use **`[text](url)`** only for navigation links in Markdown.

### Link syntax to validate

- **Inline:** `[label](destination)` and `![alt](destination)` (same rules for both).
- **Reference-style:** Resolve `[label][ref]` / `[ref][]` using per-file **`[ref]: url`** definitions (strip optional title after the URL; validate the URL path).
- **Skip:** Fragment-only or empty destinations, e.g. `[text](#heading)` or `[text]()`.

### Destinations to check

- **Include:** Scheme-free paths that name a file under the repository: the destination must be the **path from the git repository root** with **no** leading `/` (e.g. `vault/foo.md`). **Do not** use `../`, `./`, or bare sibling names; **do not** use a leading `/` (validator error).
- **Exclude schemes** (do not validate as repo paths): e.g. `https:`, `mailto:`, `file:`, and other non-filesystem URL schemes.
- **Normalization:** Strip **`#fragment`** and **`?query`** before existence checks. Apply **URI percent-decoding** on the path (e.g. `%20`). Reject paths containing `..` after parsing.
- **Targets:** Any **git-tracked file** (not only `.md`)—images and other assets count the same as notes.

### Valid target rule

- Resolved path must exist in the **git index as tracked**, with **strict path casing** (portable with Linux/CI, not only case-insensitive local FS).
- **Symlinks:** **Error** if the path produced by the link resolves to a **symlink**—authors must link to the **canonical tracked regular file**, not a symlink path. (Implementation may use a single “invalid target” message; distinct reasons optional if cheap.)

### `send` and `health`

- **`vault_fm send`:** When there is at least one **staged** in-scope `.md` file, runs **full-repo** link validation (and rename-based repair when needed) before the shell script commits. Validation uses the **current working tree** against **tracked** targets.
- **`vault_fm health`:** Same validation rules over all in-scope tracked markdown. **`--fix`** runs a repair loop: first **canonical** rewrites (relative or ``/``-prefixed targets → repo-root path without leading slash), then **rename** repairs from git index vs `HEAD`, then re-validates (bounded iterations).

### Errors and exit code

- **Collect all** broken links in one run, print them (source file, location, bad destination), then **exit non-zero** if any failures—one fix pass can clear the list.
- **Implementation:** link discovery uses a **Markdown AST** ([mistune](https://pypi.org/project/mistune/)) so behaviour aligns with a real parser; see [ast-based-markdown-parsing-for-links.md](vault/projects/hal9000/done/ast-based-markdown-parsing-for-links.md).

## Stretch (automatic repair after moves)

See [auto-fix-relative-links-to-md.md](vault/projects/hal9000/done/auto-fix-relative-links-to-md.md).
