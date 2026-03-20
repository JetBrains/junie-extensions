# Java 21 — Language Features & Idioms

## Records

```java
// Immutable data carrier — generates constructor, accessors, equals, hashCode, toString
public record Money(BigDecimal amount, Currency currency) {
    // Compact constructor for validation
    public Money {
        Objects.requireNonNull(amount);
        if (amount.compareTo(BigDecimal.ZERO) < 0) throw new IllegalArgumentException("negative amount");
    }

    public Money add(Money other) {
        if (!currency.equals(other.currency)) throw new IllegalArgumentException("currency mismatch");
        return new Money(amount.add(other.amount), currency);
    }
}

// Use records for DTOs and value objects — not for mutable JPA entities
public record UserCreateRequest(
    @NotBlank String email,
    @NotBlank @Size(min = 8) String password
) {}
```

## Sealed Classes & Pattern Matching

```java
// Sealed hierarchy — exhaustive, compiler-enforced
public sealed interface PaymentResult
    permits PaymentResult.Success, PaymentResult.Failure, PaymentResult.Pending {}

public record Success(String transactionId) implements PaymentResult {}
public record Failure(String reason, ErrorCode code) implements PaymentResult {}
public record Pending(String referenceId) implements PaymentResult {}

// Pattern matching switch — no default needed when all permits are handled
String message = switch (result) {
    case Success s  -> "Paid: " + s.transactionId();
    case Failure f  -> "Failed: " + f.reason();
    case Pending p  -> "Pending: " + p.referenceId();
};

// Pattern matching instanceof — eliminates explicit cast
if (result instanceof Failure f && f.code() == ErrorCode.INSUFFICIENT_FUNDS) {
    log.warn("Insufficient funds for reference {}", f.referenceId());
}
```

## Switch Expressions

```java
// Arrow form — no fall-through, expression yields a value
int discount = switch (customer.tier()) {
    case GOLD    -> 20;
    case SILVER  -> 10;
    case BRONZE  -> 5;
    default      -> 0;
};

// yield for multi-statement branches
String label = switch (status) {
    case ACTIVE -> "Active";
    case INACTIVE -> {
        log.debug("Inactive customer: {}", customer.id());
        yield "Inactive";
    }
};
```

## Text Blocks

```java
String json = """
        {
            "name": "%s",
            "email": "%s"
        }
        """.formatted(user.name(), user.email());

String sql = """
        SELECT u.id, u.email
        FROM users u
        WHERE u.active = true
          AND u.created_at >= :since
        ORDER BY u.created_at DESC
        """;
```

## Virtual Threads (Java 21)

```java
// Structured concurrency — tasks live within the scope's lifetime
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Future<User>  user    = scope.fork(() -> userService.findById(userId));
    Future<Order> order   = scope.fork(() -> orderService.findLatest(userId));

    scope.join().throwIfFailed();

    return new DashboardResponse(user.get(), order.get());
}

// Virtual thread executor — cheap, non-pinning I/O concurrency
ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
```

## Streams

```java
// Transform + filter + collect
List<String> emails = users.stream()
    .filter(User::isActive)
    .map(User::email)
    .toList();  // Unmodifiable list, Java 16+

// Grouping
Map<Department, List<Employee>> byDept = employees.stream()
    .collect(Collectors.groupingBy(Employee::department));

// FlatMap for nested collections
List<String> allTags = posts.stream()
    .flatMap(post -> post.tags().stream())
    .distinct()
    .toList();

// Reduction
BigDecimal total = items.stream()
    .map(Item::price)
    .reduce(BigDecimal.ZERO, BigDecimal::add);

// ❌ Avoid complex nested streams — use loops for readability when logic exceeds 3 steps
```

## Optional

```java
// ✅ Return Optional from find* methods — signals "may be absent"
Optional<User> user = userRepository.findByEmail(email);

// ✅ Chain transformations
return userRepository.findByEmail(email)
    .map(UserResponse::from)
    .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));

// ✅ Default value
String displayName = user.map(User::displayName).orElse("Anonymous");

// ❌ Never use Optional as method parameter or field — only as return type
// ❌ Never call .get() without isPresent() check — use map/orElseThrow
```

## Generics & Type Safety

