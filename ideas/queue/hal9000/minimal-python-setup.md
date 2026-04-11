# Minimal Python setup (vault tooling)

Companion to [stable identities for files in the vault](stable-identities-for-files-in-vault.md). This note records **requirements**, **reasoning**, **decisions**, and an **implementation plan** for Python under `scripts/` without poetry, pyenv, or committed third-party dependencies.

---

## Requirements

- **Python:** 3.14 or higher on the machine. Entry points must **verify** the version at runtime rather than assume it.
- **Layout:** Shell at the repository root (`send.sh`, future helpers). **Python under `scripts/`** for front-matter ensure/merge, parsing, vault-wide scans, and reporting.
- **Dependencies:** **Standard library only** for this track: no committed lockfiles, no `.venv` in the repo, no pyenv, poetry, pipenv, or similar unless the approach changes explicitly.
- **Front matter:** YAML between `---` … `---`. Each participating note needs **`id`** (UUID7) and **`references`** (list of UUID7). **`references` must always be present**, even when empty.
- **YAML subset for parsing (must be correct and documented):**
  - **`references` as an array:** accept both **block sequence** (`- item` under the key) and **flow sequence** (`[a, b]` on the line with `references:` or immediately following the colon per agreed rules).
  - **Scalars:** support **unquoted**, **single-quoted**, and **double-quoted** values for `id` and for each entry in `references`.
- **Code style:** Small surface area; avoid sprawl of one-off helpers. Prefer one scalar parser, two list paths (block vs flow), and shared front-matter split/merge logic.
- **Behavior:** Send pipeline enforces **immutable `id`** and **append-only `references`** (see the stable-identities doc). Health check is separate; optional `--fix` comes later.

---

## Reasoning

- **Identity and relations in front matter** stay next to content, move with Git, and survive renames without a separate registry.
- **UUID7** gives opaque, time-ordered ids. **Python 3.14** provides `uuid.uuid7()` in the standard library, so no extra package is required for generation.
- There is **no YAML parser in the stdlib**. Pulling in PyYAML implies a virtualenv and install steps, which conflicts with “minimal moving parts” for this track. The contract only needs **`id`** and **`references`** at the note level, so a **strict, documented YAML subset** is sufficient if unsupported constructs are **rejected with a clear error**.
- **Block vs flow and quoted vs unquoted** formats will appear as humans and editors edit notes. The reader should accept common variants; the writer can use a **single canonical form** (recommended: block list for `references`) so diffs stay predictable.

---

## Decisions made

| Topic | Decision |
|--------|----------|
| Tooling | No pyenv, poetry, pipenv. Use `python3` and the stdlib only. |
| Virtualenv | None while dependencies remain zero; nothing to install or gitignore for Python packages. |
| UUID7 | `uuid.uuid7()` from `uuid` (Python 3.14+). |
| YAML | Hand-rolled **subset** for `id` and `references` only; not a general YAML 1.1/1.2 implementation. |
| Block vs flow | **Parse both**; specify rules (indentation for block; bracket matching and comma splitting **outside** quotes for flow). |
| Quotes | Unquoted tokens; single-quoted with `''` for a literal quote; double-quoted with at least `\"` and `\\`. |
| Serialization | **Emit one canonical style** (e.g. block `references`) even when the file previously used flow. |
| Other keys | Decide explicitly: either **only** `id` / `references` at the top level of the managed block, or **preserve** other front-matter lines as opaque text when rewriting. |

---

## Implementation plan

1. **Layout** — Add `scripts/` with one module (or a very small package) holding front-matter I/O, parsing, and shared types. Optionally add `.gitignore` entry for `.venv/` only if third-party deps are introduced later.

2. **Version gate** — At CLI startup (and optionally in `send.sh` before invoking Python): require `sys.version_info >= (3, 14)`.

3. **Front matter I/O** — Split each file into opening delimiter, **front matter text**, closing delimiter, and **body**; preserve body bytes. If there is no front matter block, define the default block to insert.

4. **Scalar parser** — One function: trim, then unquoted token, or single-quoted string, or double-quoted string with minimal escapes. Use it for `id` and for each list element.

5. **`references` parsing** — After `references:`:
   - If the remainder on the same line contains `[` before end of line → **flow**: scan to matching `]`, split on commas at bracket depth one, **not** inside quotes.
   - Else → **block**: read following lines indented deeper than the `references` key; each line `- …` yields one element after scalar parsing.

6. **`ensure_front_matter` (send path)** — If no block: insert default with new `uuid.uuid7()` and `references: []` (canonical). If `id` exists: never change it; if missing: set once. Ensure `references` exists; merge new reference ids only per append-only rules. Re-serialize in canonical form.

7. **`send.sh`** — After version check, run `python3 scripts/…` over the markdown set that participates in the commit (define: all relevant `.md` vs staged-only). Then existing `git add`, commit, push.

8. **Health check** — Separate `scripts/` entry point: walk vault `*.md`, reuse the same parser, build `id → paths`, collect outgoing references, report missing references and duplicate ids; add `--fix` later per the stable-identities doc.

9. **Tests** — Table-driven cases for scalars, block lists, flow lists, quoted values, and commas inside quoted flow elements. Run with `python3 -m unittest` or a small test module under `scripts/`.

10. **AI-facing docs** — Keep Cursor/CLAUDE bullets short; link to [stable-identities-for-files-in-vault.md](stable-identities-for-files-in-vault.md) for enforceable behavior.

---

## YAML subset spec (normative for the parser)

Document these rules next to the implementation and in tests:

- **Supported:** top-level keys `id` and `references` with the scalar and list forms above.
- **Flow lists:** comma-separated inside `[` `]`; splitting respects quotes; unclosed brackets or quotes are errors.
- **Block lists:** `-` lines indented more than `references:`; stop when indentation returns to the key’s level or less.
- **Unsupported (reject or error clearly):** anchors, aliases, tags, merges, multiline scalars in exotic forms, arbitrary nested structures — unless you later widen the spec on purpose.

Canonical **write** format should match what the tooling emits (recommended: block `references` for readability and stable diffs).
