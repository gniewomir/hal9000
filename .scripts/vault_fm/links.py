from __future__ import annotations

import os
import re
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

from vault_fm.gitutil import list_tracked_files
from vault_fm.paths import normalize_rel_path

# Link reference definition: up to 3 spaces, [id]: dest with optional <> and trailing title.
_REF_DEF_RE = re.compile(
    r"^ {0,3}\[([^\]]+)\]:\s*(?:<([^>\n]*)>|(\S+))(?:\s+[\"'(\[].*)?$"
)
# Reference-style link use: [text][ref] or ![alt][ref]; second bracket may be empty (shortcut).
_REF_USE_RE = re.compile(r"!?\[([^\]]*)\]\s*\[([^\]]*)\]")


def list_tracked_files_set(repo_root: Path) -> frozenset[str]:
    """Set of all git-tracked paths (forward slashes, relative to repo root)."""
    return frozenset(list_tracked_files(repo_root))


def _inline_code_spans(line: str) -> list[tuple[int, int]]:
    """Half-open [start, end) spans of inline code on this line (backtick runs)."""
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(line)
    while i < n:
        if line[i] != "`":
            i += 1
            continue
        start = i
        tick = 0
        while i < n and line[i] == "`":
            tick += 1
            i += 1
        close = line.find("`" * tick, i)
        if close == -1:
            spans.append((start, n))
            break
        end = close + tick
        spans.append((start, end))
        i = end
    return spans


def _in_spans(idx: int, spans: list[tuple[int, int]]) -> bool:
    for a, b in spans:
        if a <= idx < b:
            return True
    return False


def _iter_body_lines_outside_fences(body: str) -> list[tuple[int, str]]:
    """(1-based line number, line text) for lines not inside ``` / ~~~ fences."""
    out: list[tuple[int, str]] = []
    in_fence = False
    for line_no, line in enumerate(body.splitlines(), start=1):
        m = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if m:
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append((line_no, line))
    return out


def _parse_ref_definitions(lines: list[tuple[int, str]]) -> dict[str, str]:
    """Map lowercased reference label -> raw destination string."""
    defs: dict[str, str] = {}
    for _line_no, line in lines:
        m = _REF_DEF_RE.match(line.rstrip())
        if not m:
            continue
        label = m.group(1).strip().lower()
        dest = (m.group(2) or m.group(3) or "").strip()
        if dest:
            defs[label] = dest
    return defs


def _parse_link_dest_parens(line: str, open_paren_idx: int) -> tuple[str, int] | None:
    """open_paren_idx points at `(` in `](`. Returns (dest, index of closing `)`."""
    dest_start = open_paren_idx + 1
    if dest_start >= len(line):
        return None
    if line[dest_start] == "<":
        gt = line.find(">", dest_start + 1)
        if gt == -1:
            return None
        dest = line[dest_start + 1 : gt]
        if gt + 1 >= len(line) or line[gt + 1] != ")":
            return None
        return dest, gt + 1
    depth = 0
    p = dest_start
    while p < len(line):
        c = line[p]
        if c == "(":
            depth += 1
        elif c == ")":
            if depth == 0:
                return line[dest_start:p], p
            depth -= 1
        p += 1
    return None


def _parse_inline_link_dests(
    line: str, code_spans: list[tuple[int, int]]
) -> list[tuple[int, str]]:
    """(1-based column of destination start, raw dest) for `](dest)` on this line."""
    results: list[tuple[int, str]] = []
    i = 0
    while True:
        j = line.find("](", i)
        if j == -1:
            break
        if _in_spans(j, code_spans) or _in_spans(j + 1, code_spans):
            i = j + 2
            continue
        parsed = _parse_link_dest_parens(line, j + 1)
        if parsed is None:
            i = j + 2
            continue
        dest, close_idx = parsed
        dest_start = j + 2
        col = dest_start + 1
        results.append((col, dest))
        i = close_idx + 1
    return results


def _parse_ref_uses(
    line: str, code_spans: list[tuple[int, int]]
) -> list[tuple[int, str]]:
    """(1-based column of match start, raw url from definition lookup done outside)."""
    out: list[tuple[int, str]] = []
    for m in _REF_USE_RE.finditer(line):
        if _in_spans(m.start(), code_spans) or _in_spans(m.end() - 1, code_spans):
            continue
        g1, g2 = m.group(1), m.group(2)
        ref_key = (g2.strip() if g2.strip() else g1.strip()).lower()
        if not ref_key:
            continue
        out.append((m.start() + 1, ref_key))
    return out


def _should_skip_destination(raw: str) -> bool:
    s = raw.strip()
    if not s or s.startswith("#"):
        return True
    if "://" in s:
        return True
    if len(s) >= 2 and s[0].isalpha() and s[1] == ":" and len(s) > 2 and s[2] in "/\\":
        return True
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*):", s)
    if m:
        return True
    return False