```java
// Bounded type parameter
public <T extends Comparable<T>> T max(List<T> items) {
    return items.stream().max(Comparator.naturalOrder())
        .orElseThrow(() -> new IllegalArgumentException("empty list"));
}

// Wildcard for read-only collections
public void printAll(List<? extends Shape> shapes) {
    shapes.forEach(s -> System.out.println(s.area()));
}

// Generic repository pattern
public interface Repository<T, ID> {
    Optional<T> findById(ID id);
    T save(T entity);
    void deleteById(ID id);
}

// ❌ Avoid raw types — always declare type parameters
```

## Exceptions

```java
// Domain-specific unchecked exceptions
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) { super(message); }
    public ResourceNotFoundException(String message, Throwable cause) { super(message, cause); }
}

// ✅ Wrap technical exceptions with context
try {
    return externalClient.fetch(id);
} catch (HttpClientErrorException ex) {
    throw new ResourceNotFoundException("External resource not found: " + id, ex);
}

// ✅ Fail fast — validate at boundaries
public Order createOrder(CreateOrderRequest request) {
    if (request.items().isEmpty()) throw new IllegalArgumentException("Order must have items");
    // ...
}

// ❌ Avoid catching Exception broadly unless logging+rethrowing
// ❌ Never swallow exceptions silently
```

## Naming & Style

```java
// Classes, Records, Interfaces: PascalCase
public class OrderService {}
public record Money(BigDecimal amount, Currency currency) {}
public interface PaymentGateway {}

// Methods, fields: camelCase
private final UserRepository userRepository;
public Optional<User> findByEmail(String email) {}

// Constants: UPPER_SNAKE_CASE
private static final int MAX_RETRY_ATTEMPTS = 3;
private static final Duration TIMEOUT = Duration.ofSeconds(5);

// Boolean methods: is/has/can prefix
public boolean isActive() {}
public boolean hasPermission(String role) {}
```

## Immutability

```java
// ✅ Final fields by default
public class UserService {
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public UserService(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }
}

// ✅ Unmodifiable collections
private static final List<String> ALLOWED_ROLES = List.of("ADMIN", "USER", "MODERATOR");

// ✅ Copy on intake to prevent aliasing
public Order(List<OrderItem> items) {
    this.items = List.copyOf(items);
}
```

## Logging

```java
private static final Logger log = LoggerFactory.getLogger(OrderService.class);

// ✅ Structured — stable field names, parameterized
log.info("order_created orderId={} customerId={} total={}", order.id(), order.customerId(), order.total());
log.warn("payment_failed orderId={} reason={}", orderId, reason);
log.error("unexpected_error orderId={}", orderId, ex);  // exception as last arg

// ❌ Never log PII (emails, phone, address), tokens, or raw passwords
// ❌ No string concatenation in log calls — always use parameterized form
```

## Null Handling

```java
// ✅ Use @NonNull / @Nullable to document intent at API boundaries
public UserResponse findById(@NonNull Long id) { ... }
public @Nullable String getNickname() { ... }

// ✅ Validate parameters early
public void process(@NonNull Order order, @NonNull String currency) {
    Objects.requireNonNull(order, "order must not be null");
    Objects.requireNonNull(currency, "currency must not be null");
}
```

## Code Smells to Avoid

- Long parameter lists → use a request record or builder
- Deep nesting → early returns and guard clauses
- Magic numbers/strings → named constants
- Static mutable state → dependency injection
- Silent catch blocks → log and rethrow or convert to domain exception
- `instanceof` chains → sealed classes with switch

## Testing Standards

```java
// JUnit 5 + AssertJ
@Test
void shouldRejectNegativeAmount() {
    assertThatThrownBy(() -> new Money(new BigDecimal("-1"), Currency.getInstance("USD")))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("negative amount");
}

@Test
void shouldAddMoneyOfSameCurrency() {
    Money a = new Money(new BigDecimal("10.00"), Currency.getInstance("USD"));
    Money b = new Money(new BigDecimal("5.50"), Currency.getInstance("USD"));

    assertThat(a.add(b).amount()).isEqualByComparingTo("15.50");
}
```

- Mockito for dependencies; avoid partial mocks (spy) unless unavoidable
- Test method names: `should<ExpectedBehavior>[When<Condition>]`
- One assertion focus per test — multiple `assertThat` on the same result is fine
