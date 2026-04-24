# Database migrations — Flyway / Liquibase policy

Generic knowledge of Flyway / Liquibase is assumed (`V1__init.sql`, `changelog.xml`). This file is about safe schema evolution in production.

## Choose one, stick with it

- **Flyway** — SQL-first, linear versioning (`V{version}__{description}.sql`). Simpler, preferred for most Spring Boot projects.
- **Liquibase** — XML / YAML / JSON changelog with rollback support. Use when you need DB-agnostic abstractions or complex rollback requirements.
- Never mix both in the same app.

## Non-negotiable rules

- **Never edit a migration that has been applied.** Flyway's checksum validation will fail on next start; teams will develop clever workarounds that cause production drift. Create a new migration instead.
- **Migrations are forward-only in prod.** `flyway.clean` should never run against a real database (set `spring.flyway.clean-disabled=true` — this is the default since Flyway 9, but verify).
- One logical change per migration. `V12__add_user_email_and_reindex_orders.sql` is a lie by the time you need to debug it.
- Small migrations only. A 200-line DDL script in one file means a 200-line rollback PR when something fails.

## Safe-by-default patterns (zero / low-downtime)

- **Add a non-null column without default** — locks the table while every row is rewritten. On large tables: add nullable → backfill in batches → add `NOT NULL` constraint with `NOT VALID` → validate.
- **Drop a column** — don't. Step 1: stop writing to it in code. Step 2: release, verify. Step 3: drop in a later migration.
- **Rename a column** — expand-contract: add new column, dual-write, backfill, switch reads, stop writing to old, drop old. Across 3–4 releases.
- **Add an index on Postgres** — `CREATE INDEX CONCURRENTLY` (cannot run in a transaction; requires Flyway / Liquibase to run that statement outside its default transaction).
- **Split a table** — always via expand-contract, never a big-bang migration.

## Spring Boot + Flyway wiring

- Flyway runs **before** JPA bootstrap. This means Hibernate sees only the post-migration schema — set `spring.jpa.hibernate.ddl-auto=validate` to catch entity / schema drift at startup.
- Default location: `classpath:db/migration`. Naming: `V1__init.sql`, `V2__add_users.sql`. Underscore rules matter — `V1__` (two underscores before description).
- For multi-module apps or multi-tenant setups: `spring.flyway.schemas` + `spring.flyway.default-schema`.

## Baseline on an existing DB

If the database already has data before you introduce Flyway:

```properties
spring.flyway.baseline-on-migrate=true
spring.flyway.baseline-version=1
spring.flyway.baseline-description=baseline
```

Ship an empty `V1__baseline.sql` (or schema dump) matching that version, then new migrations from `V2` onward.

## Testing migrations

- `@DataJpaTest` + Testcontainers + `@ServiceConnection` → Flyway runs against a real DB each test class. Keeps `ddl-auto=validate` honest.
- Dry-run / plan only: Flyway `info` (before `migrate`) prints pending migrations and current state.
- Pre-prod smoke: `flyway migrate` against a snapshot of prod data to catch slow migrations (locks, rewrites).

## Common mistakes

- Editing an applied migration → `FlywayException: Validate failed: Migration checksum mismatch`. Fix: create a corrective migration, or (rare, last resort) `flyway repair` in non-prod.
- Putting `BEGIN; … COMMIT;` inside a Flyway SQL file → Flyway already runs each migration in a transaction; manual `BEGIN` breaks that and can leave partial state.
- `CREATE INDEX CONCURRENTLY` inside a transactional migration → Postgres rejects it. Put the statement in its own migration file and add `-- flyway.nonTransactional=true` as the first line to run it outside a transaction.
- Relying on `ddl-auto=update` "just this once" → divergence between dev and prod schemas, migrations stop matching reality.
- Running `flyway clean` in a shared environment → all data wiped. Always `clean-disabled=true` outside isolated local dev.
