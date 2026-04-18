
# Drop front matter — decisions (dead end for UUID + `references:`)

Working goal: **remove all YAML front matter and all tooling that reads/writes it**, and treat the vault as **relative links only** for structure and automation.

## What replaces FM semantics

- **Identity** is the **strict resolved repo-relative path** (POSIX, normalized `..` / `.`, no parallel UUID layer).
- **Edges** are **only** resolvable links in markdown bodies (same rules as `vault_fm.links`).
- **`id:` / `references:`** go away; no machine-maintained reference lists alongside the body.

## Link validation rules (post-FM)

- **`#fragment` / `?query`:** validate that the **target file exists**; **do not** require heading slugs to match (fragments ignored for CI).
- When tooling **rewrites** link paths (e.g. after renames), recompute only the **path** and **preserve** the original `?…` and `#…` suffixes on the destination string.

## Rename automation (ships before FM removal)

- **Phase 1:** Keep current FM + add **rename-based link repair** (already implemented in `vault_fm send` / `health --fix`).
- **Phase 2:** **Strip FM** and delete FM-specific code, hooks, and rules once link-only workflow is stable.

### Rename repair behavior

- **Trigger:** Run repair **only when** link validation fails (not speculatively on every `git` rename).
- **Source of truth for moves:** `git diff --cached --name-status -z -M` → **`R*` / `C*`** pairs (index vs `HEAD`).
- **Scope:** Update links in **every tracked in-scope `.md`** whose resolved target equals the **old** path; then **`git add`** touched files so the tree is not half-fixed.
- **Where it runs:** Both **`vault_fm send`** and **`vault_fm health --fix`** (shared loop, max **3** iterations).
- **Output:** Emit **one canonical minimal** relative path from each source file to the new target (deterministic spelling).

## What to delete in phase 2 (inventory)

- `.scripts/vault_fm` pieces that **split/compose FM**, **`id` / `references`**, send/health FM ensure and append-only rules.
- **Cursor:** [`immutable-frontmatter`](../../../../.cursor/rules/immutable-frontmatter.mdc) rule and **`block-frontmatter`** hook — replace or remove so they match a no-FM vault.
- **Docs** that describe the UUID + FM contract (update or mark superseded so FM is not reintroduced by habit).

## Non-goals / limits

- Rename repair **does not** fix typos or missing files **without** a matching Git rename pair; those stay **hard failures** with validator line/column output.
- **Path index / backlinks** by UUID are **out** unless recreated **by path** (optional later).
