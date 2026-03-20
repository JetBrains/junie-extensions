# Kotlin — Spring Boot Patterns

## Controller

```kotlin
@RestController
@RequestMapping("/api/v1/users")
class UserController(private val userService: UserService) {

    @GetMapping
    fun getAll(): List<UserResponse> = userService.findAll()

    @GetMapping("/{id}")
    fun getById(@PathVariable id: Long): ResponseEntity<UserResponse> =
        ResponseEntity.ok(userService.findById(id))

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    fun create(@Valid @RequestBody request: CreateUserRequest): UserResponse =
        userService.create(request)

    @PutMapping("/{id}")
    fun update(@PathVariable id: Long, @Valid @RequestBody request: UpdateUserRequest): UserResponse =
        userService.update(id, request)

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    fun delete(@PathVariable id: Long) = userService.delete(id)
}
```

## Service (constructor injection — no @RequiredArgsConstructor needed)

```kotlin
@Service
@Transactional(readOnly = true)
class UserService(
    private val userRepository: UserRepository,
    private val userMapper: UserMapper,
) {
    fun findAll(): List<UserResponse> = userRepository.findAll().map(userMapper::toResponse)

    fun findById(id: Long): UserResponse =
        userRepository.findById(id)
            .map(userMapper::toResponse)
            .orElseThrow { ResourceNotFoundException("User", id) }

    @Transactional
    fun create(request: CreateUserRequest): UserResponse {
        val user = userMapper.toEntity(request)
        return userMapper.toResponse(userRepository.save(user))
    }

    @Transactional
    fun delete(id: Long) {
        if (!userRepository.existsById(id)) throw ResourceNotFoundException("User", id)
        userRepository.deleteById(id)
    }
}
```

## DTOs — use `@field:` prefix for Bean Validation

```kotlin
// Request DTO
data class CreateUserRequest(
    @field:NotBlank(message = "Name is required")
    @field:Size(min = 2, max = 100)
    val name: String,

    @field:Email(message = "Invalid email format")
    @field:NotBlank
    val email: String,

    @field:Min(18)
    val age: Int,
)

// Response DTO — immutable data class
data class UserResponse(
    val id: Long,
    val name: String,
    val email: String,
    val createdAt: LocalDateTime,
)
```

> **Rule**: Always use `@field:` in Kotlin data classes. Without it, the annotation targets the constructor parameter, not the backing field — Bean Validation silently skips it.

## Configuration Properties

```kotlin
@ConfigurationProperties(prefix = "app.jwt")
@Validated
data class JwtProperties(
    @field:NotBlank val secret: String,
    @field:Min(60000) val expiration: Long = 86400000,
)
```

## Entity

```kotlin
@Entity
@Table(name = "users")
class User(
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long? = null,           // nullable — assigned by DB

    @Column(nullable = false)
    var name: String,

    @Column(nullable = false, unique = true)
    var email: String,
)
```

> Prefer mutable `var` for fields JPA needs to set. Keep `id` as `Long?` and never set it manually.

## Anti-Patterns

```kotlin
// ❌ lateinit for repository — use constructor injection
@Service
class UserService {
    @Autowired lateinit var userRepository: UserRepository  // Bad
}

// ✅ constructor injection
@Service
class UserService(private val userRepository: UserRepository)

// ❌ @NotBlank without @field: — silently ignored
data class Request(@NotBlank val name: String)

// ✅
data class Request(@field:NotBlank val name: String)
```

---

## Kotlin + Coroutines (WebFlux)

> For reactive Spring WebFlux with coroutines, see `references/reactive.md` → Kotlin section.

### Suspend Controller (WebFlux only)

```kotlin
@RestController
@RequestMapping("/api/v1/users")
class UserController(private val userService: UserService) {

    @GetMapping
    fun getAll(): Flow<UserResponse> = userService.findAll()

    @GetMapping("/{id}")
    suspend fun getById(@PathVariable id: Long): UserResponse = userService.findById(id)

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    suspend fun create(@Valid @RequestBody request: CreateUserRequest): UserResponse =
        userService.create(request)
}
```

### Coroutine Repository (R2DBC)

```kotlin
interface UserRepository : CoroutineCrudRepository<User, Long> {
    suspend fun findByEmail(email: String): User?
    fun findByActiveTrue(): Flow<User>
}
```

### Parallel Calls with coroutineScope

```kotlin
suspend fun getDashboard(userId: Long): DashboardResponse = coroutineScope {
    val user    = async { userService.findById(userId) }
    val orders  = async { orderService.findByUser(userId) }
    val balance = async { accountService.getBalance(userId) }
    DashboardResponse(user.await(), orders.await(), balance.await())
}
```

### Blocking Code — use Dispatchers.IO

```kotlin
// ❌ Never block on the WebFlux event loop
suspend fun bad(): String = File("data.txt").readText()

// ✅ Offload to IO dispatcher
suspend fun good(): String = withContext(Dispatchers.IO) { File("data.txt").readText() }
```
