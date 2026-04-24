# Concurrency in modern Java (17–21)

Generic `ExecutorService` / `CompletableFuture` API is assumed. This file covers how to use virtual threads, structured concurrency, and locking without the classic footguns.

## Virtual threads — when they help, when they hurt

**Use virtual threads when:**

- The thread spends most of its time waiting on I/O: HTTP, DB (JDBC with a modern driver), blocking queues, files.
- You want to replace a thread pool of hundreds / thousands of platform threads with a one-task-per-thread model.

**Don't use virtual threads when:**

- The work is CPU-bound (tight loops, crypto, JSON parsing of huge payloads). Virtual threads don't add parallelism — they multiplex on `ForkJoinPool` carriers. For CPU-bound work use `ForkJoinPool` / `parallelStream` with sized pools.
- You rely on thread identity for caching (`ThreadLocal` per pooled worker). Virtual threads are cheap and disposable — millions can exist, `ThreadLocal` without proper lifecycle becomes a leak.
- Third-party code uses `synchronized` around blocking calls. That pins the carrier and defeats the point (see below).

## Carrier pinning — the one problem that keeps biting

A virtual thread is pinned to its carrier thread while:

- Inside a `synchronized` block or method, **if** it blocks on I/O.
- Inside a native method (`JNI`).

During pinning, other virtual threads can't be scheduled on that carrier. Enough pinned threads → scheduler starves → latency spikes.

Fixes, in priority order:

1. Replace `synchronized` with `java.util.concurrent.locks.ReentrantLock` — it's virtual-thread-friendly.
2. Shorten the critical section so it doesn't contain blocking I/O.
3. JDK 21+ diagnostic: `-Djdk.tracePinnedThreads=full` (or `short`) logs every pin event with stack trace. Use it when profiling an app that switched to virtual threads and got slower.

JDK 24+ removes pinning for most `synchronized` cases — but production today still has it.

## Structured concurrency (`StructuredTaskScope`)

Preview in 21, finalized in Java 24 (JEP 499). The point: child tasks **live within the scope**, cancellation propagates, leaks are impossible.

```java
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    var userFut  = scope.fork(() -> userService.findById(id));     // Supplier<User>
    var orderFut = scope.fork(() -> orderService.findLatest(id));

    scope.join();                 // wait for all
    scope.throwIfFailed();        // rethrow first failure, cancel others

    return new Dashboard(userFut.get(), orderFut.get());
}
```

Rules:

- Every `fork(...)` must be followed by exactly one of `join()` / `joinUntil(deadline)`. Not calling it = leak.
- Don't hand the `Subtask` out of the scope — it's only valid inside the `try` block.
- Two built-in policies: `ShutdownOnFailure` (fail-fast) and `ShutdownOnSuccess` (race — first success wins, siblings cancelled).
- Write your own policy by subclassing `StructuredTaskScope` — e.g. "cancel after 3 failures out of 10".

## `CompletableFuture`

- Default executor for `supplyAsync` / `thenApplyAsync` is `ForkJoinPool.commonPool()` — a shared, small, CPU-sized pool. Don't run blocking I/O on it. Pass an explicit `Executor`: `supplyAsync(task, myExecutor)`.
- `join()` / `get()` inside another async chain = blocking a pool thread on another pool thread. Recipe for deadlock. Chain with `thenCompose` / `thenCombine` instead.
- Exception propagation: `thenApply` sees the upstream exception only through `whenComplete(bifunc)` or `exceptionally(fn)` / `handle(bifunc)`. A `thenApply(fn)` after a failed stage is skipped silently.
- `allOf(futs).thenApply(...)` — the combined future has no result; you still have to `.get()` each original.

## `ExecutorService` lifecycle

- JDK 19+: `ExecutorService` implements `AutoCloseable`. Use `try (var exec = Executors.newVirtualThreadPerTaskExecutor()) { ... }`. On close, it shuts down and awaits termination.
- Pre-19: always a pair `shutdown()` + `awaitTermination(timeout)` in a `finally`. `shutdownNow()` only on unrecoverable timeout — it interrupts running tasks, which is often not what pool users want.
- `Executors.newFixedThreadPool(n)` uses an unbounded `LinkedBlockingQueue` — under overload the queue grows until OOM. Prefer `new ThreadPoolExecutor(core, max, keepAlive, unit, new ArrayBlockingQueue<>(capacity), rejectionPolicy)`.

## Thread-local and scoped values

- `ThreadLocal` with pooled threads: must be cleared (`remove()`) at the end of each task, or the pool propagates state across unrelated requests.
- **`ThreadLocal` + virtual threads = memory leak at scale.** Each virtual thread owns its own `ThreadLocalMap`. With a per-task-per-thread model, millions of live vthreads can each hold a MB-sized cached buffer, tokenizer, formatter, SDK client, etc. Heap dumps show `java.lang.Thread[]` → `ThreadLocalMap$Entry[]` dominating retained size. Three fixes, in order of preference:
  1. Move the cached object to a **single static field** (if it's thread-safe — e.g. `DateTimeFormatter`, `ObjectMapper`) and delete the `ThreadLocal`.
  2. Use a **pooled / shared resource** (connection pool, buffer pool) and check out/check in around the call.
  3. If you truly need per-thread caching, use `ScopedValue` for the lifetime of a request, or `remove()` in a `finally` at the exact lifetime boundary.
- `InheritableThreadLocal` on virtual threads inherits from the **carrier** at fork time, not from the logical parent. Surprising results during structured concurrency — prefer `ScopedValue`.
- Libraries that cache in `ThreadLocal` under the hood (Jackson's `BufferRecyclerPool` pre-2.16, `DateFormat` wrappers, SDK clients with "per-thread" builders): audit on migration. `-XX:NativeMemoryTracking=summary` plus `jcmd <pid> VM.native_memory summary` helps spot native buffers retained via `ThreadLocal`.
- `ScopedValue` (preview in 21, finalized in Java 24 — JEP 487) — immutable, tied to the structured scope, no cleanup needed:
  ```java
  static final ScopedValue<UserId> CURRENT = ScopedValue.newInstance();

  ScopedValue.where(CURRENT, userId).run(() -> {
      // inside this block CURRENT.get() returns userId
  });
  ```
  Prefer `ScopedValue` over `ThreadLocal` for request-scoped context — they're safer and faster with virtual threads.

## Race conditions in "simple" code

- `Map.computeIfAbsent(k, f)` inside another `computeIfAbsent` on the same `ConcurrentHashMap` — deadlocks on the bin lock.
- `map.putIfAbsent(k, make())` always evaluates `make()`. Use `computeIfAbsent(k, key -> make())` for lazy insertion.
- Check-then-act on `AtomicReference`: `if (ref.get() == null) ref.set(new X())` — two threads can both see null. Use `compareAndSet` or `updateAndGet`.
- `Collections.synchronizedList(...)` locks each call; iteration requires external `synchronized (list) { for (...) ... }`. A `CopyOnWriteArrayList` is often the better answer for read-heavy lists.

## Debugging concurrency

- Thread dump: `jstack <pid>` or `Ctrl+\` on the terminal running a JVM. Look for `BLOCKED`, `WAITING on ... locked by <other>`.
- `-XX:+HeapDumpOnOutOfMemoryError` — combined with virtual threads, OOM usually means an unbounded `ThreadLocal` / queue.
- JFR (Java Flight Recorder): `jcmd <pid> JFR.start duration=60s filename=rec.jfr` → open in JDK Mission Control. The `Virtual Thread Pinning` event is the one to look at if performance regressed after switching to virtual threads.
