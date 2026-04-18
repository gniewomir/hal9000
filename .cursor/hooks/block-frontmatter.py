#!/usr/bin/env python3
"""preToolUse: deny agent tools that add, change, or remove YAML frontmatter in vault *.md files."""

from __future__ import annotations

import json
import os
import sys


def extract_frontmatter(text: str) -> str | None:
    if not text:
        return None
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "".join(lines[: i + 1])
    return None


def resolve_path(path_str: str, payload: dict) -> str:
    if os.path.isabs(path_str):
        return os.path.normpath(path_str)
    roots = payload.get("workspace_roots") or []
    base = payload.get("cwd") or (roots[0] if roots else os.getcwd())
    return os.path.normpath(os.path.join(base, path_str))


def vault_directory_candidates(payload: dict) -> list[str]:
    """Absolute paths to each workspace's `vault/` directory."""
    roots = payload.get("workspace_roots") or []
    if not roots:
        base = payload.get("cwd")
        if isinstance(base, str) and base:
            roots = [base]
        else:
            roots = [os.getcwd()]
    out: list[str] = []
    for r in roots:
        if isinstance(r, str) and r:
            out.append(os.path.normpath(os.path.join(r, "vault")))
    return out


def is_under_vault(abs_path: str, payload: dict) -> bool:
    """True if abs_path is inside a workspace `vault/` tree (not sibling names like `vault-extra`)."""
    norm = os.path.normpath(abs_path)
    for vd in vault_directory_candidates(payload):
        if norm == vd:
            return True
        prefix = vd + os.sep
        if norm.startswith(prefix):
            return True
    return False


def read_file(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def tool_path(tool_input: object) -> str | None:
    if not isinstance(tool_input, dict):
        return None
    for key in ("path", "file_path", "target_file"):
        v = tool_input.get(key)
        if isinstance(v, str) and v:
            return v
    return None


def tool_contents(tool_input: object) -> str | None:
    if not isinstance(tool_input, dict):
        return None
    for key in ("contents", "content"):
        v = tool_input.get(key)
        if isinstance(v, str):
            return v
    return None


def deny(msg: str) -> None:
    out = {
        "permission": "deny",
        "user_message": msg,
        "agent_message": msg
        + " Edit the body only; leave the --- ... --- block unchanged.",
    }
    print(json.dumps(out), flush=True)


def allow() -> None:
    print(json.dumps({"permission": "allow"}), flush=True)


def check_md(path: str, before: str | None, after: str | None) -> bool:
    """Return True if the edit should be denied."""
    if not path.lower().endswith(".md"):
        return False
    fm_before = extract_frontmatter(before or "")
    fm_after = extract_frontmatter(after or "")
    if fm_before == fm_after:
        return False
    return True


def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        allow()
        return

    try:
        tool = payload.get("tool_name") or ""
        tool_input = payload.get("tool_input")

        if tool not in ("Write", "StrReplace"):
            allow()
            return

        path = tool_path(tool_input)
        if not path:
            allow()
            return

        abs_path = resolve_path(path, payload)

        if not is_under_vault(abs_path, payload):
            allow()
            return

        if tool == "Write":
            new_text = tool_contents(tool_input)
            if new_text is None:
                allow()
                return
            old_text = read_file(abs_path)
            if check_md(abs_path, old_text, new_text):
                deny("Blocked: this edit would add, change, or remove YAML frontmatter.")
                return
            allow()
            return

        # StrReplace
        if not isinstance(tool_input, dict):
            allow()
            return
        old_s = tool_input.get("old_string")
        new_s = tool_input.get("new_string")
        if not isinstance(old_s, str) or not isinstance(new_s, str):
            allow()
            return

        cur = read_file(abs_path)
        if cur is None:
            allow()
            return

        idx = cur.find(old_s)
        if idx < 0:
            allow()
            return

        updated = cur[:idx] + new_s + cur[idx + len(old_s) :]
        if check_md(abs_path, cur, updated):
            deny("Blocked: this edit would add, change, or remove YAML frontmatter.")
            return
        allow()
    except Exception:
        allow()


if __name__ == "__main__":
    main()
