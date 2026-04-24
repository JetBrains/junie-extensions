# Coroutines & Flow — policy & pitfalls

Assumes you know `suspend`, `launch` / `async`, `Flow` / `StateFlow` / `SharedFlow`, `withContext`, `Dispatchers`. This file is only the traps and the rules.

## Scopes & lifecycles

- **Every coroutine must have an owner.** Framework-provided (`viewModelScope`, `lifecycleScope`, Ktor `call`), or a custom `CoroutineScope(SupervisorJob() + Dispatchers.Default + CoroutineName("service-x"))` held by the service.
- **`SupervisorJob` for long-lived services** (one child failing shouldn't kill siblings). **Regular `Job` inside a use case** — when one subtask fails, cancel the rest.
- `CoroutineScope(...)` as a local is almost always a bug — it doesn't cancel when its "parent" function returns. Use `coroutineScope { }` / `supervisorScope { }` instead, which are structured.
- Never store a `CoroutineScope` as a top-level / object property — that's `GlobalScope` with extra steps.

## Cancellation

- `CancellationException` is a **normal control-flow signal**, not an error. Always rethrow from generic catches:
  ```kotlin
  try { work() } catch (e: Exception) {
      if (e is CancellationException) throw e
      log.error("work failed", e)
  }
  ```
- Non-suspending loops don't check for cancellation. Insert `ensureActive()` / `yield()` inside CPU-heavy loops that you want to cancel promptly.
- `NonCancellable` block is for cleanup (`withContext(NonCancellable) { close() }`) — never wrap business logic in it.
- `finally` after a `withTimeout` runs on a cancelled coroutine — don't call suspend functions there without `withContext(NonCancellable)` wrapping.

## Dispatcher discipline

- `Dispatchers.Main` — UI callbacks only.
- `Dispatchers.IO` — blocking I/O (JDBC, `File`, `Socket`). Pool size is `max(64, availableProcessors)` by default (so on a 128-core box it's 128, not 64); tune with `kotlinx.coroutines.io.parallelism` if you know you need more.
- `Dispatchers.Default` — CPU work. Sized = number of cores.
- `Dispatchers.Unconfined` — advanced use only; resumes on whatever thread completed the suspension point. Don't sprinkle it.
- **Inject dispatchers** for testing: `class Repo(private val io: CoroutineDispatcher = Dispatchers.IO)`. Makes `runTest` + `StandardTestDispatcher` actually usable.

## Parallel work

- Sequential (wrong for parallelism):
  ```kotlin
  val a = async { fetchA() }.await()
  val b = async { fetchB() }.await()  // only starts after a finishes!
  ```
- Parallel (correct):
  ```kotlin
  coroutineScope {
      val a = async { fetchA() }
      val b = async { fetchB() }
      a.await() to b.await()
  }
  ```
- `awaitAll(list)` on a collection of `Deferred` — propagates the first failure and cancels siblings.
- `supervisorScope { }` — used when one failing child **shouldn't** cancel siblings (fan-out to 10 endpoints where partial success is fine).

## `StateFlow` vs `SharedFlow`

- **`StateFlow<T>`** — always has a current value; conflates (fast producers drop intermediate values). Use for "current state of something" (UI state, settings). Replay = 1 by contract.
- **`SharedFlow<T>`** — for events (navigation, one-shot signals). Configure explicitly: `MutableSharedFlow(replay = 0, extraBufferCapacity = 64, onBufferOverflow = BufferOverflow.DROP_OLDEST)`.
- **Never a `SharedFlow` with `replay > 0` for events** — new subscribers will receive old events (toasts from 10 minutes ago). Use `replay = 0` + handle missed-signals differently.
- `StateFlow.value = x` is read-modify-write under contention — use `.update { it.copy(...) }` for correct atomic updates.

## `Flow` correctness

- `flow { }` is cold — the block runs per collector. Don't put side effects outside `emit` assuming they run once.
- `emit` is not thread-safe across multiple launched coroutines inside one `flow { }`. Use `channelFlow` / `callbackFlow` if you need multi-threaded emission.
- `flowOn(dispatcher)` affects **upstream only**. `flowOn(IO).map { }` — the `map` still runs on the downstream dispatcher. Put `flowOn` as late as possible, right before collection.
- `catch { }` catches only upstream exceptions. A throw inside `collect { }` goes to the caller, not to `catch`. This is exception transparency — don't violate by catching everything inside an operator.
- `Flow.first()` / `single()` / `toList()` on an infinite upstream hangs forever. Combine with `withTimeoutOrNull(...)`.

## `SharingStarted` for hot Flows in UI

- `MutableStateFlow(initial).asStateFlow()` — always active.
- `flow.stateIn(scope, SharingStarted.Eagerly, initial)` — active while scope alive.
- `flow.stateIn(scope, SharingStarted.Lazily, initial)` — activates on first subscriber, stays.
- `flow.stateIn(scope, SharingStarted.WhileSubscribed(5_000), initial)` — **the right default for mobile / screen-scoped state** (keeps alive 5 s after last subscriber to survive rotation without restart).

## `callbackFlow` / `channelFlow`

- `callbackFlow { }` to bridge listener-based APIs. **Must end with `awaitClose { unregister() }`** — otherwise the collector leaks the listener.
- Don't `trySend(x).getOrThrow()` — if the buffer is full, `trySend` returns a failure; decide between dropping, suspending (`send`), or increasing `BUFFERED` capacity.

## Testing coroutines

- `runTest { }` from `kotlinx-coroutines-test` — virtual time, skips delays automatically.
- Inject `TestDispatcher` into your scope: `StandardTestDispatcher()` (ordered, manual advance) or `UnconfinedTestDispatcher()` (immediate).
- `MainDispatcherRule` for Android / anything using `Dispatchers.Main`.
- `Turbine` library for asserting on `Flow` emissions deterministically.
- Don't call `Thread.sleep` in a coroutine test — it blocks virtual time. Use `delay(...)` and `advanceTimeBy(...)`.

## Common anti-patterns

| Anti-pattern | Correct |
|---|---|
| `GlobalScope.launch { ... }` | Inject `CoroutineScope` or use framework scope |
| `runBlocking { suspendCall() }` inside a suspend function | Just `suspendCall()` — remove `runBlocking` |
| `MutableStateFlow` returned from a public API | `val state: StateFlow<X> = _state.asStateFlow()` |
| `.value = state.value.copy(x = y)` | `state.update { it.copy(x = y) }` |
| `flow { withContext(IO) { emit(...) } }` | `flow { emit(...) }.flowOn(IO)` |
| `try { work() } catch (e: Exception) { log(e) }` | Same plus `if (e is CancellationException) throw e` first |
| Parallel fan-out with `.map { async { it.fetch() } }.map { it.await() }` inside `List` | Wrap in `coroutineScope { ... awaitAll() }` for proper cancellation semantics |
