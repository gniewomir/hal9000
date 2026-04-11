# Memory bank

External storage for tech related things not fitting in my head

## Vault tooling (stable ids / references)

Requires **Python 3.14+** (stdlib `uuid.uuid7`). From the repo root, with `PYTHONPATH=scripts` (see `./send.sh`):

- **Send (stage → normalize → commit):** stage the `.md` files you want, then run `./send.sh`. In-scope paths are all tracked `*.md` except top-level `*.md` and anything under `scripts/`.
- **Health check:** `PYTHONPATH=scripts python3 -m vault_fm.health` — add `--fix` to apply safe repairs (writes immediately). Non-zero exit if issues remain.

Details: [ideas/queue/hal9000/stable-identities-for-files-in-vault.md](ideas/queue/hal9000/stable-identities-for-files-in-vault.md), [ideas/queue/hal9000/minimal-python-setup.md](ideas/queue/hal9000/minimal-python-setup.md).
