from __future__ import annotations

from pathlib import Path

from vault_fm.errors import EncodingError
from vault_fm.gitutil import git_add, list_cached_renames, list_tracked_md
from vault_fm.io import read_file_utf8
from vault_fm.links import (
    _path_part_for_check,
    _should_skip_destination,
    logical_target_rel,
    list_tracked_files_set,
    resolve_link_for_canonical_fix,
    rewrite_note_body_links,
    split_path_and_suffix,
    validate_in_scope_notes,
)
from vault_fm.paths import normalize_rel_path

MAX_REPAIR_ITERS = 3


def _same_repo_path_spelling(path_part: str, canonical: str) -> bool:
    """True if path_part already uses canonical repo-root spelling (no ``/``, no ``..``)."""
    p = path_part.replace("\\", "/").strip()
    if not p or p.startswith("/"):
        return False
    if ".." in p:
        return False
    if p.startswith("./"):
        p = p[2:]
    return normalize_rel_path(p) == canonical


def _make_canonical_replace_dest(source_rel: str, tracked: frozenset[str]):
    """Rewrite destinations to repo-root canonical form (no /, no ..) when resolvable."""

    def replace_dest(raw: str) -> str | None:
        if _should_skip_destination(raw):
            return None
        pp = _path_part_for_check(raw)
        if not pp:
            return None
        resolved = resolve_link_for_canonical_fix(source_rel, pp, tracked)
        if resolved is None:
            return None
        canonical = normalize_rel_path(resolved)
        if _same_repo_path_spelling(pp, canonical):
            return None
        _, suffix = split_path_and_suffix(raw)
        return canonical + suffix

    return replace_dest


def apply_canonical_link_repairs_to_vault(repo_root: Path) -> list[str]:
    """
    Rewrite links that still use relative or ``/``-prefixed spellings to repo-root paths
    (no leading slash). Returns rel paths of files written.
    """
    paths = list_tracked_md(repo_root)
    tracked = list_tracked_files_set(repo_root)
    touched: list[str] = []
    for rel in paths:
        path = repo_root / rel
        try:
            text, raw = read_file_utf8(path)
        except (EncodingError, OSError):
            continue
        replace_dest = _make_canonical_replace_dest(rel, tracked)
        new_body = rewrite_note_body_links(rel, text, replace_dest)
        if new_body is None:
            continue
        new_bytes = new_body.encode("utf-8")
        if new_bytes != raw:
            path.write_bytes(new_bytes)
            touched.append(rel)
    return touched


def validate_tracked_links(repo_root: Path) -> list[str]:
    """Validate repo-root path links in all tracked in-scope markdown files."""
    paths = list_tracked_md(repo_root)
    tracked = list_tracked_files_set(repo_root)
    return validate_in_scope_notes(repo_root, paths, tracked=tracked)


def _make_replace_dest(
    source_rel: str, rename: dict[str, str]
):
    def replace_dest(raw: str) -> str | None:
        if _should_skip_destination(raw):
            return None
        pp = _path_part_for_check(raw)
        if not pp:
            return None
        r = logical_target_rel(source_rel, pp)
        if r is None:
            return None
        key = normalize_rel_path(r)
        if key not in rename:
            return None
        new_target = rename[key]
        _, suffix = split_path_and_suffix(raw)
        return normalize_rel_path(new_target) + suffix

    return replace_dest


def apply_rename_repairs_to_vault(repo_root: Path) -> list[str]:
    """
    Rewrite links in all tracked in-scope notes when destinations resolve to a path
    renamed in the index vs HEAD. Returns list of rel paths written.
    """
    pairs = list_cached_renames(repo_root)
    if not pairs:
        return []
    rename: dict[str, str] = {}
    for old, new in pairs:
        rename[normalize_rel_path(old)] = normalize_rel_path(new)

    touched: list[str] = []
    for rel in list_tracked_md(repo_root):
        path = repo_root / rel
        try:
            text, raw = read_file_utf8(path)
        except (EncodingError, OSError):
            continue

        replace_dest = _make_replace_dest(rel, rename)
        new_body = rewrite_note_body_links(rel, text, replace_dest)
        if new_body is None:
            continue
        new_bytes = new_body.encode("utf-8")
        if new_bytes != raw:
            path.write_bytes(new_bytes)
            touched.append(rel)
    return touched


def run_link_validation_with_rename_repair(repo_root: Path) -> list[str]:
    """
    Validate all tracked links; on failure, apply canonical link rewrites (relative or
    ``/``-prefixed → repo-root path), then rename-based repairs (index vs HEAD), then
    re-validate up to MAX_REPAIR_ITERS times. Returns remaining issue lines.
    """
    issues = validate_tracked_links(repo_root)
    if not issues:
        return []
    for _ in range(MAX_REPAIR_ITERS):
        touched_canon = apply_canonical_link_repairs_to_vault(repo_root)
        touched_rename = apply_rename_repairs_to_vault(repo_root)
        touched = sorted(set(touched_canon + touched_rename))
        if not touched:
            return issues
        git_add(repo_root, touched)
        issues = validate_tracked_links(repo_root)
        if not issues:
            return []
    return issues
