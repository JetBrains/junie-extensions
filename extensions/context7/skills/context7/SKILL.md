---
name: context7
description: Up-to-date library and framework documentation via Context7 MCP. Use when setup, API, or version-specific questions require current documentation.
---

# Context7

Provides up-to-date library and framework documentation. Use instead of relying on training data for library-specific questions.

## When to Use

- Setup or configuration questions for any library or framework
- API references (Spring Boot, Kotlin, React, etc.)
- Code involving specific libraries where version accuracy matters
- Any question where "latest docs" are more reliable than training data

## How to Use

**Step 1 — Identify the library**: call `resolve-library-id` with the library name and the user's question

**Step 2 — Choose the best match**: select based on name accuracy, `trustScore`, `totalSnippets`, and version if mentioned

**Step 3 — Retrieve docs**: call `get-library-docs` with the selected library ID and the user's specific `topic` (and optional `tokens` budget)

**Step 4 — Respond**: incorporate documentation findings with code examples and version citations

## Best Practices

- Be specific with queries — include the user's exact question, not just the library name
- Respect version preferences when the user specifies one
- Prefer official package sources over community alternatives when multiple matches exist
