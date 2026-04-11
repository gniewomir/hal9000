---
id: 019d79fc-6a0c-7367-b3a9-de6e48426bc6
references: []
---
# Minimal Python setup (vault tooling)

Companion to [stable identities for files in the vault](stable-identities-for-files-in-vault.md). This note records **requirements**, **reasoning**, **decisions**, and an **implementation plan** for Python under `scripts/` without poetry, pyenv, or committed third-party dependencies.

---

## Requirements

- **Python:** 3.14 or higher on the machine. Entry points must **verify** the version at runtime rather than assume it.
- **Layout:** Shell at the repository root (`send.sh`, future helpers). **Python under `scripts/`** for front-matter ensure/merge, parsing, vault-wide scans, and reporting.
- **Dependencies:** **Standard library only** for this track: no committed lockfiles, no `.venv` in the repo, no pyenv, poetry, pipenv, or similar unless the approach changes explicitly.
- **Encoding:** In-scope files are **UTF-8**; invalid UTF-8 is an error with a clear message.
- **Front matter:** YAML between `---` … `---`. Each participating note needs **`id`** (UUID7) and **`references`** (list of UUID7). **`references` must always be present**, even when empty. Managed keys are **`id` and `references` in lowercase only**; other casings (e.g. `Id:`) are **malformed** (see stable-identities doc for scope: which paths participate).
- **YAML subset for parsing (must be correct and documented):**
  - **`references` as an array:** accept both **block sequence** (`- item` under the key) and **flow sequence** (`[a, b]` on the line with `references:` or immediately following the colon per agreed rules).
  - **Scalars:** support **unquoted**, **single-quoted**, and **double-quoted** values for `id` and for each entry in `references`.
- **Code style:** Small surface area; avoid sprawl of one-off helpers. Prefer one scalar parser, two list paths (block vs flow), and shared front-matter split/merge logic.
- **Behavior:** Send enforces **immutable `id`** and **append-only `references`**, with explicit normalizations (duplicate ref collapse, self-reference strip—see stable-identities doc). Health check is separate; **`--fix` writes immediately** to disk (default front matter if the note has no block, then other safe repairs—see stable-identities doc); Git is the review gate.

---

## Reasoning

- **Identity and relations in front matter** stay next to content, move with Git, and survive renames without a separate registry.
- **UUID7** gives opaque, time-ordered ids. **Python 3.14** provides `uuid.uuid7()` in the standard library, so no extra package is required for generation.
- There is **no YAML parser in the stdlib**. Pulling in PyYAML implies a virtualenv and install steps, which conflicts with “minimal moving parts” for this track. The contract only needs **`id`** and **`references`** at the note level, so a **strict, documented YAML subset** is sufficient if unsupported constructs are **rejected with a clear error**.
- **Block vs flow and quoted vs unquoted** formats will appear as humans and editors edit notes. The reader should accept common variants; the writer uses a **single canonical form** for **`references`** (block list). **Other top-level keys** in the block stay **opaque**: tooling replaces only the **`id`** and **`references`** regions and **preserves original key order** elsewhere.

---

## Decisions made

| Topic | Decision |
|--------|----------|
| Tooling | No pyenv, poetry, pipenv. Use `python3` and the stdlib only. |
| Virtualenv | None while dependencies remain zero; nothing to install or gitignore for Python packages. |
| Encoding | **UTF-8** only for in-scope files. |
| UUID7 | Values in `id` and `references` must be **UUID7** only; generation via `uuid.uuid7()` (Python 3.14+). Reject other UUID versions when parsing. |
| YAML | Hand-rolled **subset** for **`id`** and **`references`**; not a general YAML 1.1/1.2 implementation. **Other keys** are **opaque** (unparsed except for locating managed regions); **preserve top-level key order** on rewrite. |
| Key names | **`id`** and **`references`** — **strict lowercase**. Any other casing is **malformed**. |
| Duplicate keys | More than one **`id:`** or **`references:`** at the same level → **malformed**. |
| Block vs flow | **Parse both**; specify rules (indentation for block; bracket matching and comma splitting **outside** quotes for flow). |
| Quotes | Unquoted tokens; single-quoted with `''` for a literal quote; double-quoted with at least `\"` and `\\`. |
| Serialization | **Canonical value shape** for **`references`** (block list) even when the file previously used flow; **preserve key order** for the whole block. |
| Duplicate ref entries | On write, **collapse duplicates** preserving **first-seen order** of distinct ids. |
| Self-reference | **`references`** must not include this note’s own **`id`**; send **strips** self-refs and **warns** (stderr); exit **0** if nothing else failed. |

