# Kotlin idioms — API design policy & pitfalls

Assumes you know scope functions, data/sealed/value classes, extension functions, inline/reified. This file is which to pick, and where LLMs pick wrong.

## Scope functions — pick by intent

| Function | Receiver is | Returns | Use for |
|---|---|---|---|
| `let` | `it` | lambda result | null-safe transform, introduce temporary scope |
| `run` | `this` | lambda result | compute a value from a receiver |
| `with(x) { }` | `this` | lambda result | same as `run` but non-extension (explicit target) |
| `apply` | `this` | receiver | configure a mutable object, return it |
| `also` | `it` | receiver | side-effect on a value (log, register), keep value |

Rules:
- Only one of them per expression. Nesting `.apply { ... .let { ... } }` is a sign to extract a function.
- `?.let { }` for the "do X if non-null" pattern — not `if (x != null) ...`.
- Don't use `apply` to call a single function — just call it. `x.apply { foo() }` vs `x.also { it.foo() }` — prefer the one that matches return semantics (use `apply` when you're configuring many things on a builder).

## Classes — pick the right kind

- **`data class`** — pure value type with a primary constructor. Gives `equals` / `hashCode` / `copy` / `componentN`. Not for entities, services, or anything with identity / behavior.
- **`sealed interface` / `sealed class`** — closed hierarchies (result types, UI states, commands). Prefer `sealed interface` — lets implementations be `object` / `data object` / class, supports multiple interface inheritance.
- **`value class` (`@JvmInline`)** — domain primitives (`UserId`, `Email`, `Temperature`). Compiles to the underlying type, zero overhead. `init { require(...) }` for validation.
- **`object`** — stateless services, singletons, `Comparator` instances, companion objects for factory methods.
- **`data object`** — sealed-hierarchy singletons with nice `toString` (`Loading`, `Empty`).

Pitfalls:
- `data class Foo(val id: Long, val name: String)` used as an entity → `equals` based on all fields changes with mutation, bugs in sets / maps.
- Value classes don't satisfy Java interop for `@Entity` / JPA — they're inlined and have no no-arg constructor.
- `copy()` calls the primary constructor, so `init` blocks **do** run — `require(...)` in `init` IS enforced on `copy()`. However, `copy()` bypasses secondary constructors and factory methods. If validation lives only there (not in `init`), `copy()` will skip it — put invariants in `init`.

## Extension functions — when and where

- **Extend types you don't own** to add domain-specific helpers (`String.isValidEmail()`).
- **Don't extend types you own** when a method would do — extensions are statically dispatched, so `open`-like polymorphism doesn't apply.
- **Never extend `Any` / `Any?`** — pollutes autocomplete for the whole project.
- **File-level** (top-level) extensions, not inside a class, unless the extension is conceptually a member of the enclosing class.
- Don't shadow members: an extension with the same name as a member is silently ignored.

## `inline` / `reified` — when it earns its cost

- `inline` removes lambda allocation — useful for **hot paths** with small lambdas (`measureTimeMillis { }`, locking helpers).
- `reified` — lets you use `T::class` inside the function, required for `Gson.fromJson<User>()` style APIs.
- `inline` bloats call sites — don't inline large functions; compiler warns when body is large.
- `noinline` / `crossinline` are for specific scenarios (`noinline` to pass a lambda elsewhere, `crossinline` to disallow non-local returns from a lambda used in a different scope). Don't use them unless the compiler forces you.

## Delegation

- **Interface delegation** (`class A(b: B) : Iface by b`) — composition over inheritance, avoids boilerplate.
- **Property delegation** — `by lazy { ... }` (thread-safe by default), `by Delegates.observable(x) { _, old, new -> }`, `by map` / `by mutableMap` for config-like objects.
- `lateinit var` **doesn't support primitives or nullable types**. Use `Delegates.notNull<Int>()` for primitives; for nullable, just initialize to `null`.
- `lazy` has `LazyThreadSafetyMode.SYNCHRONIZED` by default; `.NONE` is faster for single-threaded code but unsafe across threads.

## `Result<T>` vs exceptions

