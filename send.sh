#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$ROOT/scripts"

git add .
python3 -m vault_fm.send
if command -v ruff >/dev/null 2>&1; then
  ruff format "$ROOT/scripts"
fi
git add .
git commit -m "update $(date '+%Y-%m-%d %H:%M')"
git push
