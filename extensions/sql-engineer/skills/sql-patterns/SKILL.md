---
name: "sql-patterns"
description: "SQL policy & pitfalls — query correctness, indexing strategy, safe migrations. Use when writing SQL, diagnosing slow queries, designing schemas, or reviewing Flyway/Liquibase migrations. Covers the traps LLMs miss by default: NOT IN with NULLs, function-on-column breaking indexes, OFFSET on large tables, NOT NULL column lock, CREATE INDEX blocking writes, immutable migrations."
---

# SQL — policy & pitfalls

Baseline SQL knowledge (CTE, window functions, joins, DML, Flyway/Liquibase syntax) is assumed. This skill encodes policy and the traps that keep appearing in review — dialect-specific, blocking-behavior-specific, and optimizer-specific.

## Setup Check (run first)

Before writing non-trivial SQL:

1. **Dialect** — identify the target (Postgres, MySQL, MariaDB, SQLite, SQL Server). Optimizer behavior, locking rules, and index features differ. Never assume Postgres semantics on MySQL or vice versa.
2. **Migration tool** — check `db/migration/` (Flyway) or `db/changelog/` (Liquibase). Both are immutable: already-applied migrations must NEVER be edited.
3. **EXPLAIN access** — if the DBHub MCP is configured, use it to run `EXPLAIN (ANALYZE, BUFFERS)` (Postgres) or `EXPLAIN FORMAT=JSON` (MySQL) against a representative dataset. Advice without a real query plan is a guess.
4. **Table sizes** — query advice differs by orders of magnitude between 10K and 100M rows. Use DBHub (or `pg_stat_user_tables` / `information_schema.tables`) to check sizes when choosing pagination, indexing, and migration strategy.

## DBHub MCP

When the DBHub MCP server is available (configured in `mcp/.mcp.json`), use it actively:

- **Schema inspection** — list tables, columns, types, and indexes before writing queries or migrations.
- **`EXPLAIN ANALYZE`** — run against real data to verify index usage and row estimates before declaring a query optimized.
- **Row counts / size estimates** — query `pg_stat_user_tables` (Postgres) or `information_schema.tables` (MySQL) to determine pagination and migration strategy.
- **Validate migrations** — check current schema state before generating DDL to avoid duplicate columns or conflicting constraints.

Do not suggest schema changes or index additions without first confirming the current schema via DBHub or the codebase.

## MUST DO

- **List columns explicitly** — never `SELECT *` in application code (breaks on schema change, pulls unused columns).
- **`NOT EXISTS` / `LEFT JOIN ... IS NULL`** instead of `NOT IN` when the subquery can return `NULL` (NOT IN with a single NULL returns zero rows — silently).
- **Keyset pagination** (`WHERE id > :last ORDER BY id LIMIT n`) for large / user-driven lists. OFFSET degrades as it grows.
- **Parameterize every query** — prepared statements / bound parameters. Never string-concat user input even with escaping.
- **Index what you filter and join on** — `WHERE`, `JOIN ON`, `ORDER BY` columns. Composite index order matters: leftmost columns usable, tail columns only with leading predicates.
- **Transaction-scope migrations where possible** — Flyway wraps single migration in a transaction by default; Postgres supports DDL in transactions, MySQL does NOT (each DDL auto-commits, a failed migration leaves partial state).
- **`EXPLAIN ANALYZE`** before declaring a query "optimized" — optimizer choice depends on stats, table size, and dialect.

## MUST NOT DO

- **No `NOT IN (SELECT ... )` on nullable columns.** `WHERE x NOT IN (NULL, 1, 2)` returns empty. Use `NOT EXISTS` or `LEFT JOIN ... IS NULL`.
- **No functions on indexed columns in `WHERE`.** `WHERE YEAR(created_at) = 2024` ignores the index — use `WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'`. Or create a functional / expression index.
- **No `OR` across different columns in `WHERE`** when one side isn't indexed — split into `UNION ALL` (or create a combined index).
- **No `ALTER TABLE ... ADD COLUMN NOT NULL` without default** on a large table — locks the table, rewrites every row. Split into: add nullable column → backfill in batches → add NOT NULL constraint.
- **No `CREATE INDEX`** on a large write-active table without `CONCURRENTLY` (Postgres) / `ONLINE` (MySQL 5.6+, default in 8.0) / `WITH (ONLINE = ON)` (SQL Server) — blocks writes for the duration.
- **No editing applied migrations.** Flyway checksums them; Liquibase hashes them. Changing a released `V3__add_email.sql` breaks every environment. Add a new migration.
- **No `SELECT COUNT(*)` on large tables** for pagination UIs — it's a full scan on Postgres (MVCC can't use index). Use approximate counts (`pg_class.reltuples`) or "more results" cursor.
- **No `DISTINCT` to fix duplicate rows** — it masks a broken JOIN. Fix the join.
- **No implicit type casts in joins** (`JOIN x ON x.id = y.id_str`) — disables indexes, silently wrong if types differ. Match types.
- **No credentials, PII, or secrets in migration files** — they go to version control forever.

## Reference Guide

| Load when | File |
|---|---|
| Writing / reviewing Flyway / Liquibase migrations; running online schema changes | `references/migrations.md` |
| Diagnosing a slow query; choosing indexes; reading EXPLAIN output | `references/performance.md` |

## Output Format

When producing SQL:

1. Short plan (1–3 bullets) — what the query / migration does and which tables / indexes it touches.
2. The SQL, dialect-qualified when dialect-specific (`-- Postgres only`).
3. If modifying schema on a large table, describe the locking / backfill plan (not just the DDL).
4. For non-trivial queries — include the expected plan shape (index scan vs seq scan) and the index it relies on. If no such index exists, flag that as part of the change.

When reviewing SQL: call out MUST-DO / MUST-NOT violations, point out NULL / type / locking traps, and suggest the minimal fix. Prefer `EXPLAIN`-verified advice over cargo-cult rules.
