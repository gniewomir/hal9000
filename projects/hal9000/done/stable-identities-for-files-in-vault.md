---
id: 019d79fc-6a0c-7367-b3a9-de6f3141d363
references: []
---

# Stable identities for files in the vault

## Problem

Markdown notes live in a Git-backed vault that will grow to many thousands of files. Folders and filenames are useful for humans but **change often** (moves, renames, reorganisation). Anything that identifies a note only by **path** breaks when the tree changes.

We need **stable identities** for notes and a **durable way to record relations** between them, without tying that machinery to a specific editor or renderer.

## Reasoning

- **Identity in front matter** keeps the canonical id next to the content, travels with the file in Git, and survives moves and renames without a separate registry that can drift.
- **Relations in front matter** (a list of referenced ids) avoids putting opaque ids in the body. Generic Markdown tools and hosts do not know how to resolve or follow `[[uuid]]`-style links; keeping the body as normal prose preserves portability. The graph stays explicit and machine-readable.
- **UUID7** for ids and references gives opaque, collision-resistant identifiers with a **time-ordered** shape, which helps debugging and casual sorting without embedding meaning in the id.
- **Hard invariants belong in automation**, not in long natural-language instructions: the **send** pipeline should enforce **immutable `id`** and **append-only `references`** so tooling and editors cannot accidentally violate the contract during normal sync.
- **No mandatory Git hook** keeps daily work fast; **send** enforces the contract when you run it (staged, in-scope files). **Broader integrity and repair** are handled by a **separate health check** run when you choose—report by default, **`--fix`** where unambiguous, strict exit codes.
- **Shell at the vault root, Python under `.scripts/`** keeps entry points obvious (`./send.sh`, future helpers) while parsing and graph logic stay testable and maintainable.
- **AI IDE instructions** (Cursor rules, `CLAUDE.md`, etc.) must stay **brief**: they are included in context for **every** conversation, so only non-negotiable bullets belong there; deeper explanation lives in this document. They are **advisory**; **send** and **health check** carry enforceable behavior.

## Chosen solution

### Tooling layout

- **Shell scripts** in the **repository root** act as the thin interface (invocation, Git, environment).
- **Python scripts** under **`.scripts/`** perform heavy lifting: front-matter ensure/merge, parsing, vault-wide scans, reporting, and optional fixes.

### Which files participate (scope)

**Send** and **health** use the **same rules** so anything that gets normalized on send is also checked by health.

- **Included:** any **`.md`** file **under** the repository root **except**:
  - files whose path is **directly in the repo root** (no top-level `*.md`), and
  - any file **under `.scripts/`** (recursively), and
  - any file **under `.cursor/`** (recursively).
- **Encoding:** in-scope files are **UTF-8**; invalid UTF-8 is an error.

Enumeration should match Git’s view of the tree (e.g. **`git ls-files`** for tracked paths) plus the path filters above—spell this in implementation so untracked paths do not silently diverge from what you commit.

### Front matter contract

For each **in-scope** Markdown document:

- Ensure a **YAML front matter block** exists: add it for files **without** `---` … `---` on the **send** path (new `uuid.uuid7()`, `references: []`, canonical shape).
- Inside that block:
  - **`id`** and **`references`** must appear exactly as **`id`** and **`references`** (**lowercase**). Any other casing (e.g. `Id:`) is **malformed**.
  - **Duplicate** `id:` or `references:` keys at the same level → **malformed**.
  - **`id`**: a **UUID7** for the note (stable for the lifetime of that logical note; when copying a file to create a new note, treat it as a **new** id—do not duplicate identity). Non-UUID7 values are invalid.
  - **`references`**: a list of **UUID7** values—**always present**, even when **empty**.
- **Other keys** at the top level of the block are **opaque** to tooling: only **`id`** and **`references`** regions are parsed and rewritten; **original key order** is preserved.
- **Layout after the block:** on **write**, the closing `---` is always followed by a **newline** before the markdown body. If the body does not already begin with a line break, the writer inserts one so the note body starts on its own line below the fence (typically a **blank** line between the fence and the first body line when the body had no leading newline).

### Send pipeline (enforced)

The **send** script (shell) invokes **`.scripts/`** for **staged** `.md` files that are **in scope** (see above).

**Staging and exit behavior**

- **No staged `.md` at all** → **warning**, **non-zero** exit (abort; do not commit/push).
- **Staged `.md` exists but none are in scope** (e.g. only root, `.scripts/`, or `.cursor/`) → **warning**, **exit 0** (nothing to normalize).
- **Warnings** (e.g. stripped self-refs) go to stderr; **exit 0** if the run **succeeded** (validation + writes + re-stage).

**Validation before write**

- **Validate every** in-scope staged file **before** writing **any** of them: **aggregate all errors**, print them, **non-zero** exit, **no** file writes.
- **Malformed** front matter (subset violation, invalid UUID7, etc.) → error naming the file(s).

**Per-file rules**

