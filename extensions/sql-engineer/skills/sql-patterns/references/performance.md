# Query performance — diagnosis, indexing, optimizer traps

Everything here assumes you can run `EXPLAIN` on the target DB with a representative dataset. Advice without a plan is a guess.

## Read the plan, don't guess

- **Postgres**: `EXPLAIN (ANALYZE, BUFFERS, VERBOSE) <query>`. `ANALYZE` actually executes; guard with a transaction + rollback for destructive queries.
- **MySQL**: `EXPLAIN FORMAT=JSON <query>`, or `EXPLAIN ANALYZE` (MySQL 8.0.18+).
- **SQL Server**: `SET STATISTICS IO ON; SET STATISTICS TIME ON;` + "Include Actual Execution Plan".
- **SQLite**: `EXPLAIN QUERY PLAN <query>`.

Look for:
- `Seq Scan` / `Table Scan` on a large table filtered by an indexable predicate → missing or unusable index.
- `Rows Removed by Filter` high → index exists but isn't selective enough; composite index may help.
- Nested loop with large outer → hash join would be better; check stats (`ANALYZE` in Postgres, `ANALYZE TABLE` in MySQL).
- Sort spilling to disk (`Sort Method: external merge`) → increase `work_mem` temporarily, or add an index that matches the ORDER BY.
- `Index Scan` reading many rows → filtering happens after the index, consider covering / composite index.

## When indexes don't help

- **Function on column**: `WHERE LOWER(email) = ?` → can't use `idx(email)`. Fix: functional index `CREATE INDEX ON users (LOWER(email))`, or store lowercased column.
- **Implicit type cast**: `WHERE id = '123'` when `id` is INT (MySQL tolerates; Postgres warns). Disables the index. Match types.
- **Leading wildcard LIKE**: `LIKE '%foo'` → no B-tree usage. Use trigram / full-text index (Postgres: `pg_trgm`; MySQL: `FULLTEXT`).
- **OR across columns**: `WHERE a = 1 OR b = 2` can't use indexes on both. Use `UNION ALL` of two equality lookups — **but** if a row can satisfy both predicates you'll get duplicates; either ensure predicates are mutually exclusive (e.g. add `AND NOT (a = 1)` to the second branch), or use `UNION` (which dedups but costs a sort/hash).
- **Negation**: `WHERE status != 'done'` → usually seq-scan unless `status` has few values and the DB uses a bitmap scan.
- **Low selectivity**: index on `is_active` when 95% of rows are active → planner ignores the index. Use a **partial index** keyed on the minority case: `CREATE INDEX idx ON orders(created_at) WHERE status = 'PENDING'`.
- **Correlated subquery with `IN` vs `EXISTS`**: usually the same on modern optimizers, but `EXISTS` is safer for nullable columns (see MUST NOT).

## Composite index rules

- Leftmost prefix rule: `idx(a, b, c)` serves `WHERE a = ?`, `WHERE a = ? AND b = ?`, `WHERE a = ? AND b = ? AND c = ?`. NOT `WHERE b = ?`.
- Equality before range: index `(status, created_at)` for `WHERE status = ? AND created_at > ?`.
- Include `ORDER BY` columns at the tail to let the index satisfy ordering (`Index Scan` without a sort).
- **Covering index** (Postgres 11+ `INCLUDE`, MySQL secondary indexes with extra columns): `CREATE INDEX idx ON orders(user_id) INCLUDE (status, total)` — avoids heap lookup for the selected columns.
- Don't add an index "just in case". Every index slows writes and consumes buffer cache.

## Pagination

- **Keyset (cursor) pagination** — O(log n), stays fast forever:
  ```sql
  SELECT id, name FROM products
  WHERE id > :last_id
  ORDER BY id
  LIMIT 20;
  ```
  Requires a stable sort key. For composite sorts: `WHERE (created_at, id) > (:last_ts, :last_id)`.
- **OFFSET pagination** — O(n + offset), degrades linearly. Fine for admin UI with small offsets; lethal for `LIMIT 20 OFFSET 100000`.
- **`COUNT(*)`** for total on huge tables: use estimates.
  - Postgres: `SELECT reltuples::bigint FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = ? AND n.nspname = 'public'` (stats-based, stale by default; filter by schema to avoid ambiguity when the same table name exists in multiple schemas).
  - MySQL: `information_schema.TABLES.TABLE_ROWS` (InnoDB estimate).

