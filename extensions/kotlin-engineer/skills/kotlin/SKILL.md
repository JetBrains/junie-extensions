---
name: kotlin
description: Idiomatic Kotlin patterns including coroutines, Flow, multiplatform architecture, Compose UI, Ktor server, and type-safe DSL design. Use when building Kotlin applications with coroutines, KMP, Android Compose, or Ktor. Also covers architecture review, performance tuning, and debugging for JVM/Kotlin backends.
---

# Kotlin

Senior Kotlin developer patterns covering Kotlin 2.x, coroutines, Flow, Multiplatform, and idiomatic language features.

## Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Coroutines & Flow | `references/coroutines-flow.md` | Async operations, structured concurrency, StateFlow, SharedFlow |
| DSL & Idioms | `references/dsl-idioms.md` | Scope functions, delegates, extension functions, inline/reified, DSL builders |
| Ktor Server | `references/ktor-server.md` | Routing, plugins, authentication, serialization |
| Multiplatform (KMP) | `references/multiplatform-kmp.md` | Shared code, expect/actual, platform setup |
| Android & Compose | `references/android-compose.md` | Jetpack Compose, ViewModel, Material3, navigation |
| Architecture | `references/architecture.md` | Package structure, module boundaries, layering, architecture smells |
| Performance | `references/performance.md` | Profiling, caching, pool sizing, async processing |
| Debugging | `references/debugging.md` | Investigation workflow, logs, metrics, minimal reproductions |

## Key Patterns

### Sealed Classes for State Modeling

```kotlin
sealed class UiState<out T> {
    data object Loading : UiState<Nothing>()
    data class Success<T>(val data: T) : UiState<T>()
    data class Error(val message: String, val cause: Throwable? = null) : UiState<Nothing>()
}

// Exhaustive when — compiler enforces all branches
fun render(state: UiState<User>) = when (state) {
    is UiState.Loading  -> showSpinner()
    is UiState.Success  -> showUser(state.data)
    is UiState.Error    -> showError(state.message)
}
```

### Coroutines & Flow

```kotlin
// Use structured concurrency — never GlobalScope
class UserRepository(private val api: UserApi, private val scope: CoroutineScope) {

    fun userUpdates(id: String): Flow<UiState<User>> = flow {
        emit(UiState.Loading)
        try {
            emit(UiState.Success(api.fetchUser(id)))
        } catch (e: IOException) {
            emit(UiState.Error("Network error", e))
        }
    }.flowOn(Dispatchers.IO)

    private val _user = MutableStateFlow<UiState<User>>(UiState.Loading)
    val user: StateFlow<UiState<User>> = _user.asStateFlow()
}
```

### Null Safety

```kotlin
val displayName = user?.profile?.name ?: "Anonymous"

user?.email?.let { email -> sendNotification(email) }

// !! only when null is a true contract violation
val config = requireNotNull(System.getenv("APP_CONFIG")) { "APP_CONFIG must be set" }
```

### Scope Functions

```kotlin
// apply — configure object, returns receiver
val request = HttpRequest().apply {
    url = "https://api.example.com/users"
    headers["Authorization"] = "Bearer $token"
}

// let — transform nullable / introduce local scope
val length = name?.let { it.trim().length } ?: 0

// also — side-effects without breaking the chain
val user = createUser(form).also { logger.info("Created user ${it.id}") }
```

### Value Classes (zero runtime overhead)

```kotlin
@JvmInline
value class UserId(val value: String)

@JvmInline
value class Email(val value: String) {
    init { require(value.contains("@")) { "Invalid email: $value" } }
}
```

## Constraints

### MUST DO
- Use null safety (`?`, `?.`, `?:`) — use `!!` only when null is a contract violation
- Prefer `sealed class`/`sealed interface` for state and result modeling
- Use `suspend` functions for async operations; `Flow` for streams
- Apply scope functions appropriately (`let`, `run`, `apply`, `also`, `with`)
- Use structured concurrency — inject `CoroutineScope`, never use `GlobalScope`
- Handle `CancellationException` correctly — always rethrow it
- Run `detekt` and `ktlint` before committing

### MUST NOT DO
- Block coroutines with `runBlocking` in production code (only in `main` or tests)
- Use `!!` without a documented reason
- Use `GlobalScope.launch` — use structured concurrency
- Mix platform-specific code into common/shared modules (KMP)
- Ignore coroutine cancellation
