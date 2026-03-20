# Resilience4j — Fault Tolerance Patterns

## Dependencies

```xml
<!-- Maven -->
<dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-spring-boot3</artifactId>
    <version>2.2.0</version>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-aop</artifactId>
</dependency>
```

```kotlin
// Gradle (Kotlin DSL)
implementation("io.github.resilience4j:resilience4j-spring-boot3:2.2.0")
implementation("org.springframework.boot:spring-boot-starter-aop")

// For Kotlin suspend functions:
implementation("io.github.resilience4j:resilience4j-kotlin:2.2.0")
```

---

## Circuit Breaker

```java
@Service
@RequiredArgsConstructor
public class PaymentService {

    @CircuitBreaker(name = "paymentService", fallbackMethod = "paymentFallback")
    public PaymentResponse processPayment(PaymentRequest request) {
        return restTemplate.postForObject("http://payment-api/process",
            request, PaymentResponse.class);
    }

    private PaymentResponse paymentFallback(PaymentRequest request, Throwable ex) {
        return new PaymentResponse("PENDING", "Service temporarily unavailable");
    }
}
```

```yaml
resilience4j:
  circuitbreaker:
    configs:
      default:
        registerHealthIndicator: true
        slidingWindowSize: 10
        minimumNumberOfCalls: 5
        failureRateThreshold: 50          # % of failures to open
        waitDurationInOpenState: 10s
        permittedNumberOfCallsInHalfOpenState: 3
        automaticTransitionFromOpenToHalfOpenEnabled: true
    instances:
      paymentService:
        baseConfig: default
```

**States**: CLOSED (normal) → OPEN (failing, rejects calls) → HALF_OPEN (trial calls) → CLOSED

---

## Retry

```java
@Service
@RequiredArgsConstructor
public class ProductService {

    @Retry(name = "productService", fallbackMethod = "getProductFallback")
    public Product getProduct(Long productId) {
        return restTemplate.getForObject("/products/" + productId, Product.class);
    }

    private Product getProductFallback(Long productId, Throwable ex) {
        return new Product(productId, "Unavailable", false);
    }
}
```

```yaml
resilience4j:
  retry:
    configs:
      default:
        maxAttempts: 3
        waitDuration: 500ms
        enableExponentialBackoff: true
        exponentialBackoffMultiplier: 2
        retryExceptions:
          - java.io.IOException
          - java.util.concurrent.TimeoutException
        ignoreExceptions:
          - com.example.BusinessException  # Don't retry business errors
    instances:
      productService:
        baseConfig: default
        maxAttempts: 5
```

> **Warning**: Only retry idempotent operations. Never use `@Retry` on non-idempotent POST endpoints.

---

## Rate Limiter

```java
@Service
@RequiredArgsConstructor
public class NotificationService {

    @RateLimiter(name = "notificationService", fallbackMethod = "rateLimitFallback")
    public void sendEmail(EmailRequest request) {
        emailClient.send(request);
    }

    private void rateLimitFallback(EmailRequest request, Throwable ex) {
        throw new RateLimitExceededException("Too many requests. Retry after 1s.");
    }
}
```

```yaml
resilience4j:
  ratelimiter:
    instances:
      notificationService:
        limitForPeriod: 10       # max calls per period
        limitRefreshPeriod: 1s
        timeoutDuration: 500ms   # how long to wait for a permit
```

---

## Bulkhead

Use `SEMAPHORE` for synchronous methods, `THREADPOOL` for async/CompletableFuture:

```java
@Service
public class ReportService {

    @Bulkhead(name = "reportService", type = Bulkhead.Type.SEMAPHORE)
    public Report generateReport(ReportRequest request) {
        return reportGenerator.generate(request);
    }

    @Bulkhead(name = "analyticsService", type = Bulkhead.Type.THREADPOOL)
    public CompletableFuture<AnalyticsResult> runAnalytics(AnalyticsRequest request) {
        return CompletableFuture.supplyAsync(() -> analyticsEngine.analyze(request));
    }
}
```

