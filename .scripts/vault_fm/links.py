from __future__ import annotations

import os
import re
from collections.abc import Callable, Iterable
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote

from mistune import BlockState, Markdown, create_markdown
from mistune.renderers.markdown import MarkdownRenderer
from mistune.util import escape_url, unikey

from vault_fm.gitutil import list_tracked_files
from vault_fm.paths import normalize_rel_path

# Reference-style link use: [text][ref] or ![alt][ref]; second bracket may be empty (shortcut).
_REF_USE_RE = re.compile(r"!?\[([^\]]*)\]\s*\[([^\]]*)\]")

_mistune_ast: Markdown = create_markdown(renderer=None)


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


def _parse_ast_and_state(body: str) -> tuple[list[dict[str, Any]], BlockState]:
    """Parse markdown to block-level AST and parser state (ref_links, etc.)."""
    return _mistune_ast.parse(body)


def _iter_all_tokens(tokens: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    stack = list(reversed(list(tokens)))
    while stack:
        t = stack.pop()
        yield t
        for c in reversed(t.get("children") or ()):
            stack.append(c)


_LINK_LIKE = frozenset({"link", "image"})


def _token_url_raw(token: dict[str, Any]) -> str | None:
    attrs = token.get("attrs")
    if not isinstance(attrs, dict):
        return None
    u = attrs.get("url")
    return u if isinstance(u, str) else None


def _apply_replace_dest_to_tokens(
    tokens: list[dict[str, Any]],
    state: BlockState,
    replace_dest: Callable[[str], str | None],
) -> bool:
    """Mutate link/image attrs and ref_links urls in place. Returns True if anything changed."""
    changed = False
    for tok in _iter_all_tokens(tokens):
        if tok.get("type") not in _LINK_LIKE:
            continue
        raw = _token_url_raw(tok)
        if raw is None:
            continue
        rep = replace_dest(raw)
        if rep is None:
            continue
        new_url = escape_url(rep)
        if new_url != raw:
            tok.setdefault("attrs", {})["url"] = new_url
            changed = True

    ref_links = state.env.get("ref_links")
    if isinstance(ref_links, dict):
        for _k, data in ref_links.items():
            if not isinstance(data, dict):
                continue
            raw = data.get("url")
            if not isinstance(raw, str):
                continue
            rep = replace_dest(raw)
            if rep is None:
                continue
            new_url = escape_url(rep)
            if new_url != raw:
                data["url"] = new_url
                changed = True
    return changed


def _undefined_reference_issues(
    source_rel: str, body: str, state: BlockState
) -> list[str]:
    """CommonMark leaves bad refs as text; report them using the same unikey rules as mistune."""
    defined = state.env.get("ref_links")
    if not isinstance(defined, dict):
        defined = {}
    issues: list[str] = []
    for line_no, line in _iter_body_lines_outside_fences(body):
        spans = _inline_code_spans(line)
        for m in _REF_USE_RE.finditer(line):
            if _in_spans(m.start(), spans) or _in_spans(m.end() - 1, spans):
                continue
            g1, g2 = m.group(1), m.group(2)
            ref_label = (g2.strip() if g2.strip() else g1.strip())
            if not ref_label:
                continue
            key = unikey(ref_label)
            if key in defined:
                continue
            col = m.start() + 1
            issues.append(
                f"{source_rel}:{line_no}:{col}: undefined link reference [{ref_label}]"
            )
    return issues


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
    ast, state = _parse_ast_and_state(body)
    issues.extend(_undefined_reference_issues(source_rel, body, state))

    for tok in _iter_all_tokens(ast):
        if tok.get("type") not in _LINK_LIKE:
            continue
        raw = _token_url_raw(tok)
        if raw is None:
            continue
        lineno = tok.get("lineno")
        col = tok.get("col") or 1
        line_no = int(lineno) if isinstance(lineno, int) else 1
        err = _check_one_path(repo_root, source_rel, raw, tracked)
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


def rewrite_note_body_links(
    source_rel: str,
    body: str,
    replace_dest: Callable[[str], str | None],
) -> str | None:
    """
    Parse with mistune, apply ``replace_dest`` to link/image and reference-definition URLs,
    then serialize with :class:`MarkdownRenderer`. Returns new body if any replacement, else None.
    """
    _ = source_rel
    ast, state = _parse_ast_and_state(body)
    if not _apply_replace_dest_to_tokens(ast, state, replace_dest):
        return None
    out = MarkdownRenderer()(ast, state)
    if out == body:
        return None
    return out
