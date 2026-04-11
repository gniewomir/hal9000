---
id: 019d7c07-e66c-725b-a646-9b334d480d18
references: []
---

# Idea 

Memory files can have relations established by frontmatter and ids and/or file structure 

After implementing [automated reference reference updates](./automaticaly-update-references-based-on-relative-links-hal9000.md) which translates relations established by LLM to id's without friction i want to avoid. 

Natural followup would be to establish relations between conepts based on their location, 

For example, all files in `topics/machine-learning/vectorization/*.md` are related to each other to, higher level concept `topics/machine-learning` and to lower level concepts `topics/machine-learning/vectorization/databases/*.md`

While my first intuition was to store this relations in frontmatter this does not make sense. 

I do not need to make those relations explicit in metadata - as they are implied by file structure. 

I do not need to express them imiddietly and then put effort in keeping them up to date. I can establish them when ingesting content of the vault based on current, most up to date structure. 

But, this lead to assumption that while memory files have their stable identity, directories which represent higher level ideas have not. 