```yaml
resilience4j:
  bulkhead:
    instances:
      reportService:
        maxConcurrentCalls: 5
        maxWaitDuration: 100ms
  thread-pool-bulkhead:
    instances:
      analyticsService:
        maxThreadPoolSize: 8
        coreThreadPoolSize: 4
```

---

## Time Limiter

```java
@Service
public class SearchService {

    @TimeLimiter(name = "searchService", fallbackMethod = "searchFallback")
    public CompletableFuture<SearchResults> search(SearchQuery query) {
        return CompletableFuture.supplyAsync(() -> searchEngine.execute(query));
    }

    private CompletableFuture<SearchResults> searchFallback(SearchQuery query, Throwable ex) {
        return CompletableFuture.completedFuture(SearchResults.empty("Search timed out"));
    }
}
```

```yaml
resilience4j:
  timelimiter:
    instances:
      searchService:
        timeoutDuration: 3s
        cancelRunningFuture: true
```

---

## Combining Patterns

Execution order: **Retry → CircuitBreaker → RateLimiter → Bulkhead → Method**

```java
@Service
public class OrderService {

    @CircuitBreaker(name = "orderService")
    @Retry(name = "orderService")
    @RateLimiter(name = "orderService")
    @Bulkhead(name = "orderService")
    public Order createOrder(OrderRequest request) {
        return orderClient.create(request);
    }
}
```

---

## Kotlin Suspend Functions

Annotation-based Resilience4j does **not** work on `suspend` functions — use the functional API:

```kotlin
@Service
class PaymentService(
    private val cbRegistry: CircuitBreakerRegistry,
    private val retryRegistry: RetryRegistry,
    private val webClient: WebClient,
) {
    private val cb    = cbRegistry.circuitBreaker("paymentService")
    private val retry = retryRegistry.retry("paymentService")

    suspend fun processPayment(request: PaymentRequest): PaymentResponse =
        retry.executeSuspendFunction {
            cb.executeSuspendFunction {
                webClient.post().uri("/process")
                    .bodyValue(request)
                    .retrieve()
                    .awaitBody<PaymentResponse>()
            }
        }
}
```

---

## Exception Handler for Resilience4j

```java
@RestControllerAdvice
public class ResilienceExceptionHandler {

    @ExceptionHandler(CallNotPermittedException.class)
    @ResponseStatus(HttpStatus.SERVICE_UNAVAILABLE)
    public ErrorResponse handleCircuitOpen(CallNotPermittedException ex) {
        return new ErrorResponse("SERVICE_UNAVAILABLE", "Service temporarily unavailable");
    }

    @ExceptionHandler(RequestNotPermitted.class)
    @ResponseStatus(HttpStatus.TOO_MANY_REQUESTS)
    public ErrorResponse handleRateLimited(RequestNotPermitted ex) {
        return new ErrorResponse("TOO_MANY_REQUESTS", "Rate limit exceeded");
    }

    @ExceptionHandler(BulkheadFullException.class)
    @ResponseStatus(HttpStatus.SERVICE_UNAVAILABLE)
    public ErrorResponse handleBulkheadFull(BulkheadFullException ex) {
        return new ErrorResponse("CAPACITY_EXCEEDED", "Service at capacity");
    }
}
```

## Monitoring (Actuator)

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,metrics,circuitbreakers,retries,ratelimiters
  endpoint:
    health:
      show-details: always
  health:
    circuitbreakers:
      enabled: true
```

Endpoints: `GET /actuator/circuitbreakers`, `GET /actuator/metrics/resilience4j.circuitbreaker.calls`

## Best Practices

- Always provide fallback methods with meaningful degraded responses
- Use exponential backoff for retries (`exponentialBackoffMultiplier: 2`)
- Set `failureRateThreshold` between 50–70% depending on error tolerance
- Only retry transient errors (network, 5xx) — never business exceptions (4xx)
- Size bulkheads from expected concurrent load × average latency
- Enable `registerHealthIndicator: true` on all instances for visibility
