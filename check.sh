#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

PATH="$PWD/.scripts/.venv/bin:$PATH"

# shellcheck source=.scripts/ensure_python.sh
. "$ROOT/.scripts/ensure_python.sh"

git add .
PYTHONPATH="$ROOT/.scripts" python3 -m vault_fm.health