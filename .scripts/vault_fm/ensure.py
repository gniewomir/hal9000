from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from vault_fm.errors import ParseError, ValidationError
from vault_fm.gitutil import git_show_index_text
from vault_fm.io import (
    compose_front_matter,
    default_fm_text,
    read_file_utf8,
    split_front_matter,
)
from vault_fm.parse import format_references_block, parse_fm_inner, rebuild_fm_canonical
from vault_fm.refs_util import dedupe_preserve, is_subsequence, strip_self_refs


@dataclass
class SendPlan:
    rel_path: str
    new_bytes: bytes | None
    warnings: list[str]


def _parse_index_refs_and_id(
    repo_root: Path, rel: str
) -> tuple[list[uuid.UUID] | None, uuid.UUID | None, str | None]:
    txt = git_show_index_text(repo_root, rel)
    if txt is None:
        return None, None, None
    raw = txt.encode("utf-8")
    try:
        sp = split_front_matter(txt, raw)
    except ParseError as e:
        return None, None, str(e)
    if not sp.has_fm:
        return [], None, None
    try:
        p = parse_fm_inner(sp.fm_text or "")
        return p.refs_parsed, p.id_val, None
    except ParseError as e:
        return None, None, str(e)


def compute_proposed(
    work_refs: list[uuid.UUID],
    note_id: uuid.UUID,
) -> tuple[list[uuid.UUID], list[str]]:
    warnings: list[str] = []
    d = dedupe_preserve(work_refs)
    out, stripped = strip_self_refs(d, note_id)
    if stripped:
        warnings.append(f"{note_id}: stripped self-reference from references")
    return out, warnings


def check_append_only(
    index_refs: list[uuid.UUID],
    proposed_refs: list[uuid.UUID],
    note_id: uuid.UUID,
) -> None:
    idx_d = dedupe_preserve(index_refs)
    idx_eff = [r for r in idx_d if r != note_id]
    if not is_subsequence(idx_eff, proposed_refs):
        raise ValidationError(
            "references append-only violation: staged index refs are not a subsequence "
            "of normalized working-tree refs"
        )


def prepare_send_file(repo_root: Path, rel: str) -> SendPlan:
    """Validate and compute new file bytes; does not write."""
    path = repo_root / rel
    text, raw = read_file_utf8(path)

    try:
        sp = split_front_matter(text, raw)
    except ParseError as e:
        raise ParseError(f"{rel}: {e}") from e

    warnings: list[str] = []

    if not sp.has_fm:
        note_id = uuid.uuid7()
        fm_new = default_fm_text(str(note_id))
        new_bytes = compose_front_matter(fm_new, sp.body_bytes)
        old_bytes = path.read_bytes()
        return SendPlan(rel, new_bytes if new_bytes != old_bytes else None, warnings)

    fm_text = sp.fm_text or ""
    try:
        parsed = parse_fm_inner(fm_text)
    except ParseError as e:
        raise ParseError(f"{rel}: {e}") from e

    idx_refs, idx_id, idx_err = _parse_index_refs_and_id(repo_root, rel)
    if idx_err:
        raise ParseError(f"{rel}: index blob parse error: {idx_err}")

    if parsed.id_val is not None and idx_id is not None and parsed.id_val != idx_id:
        raise ValidationError(
            f"{rel}: id is immutable (index has {idx_id}, working tree has {parsed.id_val})"
        )

    note_id = parsed.id_val or idx_id or uuid.uuid7()
    work_refs = list(parsed.refs_parsed)

    proposed, w = compute_proposed(work_refs, note_id)
    warnings.extend(f"{rel}: {x}" for x in w)

    if idx_refs is not None:
        check_append_only(idx_refs, proposed, note_id)

    fm_work = fm_text
    if not parsed.has_id_key:
        fm_work = f"id: {note_id}\n" + fm_work
        parsed = parse_fm_inner(fm_work)
    if not parsed.has_references_key:
        fm_work = fm_work + format_references_block(proposed)
        parsed = parse_fm_inner(fm_work)

    new_inner = rebuild_fm_canonical(fm_work, note_id, proposed)
    new_bytes = compose_front_matter(new_inner, sp.body_bytes)
    old_bytes = path.read_bytes()
    if new_bytes == old_bytes:
        return SendPlan(rel, None, warnings)
    return SendPlan(rel, new_bytes, warnings)


def apply_send_plan(repo_root: Path, plan: SendPlan) -> None:
    if plan.new_bytes is None:
        return
    path = repo_root / plan.rel_path
    path.write_bytes(plan.new_bytes)
