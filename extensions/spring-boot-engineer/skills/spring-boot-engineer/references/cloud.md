# Spring Cloud — policy & pitfalls

Generic knowledge of Spring Cloud Config, Service Discovery (Eureka / Consul), Spring Cloud Gateway is assumed. This file is "the things tutorials don't warn you about".

## `bootstrap.yml` is gone

- Since Spring Cloud 2020.0 / Spring Boot 2.4, `bootstrap.yml` is **deprecated**. Use `spring.config.import` in `application.yml` instead:
  ```yaml
  spring:
    config:
      import: "optional:configserver:http://config-server:8888"
  ```
- `optional:` prefix prevents the app from failing to start when the config server is unreachable — critical for non-prod environments.

## Spring Cloud Config

- Config server serves files from a Git repo or filesystem. **Refresh at runtime requires `@RefreshScope` beans** + POST to `/actuator/refresh` (or Spring Cloud Bus for fan-out).
- Not every bean likes `@RefreshScope` — database connection pools, `@Scheduled` tasks, thread pools do **not** refresh cleanly. Put only simple config beans / `@ConfigurationProperties` classes in refresh scope.
- Encrypt secrets at rest (`{cipher}` prefix with server-side key) or use Vault — never plain text in a Git repo, even a private one.

## Service discovery

- Eureka's self-preservation mode hides stale instances on network partition — good for production, confusing in dev. Disable in dev profile: `eureka.server.enable-self-preservation=false`.
- Client-side load balancing via Spring Cloud LoadBalancer (the `RibbonLoadBalancer` successor). Register `WebClient` / `RestClient` with `@LoadBalanced` to resolve `http://service-name/...` URLs.
- **On Kubernetes, prefer Kubernetes-native service discovery (DNS) over Eureka.** Running Eureka inside k8s adds an extra layer that duplicates what k8s already does. Use `spring-cloud-kubernetes-discovery` or just plain DNS.

## Spring Cloud Gateway

- `Gateway` is built on WebFlux — the **whole gateway process** must be non-blocking. Don't stick blocking filters (JDBC, `RestTemplate`, sync `AuthService`) into a `GlobalFilter`; wrap with `Mono.fromCallable(...).subscribeOn(boundedElastic())` or keep auth logic out of the gateway.
- Don't mix `spring-boot-starter-web` with gateway on the same classpath — MVC autoconfig fights WebFlux. Build gateway as a dedicated service.
- For stateful routing decisions, use `RouteLocator` bean, not YAML — YAML is static, bean version can read from config server / DB.

## Correlation & tracing

- Use **Micrometer Tracing** (Boot 3.x+) or the new **`spring-boot-starter-opentelemetry`** (Boot 4.x). Spring Cloud Sleuth is retired — do not use. Micrometer Tracing wires across MVC, WebFlux, RestClient, WebClient, Kafka, R2DBC automatically.
- In Boot 4 with the OpenTelemetry starter, tracing is exported via OTLP automatically; no Sleuth or manual bridge needed.
- For log correlation in MDC, pattern: `%X{traceId:-},%X{spanId:-}`. Ensure context propagation works across reactive / async boundaries (see `reactive.md`).

## When to use Spring Cloud at all

- On Kubernetes: most of Spring Cloud becomes redundant (k8s handles discovery, config via ConfigMap / Secret, gateway via Ingress / Istio). Use Spring Cloud for the parts that truly help — tracing, resilience4j, OpenFeign — not the full suite.
- On bare VMs without orchestration: Spring Cloud makes sense end-to-end.
- Decide once, per-project. Don't drag Eureka + Config Server + Gateway into a 3-service monolith.

## Common mistakes

- `bootstrap.yml` still present in a Spring Boot 3/4 project → silently ignored (legacy bootstrap context removed since Boot 2.4), config never loads.
- `@RefreshScope` on `DataSource` / `EntityManagerFactory` / `TaskExecutor` — refresh either does nothing or corrupts state.
- Running Gateway with `spring-boot-starter-web` (MVC) — it starts on Netty but MVC autoconfig leaks, causing hangs.
- Hard-coding `http://localhost:8761/eureka/` in production — use service-specific profiles or environment variables.
- Skipping `optional:` on `spring.config.import` → app won't start when config server is temporarily down.
