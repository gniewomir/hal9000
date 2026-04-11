from __future__ import annotations

import sys
import uuid
from collections import defaultdict
from pathlib import Path

from vault_fm.errors import EncodingError, ParseError
from vault_fm.gitutil import git_repo_root, list_tracked_md
from vault_fm.links import list_tracked_files_set, validate_in_scope_notes
from vault_fm.io import (
    compose_front_matter,
    default_fm_text,
    read_file_utf8,
    split_front_matter,
)
from vault_fm.parse import parse_fm_inner, rebuild_fm_canonical
from vault_fm.version import require_python


def _load_parsed(repo_root: Path, rel: str):
    path = repo_root / rel
    try:
        text, raw = read_file_utf8(path)
        sp = split_front_matter(text, raw)
    except (EncodingError, ParseError):
        raise
    if not sp.has_fm:
        return None, sp
    p = parse_fm_inner(sp.fm_text or "")
    return p, sp


def scan_vault(
    repo_root: Path,
) -> tuple[list[str], dict[uuid.UUID, list[str]], set[uuid.UUID], set[uuid.UUID]]:
    """issues, id_to_paths, referenced_ids, note_ids."""
    paths = list_tracked_md(repo_root)
    id_to_paths: dict[uuid.UUID, list[str]] = defaultdict(list)
    referenced: set[uuid.UUID] = set()
    note_ids: set[uuid.UUID] = set()
    issues: list[str] = []

    for rel in paths:
        try:
            p, sp = _load_parsed(repo_root, rel)
        except (ParseError, EncodingError) as e:
            issues.append(str(e))
            continue
        if p is None:
            issues.append(f"{rel}: missing front matter block")
            continue
        if not p.has_id_key or p.id_val is None:
            issues.append(f"{rel}: missing id")
            continue
        if not p.has_references_key:
            issues.append(f"{rel}: missing references key")
            continue
        nid = p.id_val
        note_ids.add(nid)
        id_to_paths[nid].append(rel)
        for r in p.refs_parsed:
            referenced.add(r)

    for r in referenced:
        if r not in note_ids:
            issues.append(f"missing reference: {r} is not any note id")

    for nid, ps in id_to_paths.items():
        if len(ps) > 1:
            issues.append(f"duplicate id {nid}: {', '.join(sorted(ps))}")

    return issues, dict(id_to_paths), referenced, note_ids


def _rewrite_note(
    repo_root: Path, rel: str, note_id: uuid.UUID, refs: list[uuid.UUID]
) -> None:
    p, sp = _load_parsed(repo_root, rel)
    if p is None or not sp.has_fm:
        return
    fm_text = sp.fm_text or ""
    new_inner = rebuild_fm_canonical(fm_text, note_id, refs)
    out = compose_front_matter(new_inner, sp.body_bytes)
    (repo_root / rel).write_bytes(out)


def _insert_default_front_matter_if_missing(repo_root: Path, rel: str) -> bool:
    """
    If rel has no --- … --- block, prepend canonical default front matter.
    Returns True if the file was written.
    """
    path = repo_root / rel
    try:
        text, raw = read_file_utf8(path)
        sp = split_front_matter(text, raw)
    except (EncodingError, ParseError):
        return False
    if sp.has_fm:
        return False
    note_id = uuid.uuid7()
    fm_new = default_fm_text(str(note_id))
    out = compose_front_matter(fm_new, sp.body_bytes)
    path.write_bytes(out)
    return True


def _fix_missing_front_matter_blocks(repo_root: Path) -> None:
    """Insert canonical default front matter when a file has no --- … --- block."""
    for rel in list_tracked_md(repo_root):
        _insert_default_front_matter_if_missing(repo_root, rel)


def fix_vault(repo_root: Path) -> None:
    """Apply safe automatic fixes (may run multiple internal passes)."""
    _fix_missing_front_matter_blocks(repo_root)

    _issues, id_to_paths, referenced, _note_ids = scan_vault(repo_root)

    # 1) Duplicate ids not referenced anywhere
    dup = [(nid, paths) for nid, paths in id_to_paths.items() if len(paths) > 1]
    for nid, paths in dup:
        if nid in referenced:
            continue
        for rel in sorted(paths)[1:]:
            try:
                p, _sp = _load_parsed(repo_root, rel)
            except (ParseError, EncodingError):
                continue
            if p is None or p.id_val is None:
                continue
            new_id = uuid.uuid7()
            _rewrite_note(repo_root, rel, new_id, p.refs_parsed)

    # 2) Remove dangling references
    _issues, _idmap, _ref, note_ids = scan_vault(repo_root)
    paths = list_tracked_md(repo_root)
    for rel in paths:
        try:
            p, sp = _load_parsed(repo_root, rel)
        except ParseError:
            continue
        if p is None or p.id_val is None or not p.has_references_key:
            continue
        filt = [r for r in p.refs_parsed if r in note_ids]
        if filt == p.refs_parsed:
            continue
        _rewrite_note(repo_root, rel, p.id_val, filt)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    fix = "--fix" in argv
    require_python()
    try:
        root = git_repo_root()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2

    if fix:
        fix_vault(root)

    issues, _a, _b, _c = scan_vault(root)
    for line in issues:
        print(line)

    paths = list_tracked_md(root)
    tracked = list_tracked_files_set(root)
    for line in validate_in_scope_notes(root, paths, tracked=tracked):
        print(line)
        issues.append(line)

    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