---

## Implementation plan

1. **Layout** — Add `scripts/` with one module (or a very small package) holding front-matter I/O, parsing, and shared types. Optionally add `.gitignore` entry for `.venv/` only if third-party deps are introduced later.

2. **Version gate** — At CLI startup (and optionally in `send.sh` before invoking Python): require `sys.version_info >= (3, 14)`.

3. **Front matter I/O** — Split each file into opening delimiter, **front matter text**, closing delimiter, and **body**; preserve body bytes. **No** `---` … `---` block: insert default (new `uuid.uuid7()`, `references: []`, canonical). When rewriting, replace only **`id`** / **`references`** regions; **opaque** lines for other keys stay in **original key order**.

4. **Scalar parser** — One function: trim, then unquoted token, or single-quoted string, or double-quoted string with minimal escapes. Use it for `id` and for each list element. Validate **UUID7** after parse.

5. **`references` parsing** — After `references:`:
   - If the remainder on the same line contains `[` before end of line → **flow**: scan to matching `]`, split on commas at bracket depth one, **not** inside quotes.
   - Else → **block**: read following lines indented deeper than the `references` key; each line `- …` yields one element after scalar parsing.

6. **`ensure_front_matter` (send path)** — If no block: insert default with new `uuid.uuid7()` and `references: []` (canonical). If `id` exists: never change it; if missing: set once. Ensure `references` exists; merge new reference ids per append-only rules; **collapse duplicate** ref entries (first occurrence wins); **strip** self-refs, **warn**. Re-serialize managed keys in canonical form inside their regions. **Send:** validate **all** in-scope staged files first, **aggregate errors**, **no writes** if any fail; on success, **`git add`** every path the tool rewrote, then shell continues to commit/push.

7. **`send.sh`** — After version check, run Python over **staged** `.md` paths that **participate** (same path rules as health—see stable-identities doc). **No** staged `.md` at all → **warning, non-zero exit** (abort). **Staged only out-of-scope** (e.g. only root/`scripts/`/`.cursor/`) → **warning, exit 0**. On success, processed files are re-staged as above.

8. **Health check** — Separate `scripts/` entry point: scan **in-scope** `*.md` (see stable-identities doc for enumeration and exclusions), reuse the same parser, build `id → paths`, collect outgoing references, report issues. **`--fix`** applies writes **immediately** (including inserting a default `---` … `---` block when missing). Exit **0** only when the in-scope vault is **fully clean** (strict); otherwise **non-zero**.

9. **Tests** — Table-driven cases for scalars, block lists, flow lists, quoted values, and commas inside quoted flow elements. Run with `python3 -m unittest` or a small test module under `scripts/`.

10. **AI-facing docs** — Keep Cursor/CLAUDE bullets short; link to [stable-identities-for-files-in-vault.md](stable-identities-for-files-in-vault.md) for enforceable behavior.

---

## YAML subset spec (normative for the parser)

Document these rules next to the implementation and in tests:

- **Managed keys:** only **`id`** and **`references`**, **lowercase** — required spelling; anything else (e.g. `Id:`) is **unsupported / malformed**.
- **Duplicate keys:** two **`id:`** or two **`references:`** lines at the same level → **malformed**.
- **Supported values:** `id` scalar and `references` as list (scalar and list forms above); validate **UUID7** for every id and list element.
- **Flow lists:** comma-separated inside `[` `]`; splitting respects quotes; unclosed brackets or quotes are errors.
- **Block lists:** `-` lines indented more than `references:`; stop when indentation returns to the key’s level or less.
- **Other top-level keys:** **opaque** — preserved as text spans; not interpreted as full YAML objects (still **reject** if the overall block cannot be scanned safely for managed regions).
- **Unsupported (reject or error clearly):** anchors, aliases, tags, merges, multiline scalars in exotic forms, arbitrary nested structures — unless you later widen the spec on purpose.

Canonical **write** format for **`references`** should match what the tooling emits (block list for readability and stable diffs).