## Joins

- Prefer explicit `INNER JOIN` / `LEFT JOIN`. Comma joins (`FROM a, b WHERE ...`) work but obscure intent and are error-prone.
- **Driver / outer table should be the smaller one** for nested loop joins. Hash joins don't care. Optimizer usually gets this right when stats are current.
- `LEFT JOIN` + `WHERE right_table.col = ?` accidentally turns it into `INNER JOIN` (because NULL can't equal). Put the predicate in the `ON` clause to preserve the outer join.
- Too many joins (5+) → consider materialized views, pre-aggregation, or denormalization.
- **`DISTINCT` after a JOIN** is almost always a bug — it means the join produced duplicates. Fix the join (aggregate, or join on a unique side).

## N+1 and batching

- Application-level N+1 is the #1 performance killer. Signs: many identical queries differing only in parameter.
- Fix from the app side (prefetch / join fetch / data loader), not SQL — but SQL can help with `WHERE id = ANY(:ids)` / `WHERE (a, b) IN ((..,..), (..,..))`.
- Beware of chunking: `WHERE id IN (1..100000)` creates a 100K-element `IN` list, some DBs choke. Cap at a few thousand per batch.

## Updates & deletes

- Large `UPDATE` / `DELETE` hold row locks and inflate WAL / redo log. Batch via `LIMIT` (MySQL) or `ctid`/`RETURNING`-loops (Postgres).
- `UPDATE orders SET status = 'done' WHERE id IN (SELECT id FROM orders WHERE ... LIMIT 1000 FOR UPDATE SKIP LOCKED)` — the canonical Postgres chunked update pattern.
- `DELETE` on a huge range → consider partitioning the table so old data drops via `DROP TABLE partition` in O(1).

## Stats & autovacuum

- Optimizer uses stats; stale stats → bad plans. After bulk load: `ANALYZE <table>` (Postgres), `ANALYZE TABLE <t>` (MySQL).
- Postgres: autovacuum handles most cases; tune `autovacuum_vacuum_scale_factor` for large append-only tables (default 0.2 × table-size is too lazy).
- Bloat (dead tuples) is a Postgres concern — monitor with `pgstattuple` or `pg_stat_user_tables`. Heavy `UPDATE`/`DELETE` workloads need tighter autovacuum.

## Useful Postgres diagnostics

- `pg_stat_statements` — query normalization + counts + total time. Enable it; it's the single most useful extension.
- `pg_stat_activity` — current queries; filter by `state = 'active' AND now() - query_start > '1 min'::interval` for long-runners.
- `pg_locks` + `pg_stat_activity` — find blockers.
- `EXPLAIN (ANALYZE, BUFFERS)` — `BUFFERS` shows cache hits; a plan with millions of buffer reads is I/O-bound.

## Useful MySQL diagnostics

- `performance_schema.events_statements_summary_by_digest` — normalized query stats (`sum_timer_wait`, `sum_rows_examined`).
- `SHOW ENGINE INNODB STATUS` — deadlocks, current transactions, lock waits.
- `SELECT * FROM sys.schema_unused_indexes` — indexes eating writes for no reads.

## Don't optimize prematurely

- Measure first. "This might be slow" is a hypothesis, not evidence.
- `EXPLAIN` and table sizes beat intuition. A seq scan on 500 rows is fine.
- Optimizations that don't survive review: "add hint", "force index", "change to subquery I think is faster". Benchmark before and after.

## Review checklist

- [ ] Plan attached (at least the relevant lines of EXPLAIN).
- [ ] Index the query relies on exists AND is used in the plan.
- [ ] No `SELECT *` outside ad-hoc queries.
- [ ] No function on indexed column in predicates.
- [ ] OFFSET replaced by keyset for user-facing lists over ~10K rows.
- [ ] `COUNT(*)` replaced by approximation / cursor where feasible.
- [ ] Joins don't produce duplicates (no `DISTINCT` band-aid).
- [ ] Bulk UPDATE/DELETE batched.
- [ ] New index justified by a query plan, not "feels right".
