# Redis pitfalls — production traps that compile and silently break

Collected from real Redis incidents, not from the `redis.io` command reference. Assumes you know what each command does; this file is about when they surprise you.

## Atomicity

- **`SET key val NX EX ttl`** is the only correct way to grab a lock. The legacy `SETNX` + separate `EXPIRE` pair is two commands; a crash between them leaves a forever-key.
- **Releasing a lock with `DEL`** is wrong — your TTL may have expired and someone else now owns it. Use the Lua compare-and-delete pattern (GET + DEL).
- **Redlock across multiple masters** is only worth the complexity in rare cases. For most systems, a single-instance `SET NX EX` lock is sufficient; rely on the lease TTL for correctness under failover.
- **`WATCH` + `MULTI` + `EXEC`** is optimistic concurrency. `EXEC` returns `nil` if the watched key changed — your code MUST handle that and retry. Many libraries swallow the `nil`.
- **Lua scripts are atomic**, single-threaded, and block the server. Keep them short (<50 ms). `redis.call` forwards errors; use `pcall` to catch and return a sentinel.
- **Pipelines are NOT transactions.** Other clients can interleave between your pipelined commands. Pipelines are purely a network-round-trip optimization. For atomicity use Lua or `MULTI/EXEC`.

## Expiration

- `EXPIRE key 0` — **deletes the key immediately**. Often a source of surprise when TTL is computed (`now + delay`) and `delay` goes negative.
- `EXPIRE` on a non-existent key returns 0 and does nothing. Check your write path — TTL must come **after** the key exists.
- `SET key val` (without `EX`, `KEEPTTL`) **removes** any existing TTL. `SET key val KEEPTTL` (Redis 6.0+) preserves the TTL.
- `PERSIST key` removes TTL. Rarely used correctly — usually the caller wanted `GETEX` / re-`SET` with new TTL.
- Subsecond TTL: use `PEXPIRE` / `SET ... PX`. `EX` is whole seconds; `EXPIRE 0` behavior becomes surprising.
- Redis expires keys **lazily** (on access) + actively (background sample). Setting TTL doesn't guarantee immediate memory release. With massive bulk expirations, memory reclaim lags behind.

## Cache stampede / thundering herd

- When a popular key expires, N concurrent callers miss the cache, hit the backend, and write. Fixes:
  - **TTL jitter**: write with `EX = base + random(0, base * 0.1)`.
  - **Single-flight via lock**: when MISS, acquire `lock:<key>` (SET NX EX 5), fill cache if lock acquired, else wait and re-read.
  - **Probabilistic early expiration (XFetch / stale-while-revalidate)**: refresh when within 10% of TTL with increasing probability.
- Don't panic-refresh by scanning all keys near expiry — that's the opposite.

## Eviction & memory

- `maxmemory-policy` matrix:
  - `noeviction` — writes fail. Default in upstream Redis; dangerous for caches.
  - `allkeys-lru` / `allkeys-lfu` — evict by recency / frequency across all keys. Use for pure caches.
  - `volatile-lru` / `volatile-lfu` / `volatile-ttl` / `volatile-random` — evict only keys with TTL set. Use for mixed workloads (durable data + cached data), and set TTL only on the cache.
- **`MEMORY USAGE <key>`** — inspect a single key. `--bigkeys` from `redis-cli` samples the keyspace for outliers. `--memkeys` (6.0+) shows biggest actual memory consumers.
- **Hot keys** — a single key hit millions of times per second. `--hotkeys` (requires `maxmemory-policy=allkeys-lfu`) finds them. Fix: add a local (in-process) cache layer, shard the key, or rethink access pattern.
- **Big keys** (>1 MB values, >10K element containers) cause latency spikes on any O(N) operation, RDB fork stalls, replication backlog buildup. Sentinel-watch `SLOWLOG GET 10` for them.
- **RDB fork memory**: forking doubles memory in the worst case (write-heavy workload, copy-on-write copies most pages). Keep `maxmemory` well below 50% of RAM on write-heavy instances with RDB.
- `OBJECT ENCODING` — tells you whether a hash is `listpack` (small, packed) or `hashtable` (large, O(1) access but more memory). `hash-max-listpack-entries` / `-value` control the threshold.

## Data structures — when they surprise you

- **Lists**: `LPUSH` + `RPOP` is a queue; `LPUSH` + `LPOP` is a stack. `LTRIM` after `LPUSH` caps length. `LPOS` (6.0.6+) replaces manual scan.
- **Sets**: `SMEMBERS` on a big set is O(N). Use `SSCAN`.
- **Sorted sets**: `ZADD NX` = insert only; `XX` = update only (both since Redis 3.0.2). `ZADD GT`/`LT` = update only if score is greater/less — added in Redis 6.2 and easy to miss.
- **Hashes**: `HGETALL` on a 1M-field hash is a server stall. Split: `HGETALL u:42` is fine; `HGETALL all_users` is not.
- **Streams** (`XADD`, `XREAD`, `XREADGROUP`, consumer groups) are the correct primitive for at-least-once messaging. Pub/Sub isn't.
  - `XADD k MAXLEN ~ 10000 *` — capped trim (`~` is approximate, much faster than exact).
  - `XADD k MINID <ms>` (6.2+) — time-based retention.
  - Consumer groups track Pending Entry List (PEL); consumers must `XACK` or stale entries grow. `XCLAIM` / `XAUTOCLAIM` to re-assign after worker death.

## Cluster specifics

