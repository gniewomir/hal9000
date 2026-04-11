from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from vault_fm.errors import ParseError

_KEY_LINE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_]*)\s*:(.*)$")


def parse_uuid7_token(raw: str, ctx: str) -> uuid.UUID:
    s = raw.strip()
    if not s:
        raise ParseError(f"{ctx}: empty UUID")
    try:
        u = uuid.UUID(s)
    except ValueError as e:
        raise ParseError(f"{ctx}: invalid UUID: {raw!r}") from e
    if u.version != 7:
        raise ParseError(f"{ctx}: expected UUID7, got version {u.version}: {raw!r}")
    return u


def parse_scalar_fragment(s: str, ctx: str) -> tuple[str, int]:
    """Parse scalar at start of s; return (value, chars consumed)."""
    s = s.lstrip()
    if not s:
        raise ParseError(f"{ctx}: empty scalar")
    if s[0] == "'":
        i = 1
        out: list[str] = []
        while i < len(s):
            c = s[i]
            if c == "'":
                if i + 1 < len(s) and s[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                return "".join(out), i + 1
            out.append(c)
            i += 1
        raise ParseError(f"{ctx}: unterminated single-quoted string")
    if s[0] == '"':
        i = 1
        out = []
        while i < len(s):
            c = s[i]
            if c == "\\":
                if i + 1 >= len(s):
                    raise ParseError(f"{ctx}: bad escape in double-quoted string")
                n = s[i + 1]
                if n in '\\"':
                    out.append(n)
                    i += 2
                    continue
                if n == "n":
                    out.append("\n")
                    i += 2
                    continue
                if n == "t":
                    out.append("\t")
                    i += 2
                    continue
                raise ParseError(f"{ctx}: unsupported escape: {n!r}")
            if c == '"':
                return "".join(out), i + 1
            out.append(c)
            i += 1
        raise ParseError(f"{ctx}: unterminated double-quoted string")
    j = 0
    while j < len(s):
        if s[j] in " \t,]#\n\r":
            break
        j += 1
    if j == 0:
        raise ParseError(f"{ctx}: empty unquoted scalar")
    return s[:j], j


def split_flow_list_inner(inner: str, ctx: str) -> list[str]:
    inner = inner.strip()
    parts: list[str] = []
    i = 0
    while i < len(inner):
        while i < len(inner) and inner[i] in " \t\n\r,":
            i += 1
        if i >= len(inner):
            break
        val, end = parse_scalar_fragment(inner[i:], f"{ctx}[{i}]")
        parts.append(val)
        i += end
        while i < len(inner) and inner[i] in " \t\n\r":
            i += 1
        if i >= len(inner):
            break
        if inner[i] != ",":
            raise ParseError(f"{ctx}: expected ',' or end, got {inner[i:]!r}")
        i += 1
    return parts


def find_matching_bracket(s: str, open_pos: int) -> int:
    """s[open_pos] == '[' — return index of matching ] with quote awareness."""
    i = open_pos + 1
    depth = 1
    in_single = False
    in_double = False
    while i < len(s) and depth:
        c = s[i]
        if in_single:
            if c == "'":
                if i + 1 < len(s) and s[i + 1] == "'":
                    i += 2
                    continue
                in_single = False
            i += 1
            continue
        if in_double:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_double = False
            i += 1
            continue
        if c == "'":
            in_single = True
            i += 1
            continue
        if c == '"':
            in_double = True
            i += 1
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ParseError("unclosed '[' in flow list")


@dataclass
class ParsedFm:
    id_val: uuid.UUID | None
    refs_parsed: list[uuid.UUID]
    id_line_span: tuple[int, int] | None
    references_span: tuple[int, int] | None
    has_id_key: bool
    has_references_key: bool
    fm: str = field(repr=False)


def _char_offset(lines: list[str], line_idx: int) -> int:
    return sum(len(lines[j]) for j in range(line_idx))


def parse_fm_inner(fm: str) -> ParsedFm:
    """Parse inner front matter text (between --- delimiters)."""
    if fm and not fm.endswith("\n"):
        fm = fm + "\n"
    lines = fm.splitlines(keepends=True)
    id_val: uuid.UUID | None = None
    refs_parsed: list[uuid.UUID] = []
    id_line_span: tuple[int, int] | None = None
    references_span: tuple[int, int] | None = None
    id_seen = 0
    ref_seen = 0
    has_id_key = False
    has_references_key = False

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = _KEY_LINE.match(line.rstrip("\n"))
        if not m:
            i += 1
            continue
        key = m.group(1)
        rest = m.group(2)
        if key != key.lower() and key.lower() in ("id", "references"):
            raise ParseError(f"malformed key casing: {key!r} (use lowercase)")
        if key == "id":
            id_seen += 1
            if id_seen > 1:
                raise ParseError("duplicate id: key")
            start = _char_offset(lines, i)
            ls = rest.lstrip()
            val_s, consumed = parse_scalar_fragment(ls, "id")
            tail = ls[consumed:].strip()
            if tail and not tail.startswith("#"):
                raise ParseError(f"id line: trailing content: {tail!r}")
            id_val = parse_uuid7_token(val_s, "id")
            id_line_span = (start, start + len(line))
            has_id_key = True
            i += 1
            continue
        if key == "references":
            ref_seen += 1
            if ref_seen > 1:
                raise ParseError("duplicate references: key")
            start = _char_offset(lines, i)
            joined = "".join(lines[i:])
            rel_idx = joined.index("references:")
            tail = joined[rel_idx + len("references:") :]
            lstripped = tail.lstrip()
            offset_skip = len(tail) - len(lstripped)
            br = lstripped.find("[")
            if br >= 0:
                abs_open = rel_idx + len("references:") + offset_skip + br
                close_rel = find_matching_bracket(joined, abs_open)
                inner = joined[abs_open + 1 : close_rel]
                items_s = split_flow_list_inner(inner, "references flow")
                refs_parsed = [parse_uuid7_token(x, "references item") for x in items_s]
                tail_after = joined[close_rel + 1 :].lstrip()
                first_line = tail_after.split("\n", 1)[0] if tail_after else ""
                if first_line and not first_line.startswith("#"):
                    raise ParseError(
                        f"references flow: trailing garbage on first line: {first_line!r}"
                    )
                end_in_joined = close_rel + 1
                span_end = _char_offset(lines, i) + end_in_joined
                references_span = (start, span_end)
                has_references_key = True
                acc = 0
                for j in range(i, len(lines)):
                    acc += len(lines[j])
                    if acc >= end_in_joined:
                        i = j + 1
                        break
                else:
                    i = len(lines)
                continue
            # block form
            rest_stripped = rest.strip()
            if rest_stripped and not rest_stripped.startswith("#"):
                raise ParseError("references block: expected newline after references:")
            items_s: list[str] = []
            j = i + 1
            while j < len(lines):
                ln = lines[j]
                if not ln.strip():
                    j += 1
                    continue
                lead = len(ln) - len(ln.lstrip(" "))
                if lead == 0:
                    m2 = _KEY_LINE.match(ln.rstrip("\n"))
                    if m2:
                        break
                if lead < 2:
                    break
                st = ln.strip()
                if not st.startswith("- "):
                    raise ParseError(
                        f"references block: expected list item '- ', got {ln!r}"
                    )
                item_rest = st[2:]
                val, _ = parse_scalar_fragment(item_rest, "references block item")
                items_s.append(val)
                j += 1
            refs_parsed = [parse_uuid7_token(x, "references item") for x in items_s]
            end_line = j - 1 if j > i else i
            end_off = _char_offset(lines, end_line) + len(lines[end_line])
            references_span = (start, end_off)
            has_references_key = True
            i = j
            continue
        i += 1

    return ParsedFm(
        id_val=id_val,
        refs_parsed=refs_parsed,
        id_line_span=id_line_span,
        references_span=references_span,
        has_id_key=has_id_key,
        has_references_key=has_references_key,
        fm=fm,
    )


def format_references_block(refs: list[uuid.UUID]) -> str:
    if not refs:
        return "references: []\n"
    out = ["references:\n"]
    for r in refs:
        out.append(f"  - {r}\n")
    return "".join(out)


def rebuild_fm_canonical(fm: str, new_id: uuid.UUID, new_refs: list[uuid.UUID]) -> str:
    """
    Re-parse structure and emit canonical id + references lines; preserve other lines order.
    """
    if fm and not fm.endswith("\n"):
        fm = fm + "\n"
    lines = fm.splitlines(keepends=True)
    id_s = str(new_id)
    refs_block = format_references_block(new_refs)
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            out.append(line)
            i += 1
            continue
        m = _KEY_LINE.match(line.rstrip("\n"))
        if not m:
            out.append(line)
            i += 1
            continue
        key = m.group(1)
        rest = m.group(2)
        if key != key.lower() and key.lower() in ("id", "references"):
            raise ParseError(f"malformed key casing: {key!r}")
        if key == "id":
            out.append(f"id: {id_s}\n")
            i += 1
            continue
        if key == "references":
            joined = "".join(lines[i:])
            rel_idx = joined.index("references:")
            tail = joined[rel_idx + len("references:") :]
            lstripped = tail.lstrip()
            offset_skip = len(tail) - len(lstripped)
            br = lstripped.find("[")
            if br >= 0:
                abs_open = rel_idx + len("references:") + offset_skip + br
                close_rel = find_matching_bracket(joined, abs_open)
                end_in_joined = close_rel + 1
                acc = 0
                for j in range(i, len(lines)):
                    acc += len(lines[j])
                    if acc >= end_in_joined:
                        out.append(refs_block)
                        i = j + 1
                        break
                else:
                    out.append(refs_block)
                    i = len(lines)
                continue
            j = i + 1
            while j < len(lines):
                ln = lines[j]
                if not ln.strip():
                    j += 1
                    continue
                lead = len(ln) - len(ln.lstrip(" "))
                if lead == 0:
                    m2 = _KEY_LINE.match(ln.rstrip("\n"))
                    if m2:
                        break
                if lead < 2:
                    break
                if not ln.strip().startswith("- "):
                    break
                j += 1
            out.append(refs_block)
            i = j
            continue
        out.append(line)
        i += 1
    return "".join(out)


def insert_missing_keys(fm: str, new_id: uuid.UUID) -> str:
    """Prepend id and references if completely missing."""
    p = parse_fm_inner(fm)
    refs = format_references_block([])
    if not p.has_id_key and not p.has_references_key:
        return f"id: {new_id}\n{refs}" + fm
    if not p.has_id_key:
        return f"id: {new_id}\n" + fm
    if not p.has_references_key:
        return fm + refs
    return fm
