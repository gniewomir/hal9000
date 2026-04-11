from __future__ import annotations

import sys


MIN_PYTHON = (3, 14)


def require_python() -> None:
    if sys.version_info < MIN_PYTHON:
        ver = ".".join(str(x) for x in sys.version_info[:3])
        need = ".".join(str(x) for x in MIN_PYTHON)
        print(
            f"vault_fm requires Python {need}+ (stdlib uuid.uuid7). "
            f"This interpreter is {ver}.",
            file=sys.stderr,
        )
        sys.exit(2)