- **Hash tag**: `{tag}` in key name forces slot assignment by `tag`, not full key. Use to co-locate related keys: `{user:42}:profile`, `{user:42}:sessions`.
- **`CROSSSLOT` error**: multi-key command touches different slots. Solutions: hash tags, split the command, accept N round trips.
- **MOVED / ASK** responses: clients must follow. Most modern libraries handle it; if you see them reaching application code, the library config is wrong.
- **Pub/Sub in cluster**: broadcasts to ALL nodes (every `PUBLISH` fans out). Use sharded Pub/Sub (`SPUBLISH` / `SSUBSCRIBE`, 7.0+) if throughput matters.
- **No multi-DB selection**: cluster has only DB 0. `SELECT 1` fails in cluster mode.

## Persistence

- **RDB**: periodic snapshot; losing last N seconds on crash. `save 900 1` = snapshot if ≥1 write in 900s. Cheap at read time, expensive on fork.
- **AOF**: append every write. `appendfsync everysec` is the sane default (≤1s loss, low overhead). `always` = durable, slow. `no` = fastest, loses everything on crash.
- **AOF rewrite** (`BGREWRITEAOF`) compacts the file; done automatically when it doubles. Needs fork → memory spike.
- **Replica full resync**: master forks to produce RDB snapshot, streams to replica, then buffers writes. If the buffer overflows (slow replica / big keys), resync restarts. `client-output-buffer-limit slave 256mb 64mb 60` — tune for write rate.
- **AOF truncation on crash**: default `aof-load-truncated yes` recovers; if set to `no`, Redis refuses to start after any unclean shutdown.

## Security

- **Default port 6379 bound to all interfaces is a known attack vector.** Bind to `127.0.0.1` for single-host, or use `bind` with explicit internal IPs; require `AUTH`.
- **`ACL SETUSER`** (6.0+) — least-privilege users. Cache workload user needs only `~cache:* +get +set +del +expire +scan +ping` (no `&*` — that grants pub/sub channel access, not needed for cache). Kill the default `default` user's ability to `FLUSHALL` in production.
- **TLS**: enable on all client connections in multi-tenant / cross-network deployments. Built-in since 6.0.
- **Lua sandbox**: scripts run in a sandbox but CAN read any key. Don't accept Lua scripts from user input.
- **Rename dangerous commands** in redis.conf: `rename-command FLUSHALL ""`, same for `KEYS`, `DEBUG`, `CONFIG`, `SHUTDOWN` if not needed.

## Observability

- **`SLOWLOG GET 10`** — most important diagnostic. Latency outliers are almost always big-key operations.
- **`LATENCY DOCTOR`** — Redis's built-in analyzer.
- **`INFO commandstats`** — calls + avg latency per command. Look for high avg on `HGETALL`, `SMEMBERS`, `KEYS`.
- **`CLIENT LIST`** — ongoing connections. Check for idle, for aged connections, for blocked consumers.
- **`MONITOR`** — don't use in production for >10 seconds. It streams every command.
- **Key count: `DBSIZE`** — O(1). `KEYS *` is NOT the right way.

## Connection client-side

- **Connection pool size** — per-process, not global. Too small → connection wait + tail latency. Too large → server-side `maxclients` exhaustion. Start at 2× worker threads.
- **Blocking commands** (`BLPOP`, `XREAD BLOCK 0`) pin the connection. Use a dedicated pool for blockers; the general pool must not block.
- **`socket_timeout` vs `socket_connect_timeout`** — both must be finite. Without them, a network partition hangs the client indefinitely.
- **Retry policy**: retry only idempotent commands. `INCR` retried naively under timeout double-counts — add a dedup key if the counter matters.

## Anti-patterns

| Mistake | Why | Fix |
|---|---|---|
| `SETNX` + separate `EXPIRE` | Non-atomic, lock leak on crash | `SET key val NX EX` |
| `DEL lock:x` to release a lock | May delete someone else's lock | Lua compare-and-delete |
| `KEYS cache:user:*` on production | O(N) full keyspace scan, blocks server | `SCAN 0 MATCH cache:user:* COUNT 100` |
| `HGETALL bighash` | O(N) single blocking call | `HSCAN` or redesign |
| Pub/Sub for reliable delivery | No persistence, no ACKs | Streams + consumer groups |
| `SELECT 1` in a cluster | Cluster is DB-0 only | Separate cluster / use namespaces |
| Cache without TTL | Memory fills, eventual `OOM` | `SET ... EX <ttl>` always |
| `maxmemory-policy=noeviction` for cache | Writes start failing under load | `allkeys-lru` / `allkeys-lfu` |
| Huge values (>100 KB) | Replication lag, fork spike, slow ops | Offload to object storage, store metadata in Redis |
| Pipelining instead of Lua for atomicity | Other clients interleave | Lua script or `MULTI/EXEC + WATCH` |
| Single connection for BLPOP + others | Connection stuck for timeout | Dedicated connection/pool for blockers |
| `INCR` for rate limiting without TTL | Counter grows forever | Fixed-window: `INCR` + `EXPIRE` first time, or sliding log via sorted set |

## Rate limiter — fixed window

```
# On first increment in a window, set TTL. INCR is atomic; EXPIRE is not part of INCR.
# Use a Lua script to make INCR + EXPIRE atomic:
local n = redis.call("INCR", KEYS[1])
if n == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end
return n
```

For sliding-log style: sorted set by timestamp, `ZREMRANGEBYSCORE` older entries, `ZCARD` count, `ZADD` now — in a Lua script.

## Benchmark before you trust

- `redis-benchmark` gives synthetic numbers; real workloads differ wildly.
- Measure p99 latency under actual concurrency, not throughput. Redis single-threaded data path means one slow command tail-blocks the others.
- `MONITOR` plus production traffic replay — dangerous but accurate for debugging.
