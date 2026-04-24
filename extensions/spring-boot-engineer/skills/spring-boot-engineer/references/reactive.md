# Reactive (WebFlux) — policy & pitfalls

Generic Reactor knowledge (`Mono`, `Flux`, `map`, `flatMap`, `subscribe`) is assumed. This file covers "when to use WebFlux at all" and the blocking traps that bite in prod.

## When to use WebFlux

Use it when **any** of these is true:

- Most of the request flow is waiting on I/O you can express reactively (non-blocking HTTP via `WebClient`, R2DBC, reactive Kafka / Redis).
- You need server-sent events (SSE) or streaming responses.
- You need very high concurrency with a small thread pool and the downstreams are fully non-blocking.

Use plain MVC otherwise. **Wrapping a blocking JDBC repo in `Mono.fromCallable(...).subscribeOn(boundedElastic())` is not WebFlux — it's MVC with extra steps and worse debugging.**

Spring Boot virtual threads (`spring.threads.virtual.enabled=true`, available since 3.2, standard in Boot 4.x) are often the better answer when you want "lots of concurrent blocking I/O" without rewriting everything reactively.

## Absolute rules

- **Never `.block()` / `.toFuture().get()` inside a reactive chain.** It pins the event-loop thread and will deadlock under load.
- **No blocking JDBC / `RestTemplate` / `Thread.sleep` on a WebFlux thread.** If you have to call blocking code, isolate it: `Mono.fromCallable(() -> blockingCall()).subscribeOn(Schedulers.boundedElastic())`.
- Never use `Schedulers.parallel()` for blocking work — it's a fixed small pool, made for CPU tasks. `boundedElastic()` is the "blocking I/O" scheduler (elastic, capped, thread-per-task-ish).
- Return `Mono<T>` / `Flux<T>` — don't invoke `.subscribe()` yourself inside a controller. Framework subscribes.

## Context & logging

- MDC doesn't propagate automatically across reactive operators. Use Micrometer's **Context Propagation** library (`io.micrometer:context-propagation`) + `Hooks.enableAutomaticContextPropagation()` — Spring Boot auto-wires this.
- Never store per-request data in `ThreadLocal` — the thread changes between operators. Pass through `ContextView` / Reactor `Context`.

## Backpressure

- Default: `Flux` propagates backpressure automatically through operators that support it. `Flux.fromIterable(...)` + `WebClient.bodyToFlux(...)` → fine.
- Hot producers (Kafka consumer, timer, WebSocket): wrap with explicit strategy — `.onBackpressureBuffer(size)`, `.onBackpressureDrop()`, `.onBackpressureLatest()`.
- `Sinks.many().multicast().onBackpressureBuffer()` for fan-out. Never share `Sinks.Many` across threads without `tryEmitNext` + retry loop — it's not thread-safe by default.

## Error handling

- `.onErrorResume(ex -> ...)` to recover with a fallback value.
- `.onErrorMap(ex -> new DomainException(...))` to translate (don't let `WebClient`'s `WebClientResponseException` leak into domain layer).
- `.retryWhen(Retry.backoff(3, Duration.ofMillis(200)))` — never bare `.retry(N)` without backoff (hammers a failing dependency).
- Exceptions swallowed by `subscribe()` without an error consumer — always provide `subscribe(next, error)` or let the framework handle it by returning the publisher.

## WebClient specifics

- Share one `WebClient` per external service (configured via `WebClient.Builder`) — don't `WebClient.create()` per request; you leak connections.
- Always set a timeout: `.responseTimeout(Duration.ofSeconds(5))` on the underlying `HttpClient` **and** `.timeout(Duration.ofSeconds(5))` on the `Mono` for total deadline.
- `bodyToMono(MyClass.class)` on an error status throws `WebClientResponseException` by default — use `.onStatus(HttpStatusCode::isError, resp -> ...)` to translate.

## R2DBC gotchas

- R2DBC is not a drop-in for JPA. No dirty checking, no lazy loading, explicit `save()` / `upsert()`.
- Transactions: `@Transactional` on WebFlux works but needs `ReactiveTransactionManager` (auto-configured when R2DBC is on the classpath).
- Don't mix JPA and R2DBC in the same service — connection pools collide, transactions don't compose.

## Common anti-patterns

| Anti-pattern | Correct |
|---|---|
| `mono.block()` to get a value in a controller | Return `Mono<T>` directly |
| `Flux.fromStream(stream).map(blockingCall)` | `.flatMap(x -> Mono.fromCallable(...).subscribeOn(boundedElastic()))` |
| `Mono.just(blockingCall())` | `Mono.fromCallable(() -> blockingCall()).subscribeOn(boundedElastic())` — `just` evaluates eagerly |
| `subscribe()` inside controller to "fire and forget" | Side effects belong in `.doOnNext` / `.then(...)` + return a publisher; truly fire-and-forget → publish to an event/queue |
| Creating `WebClient` per call | One `@Bean` per external service |
