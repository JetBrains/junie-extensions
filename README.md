# Junie Extensions

Curated extensions for [Junie](https://www.jetbrains.com/junie/) — the AI coding agent by JetBrains.

Extensions give Junie domain expertise: best practices, code patterns, anti-patterns, and checklists for specific technologies. Each extension can include skills (knowledge files), agents, guidelines, and MCP servers (tools).

> [!IMPORTANT]
> **Make sure you trust an extension before installing, updating, or using it.** JetBrains does not control what MCP servers, files, or other software are included in extensions and cannot verify that they will work as intended or that they won't change. Always review the extension's contents and source code before use.

## Structure

Each extension lives in `extensions/<name>/` and may contain:

```
extensions/<name>/
  extension.json          # name + description
  skills/<skill-name>/
    SKILL.md              # main skill file
    references/           # optional detailed references loaded on-demand
  agents/                 # optional custom agent definitions
  guidelines/             # optional project-level guidelines and conventions
  mcp/
    .mcp.json             # optional MCP server definitions
```

**`skills/`** — knowledge files that give Junie domain expertise. Each skill has a main `SKILL.md` and optional `references/` loaded on-demand.

**`agents/`** — custom agent definitions for specialized workflows within the extension's domain.

**`guidelines/`** — project-level conventions, coding standards, and decision records that Junie should follow when working on the project.

**`mcp/`** — MCP server definitions that provide additional tools (databases, APIs, etc.) for the extension.

### Skill Format

```markdown
---
name: "skill-name"
description: "One-line description."
---

# Title

## Reference Guide         ← hub-and-spoke: table pointing to references/
## Key Patterns            ← quick-start code examples
## Constraints             ← MUST DO / MUST NOT DO
```

Reference files are loaded on-demand based on context — only the relevant ones are read for each task.
