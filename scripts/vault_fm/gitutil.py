from __future__ import annotations

import subprocess
from pathlib import Path

from vault_fm.paths import is_in_scope, normalize_rel_path


def git_repo_root(cwd: Path | None = None) -> Path:
    cp = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd or Path("."),
        capture_output=True,
        text=True,
    )
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr or "not a git repository")
    return Path(cp.stdout.strip())


def list_staged_all_md(repo_root: Path) -> list[str]:
    """All staged *.md paths (not filtered by vault scope)."""
    cp = _run_git(repo_root, "diff", "--cached", "--name-only", "-z", "--", "*.md")
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.decode(errors="replace"))
    out: list[str] = []
    for raw in cp.stdout.split(b"\0"):
        if not raw:
            continue
        out.append(normalize_rel_path(raw.decode("utf-8")))
    out.sort()
    return out


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
    )


def list_tracked_md(repo_root: Path) -> list[str]:
    """git ls-files '*.md', filtered by vault scope."""
    cp = _run_git(repo_root, "ls-files", "-z", "--", "*.md")
    if cp.returncode != 0:
        raise RuntimeError(
            f"git ls-files failed: {cp.stderr.decode(errors='replace')!r}"
        )
    out: list[str] = []
    for raw in cp.stdout.split(b"\0"):
        if not raw:
            continue
        rel = normalize_rel_path(raw.decode("utf-8"))
        if is_in_scope(rel):
            out.append(rel)
    out.sort()
    return out


def list_staged_md(repo_root: Path) -> list[str]:
    """git diff --cached --name-only for *.md, filtered by vault scope."""
    cp = _run_git(repo_root, "diff", "--cached", "--name-only", "-z", "--", "*.md")
    if cp.returncode != 0:
        raise RuntimeError(
            f"git diff --cached failed: {cp.stderr.decode(errors='replace')!r}"
        )
    out: list[str] = []
    for raw in cp.stdout.split(b"\0"):
        if not raw:
            continue
        rel = normalize_rel_path(raw.decode("utf-8"))
        if is_in_scope(rel):
            out.append(rel)
    out.sort()
    return out


def git_show_index_text(repo_root: Path, rel_path: str) -> str | None:
    """
    Return text blob for path at stage 0, or None if missing / not in index.
    """
    rel = normalize_rel_path(rel_path)
    cp = _run_git(repo_root, "show", f":{rel}")
    if cp.returncode != 0:
        return None
    return cp.stdout.decode("utf-8")


def git_add(repo_root: Path, paths: list[str]) -> None:
    if not paths:
        return
    rels = [normalize_rel_path(p) for p in paths]
    cp = subprocess.run(
        ["git", "-C", str(repo_root), "add", "--", *rels],
        capture_output=True,
    )
    if cp.returncode != 0:
        err = cp.stderr.decode(errors="replace")
        raise RuntimeError(f"git add failed: {err}")
