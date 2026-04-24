# sql-engineer

Junie extension that turns the agent into a disciplined SQL engineer: enforces query correctness, safe schema changes, and indexing strategy — and catches the production traps that LLMs get wrong by default: `NOT IN` with NULLs, function-on-column destroying index usage, `OFFSET` degrading on large tables, `ALTER TABLE ADD NOT NULL` locking, `CREATE INDEX` blocking writes, editing applied migrations.

## Philosophy

Baseline SQL knowledge (CTE, window functions, joins, DML, Flyway/Liquibase syntax) is assumed — the extension does not re-teach query syntax. Instead it encodes:

- **Policy** — MUST / MUST NOT rules covering correctness, safety, and performance.
- **Pitfalls** — behaviors that work on small datasets and break in production (wrong NULL semantics, full-table locks, planner regressions).
- **Setup awareness** — detect dialect, migration tool, EXPLAIN access, and table sizes before giving index or migration advice.

## What it covers

- Query correctness: `NOT IN` / `NOT EXISTS` NULL trap, implicit type casts in joins, `DISTINCT` masking broken joins.
- Indexing: composite index column order, functional/expression indexes, `CONCURRENTLY` / `ONLINE` to avoid write locks.
- Migrations: immutability rule, expand-contract pattern for zero-downtime `RENAME` / `DROP` / `NOT NULL` changes, dialect transaction semantics (Postgres vs MySQL DDL).
- Performance: keyset pagination vs `OFFSET`, `EXPLAIN ANALYZE` workflow, `COUNT(*)` on large tables.

## Files

- `skills/sql-patterns/SKILL.md` — hub: Setup Check, MUST DO / MUST NOT, Reference Guide, Output Format.
- `skills/sql-patterns/references/migrations.md` — Flyway/Liquibase immutability, online schema change patterns.
- `skills/sql-patterns/references/performance.md` — EXPLAIN reading, indexing strategy, keyset pagination.

## MCP — DBHub

The extension ships with a DBHub MCP server (`mcp/.mcp.json`). When configured, it gives the agent direct read access to a live database — enabling `EXPLAIN ANALYZE` against real data, schema inspection, and row-count queries without leaving the conversation.

**Setup:** replace `DB_URL` in `mcp/.mcp.json` with your connection string (e.g. `postgres://user:pass@localhost:5432/mydb`).

## Requirements

- Any of: Postgres 12+, MySQL 8+, MariaDB, SQLite, SQL Server.
- Migration tool: Flyway (`db/migration/`) or Liquibase (`db/changelog/`).
- Optional: DBHub MCP configured for live EXPLAIN access.

## Installation

Drop the extension folder into your Junie extensions directory and enable it. Junie picks up `SKILL.md` automatically and loads references on demand.
