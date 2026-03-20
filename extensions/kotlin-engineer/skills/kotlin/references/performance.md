# Performance Patterns

## Performance Workflow

1. Reproduce the slowdown with a representative scenario
2. **Measure before changing code** — latency percentiles, throughput, error rate, CPU/memory/GC/pool saturation
3. Identify the dominant bottleneck (DB I/O, lock contention, allocation/GC, algorithm)
4. Fix the most expensive bottleneck first
5. Re-measure — keep the change only if the result is material

## Code-Level Smells

- Repeated database or HTTP calls inside loops
- Building large intermediate collections when streaming or batching would suffice
- Regex compilation, JSON mapper creation, or expensive object creation on hot paths
- Excessive boxing, copying, or conversion between collection types in tight loops
- Adding a cache before measuring whether the repeated work is actually expensive

## Sequences for Lazy Evaluation

```kotlin
// ✅ Sequences avoid intermediate collections — useful for large lists with early termination
fun processLargeList(items: List<Item>): List<Result> =
    items.asSequence()
        .filter { it.isValid }
        .map { transform(it) }
        .take(100)
        .toList()  // Only processes first 100 valid items

// ❌ Eager evaluation — creates intermediate lists at each step
items.filter { it.isValid }.map { transform(it) }.take(100)
```

Use sequences when: the list is large AND you have early termination (`take`, `first`, `find`). For small collections, eager is fine.

## Parallel Processing with Coroutines

```kotlin
// ✅ Process independent items in parallel
suspend fun processInParallel(items: List<Item>): List<Result> =
    coroutineScope {
        items.map { item -> async { process(item) } }.awaitAll()
    }

// ✅ Bounded parallelism — avoid overwhelming downstream
suspend fun processBounded(items: List<Item>, concurrency: Int = 10): List<Result> =
    items.chunked(concurrency)
        .flatMap { chunk ->
            coroutineScope { chunk.map { async { process(it) } }.awaitAll() }
        }
```

## Caching

- Measure that the repeated work is expensive before adding a cache
- Set a memory budget and TTL — unbounded caches become memory leaks
- Use TTL jitter to prevent stampede (all keys expiring simultaneously)
- Invalidation strategy must be explicit: who evicts, when, and what happens on stale reads
- Monitor hit ratio — a cache with < 50% hit rate may not be worth the complexity

## JVM / Kotlin-Specific

```kotlin
// ✅ Inline functions eliminate lambda allocation overhead on hot paths
inline fun <T> measure(block: () -> T): Pair<T, Long> {
    val start = System.currentTimeMillis()
    val result = block()
    return result to (System.currentTimeMillis() - start)
}

// ✅ Value classes — zero runtime overhead for type-safe wrappers
@JvmInline
value class UserId(val value: String)

// ✅ data object instead of object for singletons used in sealed hierarchies (Kotlin 1.9+)
sealed class Result {
    data object Loading : Result()
    data class Success(val data: String) : Result()
}
```

## Anti-Patterns

- Micro-optimizing code before finding the dominant bottleneck
- Adding caches without ownership, invalidation strategy, or memory budget
- Increasing thread or connection pools to compensate for slow dependencies
- Reporting average latency only — always check p95/p99 tail latency
- Using `GlobalScope` for "performance" — it bypasses structured concurrency and leaks coroutines
