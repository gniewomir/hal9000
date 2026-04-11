#!/usr/bin/env bash
set -euo pipefail
git add .
PYTHONPATH=scripts python3 -m vault_fm.health