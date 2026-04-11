# Memory vault

External storage for tech related things not always fitting in my head

## Vault tooling

Requires **Python 3.14+** or higher

* Priority #0: Don't ask me things - do the right thing by default
* Priority #1: Convention over configuration
* Priority #2: Let me know, if something is wrong before pushing
* Priority #3: No branching, html in md etc.
* Priority #4: If something can by done/fixed automaticaly - do it

### send.sh

* stages all changes, validates links, creates frontmatter if not present, stage, push
* adds identity to new files (frontmatter block with id)
* checks for broken relative links
* checks for duplicated ids in staged changes

### check.sh

* run the same validation checks as send.sh
* check for broken references in all markdown 
* check for duplicated ids in all markdown
* checks for broken relative links in all markdown 

NOTE: markdown in root, .scripts, and .cursor directory is excluded 

### fix.sh

* same as check, but fixing problems that can be fixed automaticaly

NOTE: markdown in root, .scripts, and .cursor directory is excluded 