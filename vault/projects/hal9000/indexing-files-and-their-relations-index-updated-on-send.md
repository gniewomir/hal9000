---
id: 019d7c07-e66b-7438-b70c-15131397a94f
references: []
---

# Persistent link/relation index (updated on send)

## Problem

A full scan of the vault on every check does not scale. A **local, persistent index** lets validation and link/relation fixes target only notes that matter for the current change set, while still keeping the graph consistent.

## Storage and tooling

* Index lives in a **file** (e.g. JSON) for now—not a database; format can be revisited if size or query patterns demand it.
* Index is **local** and **not committed** to the repo (no merge noise; each clone rebuilds or uses its own cache).
* **`vault_fm index`** (like `send` or `health`): by default **create the index if it is missing**; a **flag forces a full rebuild from scratch** (cold repair, corruption, or after large refactors).

## Data model

Each **note id** maps to one **record** (implementation may use one JSON object per id or equivalent). The record must include:

* **`filepath`** — canonical path for that id (e.g. repo-relative), so the tool can go from id to file without scanning the vault. On rename, update this field; ids in front matter stay authoritative per vault rules.
* **`referencing`** — map or set of **note ids** this note **links to** (outgoing edges).
* **`referenced_by`** — map or set of **note ids** that **link to** this note (incoming edges). This is the **reverse index**: when note **A** changes, only notes in `referenced_by` for **A** (plus **A** itself for its own outgoing links) need recomputation, not the whole vault. `referenced_by` is derivable from all `referencing` but is **materialized** for fast incremental updates.

Links and relations in those two edge collections are keyed by **target/source id**, not by path alone; paths live only in **`filepath`** on each record.

Together this is **`id → { filepath, referencing, referenced_by }`** (naming may vary; semantics must not).

## Alternative data model (strongly worth considering)

**Strongly consider** a simpler split: the **index file** holds only **`id → filepath`** (enough to resolve ids to paths without a vault scan). **What references what**—outgoing links and incoming backlinks—is **not** duplicated in the index; it lives in **front matter** on each note (e.g. fields for links out and/or backlinks in, exact shape TBD).

**Why it looks simpler:** one small persistent artifact (path map), graph semantics live **with** the content instead of a parallel JSON graph. **Tradeoffs to weigh:** front matter edits on every relation change; merge conflicts if multiple branches touch the same note’s relation fields; incremental send may still **derive** edges in memory for the dirty/touched set even if nothing writes a full graph file.

## Order of operations (send / commit pipeline)

1. **Front matter** is validated and updated **first** so every in-scope note has a stable **`id`** (and any other required fields). Nothing consults or updates the link index **before** identities exist.
2. **Change signal**: **staged, in-scope markdown** defines what is **dirty** for this run.
3. **Expand the check set**: for each dirty id, use **`referenced_by`** (and **`referencing`** as needed) to include any note that might need link/relation reads or writes. Unstaged files that **reference** a dirty note belong in this set even if they were not staged—otherwise backlinks outside the stage are missed.
4. **Validate** links and relations on that set; **apply fixes** (e.g. rewrite links).
5. **Revalidate** until clean (or surface errors and stop).
6. **Update the index** to reflect the **final** graph: all **touched** ids (including notes modified while fixing referrers), **id→filepath** for any path changes, and **remove** deleted notes from both directions of the graph. This happens **after** fixes and successful revalidation, **before** the git **commit** step of the send workflow completes.
7. Commit (or the remainder of `send`) proceeds.

## Clarifications (locked)

* **Dirty set vs. touched set**: “Staged” seeds **dirty**; **fixing** may edit additional files. The index update must reflect **every** note whose edges or path mapping changed in that run, not only originally staged paths.
* **Deletes**: Removing a note removes its entry, drops it from others’ `referencing` / `referenced_by`, and clears **`id → filepath`** for that id.
* **Cold start**: If no index file exists, **build a full index once**; afterwards incremental rules apply. **`index --force`** (or equivalent) rebuilds from scratch.

## Consistency

If the index is missing, forced to rebuild, or detected as inconsistent with disk (optional future: checksums or mtimes), fall back to **full reindex** rather than incremental updates. Incremental paths assume the previous index matched the repo after the last successful send.
