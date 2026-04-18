#!/usr/bin/env bash
# Resolve Python >= 3.14 for vault_fm (stdlib uuid.uuid7). Exports VAULT_FM_PYTHON.
# Source from repo root UI scripts after setting ROOT, or from .scripts/ (ROOT inferred).

if [[ -n "${ROOT:-}" ]]; then
  _vault_fm_root="$ROOT"
else
  _vault_fm_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

_venv_python="$_vault_fm_root/.scripts/.venv/bin/python"

_vault_fm_ok() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 14) else 1)' 2>/dev/null
}

if [[ -x "$_venv_python" ]] && _vault_fm_ok "$_venv_python"; then
  VAULT_FM_PYTHON="$_venv_python"
elif command -v python3.14 >/dev/null 2>&1 && _vault_fm_ok "$(command -v python3.14)"; then
  VAULT_FM_PYTHON="$(command -v python3.14)"
elif command -v python3 >/dev/null 2>&1 && _vault_fm_ok "$(command -v python3)"; then
  VAULT_FM_PYTHON="$(command -v python3)"
else
  ver="$(python3 -c 'import sys; print(".".join(str(x) for x in sys.version_info[:3]))' 2>/dev/null || echo unknown)"
  echo "vault_fm requires Python 3.14+ (stdlib uuid.uuid7). This interpreter is ${ver}." >&2
  echo "Install python3.14 or create .scripts/.venv (with pip), then: .scripts/.venv/bin/pip install -r .scripts/requirements.txt" >&2
  exit 2
fi

export VAULT_FM_PYTHON
