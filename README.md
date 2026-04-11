# Memory vault

External storage for tech related things not always fitting in my head

## Vault tooling

Requires **Python 3.14+**

Priority #1: Let me know, if something is wrong before I commit 
Priority #2: If problem can by fixed automaticaly - fix it 

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

NOTE: markdown in root, scripts, and .cursor directory is excluded 

### fix.sh

* same as check, but fixing problems that can be fixed automaticaly

NOTE: markdown in root, scripts, and .cursor directory is excluded 