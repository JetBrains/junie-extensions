# Resilience4j — policy & pitfalls

Generic knowledge of `@CircuitBreaker`, `@Retry`, `@RateLimiter`, `@Bulkhead`, `@TimeLimiter` is assumed. This file is about where they break.

## Annotation order matters

When stacking on the same method, the order (outer → inner) is:

```
@CircuitBreaker → @RateLimiter → @TimeLimiter → @Bulkhead → @Retry → method
```

Pick stacking order deliberately; most apps need at most `@CircuitBreaker` + `@Retry` + `@TimeLimiter`.

## `fallbackMethod`

- Must be in the **same class** as the annotated method.
- Same return type.
- Signature must accept the same parameters **plus one extra** `Throwable` (or a specific subtype) as the last parameter. One fallback per exception type is fine; resolution picks the most specific.
- Reactive methods (`Mono` / `Flux`): fallback must also return `Mono` / `Flux` — **never `.block()` inside fallback**.

## Proxy rules (same as `@Transactional`)

- Annotation only works on `public` non-final methods via the Spring proxy.
- **Self-invocation skips the advice** — call from another bean, or inject `self`.
- Kotlin: `kotlin-spring` plugin required so classes / methods are `open`.

## Retry

- Always exponential backoff with jitter: `wait-duration=200ms`, `exponential-backoff-multiplier=2`, `randomized-wait-factor=0.5`. Fixed-interval retry across many clients creates thundering herds.
- `retry-exceptions` / `ignore-exceptions` are checked by class. For idempotent operations only — **don't retry `POST` that mutates state** unless you have an idempotency key.
- `@Retry` + `@CircuitBreaker`: the circuit breaker counts each retry as a call. Prefer retrying **inside** the circuit breaker (default order above does this), or tune breaker thresholds.

## Circuit breaker

- `slidingWindowType=COUNT_BASED` with a small window (e.g. 10) reacts fast but is noisy; `TIME_BASED` is smoother for bursty traffic.
- `minimumNumberOfCalls` must be lower than `slidingWindowSize` — otherwise the breaker never evaluates. A common bug.
- `slowCallDurationThreshold` + `slowCallRateThreshold` are what actually catch "everything is timing out but still returns 200". Set them alongside `failureRateThreshold`.
- Breaker state is **per instance** — no cluster awareness. For shared state you need an external system (this is rarely worth it).

## Time limiter

- Required for reactive flows — `@CircuitBreaker` on a `Mono` won't detect hangs; only `@TimeLimiter` does.
- On blocking methods use `@TimeLimiter` with `CompletableFuture<T>` return type; it runs the call on a separate thread, which is cheap only up to a point — don't time-limit everything.

## Bulkhead

- `SemaphoreBulkhead` (default) — caps concurrent calls on the calling thread. Cheap.
- `ThreadPoolBulkhead` — isolates with a dedicated pool. Use sparingly; each bulkhead = separate pool.

## Rate limiter

- `@RateLimiter` throttles local callers — not a distributed rate limit. For cross-instance limiting you need Redis / Bucket4j + external storage.
- Default `timeoutDuration=5s` means the rate limiter **waits** for a permit. For strict fail-fast, set `timeoutDuration=0ms`.

## Observability

- Actuator endpoints `/actuator/circuitbreakers`, `/actuator/retries`, `/actuator/ratelimiters` show live state. Expose them behind auth.
- Micrometer metrics are published automatically when `spring-boot-starter-actuator` + Resilience4j are both on the classpath. Alert on `resilience4j.circuitbreaker.state{state="open"}`.

## Common mistakes

- Using `@Retry` on non-idempotent writes without idempotency keys — duplicate orders / charges.
- `fallbackMethod` lives in another class → `NoSuchMethodException` at startup.
- Wrapping a reactive chain with only `@CircuitBreaker` (no `@TimeLimiter`) → slow calls never count as failures.
- Stacking `@Retry` (say 3 attempts) on top of another `@Retry` upstream → combinatorial explosion (9 retries, 27...).
- Relying on `@RateLimiter` for distributed limiting.
