# Memory vault

External storage for tech related things not always fitting in my head

## Intended UX

- one branch
- one command to update
- scripts in root are the intended UI - if work around them it it's a you problem
- no predefined vault structure - it should emerge organically
  - frictionless renaming, moving files & directories around to reflect how ideas are related to each other in my mind
  - relative links between notes stay consistent via validation and automatic repair after git-detected renames

## Vault tooling

Requires **Python 3.14+** or higher to be available.

### Python dependencies

Link validation and repair (`vault_fm`) use **[mistune](https://pypi.org/project/mistune/)** for parsing markdown. Install it into the environment you use for `send.sh` / `check.sh` / `fix.sh` (the repo prefers a local venv at `.scripts/.venv`):

```bash
# From the repository root (create the venv once if it does not exist)
python3.14 -m venv .scripts/.venv
.scripts/.venv/bin/pip install -r .scripts/requirements.txt
```

Pinned packages are listed in [`.scripts/requirements.txt`](.scripts/requirements.txt) ([`vault_fm/requirements.txt`](.scripts/vault_fm/requirements.txt) includes that file for compatibility).

**If `python3.14 -m venv .scripts/.venv` fails** with an error about `ensurepip` (common when the OS Python package does not ship `venv`/`ensurepip` support):

- On Debian/Ubuntu, install the matching venv package (name varies), e.g. `python3.14-venv`, then retry the commands above; **or**
- Create the venv without pip and install pip with [get-pip.py](https://bootstrap.pypa.io/get-pip.py):

```bash
python3.14 -m venv .scripts/.venv --without-pip
curl -sS https://bootstrap.pypa.io/get-pip.py | .scripts/.venv/bin/python
.scripts/.venv/bin/pip install -r .scripts/requirements.txt
```

- Priority #0: Don't ask me things - do the right thing by default
- Priority #1: Let me know if something is wrong only if you cannot fix it
- Priority #2: No branching, html in md, githooks etc. by convention - KISS

### send.sh

- stages all changes, validates relative links in tracked vault markdown (and applies rename-based link repair when needed), then commit and push

### check.sh

- validates relative links in all tracked in-scope markdown (same resolution rules as send)

### fix.sh

- same as check, plus automatic link repair for paths that match a cached git rename/copy (index vs HEAD)

NOTE: markdown in root, .scripts, and .cursor directory is excluded
