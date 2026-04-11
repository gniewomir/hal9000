---
id: 019d7a35-4577-7313-aa19-627a50a79b54
references: []
---
# Front matter alternatives that render well in markdown

Standard YAML front matter (`---` blocks) is the most common metadata format for markdown files, but it renders as ugly raw text in plain markdown viewers.

## Alternatives

### Table at the top

```markdown
| Property | Value        |
|----------|--------------|
| tags     | node, async  |
| status   | draft        |

# My Document Title
```

Renders as a clean, readable table in any markdown viewer. Not natively parsed as metadata by most tools, but easy to write a custom parser for.

### `<details>` / `<summary>` (collapsible)

```markdown
<details>
<summary>Metadata</summary>

| Key    | Value       |
|--------|-------------|
| tags   | node, async |
| status | draft       |

</details>

# My Document Title
```

Renders as a collapsible section on GitHub and many other renderers.

### Blockquote

```markdown
> **tags:** node, async
> **status:** draft
> **created:** 2026-04-10

# My Document Title
```

Renders as a visually distinct quoted block. Easy to read, reasonably easy to parse programmatically.

### HTML comment

```markdown
<!--
tags: node, async
status: draft
-->

# My Document Title
```

Metadata is completely hidden in rendered output. Clean, but invisible in preview.

### Heading + bullet list

```markdown
# My Document Title

- **tags:** node, async
- **status:** draft

---
```

Renders cleanly everywhere. The `---` horizontal rule visually separates metadata from content.

## Comparison

| Approach          | Renders nicely     | Machine-parseable | Ecosystem tool support            |
|-------------------|--------------------|-------------------|-----------------------------------|
| YAML front matter | No                 | Yes               | Excellent (Hugo, Jekyll, Obsidian)|
| Table             | Yes                | Moderate          | Custom only                       |
| Blockquote        | Yes                | Moderate          | Custom only                       |
| `<details>`       | Yes (collapsible)  | Moderate          | GitHub, some renderers            |
| HTML comment      | Yes (hidden)       | Moderate          | Custom only                       |
| Bullet list       | Yes                | Moderate          | Custom only                       |

## YAML front matter wrapped in HTML comment

An interesting hybrid: keep YAML front matter but wrap it in an HTML comment so it's hidden when rendered, then strip the comment wrapper before processing with standard tooling.

```markdown
<!--
---
tags: node, async
status: draft
---
-->

# My Document Title
```

The transform is trivial — a regex strip of `<!--\n` and `\n-->` around the front matter block.

### What works

- **The transform itself** — dead simple, ~5 lines of code. Very low bug surface.
- **Nested HTML comments in content** — not a real issue since you only target the first block in the file.
- **Git diffs** — no impact, it's all plain text.
- **Markdown spec compliance** — HTML comments are valid markdown everywhere.

### Friction points

- **Every tool in the chain needs the preprocessing step** — not just the static site generator, but also linters, CI checks, metadata scripts, search/index tools. You're committing to maintaining a small "unwrap" utility as a permanent dependency.
- **Editor/IDE front matter support is lost** — editors detect `---` at byte 0 for YAML highlighting, validation, and autocompletion. Inside an HTML comment, it's all greyed out as comment text.
- **Ecosystem libraries won't work directly** — `gray-matter` (Node), `python-frontmatter`, Obsidian, GitHub's front matter rendering all expect `---` as the literal first bytes of the file.
- **Build pipeline complexity** — you either preprocess to a temp directory (doubling the file tree during builds) or modify in place and re-wrap (fragile).

### Verdict

The value proposition is front matter that renders cleanly in markdown viewers. But if files are primarily viewed in an editor, raw `---` blocks are invisible friction — your eyes skip them. The HTML comment wrapper adds real tooling friction for a cosmetic improvement that mostly matters when someone else browses the repo on GitHub.
