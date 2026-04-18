from __future__ import annotations

from pathlib import Path

from vault_fm.errors import EncodingError, ParseError
from vault_fm.gitutil import git_add, list_cached_renames, list_tracked_md
from vault_fm.io import compose_front_matter, read_file_utf8, split_front_matter
from vault_fm.links import (
    _path_part_for_check,
    _should_skip_destination,
    canonical_rel_link,
    logical_target_rel,
    list_tracked_files_set,
    rewrite_note_body_links,
    split_path_and_suffix,
    validate_in_scope_notes,
)
from vault_fm.paths import normalize_rel_path

MAX_REPAIR_ITERS = 3


def validate_tracked_links(repo_root: Path) -> list[str]:
    """Validate relative links in all tracked in-scope markdown files."""
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
        return canonical_rel_link(source_rel, new_target) + suffix

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
            sp = split_front_matter(text, raw)
        except (EncodingError, ParseError, OSError):
            continue
        if not sp.has_fm:
            body = text
            fm_text = None
        else:
            body = sp.body_bytes.decode("utf-8")
            fm_text = sp.fm_text

        replace_dest = _make_replace_dest(rel, rename)
        new_body = rewrite_note_body_links(rel, body, replace_dest)
        if new_body is None:
            continue
        new_bytes = (
            new_body.encode("utf-8")
            if not sp.has_fm
            else compose_front_matter(fm_text or "", new_body.encode("utf-8"))
        )
        if new_bytes != raw:
            path.write_bytes(new_bytes)
            touched.append(rel)
    return touched


def run_link_validation_with_rename_repair(repo_root: Path) -> list[str]:
    """
    Validate all tracked links; on failure, apply rename-based repairs (from index vs HEAD)
    and re-validate up to MAX_REPAIR_ITERS times. Returns remaining issue lines.
    """
    issues = validate_tracked_links(repo_root)
    if not issues:
        return []
    for _ in range(MAX_REPAIR_ITERS):
        touched = apply_rename_repairs_to_vault(repo_root)
        if not touched:
            return issues
        git_add(repo_root, touched)
        issues = validate_tracked_links(repo_root)
        if not issues:
            return []
    return issues
