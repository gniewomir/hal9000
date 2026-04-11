# Memory vault

External storage for tech related things not always fitting in my head

## Intended UX

- one branch
- one command to update
- scripts in root are the intended UI - if work around them it it's a you problem
- no predefined structure - it should emerge organically
  - frictionless renaming, moving files & directories around to reflect how ideas are related to each other in my mind
  - any attached metadata & relations keept healthy and updated automaticaly 

## Vault tooling

Requires **Python 3.14+** or higher to be available

- Priority #0: Don't ask me things - do the right thing by default
- Priority #1: Let me know if something is wrong only if you cannot fix it
- Priority #2: No branching, html in md, githooks etc. by convention - KISS

### send.sh

- stages all changes, validates links, creates frontmatter if not present, stage, push
- adds identity to new files (frontmatter block with id)
- checks for broken relative links
- checks for duplicated ids in staged changes

### check.sh

- run the same validation checks as send.sh
- checks for broken relative links
- check for duplicated ids in all markdown
- checks for broken relative links in all markdown

NOTE: markdown in root, .scripts, and .cursor directory is excluded 

### fix.sh

- same as check, but fixing problems that can be fixed automaticaly

NOTE: markdown in root, .scripts, and .cursor directory is excluded 