def _path_part_for_check(raw_dest: str) -> str:
    s = raw_dest.strip()
    s = s.split("#", 1)[0]
    s = s.split("?", 1)[0]
    return unquote(s).strip()


def split_path_and_suffix(raw_dest: str) -> tuple[str, str]:
    """
    Split `path` from optional `?query` and/or `#fragment` suffix (first `?` or `#` wins).
    Returns (path_only, suffix_including_first_sep) e.g. ("a.md", "?x#y").
    """
    s = raw_dest.strip()
    positions = [i for i in (s.find("?"), s.find("#")) if i != -1]
    if not positions:
        return s, ""
    cut = min(positions)
    return s[:cut], s[cut:]


def canonical_rel_link(source_rel: str, target_rel: str) -> str:
    """Minimal relative path from source file's directory to target (repo-relative, POSIX)."""
    src_dir = str(PurePosixPath(source_rel).parent)
    tgt = str(PurePosixPath(target_rel))
    rel = os.path.relpath(tgt, src_dir or ".")
    return normalize_rel_path(rel.replace(os.sep, "/"))


def legacy_logical_target_rel(source_rel: str, path_part: str) -> str | None:
    """
    Resolve a link the pre-policy way: leading ``/`` is from repo root; otherwise resolve
    from the source file's directory (supports ``..`` / ``./``).
    Used only to discover the intended tracked path when migrating old spellings.
    """
    raw = path_part.replace("\\", "/").strip()
    if not raw:
        return None
    if raw.startswith("/"):
        p = PurePosixPath(raw.lstrip("/"))
    else:
        parent = PurePosixPath(source_rel).parent
        p = parent / PurePosixPath(raw)
    parts: list[str] = []
    for part in p.parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
        else:
            parts.append(part)
    if not parts:
        return None
    return normalize_rel_path("/".join(parts))


def resolve_link_for_canonical_fix(
    source_rel: str, path_part: str, tracked: frozenset[str]
) -> str | None:
    """
    Decide which repo-relative path a link points at for migration to canonical spelling.

    Prefer :func:`logical_target_rel` when it matches a tracked file; if a bare filename
    matches both repo-root and source-relative resolutions, prefer the relative (legacy)
    target when both exist in ``tracked``.
    """
    legacy = legacy_logical_target_rel(source_rel, path_part)
    if legacy is None:
        return None
    strict = logical_target_rel(source_rel, path_part)

    if path_part.strip().startswith("/"):
        return legacy if legacy in tracked else None

    if strict is not None and strict in tracked:
        if (
            legacy != strict
            and legacy in tracked
            and "/" not in path_part.replace("\\", "/")
        ):
            return legacy
        return strict

    if legacy in tracked:
        return legacy
    return None


def logical_target_rel(source_rel: str, path_part: str) -> str | None:
    """
    Normalize a link destination to a repo-relative path string (forward slashes).

    In-repo links must spell the target as a path from the **git repository root**
    **without** a leading slash (avoids site-absolute URLs in hosts that treat `/…`
    as domain-root). Example: ``vault/topics/a.md``, not ``/vault/topics/a.md``.
    ``..`` and ``./`` segments are not allowed; paths are not resolved from the
    source file's directory.

    ``source_rel`` is accepted for API compatibility but ignored for resolution.
    """
    _ = source_rel
    raw = path_part.replace("\\", "/").strip()
    if not raw:
        return None
    if raw.startswith("/"):
        return None
    p = PurePosixPath(raw)
    parts: list[str] = []
    for part in p.parts:
        if part in ("", "."):
            continue
        if part == "..":
            return None
        parts.append(part)
    if not parts:
        return None
    return normalize_rel_path("/".join(parts))


def _check_one_path(
    repo_root: Path,
    source_rel: str,
    raw_dest: str,
    tracked: frozenset[str],
) -> str | None:
    """Return error message, or None if OK / skipped."""
    if _should_skip_destination(raw_dest):
        return None
    path_part = _path_part_for_check(raw_dest)
    if not path_part:
        return None
    if path_part.startswith("/"):
        return (
            "link target must not start with /; use repo-root path without "
            f"leading slash: {raw_dest!r}"
        )
    rel_str = logical_target_rel(source_rel, path_part)
    if rel_str is None:
        return (
            "invalid repo-root path (path from git root, no .. or /.): "
            f"{raw_dest!r}"
        )
    if rel_str not in tracked:
        return f"broken link (not tracked or wrong casing): {raw_dest!r} -> {rel_str}"
    cand = repo_root.joinpath(*rel_str.split("/"))
    if not cand.exists():
        return f"broken link (missing from working tree): {raw_dest!r} -> {rel_str}"
    if cand.is_symlink():
        return f"symlink not allowed as link target (use real file path): {raw_dest!r} -> {rel_str}"
    return None


