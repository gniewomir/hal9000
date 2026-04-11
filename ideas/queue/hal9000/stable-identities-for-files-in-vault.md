# Stable identities for files in the vault

## Problem

Markdown notes live in a Git-backed vault that will grow to many thousands of files. Folders and filenames are useful for humans but **change often** (moves, renames, reorganisation). Anything that identifies a note only by **path** breaks when the tree changes.

We need **stable identities** for notes and a **durable way to record relations** between them, without tying that machinery to a specific editor or renderer.

## Reasoning

- **Identity in front matter** keeps the canonical id next to the content, travels with the file in Git, and survives moves and renames without a separate registry that can drift.
- **Relations in front matter** (a list of referenced ids) avoids putting opaque ids in the body. Generic Markdown tools and hosts do not know how to resolve or follow `[[uuid]]`-style links; keeping the body as normal prose preserves portability. The graph stays explicit and machine-readable.
- **UUID7** for ids and references gives opaque, collision-resistant identifiers with a **time-ordered** shape, which helps debugging and casual sorting without embedding meaning in the id.
- **Hard invariants belong in automation**, not in long natural-language instructions: the **send** pipeline should enforce **immutable `id`** and **append-only `references`** so tooling and editors cannot accidentally violate the contract during normal sync.
- **No validation on commit** keeps daily work fast; **integrity and repair** are handled by a **separate health check** run when you choose—report-only by default, optional automatic fixes where unambiguous.
- **Shell at the vault root, Python under `scripts/`** keeps entry points obvious (`./send.sh`, future helpers) while parsing and graph logic stay testable and maintainable.
- **AI IDE instructions** (Cursor rules, `CLAUDE.md`, etc.) must stay **brief**: they are included in context for **every** conversation, so only non-negotiable bullets belong there; deeper explanation lives in this document. They are **advisory**; **send** and **health check** carry enforceable behavior.

## Chosen solution

### Tooling layout

- **Shell scripts** in the **repository root** act as the thin interface (invocation, Git, environment).
- **Python scripts** under **`scripts/`** perform heavy lifting: front-matter ensure/merge, parsing, vault-wide scans, reporting, and optional fixes.

### Front matter contract

For each Markdown document that should participate in the system:

- Ensure a **YAML front matter block** exists: add it for **new** files and for **existing** files that do not yet have one (wired into the **send** path so metadata is applied before commit when notes are staged).
- Inside that block:
  - **`id`**: a generated **UUID7** for the note (stable for the lifetime of that logical note; when copying a file to create a new note, treat it as a **new** id—do not duplicate identity).
  - **`references`**: a list of **UUID7** values this note points to—**always present**, even when **empty**.

### Send pipeline (enforced)

The **send** script (shell) invokes **`scripts/`** so that, for every markdown file included in the operation:

- **`id` is immutable:** if an `id` already exists in front matter, it **must not** be changed or regenerated. If missing, generate one UUID7 and write it.
- **`references` is append-only for existing values:** adding new reference ids when needed is allowed; **removing, replacing, or reordering** entries that were already present is **not** allowed by send (same-value deduplication policy can be defined if needed). New ids may be **appended** per product rules.

This is the **authoritative** enforcement of identity and reference stability for the normal push workflow—not optional IDE text.

### Health check (manual, whole vault)

A **separate script** under `scripts/` (not a Git hook) scans the entire vault when run.

**Data structures:** build a map **`id → file path(s)`** and collect all **referenced** ids from every `references` list (and any structures needed to detect duplicates and reverse links).

**Report (always):**

- **Missing references:** a referenced id that does not exist as any note’s `id`.
- **Duplicate ids:** the same `id` appears in more than one file.

**Optional automatic fix mode** (flag), applying only safe transforms:

- **Dangling references:** remove from `references` any id that does not exist in the vault.
- **Duplicate ids when the id is not referenced anywhere:** auto-resolve by choosing a **canonical** file (define a deterministic rule, e.g. sort paths and pick one), **keep** its `id`, assign **new UUID7** `id`s to the other files. Safe because nothing in the graph points at that id yet.

**Escalate to the user (do not auto-fix):**

- **Duplicate ids where that id appears in at least one `references` list:** resolving which file “owns” the id would break or ambiguously retarget edges; the tool must **list** the conflicting files and where the id is referenced and require a human decision.

Malformed front matter, missing keys, or self-reference policy can be additional categories in the same tool as it matures.

### Operational tradeoff

Broken or dangling references can exist in Git **until** the health check is run; that is accepted in exchange for **simple commits** and **on-demand** cleanup.

### AI / IDE assistants

Instructions for Cursor, Claude Code, or similar must be **short** (a few bullets), because they load into **every** session’s context. They should restate only: protected front matter region, **do not edit `id` / existing `references` entries** without explicit user instruction, body below `---` editable—and **point here** for full detail.

Hard guarantees come from **send** and **health check**, not from model behavior alone.

---

## Implementation todo

- [ ] Add **`scripts/`** layout (e.g. one module or small package for shared front-matter parsing and UUID7 generation; decide dependency: stdlib-only vs small YAML lib).
- [ ] Implement **front matter I/O**: read first `---` … `---` block, parse YAML enough for `id` / `references`, preserve body bytes; define normalization rules for comparisons.
- [ ] Implement **UUID7** generation compatible with the chosen library or a minimal correct implementation.
- [ ] Implement **`ensure_front_matter` (or equivalent)** used by send: create block if missing; ensure `id` exists; ensure `references` key exists (default `[]`); **never** overwrite existing `id`; **merge** new reference ids only (append-only for existing list semantics).
- [ ] Update **`send.sh`** to call the Python step for all markdown files that will be staged/committed (exact file set as per final workflow), then proceed with `git add`, commit, push.
- [ ] Implement **`healthcheck` command**: walk vault `*.md`, build `id → paths` and all outgoing references; print missing references and duplicate ids.
- [ ] Add **`--fix`** (or similar) to health check: remove dangling reference ids; resolve duplicate ids **only** when that id is not referenced anywhere (document canonical-file rule); print actionable report for unresolved duplicate-id cases.
- [ ] Add **dry-run** or confirmation for `--fix` if desired (optional safety).
- [ ] Smoke-test on a few real notes: new file, existing without FM, append reference, duplicate-id scenarios.
- [ ] Add **brief** AI-facing instructions (e.g. short `CLAUDE.md` section and/or one Cursor rule) that mirror this doc’s non-negotiables and link here; keep under a few bullets.
