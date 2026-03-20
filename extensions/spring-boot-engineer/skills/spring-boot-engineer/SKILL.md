---
name: spring-boot-engineer
description: Generates Spring Boot 3.x configurations, creates REST controllers, implements Spring Security 6 authentication flows, sets up Spring Data JPA repositories, configures reactive WebFlux endpoints, and applies Resilience4j fault-tolerance patterns. Use when building Spring Boot 3.x applications, microservices, or reactive Java/Kotlin applications.
---

# Spring Boot Engineer

## Core Workflow

1. **Analyze requirements** — Identify service boundaries, APIs, data models, security needs
2. **Design architecture** — Plan microservices, data access, cloud integration, security; confirm design before coding
3. **Implement** — Create services with constructor injection and layered architecture (see Quick Start below)
4. **Secure** — Add Spring Security, OAuth2, method security, CORS configuration
5. **Test** — Write unit, integration, and slice tests; confirm all pass before proceeding
6. **Deploy** — Configure health checks and observability via Actuator; validate `/actuator/health` returns `UP`

## Reference Guide

Load detailed guidance based on context:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Web Layer | `references/web.md` | Controllers, REST APIs, validation, exception handling |
| Data Access | `references/data.md` | Spring Data JPA, repositories, transactions, projections |
| Security | `references/security.md` | Spring Security 6, OAuth2, JWT, method security |
| Cloud Native | `references/cloud.md` | Spring Cloud, Config, Discovery, Gateway, resilience |
| Testing | `references/testing.md` | @SpringBootTest, MockMvc, Testcontainers, test slices |
| Kotlin | `references/kotlin.md` | Kotlin controllers, services, DTOs, coroutines, WebFlux suspend |
| Event-Driven | `references/event-driven.md` | Domain events, @TransactionalEventListener, Kafka, outbox pattern |
| Resilience | `references/resilience.md` | Circuit breaker, retry, rate limiter, bulkhead, time limiter |
| Reactive (WebFlux) | `references/reactive.md` | Mono/Flux operators, reactive controllers, SSE, anti-patterns |

## Quick Start — Minimal Working Structure

### Entity

```java
@Entity
@Table(name = "products")
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank
    private String name;

    @DecimalMin("0.0")
    private BigDecimal price;

    // getters / setters or use @Data (Lombok)
}
```

### Repository

```java
public interface ProductRepository extends JpaRepository<Product, Long> {
    List<Product> findByNameContainingIgnoreCase(String name);
}
```

### Service (constructor injection)

```java
@Service
public class ProductService {
    private final ProductRepository repo;

    public ProductService(ProductRepository repo) {
        this.repo = repo;
    }

    @Transactional(readOnly = true)
    public List<Product> search(String name) {
        return repo.findByNameContainingIgnoreCase(name);
    }

    @Transactional
    public Product create(ProductRequest request) {
        var product = new Product();
        product.setName(request.name());
        product.setPrice(request.price());
        return repo.save(product);
    }
}
```

### REST Controller

```java
@RestController
@RequestMapping("/api/v1/products")
@Validated
@RequiredArgsConstructor
public class ProductController {
    private final ProductService service;

    @GetMapping
    public List<ProductResponse> search(@RequestParam(defaultValue = "") String name) {
        return service.search(name);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ProductResponse create(@Valid @RequestBody ProductRequest request) {
        return service.create(request);
    }
}
```

### DTOs (records)

```java
public record ProductRequest(
    @NotBlank String name,
    @DecimalMin("0.0") BigDecimal price
) {}

public record ProductResponse(Long id, String name, BigDecimal price) {
    public static ProductResponse from(Product p) {
        return new ProductResponse(p.getId(), p.getName(), p.getPrice());
    }
}
```

### Global Exception Handler

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Validation failed");
        problem.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
            .map(e -> e.getField() + ": " + e.getDefaultMessage()).toList());
        return problem;
    }

    @ExceptionHandler(EntityNotFoundException.class)
    public ProblemDetail handleNotFound(EntityNotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    }
}
```

### Test Slice

```java
@WebMvcTest(ProductController.class)
class ProductControllerTest {
    @Autowired MockMvc mockMvc;
    @MockBean ProductService service;

    @Test
    void createProduct_validRequest_returns201() throws Exception {
        var product = new Product(); product.setName("Widget"); product.setPrice(BigDecimal.TEN);
        when(service.create(any())).thenReturn(product);

        mockMvc.perform(post("/api/v1/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""{"name":"Widget","price":10.0}"""))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.name").value("Widget"));
    }
}
```

## Constraints

### MUST DO

| Rule | Correct Pattern |
|------|----------------|
| Constructor injection | `public MyService(Dep dep) { this.dep = dep; }` |
| Validate API input | `@Valid @RequestBody MyRequest req` on every mutating endpoint |
| Type-safe config | `@ConfigurationProperties(prefix = "app")` bound to a record/class |
| Appropriate stereotype | `@Service` for business logic, `@Repository` for data, `@RestController` for HTTP |
| Transaction scope | `@Transactional` on multi-step writes; `@Transactional(readOnly = true)` on reads |
| Hide internals | Catch domain exceptions in `@RestControllerAdvice`; return problem details, not stack traces |
| Externalize secrets | Use environment variables or Spring Cloud Config — never `application.properties` |

### MUST NOT DO
- Use field injection (`@Autowired` on fields)
- Skip input validation on API endpoints
- Use `@Component` when `@Service`/`@Repository`/`@Controller` applies
- Mix blocking and reactive code (e.g., calling `.block()` inside a WebFlux chain)
- Store secrets or credentials in `application.properties`/`application.yml`
- Hardcode URLs, credentials, or environment-specific values
- Use deprecated Spring Boot 2.x patterns (e.g., `WebSecurityConfigurerAdapter`)
