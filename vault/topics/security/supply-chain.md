---
id: 019d7a35-4578-74e6-8299-c55033979a9e
references: []
---

min-release-age (from NPM v11.10.0)

```
npm config set save-exact=true
npm config set min-release-age=true
```

~/.npmrc
```
save-exact=true
min-release-age=14
```

# Insight 
* save exact version of deps to prevent automatic instalation of poisoned updates
* always give 14 days so potential supply chain attacks can be spotted 