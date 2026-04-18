---
id: 019d7c07-e66b-7438-b70c-15131397a94f
references: []
---

# Vault index: id → filepath CSV (updated on send)

## Problem

A full scan of the vault on every check does not scale. A **local, persistent index** maps each note **`id`** to its **filepath** so tools can resolve “which file is this id?” without walking every markdown file. **Who references whom** is not stored in the index; it stays in **front matter** (and any inline links), and the send pipeline reads or updates those fields as needed.

## Storage and tooling

* **Single CSV file** — one row per note; columns **`id`** and **`filepath`** (see below). No parallel JSON graph file.
* Index is **local** and **not committed** to the repo (no merge noise; each clone rebuilds or uses its own cache).
* **`vault_fm index`** (like `send` or `health`): by default **create the index if it is missing**; a **flag forces a full rebuild from scratch** (cold repair, corruption, or after large refactors).

## CSV format

* **Header row** (first line), for example: `id,filepath`
* **`id`** — UUID string, same as the note’s front matter `id`.
* **`filepath`** — path to the markdown file **relative to the vault root** (canonical, use one convention: forward slashes, no leading `./`).
* One row per id; each id appears at most once.

Example:

```text
id,filepath
019d7c07-e66b-7438-b70c-15131397a94f,projects/hal9000/indexing-files-and-their-relations-index-updated-on-send.md
```

This file is the **only** persisted id→path map. It is enough for:

* Resolving a reference to an id to a concrete file path during validation and fixes.
* Updating **`filepath`** when a note is renamed or moved (refresh that row).
* Removing a row when a note is deleted (and cleaning ids from others’ `references` uses front matter, not the CSV).

## What is not in the index

* **Outgoing or incoming link sets** (`referencing` / `referenced_by`) are **not** duplicated here. They live in each note’s **front matter** (e.g. `references: [...]`) and/or body links, per vault conventions.
* **Incremental send** still builds whatever **in-memory** edge view it needs for the **dirty/touched** set by reading those fields from disk—it does not require a second on-disk graph.

## Order of operations (send / commit pipeline)

1. **Front matter** is validated and updated **first** so every in-scope note has a stable **`id`** (and any other required fields). Nothing relies on the CSV **before** identities exist.
2. **Change signal**: **staged, in-scope markdown** defines what is **dirty** for this run.
3. **Expand the check set**: include any note that might need reference reads or writes. Because the index does not store backlinks, this step uses **front matter `references` (and similar)** on dirty notes and, when ids change or moves occur, **finds referrers** by scanning in-scope notes (or a cached strategy—implementation detail) so unstaged files that reference a dirty id are not missed.
4. **Validate** links and references on that set; **apply fixes** (e.g. rewrite paths or `references` lists when targets move).
5. **Revalidate** until clean (or surface errors and stop).
6. **Update the CSV** to match the **final** vault layout: **upsert** `id,filepath` for every touched or moved note, **delete** rows for removed notes. This runs **after** fixes and successful revalidation, **before** the git **commit** step of the send workflow completes.
7. Commit (or the remainder of `send`) proceeds.

## Clarifications (locked)

* **Dirty set vs. touched set**: “Staged” seeds **dirty**; **fixing** may edit additional files. The CSV update must reflect **every** note whose path mapping changed in that run, not only originally staged paths.
* **Deletes**: Removing a note removes its CSV row; clearing that id from other notes’ `references` is a **front matter** step, not a column in the CSV.
* **Cold start**: If no CSV exists, **build a full index once** (scan vault for `id` in front matter, emit rows); afterwards incremental rules apply. **`index --force`** (or equivalent) rebuilds from scratch.

## Consistency

If the CSV is missing, forced to rebuild, or detected as inconsistent with disk (optional future: checksums or mtimes), fall back to **full reindex** rather than incremental updates. Incremental paths assume the previous CSV matched the repo after the last successful send.
