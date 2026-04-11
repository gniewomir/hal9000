---
id: 019d7a98-d8aa-7577-a14e-9b69719b96d7
references: []
---

## Problem

The vault tooling required **Python 3.14+** (for `uuid.uuid7` in the stdlib). The version gate lived in Python (`vault_fm.version` / `require_python()`), and `send` / `health` called it at CLI startup. That mixed **policy** (which interpreter is allowed) with **application** code, imported `vault_fm` before the user-facing shell layer could fail fast, and sat awkwardly beside the rule that **root shell scripts** are the supported entry point.

## Reasoning

- **Root scripts** (`send.sh`, `check.sh`, `fix.sh`) are the intended UI; anything that runs `python3 -m vault_fm…` directly is explicitly “on you” per the repository README at the repo root.
- Failing **before** `PYTHONPATH` and `python3 -m …` avoids importing package code when the interpreter is wrong.
- One **shared shell helper** under `.scripts/` keeps the minimum version and error message in a single place; root scripts only `source` it and pass through exit code **2** on failure.
- The rule stays **minimum 3.14, higher versions OK** (`sys.version_info >= (3, 14)` in the check snippet).

## Solution

- Added `.scripts/ensure_python.sh`: verify `python3` on `PATH`, then enforce **≥ 3.14**; on failure print a short message (incl. `uuid.uuid7`) and **`exit 2`**.
- Updated `send.sh`, `check.sh`, and `fix.sh` at the repo root to resolve repo `ROOT`, `source` that helper, then run `vault_fm` with `PYTHONPATH="$ROOT/.scripts"`.
- Removed `.scripts/vault_fm/version.py` and dropped `require_python()` from `.scripts/vault_fm/send.py` and `.scripts/vault_fm/health.py`.