- **`id` is immutable:** if an `id` already exists in front matter, it **must not** be changed or regenerated. If missing, generate one UUID7 and write it.
- **`references` is append-only** for **distinct** ids already present: **removing, replacing, or reordering** existing entries is **not** allowed. **Duplicate** entries in the list are **collapsed** on write (**first occurrence** order for unique ids). New ids may be **appended** per product rules.
- **Self-reference:** if **`references`** contains this file’s own **`id`**, send **removes** those entries and prints a **warning** (still **exit 0** if otherwise successful).

After a **successful** Python pass, **`git add`** every in-scope path that was **written** so the following commit matches disk.

This is the **authoritative** enforcement of identity and reference stability for the normal push workflow—not optional IDE text.

### Health check (manual, in-scope tree)

A **separate script** under `.scripts/` (not a Git hook) scans **in-scope** markdown when run (same path rules as send).

**Data structures:** build a map **`id → file path(s)`** and collect all **referenced** ids from every `references` list (and any structures needed to detect duplicates and reverse links).

**Report (always):**

- **Missing references:** a referenced id that does not exist as any note’s `id`.
- **Duplicate ids:** the same `id` appears in more than one file.
- **Malformed** front matter, invalid UUID7, duplicate keys, wrong key casing—same categories as send where applicable.

**Exit codes (strict):**

- **Non-zero** if **any** integrity issue remains (report-only or after **`--fix`**). **Exit 0** only when the in-scope vault is **fully clean**.

**`--fix` (writes immediately)**

- **`--fix`** applies safe transforms **on disk** as soon as it runs; Git is the review gate (no separate `--apply` step).
- **Missing front matter block:** insert a default block (new UUID7 `id`, `references: []`, canonical shape)—same outcome as send’s ensure path for a file with no `---` … `---` opener.
- **Layout after the block:** for every in-scope note that already has a front matter block, if on-disk bytes differ from the canonical **compose** output (at least one newline after the closing `---` before the body, inner YAML ending with a newline before the closing delimiter, etc.), rewrite to match—without changing parsed `id` or `references` values.
- **Dangling references:** remove from `references` any id that does not exist in the vault.
- **Duplicate ids when the id is not referenced anywhere:** auto-resolve by choosing a **canonical** file (deterministic rule, e.g. sort paths and pick one), **keep** its `id`, assign **new UUID7** `id`s to the other files. Safe because nothing in the graph points at that id yet.

**Escalate to the user (do not auto-fix):**

- **Duplicate ids where that id appears in at least one `references` list:** resolving which file “owns” the id would break or ambiguously retarget edges; the tool must **list** the conflicting files and where the id is referenced and require a human decision.

### Operational tradeoff

Broken or dangling references can exist in Git **until** the health check is run; that is accepted in exchange for **simple commits** and **on-demand** cleanup.

### AI / IDE assistants

Instructions for Cursor, Claude Code, or similar must be **short** (a few bullets), because they load into **every** session’s context. They should restate only: protected front matter region, **do not edit `id` / existing `references` entries** without explicit user instruction, body below `---` editable—and **point here** for full detail.

Hard guarantees come from **send** and **health check**, not from model behavior alone.

---

## Implementation todo

- [ ] Add **`.scripts/`** layout (e.g. one module or small package for shared front-matter parsing and UUID7 generation; **stdlib only** per [minimal-python-setup.md](minimal-python-setup.md)).
- [ ] Implement **front matter I/O**: read first `---` … `---` block, hand-rolled subset for **`id`** / **`references`**, **opaque** preservation for other keys, preserve body bytes; UTF-8 validation.
- [ ] Implement **UUID7** via `uuid.uuid7()` and **validate** UUID7 on read for `id` and every reference entry.
- [ ] Implement **`ensure_front_matter` (or equivalent)** for send: create block if missing; ensure `id` exists; ensure `references` exists (default `[]`); **never** overwrite existing `id`; **merge** new reference ids (append-only); **collapse duplicate** ref entries; **strip** self-refs with warning; **validate-all / aggregate errors / no partial writes** on failure.
- [ ] Update **`send.sh`**: Python 3.14+ gate; staged in-scope `.md` only; exit rules (no staged `.md` vs only out-of-scope); **`git add`** after successful rewrites; then commit/push as today.
- [ ] Implement **`healthcheck` command**: enumerate in-scope `*.md` (path rules + `git ls-files` or equivalent); build `id → paths` and outgoing references; strict exit codes; issues include malformed FM / invalid UUID7 / key rules.
- [ ] Add **`--fix`** to health: **writes immediately**; insert missing front matter where unambiguous; normalize compose layout (newline after fence, etc.) for all in-scope notes with front matter; remove dangling refs; resolve duplicate ids **only** when unreferenced (document canonical-file rule); print actionable report for unresolved duplicate-id cases; **strict** exit (0 only if fully clean after run).
- [ ] Smoke-test on a few real notes: new file, existing without FM, append reference, duplicate refs, self-ref strip, malformed FM, out-of-scope-only staging.
- [ ] Add **brief** AI-facing instructions (e.g. short `CLAUDE.md` section and/or one Cursor rule) that mirror this doc’s non-negotiables and link here; keep under a few bullets.
