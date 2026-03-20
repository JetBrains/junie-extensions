# Spring WebFlux — Reactive Patterns

## When to Use WebFlux vs MVC

| Factor | Spring MVC | Spring WebFlux |
|--------|-----------|----------------|
| I/O model | Thread-per-request | Non-blocking event loop |
| Blocking calls (JDBC, files) | Natural | Requires `Schedulers.boundedElastic()` |
| Database | JPA + Hibernate | R2DBC required |
| Best for | CRUD services, JPA | High-concurrency I/O, streaming, SSE |

> **Rule of thumb**: Using Spring Data JPA? Stay with MVC. Switch to WebFlux + R2DBC only for non-blocking end-to-end.

---

## Reactive Controller

```java
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping
    public Flux<UserResponse> getAll() {
        return userService.findAll();
    }

    @GetMapping("/{id}")
    public Mono<UserResponse> getById(@PathVariable Long id) {
        return userService.findById(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Mono<UserResponse> create(@Valid @RequestBody Mono<CreateUserRequest> request) {
        return request.flatMap(userService::create);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public Mono<Void> delete(@PathVariable Long id) {
        return userService.delete(id);
    }
}
```

## Reactive Service

```java
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;

    public Flux<UserResponse> findAll() {
        return userRepository.findAll().map(UserResponse::from);
    }

    public Mono<UserResponse> findById(Long id) {
        return userRepository.findById(id)
            .map(UserResponse::from)
            .switchIfEmpty(Mono.error(
                new ResponseStatusException(HttpStatus.NOT_FOUND, "User " + id + " not found")));
    }

    public Mono<UserResponse> create(CreateUserRequest request) {
        return userRepository.save(User.from(request)).map(UserResponse::from);
    }
}
```

## R2DBC Repository

```java
public interface UserRepository extends ReactiveCrudRepository<User, Long> {
    Mono<User> findByEmail(String email);
    Flux<User> findByActiveTrue();
}
```

---

## Essential Operators

```java
// Transform element
Mono<String> name = userMono.map(User::getName);

// Async transform (returns Mono/Flux)
Mono<Order> order = userMono.flatMap(user -> orderService.getLatest(user.getId()));

// Flat-map Flux
Flux<OrderItem> items = orderFlux.flatMap(order -> itemService.getItems(order.getId()));

// Filter
Flux<User> active = userFlux.filter(User::isActive);

// Default if empty
Mono<User> user = userRepository.findById(id)
    .switchIfEmpty(Mono.error(new NotFoundException("User not found")));

// Recover from error
Mono<User> safe = userRepository.findById(id)
    .onErrorReturn(User.anonymous());

// Parallel independent calls
Mono<DashboardResponse> dashboard = Mono.zip(
    userService.findById(userId),
    orderService.findLatest(userId),
    accountService.getBalance(userId)
).map(tuple -> new DashboardResponse(tuple.getT1(), tuple.getT2(), tuple.getT3()));

// Merge parallel streams
Flux<Event> events = Flux.merge(userEvents, orderEvents, paymentEvents);
```

---

## Error Handling

```java
// ✅ Lazy error — use Mono.defer to avoid eager evaluation
return Mono.defer(() -> Mono.error(new BusinessException("not allowed")));

// ❌ Eager error — exception created immediately, even if not subscribed
return Mono.error(new BusinessException("not allowed"));

// Map specific errors
Mono<User> result = userService.findById(id)
    .onErrorMap(DatabaseException.class, ex ->
        new ServiceException("Database unavailable", ex));

// Fallback on error
Mono<Config> config = configService.load()
    .onErrorResume(ex -> Mono.just(Config.defaults()));
```

---

## Blocking Code — Scheduler Rules

**Never** block on the Netty event loop thread. Offload to `boundedElastic`:

```java
// ❌ Blocks Netty event loop — deadlock risk
Mono<String> bad = Mono.just("path")
    .map(p -> Files.readString(Path.of(p)));  // blocking I/O

// ✅ Offload to boundedElastic scheduler
Mono<String> good = Mono.just("path")
    .publishOn(Schedulers.boundedElastic())
    .map(p -> Files.readString(Path.of(p)));

// ✅ Or wrap existing blocking call
Mono<String> wrapped = Mono.fromCallable(() -> Files.readString(Path.of("file.txt")))
    .subscribeOn(Schedulers.boundedElastic());
```

| Scheduler | Use for |
|-----------|---------|
| `boundedElastic()` | Blocking I/O (files, JDBC, legacy libs) |
| `parallel()` | CPU-intensive work |
| `single()` | Single-thread tasks |

---

## Server-Sent Events (SSE)

```java
@GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<String>> streamEvents() {
    return Flux.interval(Duration.ofSeconds(1))
        .map(seq -> ServerSentEvent.<String>builder()
            .id(String.valueOf(seq))
            .event("message")
            .data("Event #" + seq)
            .build());
}
```

## WebClient (non-blocking HTTP client)

