from __future__ import annotations

import sys

from vault_fm.gitutil import git_repo_root
from vault_fm.rename_links import run_link_validation_with_rename_repair, validate_tracked_links


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    fix = "--fix" in argv
    try:
        root = git_repo_root()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2

    if fix:
        issues = run_link_validation_with_rename_repair(root)
    else:
        issues = validate_tracked_links(root)

    for line in issues:
        print(line)

    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
