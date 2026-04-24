# redis-engineer

Junie extension that turns the agent into a disciplined Redis engineer: enforces atomic patterns, TTL discipline, cluster-safe design, and catches the production traps that LLMs get wrong by default — `SETNX`+`EXPIRE` race, `KEYS *` blocking, `HGETALL` on large hashes, Pub/Sub misused as a queue, `DEL` for lock release, `noeviction` on a cache.

## Philosophy

Baseline Redis knowledge (strings, hashes, lists, sets, sorted sets, streams, pub/sub, TTL, MULTI/EXEC, basic replication) is assumed — the extension does not re-teach data structures. Instead it encodes:

- **Policy** — MUST / MUST NOT rules the agent follows for every key and command it writes.
- **Pitfalls** — behaviors that work in dev (single instance, low load) and fail in production (cluster, memory pressure, high concurrency).
- **Setup awareness** — detect topology (standalone / Sentinel / Cluster), Redis version, `maxmemory-policy`, and persistence mode before writing non-trivial code.

## What it covers

- Atomic operations: `SET NX EX` for locks, Lua scripts for compare-and-delete, `WATCH`+`MULTI/EXEC` with retry.
- TTL discipline: mandatory TTLs on cache keys, jitter to prevent thundering herd.
- Cluster safety: hash tags for multi-key commands, `CROSSSLOT` avoidance.
- Memory management: `maxmemory-policy` matrix (`noeviction` vs `allkeys-lru` vs `volatile-lru`), blob size limits.
- Persistence trade-offs: RDB fork memory, AOF rewrite, fsync latency.
- Observability: `SLOWLOG`, `LATENCY DOCTOR`, `INFO commandstats`.

## Files

- `skills/redis-best-practices/SKILL.md` — hub: Setup Check, MUST DO / MUST NOT, Reference Guide, Output Format.
- `skills/redis-best-practices/references/pitfalls.md` — data structure choices, atomicity patterns, cache invalidation, cluster-safe design, persistence / eviction trade-offs.

## Requirements

- Redis 6.2+ recommended (some patterns require `SET ... KEEPTTL`, `GETEX`); streams require 5.0+; functions require 7.0+.
- Client library with connection pooling and configured timeouts.

## Installation

Drop the extension folder into your Junie extensions directory and enable it. Junie picks up `SKILL.md` automatically and loads references on demand.