```java
@Configuration
public class WebClientConfig {
    @Bean
    public WebClient webClient(WebClient.Builder builder) {
        return builder
            .baseUrl("https://api.example.com")
            .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
            .build();
    }
}

@Service
@RequiredArgsConstructor
public class ExternalApiService {
    private final WebClient webClient;

    public Mono<ExternalData> fetchData(String id) {
        return webClient.get()
            .uri("/data/{id}", id)
            .retrieve()
            .onStatus(HttpStatusCode::is4xxClientError, response ->
                Mono.error(new ResourceNotFoundException("Resource not found: " + id)))
            .onStatus(HttpStatusCode::is5xxServerError, response ->
                Mono.error(new ServiceUnavailableException("External service down")))
            .bodyToMono(ExternalData.class)
            .timeout(Duration.ofSeconds(5));
    }
}
```

---

## Anti-Patterns

```java
// ❌ .block() on Netty thread — deadlock
Mono<User> userMono = userService.findById(1L);
User user = userMono.block();  // Never do this inside a reactive chain

// ❌ subscribe() inside a reactive chain — detached stream, errors swallowed
return userMono.map(u -> {
    notificationService.sendEmail(u).subscribe();  // fire-and-forget — bad
    return u;
});
// ✅ Use flatMap instead
return userMono.flatMap(u ->
    notificationService.sendEmail(u).thenReturn(u));

// ❌ if/else in reactive chain — breaks operators
return userMono.map(user -> {
    if (user.isActive()) { return doA(user); }
    else { return doB(user); }
});
// ✅ Use filter / switchIfEmpty / flatMap
return userMono
    .filter(User::isActive)
    .flatMap(this::doA)
    .switchIfEmpty(userMono.flatMap(this::doB));

// ❌ Imperative throw in reactive chain
return userMono.map(user -> {
    if (!user.hasPermission()) throw new ForbiddenException();  // escapes chain
    return user;
});
// ✅ Lazy Mono.error via defer
return userMono.flatMap(user ->
    user.hasPermission()
        ? Mono.just(user)
        : Mono.defer(() -> Mono.error(new ForbiddenException())));
```

---

## Kotlin Coroutines with WebFlux

```kotlin
// build.gradle.kts
implementation("org.jetbrains.kotlinx:kotlinx-coroutines-reactor")
implementation("io.projectreactor.kotlin:reactor-kotlin-extensions")
```

```kotlin
@RestController
@RequestMapping("/api/v1/users")
class UserController(private val userService: UserService) {

    @GetMapping
    fun getAll(): Flow<UserResponse> = userService.findAll()  // Flux equivalent

    @GetMapping("/{id}")
    suspend fun getById(@PathVariable id: Long): UserResponse = userService.findById(id)

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    suspend fun create(@Valid @RequestBody request: CreateUserRequest): UserResponse =
        userService.create(request)
}

@Service
class UserService(private val userRepository: UserRepository) {

    fun findAll(): Flow<UserResponse> =
        userRepository.findAll().map { UserResponse.from(it) }

    suspend fun findById(id: Long): UserResponse =
        userRepository.findById(id)?.let { UserResponse.from(it) }
            ?: throw ResponseStatusException(HttpStatus.NOT_FOUND, "User $id not found")
}
```

### Reactor ↔ Coroutines Interop

```kotlin
val result: T  = mono.awaitSingle()
val nullable: T? = mono.awaitSingleOrNull()
val flow: Flow<T> = flux.asFlow()
val mono: Mono<T> = mono { suspendFunction() }
val flux: Flux<T> = flow.asFlux()

// Blocking I/O — use Dispatchers.IO
suspend fun readFile(path: String): String =
    withContext(Dispatchers.IO) { File(path).readText() }
```

---

## Backpressure — Processing Large Streams

Use `buffer` + `flatMap` with concurrency limit to process large datasets without overwhelming downstream:

```java
// Process in batches of 100, max 5 batches concurrently
Flux<Result> results = dataRepository.findAll()
    .buffer(100)
    .flatMap(batch -> processBatch(batch), 5);

// With delay between batches (rate limiting)
Flux<Result> throttled = dataRepository.findAll()
    .buffer(50)
    .delayElements(Duration.ofMillis(100))
    .flatMap(this::processBatch);

// Collect results
Mono<List<Result>> all = dataRepository.findAll()
    .buffer(100)
    .flatMap(batch -> processBatch(batch), 5)
    .collectList();
```

> Without a concurrency limit in `flatMap`, all buffers will be processed simultaneously — use the second argument to control parallelism.

## Testing Reactive Code

```java
// StepVerifier for Mono/Flux
@Test
void shouldFindUser() {
    StepVerifier.create(userService.findById(1L))
        .assertNext(user -> assertThat(user.id()).isEqualTo(1L))
        .verifyComplete();
}

// WebTestClient for controllers
@WebFluxTest(UserController.class)
class UserControllerTest {
    @Autowired WebTestClient webTestClient;
    @MockBean  UserService   userService;

    @Test
    void shouldReturnUser() {
        when(userService.findById(1L)).thenReturn(Mono.just(new UserResponse(1L, "Alice")));

        webTestClient.get().uri("/api/v1/users/1")
            .exchange()
            .expectStatus().isOk()
            .expectBody(UserResponse.class)
            .value(u -> assertThat(u.name()).isEqualTo("Alice"));
    }
}
```
