from __future__ import annotations

import re
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


def logical_target_rel(source_rel: str, path_part: str) -> str | None:
    """
    Normalize a link destination to a repo-relative path string (forward slashes),
    without touching the filesystem (strict casing preserved from the link + normalization).
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
    rel_str = logical_target_rel(source_rel, path_part)
    if rel_str is None:
        return f"invalid path: {raw_dest!r}"
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
    Validate relative links in note bodies for each path. Reads current working tree files.
    rel_paths should already be in-scope .md paths.
    """
    from vault_fm.errors import EncodingError, ParseError
    from vault_fm.io import read_file_utf8, split_front_matter

    if tracked is None:
        tracked = list_tracked_files_set(repo_root)

    all_issues: list[str] = []
    for rel in rel_paths:
        path = repo_root / rel
        try:
            text, raw = read_file_utf8(path)
            sp = split_front_matter(text, raw)
        except (EncodingError, ParseError) as e:
            all_issues.append(f"{rel}: {e}")
            continue
        if not sp.has_fm:
            body = text
        else:
            body = sp.body_bytes.decode("utf-8")
        all_issues.extend(validate_note_body_links(repo_root, rel, body, tracked))
    return all_issues
