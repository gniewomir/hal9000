#!/usr/bin/env bash
# Require python3 on PATH and interpreter >= 3.14 (stdlib uuid.uuid7).
# Source from repo root UI scripts after setting ROOT.

if ! command -v python3 >/dev/null 2>&1; then
  echo "vault_fm: python3 not found in PATH" >&2
  exit 2
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 14) else 1)' 2>/dev/null; then
  ver="$(python3 -c 'import sys; print(".".join(str(x) for x in sys.version_info[:3]))' 2>/dev/null || echo unknown)"
  echo "vault_fm requires Python 3.14+ (stdlib uuid.uuid7). This interpreter is ${ver}." >&2
  exit 2
fi
