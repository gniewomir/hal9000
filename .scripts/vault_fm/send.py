from __future__ import annotations

import sys

from vault_fm.gitutil import git_repo_root, list_staged_all_md
from vault_fm.paths import is_in_scope
from vault_fm.rename_links import run_link_validation_with_rename_repair


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    _ = argv
    try:
        root = git_repo_root()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2

    try:
        staged_all = list_staged_all_md(root)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2

    in_scope = [p for p in staged_all if is_in_scope(p)]
    if not in_scope:
        print(
            "vault_fm send: warning: no chages are in scope for validation & update",
            file=sys.stderr,
        )
        return 0

    link_issues = run_link_validation_with_rename_repair(root)
    if link_issues:
        for line in link_issues:
            print(line, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
