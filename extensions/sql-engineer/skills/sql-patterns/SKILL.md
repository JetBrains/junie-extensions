---
name: "sql-patterns"
description: "SQL and database migration best practices: Flyway/Liquibase, query optimization, indexing. Use when working with SQL queries or database migrations."
---

# SQL Patterns Skill

Write efficient SQL queries and maintainable database migrations.

## Scope and Notes

- Use this skill for raw SQL, indexing, and migration strategy.
- Verify query advice with `EXPLAIN`/actual plans on the target database; optimizer behavior differs across PostgreSQL, MySQL, Oracle, and others.
- For ORM-specific issues, prefer `jpa-patterns`.

## When to Use
- Writing SQL queries or migrations
- Reviewing database schema design
- Optimizing slow queries

---

## Flyway Migrations

```sql
-- V1__create_users_table.sql
CREATE TABLE users (
    id          BIGSERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

Naming convention: `V{version}__{description}.sql`

---

## Indexing

```sql
-- ✅ Index columns used in WHERE, JOIN, ORDER BY
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status_created ON orders(status, created_at DESC);

-- ✅ Partial index for common filtered queries (exception to the low-cardinality rule below —
-- partial indexes are efficient even on low-cardinality columns because they only index the
-- matching subset, e.g. the 5% of rows with status = 'PENDING')
CREATE INDEX idx_orders_pending ON orders(created_at)
WHERE status = 'PENDING';

-- ❌ Don't create full indexes on low-cardinality columns (boolean, status with few values)
CREATE INDEX idx_users_active ON users(is_active); -- bad if 90% are active
-- Consider a partial index instead if you only query one specific value
```

---

## Query Optimization

```sql
-- ✅ Often prefer EXISTS for correlated subqueries, but verify with EXPLAIN
SELECT * FROM orders o
WHERE EXISTS (SELECT 1 FROM users u WHERE u.id = o.user_id AND u.is_active = true);

-- ⚠️ IN with subquery can be slower on some databases/workloads
SELECT * FROM orders WHERE user_id IN (SELECT id FROM users WHERE is_active = true);

-- ✅ Good — avoid SELECT *
SELECT id, email, name FROM users WHERE id = $1;

-- ✅ Good — use LIMIT for pagination
SELECT id, name FROM products ORDER BY created_at DESC LIMIT 20 OFFSET 40;
```

---

## Safe Migrations

```sql
-- ✅ Good — add column with default (non-blocking in Postgres 11+)
ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}';

-- ✅ Good — create index concurrently (no table lock)
CREATE INDEX CONCURRENTLY idx_users_name ON users(name);

-- ❌ Bad — adding NOT NULL without default locks table
ALTER TABLE users ADD COLUMN phone VARCHAR(20) NOT NULL;
```

---

## Liquibase Migrations

Liquibase uses XML/YAML/JSON changelogs instead of plain SQL files. Each `changeSet` is tracked in `DATABASECHANGELOG` table.

```yaml
# db/changelog/db.changelog-master.yaml
databaseChangeLog:
  - include:
      file: db/changelog/changes/001-create-users-table.yaml
  - include:
      file: db/changelog/changes/002-add-users-phone.yaml
```

```yaml
# db/changelog/changes/001-create-users-table.yaml
databaseChangeLog:
  - changeSet:
      id: 001
      author: dev
      changes:
        - createTable:
            tableName: users
            columns:
              - column:
                  name: id
                  type: BIGINT
                  autoIncrement: true
                  constraints:
                    primaryKey: true
              - column:
                  name: email
                  type: VARCHAR(255)
                  constraints:
                    nullable: false
                    unique: true
              - column:
                  name: created_at
                  type: TIMESTAMP WITH TIME ZONE
                  defaultValueComputed: NOW()
                  constraints:
                    nullable: false
```

Point your framework's datasource config to `classpath:db/changelog/db.changelog-master.yaml`.

Key differences from Flyway:
- Changelogs are **immutable** — never edit an applied `changeSet`, add a new one instead.
- Supports rollback via `<rollback>` blocks (Flyway Pro only).
- Use `liquibase:rollback` or `liquibase:rollbackCount` for controlled rollbacks.
