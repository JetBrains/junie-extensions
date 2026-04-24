# Migrations — Flyway & Liquibase policy + pitfalls

Both tools enforce immutability: once a version is applied in any environment, editing it breaks every other environment. New changes → new migration. Everything below is the policy and the traps that bite in production.

## Immutability rules (both tools)

- **Never edit an applied migration.** Flyway stores SHA256 in `flyway_schema_history.checksum`; Liquibase stores MD5 in `DATABASECHANGELOG.MD5SUM`. Editing fails validation on every subsequent deploy.
- **Never delete an applied migration file** — `MissingMigration` / `CHECKSUM MISMATCH` on startup.
- **Repair only as a last resort.** `flyway repair` / `UPDATE DATABASECHANGELOG SET MD5SUM = ...` are escape hatches for broken environments, not a workflow. Every use is a postmortem.
- **Fix-forward.** If `V5` has a bug, write `V6` that corrects it. Don't revert `V5`.

## Flyway naming & layout

- `V{version}__{description}.sql` — versioned, runs once, ordered.
- `R__{description}.sql` — repeatable, runs whenever checksum changes (views, stored procedures, functions).
- `U{version}__{description}.sql` — undo (Flyway Teams only); not available in OSS.
- Versions: `V1`, `V1_1`, `V1.1`, `V2024_01_15_1200` — all valid, but pick one style per project and stick with it. Timestamps scale better than integers in teams.

## Liquibase specifics

- Changelogs are YAML/XML/JSON with `changeSet id + author` as the unique key. `id` uniqueness is per-file, not global — two files can both have `id: 001`.
- `<rollback>` / `rollback:` block is required for non-trivial changes if you want `liquibase rollback` to work — automatic rollback only exists for DDL Liquibase itself generates.
- `runOnChange: true` → re-runs on checksum change (like Flyway `R__`). Use for views / stored procs.
- `contexts: prod,stage` — conditional execution. Abuse leads to environment-specific drift.

## Safe schema changes — the expand / contract pattern

Any change that a running application cannot tolerate must be split into phases. Applies to rolling deployments (most prod systems).

### Rename a column

```sql
-- Phase 1 (expand) — both names exist
ALTER TABLE users ADD COLUMN email_address VARCHAR(255);
UPDATE users SET email_address = email WHERE email_address IS NULL;
-- Trigger to keep both in sync while old code still writes `email`
CREATE TRIGGER sync_email ...
```

Deploy app reading/writing `email_address`. Remove reads of `email`. Then:

```sql
-- Phase 2 (contract)
DROP TRIGGER sync_email;
ALTER TABLE users DROP COLUMN email;
```

Never rename in place with active traffic — the old app sees a missing column.

### Add a NOT NULL column to a large table

```sql
-- ❌ locks the table, rewrites every row
ALTER TABLE orders ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending';
```

Postgres 11+ made `ADD COLUMN ... DEFAULT ... NOT NULL` fast (no rewrite), but only for non-volatile defaults. For user-provided / computed defaults:

```sql
-- ✅ Phase 1: nullable
ALTER TABLE orders ADD COLUMN status VARCHAR(20);

-- ✅ Phase 2: backfill in batches (application-side, or chunked UPDATE in a separate migration)
UPDATE orders SET status = 'pending' WHERE status IS NULL AND id BETWEEN 1 AND 10000;
-- ... repeat

-- ✅ Phase 3: add a CHECK constraint NOT VALID (no table scan), then validate without a full lock
ALTER TABLE orders ADD CONSTRAINT orders_status_not_null CHECK (status IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_status_not_null;   -- acquires ShareUpdateExclusiveLock, not AccessExclusiveLock
-- After VALIDATE, SET NOT NULL is a metadata-only operation (Postgres 12+: planner knows no nulls exist)
ALTER TABLE orders ALTER COLUMN status SET NOT NULL;
ALTER TABLE orders DROP CONSTRAINT orders_status_not_null;       -- cleanup; optional
```

