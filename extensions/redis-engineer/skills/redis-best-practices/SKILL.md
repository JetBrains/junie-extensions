---
name: "redis-best-practices"
description: "Redis policy & pitfalls — key naming, atomicity, TTL strategy, distributed locks, cache patterns, production traps. Use when designing Redis-backed caches, locks, queues, rate limiters, or sessions. Covers the traps LLMs get wrong by default: SETNX + EX (deprecated), KEYS on production, Pub/Sub no-persistence, HGETALL on big hashes, maxmemory-policy defaults, cluster hash tags, RDB fork memory."
---

# Redis — policy & pitfalls

Baseline Redis knowledge (strings, hashes, lists, sets, sorted sets, streams, pub/sub, TTL, MULTI/EXEC, basic replication) is assumed. This skill encodes the operational policy and the traps that keep showing up in production — the parts LLMs miss by default.

## Setup Check (run first)

Before writing non-trivial Redis code:

1. **Connection & topology** — standalone, replicated (Sentinel), or Cluster? Cluster changes multi-key commands rules (hash tags required). Check `INFO replication` and `CLUSTER INFO` if unsure.
2. **Redis version** — many "modern" patterns require 6.2+ (`SET ... EX ... NX ... KEEPTTL`, `COPY`, `GETEX`); streams / ACLs require 5.0+; functions require 7.0+. `INFO server | redis_version`.
   > **Redis 8 note**: Redis 8 unified Redis Community with Redis Stack — JSON, Search, TimeSeries, Bloom filters are now built-in, not add-ons. If running Redis 8+, these data types are available by default. All patterns in this skill apply equally to Redis 7.x and 8.x.
3. **`maxmemory` + `maxmemory-policy`** — `CONFIG GET maxmemory-policy`. Default `noeviction` → writes fail when full. Caches should be `allkeys-lru` / `allkeys-lfu`. Mixed (cache + durable data) → `volatile-lru` + TTL on cached keys only.
4. **Persistence mode** — RDB, AOF, both, or none. Affects restart semantics, fork memory, fsync latency. `CONFIG GET save` + `CONFIG GET appendonly`.
5. **Client library** — connection pooling configured? Sensible `socket_timeout` and `retry_on_error`? A lazy `redis.Redis()` with no pool is a production incident waiting to happen.

## MUST DO

- **Atomic lock acquisition**: `SET lock:<resource> <owner-token> NX EX <seconds>` — one round trip, atomic. Use a random token for the owner so release is safe.
- **Safe lock release via Lua** (compare-and-delete) — not raw `DEL`:
  ```lua
  if redis.call("GET", KEYS[1]) == ARGV[1] then
      return redis.call("DEL", KEYS[1])
  end
  return 0
  ```
  Plain `DEL` would delete someone else's lock after your TTL expired.
- **`SCAN` for iteration** — never `KEYS *` on a production instance. `SCAN` is cursor-based, non-blocking, returns approximate matches per call.
- **TTL on every cache key** — set at write time (`SET ... EX`, `SETEX`, `EXPIRE`). A key without TTL lives forever and fills memory.
- **Jitter TTL** — `base + random(0, base * 0.1)` to avoid thundering herd when many keys expire simultaneously.
- **Keyspace naming**: `<service>:<entity>:<id>[:<field>]`, colon-separated, ASCII, short but readable. Consistent prefixes enable observability and safe bulk operations.
- **Pipelining for batches of independent commands** — one round trip, N commands. Distinct from transactions.
- **Idempotent writes** — `SET key value` always wins; `HSET k f v` overwrites field. `INCR` is idempotent per-command, not per-retry — combine with a dedup key if at-most-once matters.

## MUST NOT DO

- **`SETNX` + `EXPIRE` as two commands.** If the client dies between them, the key lives forever (lock leak). Always `SET ... NX EX`. The old `SETNX` command has **no `EX` option** — writing `SETNX key val EX 30` is a syntax error.
- **`KEYS *` / `KEYS pattern` in production.** O(N) over the entire keyspace, blocks the server. Use `SCAN` with `MATCH` + `COUNT`.
- **`HGETALL` on large hashes** (thousands of fields) — single-blocking O(N). Use `HSCAN`, or redesign (split the hash, store separate keys).
- **Multi-key commands across cluster slots without hash tags.** `MGET k1 k2` across shards returns `CROSSSLOT`. Force co-location with hash tags: `{user:42}:profile`, `{user:42}:settings`.
- **`EXPIRE` on a non-existent key** — silently returns 0. Check the path: some code sets TTL before insert.
- **`FLUSHDB` / `FLUSHALL` / `CONFIG RESETSTAT` unprotected.** Rename (`rename-command FLUSHALL ""` in redis.conf) or ACL-restrict these in production.
- **Pub/Sub as a message queue.** Pub/Sub is fire-and-forget — offline subscribers miss messages, no ACKs, no replay. Use Streams (`XADD` + consumer groups) for at-least-once delivery.
- **Storing huge blobs** (>100 KB per value). Redis is a RAM database; every replica / snapshot duplicates them. Use object storage + Redis for metadata.
- **Treating Redis transactions as RDBMS transactions.** `MULTI/EXEC` gives atomicity + isolation for the batch, but commands inside the block are queued without intermediate reads (use `WATCH` for optimistic locking). Errors in a command don't roll back others — syntactically invalid commands abort the batch; runtime errors let the rest execute.
- **Blocking commands** (`BLPOP`, `BRPOP`, `XREAD BLOCK`) on a shared connection — they tie up the whole connection for their timeout. Use a dedicated connection / pool for blockers.
- **Caching with `maxmemory-policy=noeviction`** — writes will fail with `OOM` when memory fills. Default of bare Redis; explicitly set `allkeys-lru` or `allkeys-lfu` for cache workloads.
- **Using MULTI/EXEC in a cluster across slots** — same `CROSSSLOT` rule; hash-tag co-locate or restructure.

## Reference Guide

All extended patterns (data-structure trade-offs, lock correctness levels, cache stampede mitigation, cluster hash-tags, persistence & eviction details, observability) live in a single file: **`references/pitfalls.md`**. Load it when the task goes beyond the MUST rules above.

## Output Format

When producing Redis code:

1. Short plan (1–3 bullets) — what keys / data structures / TTLs / atomicity guarantees are involved.
2. Commands or client code. Use language-agnostic Redis commands when the caller is unspecified.
3. For writes: state the eviction / TTL / persistence implications (e.g. "adds ~200 keys/min, TTL 1h, fits in `allkeys-lru` cache").
4. For multi-step atomic operations: state whether it's `SET NX`, `MULTI/EXEC + WATCH`, or Lua, and why.
5. Cluster-aware: if multi-key, show hash tags.

When reviewing Redis code: call out MUST-DO / MUST-NOT violations, especially missing TTL, non-atomic lock acquire/release, `KEYS` usage, and Pub/Sub used as a queue.
