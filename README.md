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

Requires **Python 3.14+** or higher to be available

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
