---
name: kotlin-engineer
description: Kotlin 2.x policy and pitfalls. Use when writing, reviewing, or refactoring Kotlin code — enforces coroutine-safety, Flow correctness, null-safety, and API-design rules that LLMs frequently get wrong.
---

# Kotlin — policy & pitfalls

Baseline Kotlin knowledge (data/sealed/value classes, scope functions, null-safety operators, extension functions, `suspend`, `Flow`, `when` exhaustiveness) is assumed. This skill does not teach the language — it encodes the project policy and the traps that keep appearing in code review.

## Setup Check (run first)

Before writing non-trivial code:

1. **Kotlin version** — target 2.x when possible. Check `build.gradle(.kts)` (`kotlin("jvm") version "2.x"`) or `libs.versions.toml`.
2. **JDK target** — `kotlin { jvmToolchain(21) }` or `compileOptions { targetCompatibility = JavaVersion.VERSION_21 }`. Matters for virtual threads (21+) and records interop (17+).
3. **Compiler plugins** — `kotlin("plugin.spring")`, `kotlin("plugin.jpa")`, `kotlinx-serialization`, `kotlin("kapt")` vs `com.google.devtools.ksp`. Missing `plugin.spring` → final Spring classes can't be proxied. Missing `plugin.jpa` → `InstantiationException: No default constructor`.
4. **Lint** — `detekt` / `ktlint` configured? Follow the existing rules; don't introduce new violations.
5. **Build wrapper** — use `./gradlew`

## MUST DO

- **Null-safety via `?`, `?.`, `?:`, `let`, `requireNotNull`.** Use `!!` only when null is a true contract violation — document why on the same line.
- **Sealed hierarchies** for closed result / state types (`sealed interface Result { data class Success(...); data class Failure(...) }`) + exhaustive `when` without `else`.
- **Value classes (`@JvmInline value class`)** for domain identifiers (`UserId`, `Email`) — zero-overhead type-safety.
- **`data class` only for pure value types.** Not for entities, services, or anything with behavior / lifecycle.
- **Structured concurrency** — inject `CoroutineScope`, use `coroutineScope { }` / framework scopes (`viewModelScope`). Never `GlobalScope.launch`.
- **Always rethrow `CancellationException`** in generic `catch (e: Exception)` blocks — swallowing it disables cancellation.
- **Expose read-only Flow types** — `val state: StateFlow<X> = _state.asStateFlow()`. Never leak `MutableStateFlow` / `MutableSharedFlow` from an API.
- **`withContext(Dispatchers.IO)` / `Default`** for blocking / CPU work inside suspend. Encapsulate dispatcher choice in the repository / data-source layer — not at call sites.
- **Immutability by default** — `val` over `var`, `List` over `MutableList` in public API, `copy()` on data classes instead of mutation.
- **Named arguments for 3+ parameters** — prevents silent argument swaps at call sites.

## MUST NOT DO

- **No `!!`** without a commented reason. Refactor to `?.let { }` / `requireNotNull(x) { "why" }`.
- **No `runBlocking` in production** — only in `main` and tests. Inside a suspend function it's always a bug.
- **No `GlobalScope.launch` / `GlobalScope.async`** — leaks, no structured cancellation.
- **No swallowing `CancellationException`.** `try/catch(Exception)` without a cancellation rethrow silently disables cancellation.
- **No `.first()` / `.single()` on a hot `Flow`** without a timeout — a source that never emits hangs the coroutine forever.
- **No `async { }.await()` sequentially** when you want parallelism — it's the same as calling `suspend` directly. Use `coroutineScope { val a = async { .. }; val b = async { .. }; a.await() + b.await() }`.
- **No `Dispatchers.Main` / `Dispatchers.IO` references from common / multiplatform code** unless the module is JVM-only.
- **No platform-type leaks (`String!`)** in public API — annotate Java interop returns with `@NotNull` / `@Nullable` on the Java side, or cast explicitly.
- **No catching `Throwable`** — you'll catch `OutOfMemoryError`, `StackOverflowError`, and cancellation. Use `Exception` and rethrow cancellation.
- **No `lateinit var` on primitives or nullable types** — compile error. Use `Delegates.notNull()` for primitives.

## Reference Guide

| Load when | File |
|---|---|
| Async / reactive code — coroutines, Flow, StateFlow/SharedFlow, cancellation, testing | `references/coroutines.md` |
| API design — scope functions, value/data/sealed classes, extension functions, inline/reified, delegates, `Result<T>` | `references/idioms.md` |
| Gradle / tooling — Kotlin DSL, version catalogs, KSP vs kapt, multi-module layout, compiler plugins | `references/build-setup.md` |

## Output Format

When producing code:

1. A short plan (1–3 bullets) of what's changing.
2. The code.
3. A checklist of the non-obvious MUST rules applied.

When reviewing code: call out MUST-DO / MUST-NOT violations explicitly and suggest the minimal fix.
