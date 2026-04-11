from __future__ import annotations

import uuid


def dedupe_preserve(items: list[uuid.UUID]) -> list[uuid.UUID]:
    seen: set[uuid.UUID] = set()
    out: list[uuid.UUID] = []
    for x in items:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def strip_self_refs(
    refs: list[uuid.UUID], note_id: uuid.UUID
) -> tuple[list[uuid.UUID], bool]:
    """Return refs without self; bool True if any removed."""
    out = [r for r in refs if r != note_id]
    return out, len(out) != len(refs)


def is_subsequence(shorter: list[uuid.UUID], longer: list[uuid.UUID]) -> bool:
    """Every element of shorter appears in longer in order."""
    it = 0
    for x in longer:
        if it < len(shorter) and x == shorter[it]:
            it += 1
    return it == len(shorter)