def validate_note_body_links(
    repo_root: Path,
    source_rel: str,
    body: str,
    tracked: frozenset[str],
) -> list[str]:
    """Return human-readable issue lines for one note body."""
    issues: list[str] = []
    lines = _iter_body_lines_outside_fences(body)
    ref_defs = _parse_ref_definitions(lines)

    for line_no, line in lines:
        spans = _inline_code_spans(line)

        for col, raw_dest in _parse_inline_link_dests(line, spans):
            err = _check_one_path(repo_root, source_rel, raw_dest, tracked)
            if err:
                issues.append(f"{source_rel}:{line_no}:{col}: {err}")

        for col, ref_key in _parse_ref_uses(line, spans):
            raw_dest = ref_defs.get(ref_key)
            if raw_dest is None:
                issues.append(
                    f"{source_rel}:{line_no}:{col}: undefined link reference [{ref_key}]"
                )
                continue
            err = _check_one_path(repo_root, source_rel, raw_dest, tracked)
            if err:
                issues.append(f"{source_rel}:{line_no}:{col}: {err}")

    return issues


def validate_in_scope_notes(
    repo_root: Path,
    rel_paths: list[str],
    tracked: frozenset[str] | None = None,
) -> list[str]:
    """
    Validate repo-root path links in note bodies for each path. Reads current working tree files.
    rel_paths should already be in-scope .md paths.
    """
    from vault_fm.errors import EncodingError
    from vault_fm.io import read_file_utf8

    if tracked is None:
        tracked = list_tracked_files_set(repo_root)

    all_issues: list[str] = []
    for rel in rel_paths:
        path = repo_root / rel
        try:
            text, _raw = read_file_utf8(path)
        except EncodingError as e:
            all_issues.append(f"{rel}: {e}")
            continue
        all_issues.extend(validate_note_body_links(repo_root, rel, text, tracked))
    return all_issues


def _rebuild_body_with_line_edits(body: str, modified: dict[int, str]) -> str:
    """Apply per-line replacements; line numbers are 1-based over all body lines (incl. fences)."""
    out: list[str] = []
    in_fence = False
    line_no = 0
    for line in body.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        line_no += 1
        m = re.match(r"^ {0,3}(`{3,}|~{3,})", content)
        if m:
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        if line_no in modified:
            nl = line[len(content) :]
            out.append(modified[line_no] + nl)
        else:
            out.append(line)
    return "".join(out)


def rewrite_note_body_links(
    source_rel: str,
    body: str,
    replace_dest: Callable[[str], str | None],
) -> str | None:
    """
    Walk the same structure as validate_note_body_links; replace destinations when
    replace_dest returns a new string. Returns new body if any change, else None.
    """
    lines_outside = _iter_body_lines_outside_fences(body)
    modified: dict[int, str] = {}

    for line_no, line in lines_outside:
        new_line = line
        spans = _inline_code_spans(line)
        replacements: list[tuple[int, int, str]] = []
        i = 0
        while True:
            j = new_line.find("](", i)
            if j == -1:
                break
            if _in_spans(j, spans) or _in_spans(j + 1, spans):
                i = j + 2
                continue
            parsed = _parse_link_dest_parens(new_line, j + 1)
            if parsed is None:
                i = j + 2
                continue
            raw_dest, close_idx = parsed
            dest_start = j + 2
            rep = replace_dest(raw_dest)
            if rep is not None and rep != raw_dest:
                replacements.append((dest_start, close_idx, rep))
            i = close_idx + 1

        for start, end, rep in sorted(replacements, key=lambda t: -t[0]):
            new_line = new_line[:start] + rep + new_line[end:]

        m = _REF_DEF_RE.match(new_line.rstrip())
        if m:
            dest = (m.group(2) or m.group(3) or "").strip()
            if dest:
                rep = replace_dest(dest)
                if rep is not None and rep != dest:
                    if m.group(2) is not None:
                        start = new_line.index("<", m.end(1))
                        gt = new_line.find(">", start + 1)
                        if gt != -1:
                            new_line = new_line[: start + 1] + rep + new_line[gt:]
                    else:
                        g3 = m.group(3)
                        if g3:
                            pos = new_line.find(g3, m.start(0))
                            if pos != -1:
                                new_line = new_line[:pos] + rep + new_line[pos + len(g3) :]

        if new_line != line:
            modified[line_no] = new_line

    if not modified:
        return None
    return _rebuild_body_with_line_edits(body, modified)
