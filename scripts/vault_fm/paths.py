from __future__ import annotations

import os


def normalize_rel_path(path: str) -> str:
    """Forward slashes, no leading ./."""
    p = path.replace(os.sep, "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p


def is_in_scope(rel_path: str) -> bool:
    """
    Participating markdown: any .md under repo except top-level *.md, scripts/**, and .cursor/**.
    rel_path uses forward slashes relative to repo root.
    """
    p = normalize_rel_path(rel_path)
    if not p.endswith(".md"):
        return False
    if "/" not in p:
        return False
    if p.startswith("scripts/"):
        return False
    if p.startswith(".cursor/"):
        return False
    return True