### Drop a column

Phase 1 (deploy): stop reading / writing the column from application code.
Phase 2 (migration): `ALTER TABLE ... DROP COLUMN ...`. If you drop first, old instances during rolling deploy will crash.

### Add an index on a large table

```sql
-- Postgres
CREATE INDEX CONCURRENTLY idx_orders_status ON orders(status);  -- non-blocking; cannot run in a transaction
-- If it fails, the index is left in INVALID state — DROP it and retry

-- MySQL 8.0 (default is ONLINE for most algorithms)
CREATE INDEX idx_orders_status ON orders(status) ALGORITHM=INPLACE LOCK=NONE;

-- SQL Server
CREATE INDEX idx_orders_status ON orders(status) WITH (ONLINE = ON);
```

Flyway: mark the migration file `-- flyway.nonTransactional=true` header (or split `CREATE INDEX CONCURRENTLY` into its own migration; Flyway will run outside a transaction if configured).

### Rename / drop a table

Same expand-contract — route via a view first, let all consumers migrate, then drop.

## Baseline on an existing database

- Flyway: `flyway baseline -baselineVersion=1 -baselineDescription="existing schema"` creates a row in history and starts tracking from `V2+`.
- Liquibase: `liquibase changelog-sync` or `generate-changelog` to import existing schema.
- **Never** run unbaselined migrations against a populated DB — order will be wrong; objects already exist; errors cascade.

## Transaction behavior by dialect

- **Postgres**: DDL is transactional. A failed migration rolls back cleanly (except `CREATE INDEX CONCURRENTLY`, `VACUUM`, `ALTER TYPE ... ADD VALUE` — these can't be in a transaction).
- **MySQL / MariaDB**: DDL auto-commits. A migration with 5 DDLs that fails on #4 leaves the DB in a half-migrated state. Split each DDL into its own migration OR wrap with idempotency (`CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS` MySQL 8.0.29+).
- **SQLite**: DDL is transactional.
- **SQL Server**: DDL is transactional; some operations lock more than others.

## Idempotency defensive patterns

- `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS` — available on Postgres, MySQL 8.0.29+, SQLite 3.35+. Helpful for repairs and re-applies.
- For types/columns without `IF NOT EXISTS`, wrap in a `DO $$ ... EXCEPTION ... END $$` (Postgres) or a conditional in `information_schema`.
- Don't over-idempotent — Flyway/Liquibase already track state. Use idempotency only where DDL isn't transactional (MySQL).

## Data migrations (vs schema migrations)

- Put data backfills in separate migration files from DDL. Easier to retry, easier to batch.
- Chunk large `UPDATE`s (10K–100K rows per transaction) to avoid long locks and WAL blowup.
- For Postgres bulk updates, consider `UPDATE ... WHERE ctid = ANY(...)` with batched `ctid`s or a `LIMIT ... FOR UPDATE SKIP LOCKED` loop. A single `UPDATE table SET x = ...` on 100M rows will block writes for minutes.
- Don't put data migrations that take hours inside the app boot path — run via job, not Flyway on startup.

## Rollback realism

- Automatic rollback is rare outside Liquibase (which requires you to write `<rollback>`).
- Data loss is irreversible. `DROP COLUMN` rollback can restore the schema but not the data (unless you snapshot first).
- Prefer "add, don't remove" during the change; clean up in a later release once safe.

## Migration review checklist

- [ ] Migration filename follows project convention (version / timestamp).
- [ ] Already-applied migrations are not edited.
- [ ] Locking impact stated for any DDL on a table > 100K rows.
- [ ] CONCURRENTLY / ONLINE used for index creation on write-active tables.
- [ ] NOT NULL / NOT VALID split for constraints on large tables.
- [ ] Expand-contract phases explicit for renames / drops with live traffic.
- [ ] No secrets, no PII in the file.
- [ ] Idempotent where dialect requires (MySQL).
- [ ] Backfill data migrations separate from DDL migrations.