- Kotlin's `Result<T>` is for **internal plumbing**, not public API (the `Result` type is generic-variance-limited and awkward from Java).
- For public APIs, throw domain exceptions (`UserNotFoundException`) or return a `sealed interface Outcome { data class Success<T>(value: T); data class Failure(reason: Reason) }`.
- `runCatching { ... }` is handy but swallows `CancellationException` unless you re-check:
  ```kotlin
  runCatching { work() }
      .onFailure { if (it is CancellationException) throw it }
  ```
- Don't use `runCatching` in coroutines as a general try/catch — rethrow cancellation explicitly.

## Generics & variance

- **`out T`** when `T` is a producer (read-only; `List<out Animal>` means "list of Animal or subtype"). **`in T`** when `T` is a consumer (write-only).
- **`where T : Comparable<T>, T : Serializable`** for multiple bounds.
- `reified` requires `inline`. Can't be used with virtual methods.
- Star-projection `List<*>` when you don't care about the element type — read-only.
- Generic `T?` vs `T` matters: `fun <T> first(list: List<T>): T` forces non-null, even though the source may contain nulls — use `T?` for nullable semantics.

## Immutability & collection choice

- **Return `List<T>` / `Map<K, V>` / `Set<T>`** from public APIs — read-only at Kotlin level (Java sees them as mutable; annotate or wrap if that matters).
- **`MutableList` / `MutableMap` only inside a function body** or as a private field when building.
- `emptyList<T>()` / `listOf<T>()` — immutable. `mutableListOf<T>()` — `ArrayList`. Don't write `ArrayList<T>()` directly when `mutableListOf` reads better.
- `buildList { add(...); addIf(...) }` — idiomatic for conditional construction without intermediate mutable var.

## Null-safety traps

- `String!` (platform type) in API responses is a footgun — explicitly handle: `response.body ?: error("empty body")`.
- `list.filter { ... }.first()` vs `list.first { ... }` — the first chains through all elements; `first { }` short-circuits.
- `Map<K, V>[key]` returns `V?`. `Map<K, V>.getValue(key)` returns `V` but throws on missing — pick based on contract.
- `lateinit var x: SomeType` — accessing before init throws `UninitializedPropertyAccessException`, not NPE. `::x.isInitialized` to check.

## Equality & hashing

- `==` is structural (`equals`), `===` is referential. In Java interop code review, watch for Kotlin `==` being translated to Java `.equals` — fine, but `null == null` works both ways.
- Data classes generate `equals` / `hashCode` based on primary-constructor fields. Fields declared in the body are not included — don't rely on it.
- For value classes, `equals` compares underlying values directly.

## Enums vs sealed

- **Enum** — known, fixed set of instances without per-case data (`enum class Color { RED, GREEN, BLUE }`).
- **Sealed interface with `data object`s** — when cases may carry data or you want exhaustive `when` with mixed shapes.
- Don't emulate sealed hierarchies with enums + `when (color) { BLUE -> "blue"; else -> error("?") }` — add a case and the `else` swallows it.

## Domain modelling — non-obvious policy

- **Do not return `kotlin.Result<T>` from public API.** It's designed for `runCatching` plumbing, doesn't compose with Java callers, and its variance-limited generics break generic wrappers. Convert at the boundary (throw, or map to a sealed domain type).
- **`Either` from Arrow** — only if the project already depends on Arrow. Don't pull it in for a single function.
- `T?` must mean one thing. If "absent" and "unknown" are both possible, use a sealed hierarchy — overloading `null` is a recurring source of silent bugs.

## When you'd reach for Java-idiom and Kotlin has a better one

| Java-style | Kotlin-style |
|---|---|
| `if (x == null) throw IllegalArgumentException("x")` | `requireNotNull(x) { "x" }` |
| `Objects.requireNonNull(x)` | `requireNotNull(x)` |
| `new ArrayList<>(list)` to copy | `list.toMutableList()` |
| `map.getOrDefault(k, default)` | `map[k] ?: default` |
| Manual `Builder` class | primary constructor + `copy()` + default args |
| Anonymous inner class for a single method | lambda or function reference |
| `if (x != null) x.foo() else null` | `x?.foo()` |
