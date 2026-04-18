#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

# shellcheck source=.scripts/ensure_python.sh
. "$ROOT/.scripts/ensure_python.sh"

git pull --ff-only

git add .
PYTHONPATH="$ROOT/.scripts" "$VAULT_FM_PYTHON" -m vault_fm.send
if command -v ruff >/dev/null 2>&1; then
  ruff format "$ROOT/.scripts"
fi
git add .
git commit -m "update $(date '+%Y-%m-%d %H:%M')"
git push
