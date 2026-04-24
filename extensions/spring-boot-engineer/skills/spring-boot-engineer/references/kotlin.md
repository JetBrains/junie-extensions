# Kotlin + Spring Boot — policy & pitfalls

Generic Kotlin / Spring knowledge is assumed (constructor injection, `data class`, `@RestController`). This file is the Kotlin-specific traps when using Spring.

## Required compiler plugins

| Plugin | Why |
|---|---|
| `kotlin("plugin.spring")` | Opens classes annotated with `@Component`, `@Service`, `@Configuration`, `@Transactional`, `@Async`, `@Cacheable`, `@SpringBootTest` — otherwise CGLIB proxies fail (Kotlin classes are `final` by default). |
| `kotlin("plugin.jpa")` | Generates a no-arg constructor for `@Entity`, `@Embeddable`, `@MappedSuperclass`. Without it: `InstantiationException: No default constructor for entity`. |

Also ensure `kotlin-reflect` is on the classpath (transitive from `spring-boot-starter`).

If you use MapStruct / custom annotations that require opening a class for proxying, add them to `allOpen` yourself:
```kotlin
allOpen {
    annotation("com.example.MyProxiedAnnotation")
}
```

## Bean Validation — `@field:` is mandatory

```kotlin
// ❌ Silently ignored — annotation targets constructor parameter, not backing field
data class Request(@NotBlank val name: String)

// ✅ Targets the field — Jakarta Validation picks it up
data class Request(@field:NotBlank val name: String)
```

Same rule for `@NotNull`, `@Size`, `@Email`, `@Pattern`, `@Min`, `@Max`, `@Valid` on nested properties.

## JPA entities in Kotlin

- Use a regular `class` (not `data class`) for `@Entity`. `data class` generates `equals` / `hashCode` / `toString` from all properties, which breaks on lazy associations (triggers loading) and on null IDs (every unsaved instance is "equal").
- `id` as `Long?` with default `null` — JPA assigns on flush.
- Mutable fields: `var`, nullable only where the column is nullable. Don't make everything `var` "to be safe" — it blows up encapsulation.
- No `companion object` with `toEntity` / `fromEntity` helpers on the entity itself — put mapping in a dedicated mapper class / extension functions. Keeps entity free of transitive dependencies.

## Coroutine controllers (WebFlux only, not MVC)

Suspend functions work in `@RestController` only when the app runs on WebFlux. In plain MVC they silently return `CompletableFuture` of the continuation — not what you want.

```kotlin
@GetMapping("/{id}")
suspend fun getById(@PathVariable id: Long): UserResponse = service.findById(id)

@GetMapping
fun stream(): Flow<UserResponse> = service.findAll()
```

- `Flow<T>` as return type → streamed response (analogous to `Flux<T>`).
- For parallel fan-out inside a handler use `coroutineScope { async { ... } }` — never `GlobalScope`.
- Blocking calls inside a `suspend` handler must be wrapped: `withContext(Dispatchers.IO) { blockingCall() }`.

## R2DBC + Coroutines

```kotlin
interface UserRepository : CoroutineCrudRepository<User, Long> {
    suspend fun findByEmail(email: String): User?
    fun findActive(): Flow<User>
}
```

- `CoroutineCrudRepository` returns `suspend` / `Flow` instead of `Mono` / `Flux`.
- `@Transactional` on a `suspend` method requires `ReactiveTransactionManager` (auto-wired when R2DBC is on classpath). Works, but don't mix with JPA in the same app.

## `@ConfigurationProperties` in Kotlin

```kotlin
@ConfigurationProperties(prefix = "app.jwt")
@Validated
data class JwtProperties(
    @field:NotBlank val secret: String,
    @field:Min(60000) val expiration: Long = 86400000,
)
```

- Enable with `@EnableConfigurationProperties(JwtProperties::class)` on a `@Configuration` class, or annotate the properties class itself with `@ConfigurationPropertiesScan` on the main app class.
- With Kotlin's immutable `val` properties, Spring binds via the canonical constructor — no setters needed. This is the recommended style.

## Common mistakes

- `@Autowired lateinit var` field injection → untestable, bypasses nullability. Always constructor injection.
- `data class` for a JPA entity → broken `equals` / `hashCode` → weird Set / cache behavior.
- `@Transactional` on a `final` class (default Kotlin) without `kotlin-spring` plugin → annotation silently ignored.
- Forgetting `@field:` on DTO validation → validation "works in tests with `Validator.validate(...)`" but is bypassed at the controller boundary (different target resolution).
- Using `runBlocking` inside a controller to call `suspend` code from MVC — blocks the servlet thread and defeats the point of coroutines. Either go full WebFlux or keep it synchronous.
