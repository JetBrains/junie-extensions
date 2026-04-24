---
name: spring-boot-engineer
description: "Use when building, modifying, or reviewing Spring Boot 4.x applications (Spring Framework 7, Spring Security 7, Hibernate 7, Jackson 3) in Java or Kotlin — REST controllers, Spring Data JPA repositories, OAuth2 / JWT, WebFlux reactive endpoints, Kafka / event-driven code, Resilience4j, Spring Cloud, or Spring Boot tests. Covers common pitfalls that break in production: @Transactional self-invocation, N+1 queries, Kotlin + JPA plugins, blocking calls inside WebFlux. Migrating from Boot 3.x? See Setup Check — major breaking changes: Jackson 3 package rename, @MockBean removed, and() in Security DSL removed, Undertow dropped."
---

# Spring Boot Engineer

## Core Workflow

1. **Setup check** — run Setup Check below before writing any code.
2. **Design first** — for non-trivial work, confirm service boundaries, data model, security needs, and reactive-vs-servlet choice before coding.
3. **Implement bottom-up** — entity → repository → service → controller. Constructor injection only. Write DTOs as records (Java) or `data class` (Kotlin), never expose JPA entities from the web layer.
4. **Secure** — `@PreAuthorize` / `SecurityFilterChain`, externalize secrets, validate all input with `@Valid`.
5. **Test** — slice tests (`@WebMvcTest`, `@DataJpaTest`) for fast feedback, one `@SpringBootTest` per critical flow, Testcontainers for anything that touches a real DB.
6. **Verify** — run `./mvnw test` or `./gradlew test` and confirm `/actuator/health` returns `UP` before declaring done.

## Setup Check

**Mandatory before any code change.**

### Step 1 — Is this actually a Spring Boot project?

Look for one of these, in this order:

- `spring-boot-starter-parent` or `spring-boot-dependencies` in `pom.xml`.
- `org.springframework.boot` plugin in `build.gradle` / `build.gradle.kts`.
- A class annotated with `@SpringBootApplication`.

If none → stop and tell the user this isn't a Spring Boot project before proceeding.

### Step 2 — Kotlin project? Verify required compiler plugins.

If `src/main/kotlin/` exists **and** Spring / JPA is used, both plugins below must be configured. Without them Spring proxies and JPA entities fail at runtime with cryptic errors:

| Plugin | Why it's needed |
|---|---|
| `kotlin("plugin.spring")` (`kotlin-spring`) | Opens classes annotated with `@Component` / `@Service` / `@Configuration` / `@Transactional` / `@Async` / `@Cacheable` / `@SpringBootTest` — CGLIB proxies cannot subclass `final` classes. |
| `kotlin("plugin.jpa")` (`kotlin-jpa`) | Generates a no-arg constructor for `@Entity` / `@Embeddable` / `@MappedSuperclass`. Required for JPA to instantiate entities via reflection. |

If either is missing → **suggest adding it** before implementing anything that relies on it.

```kotlin
plugins {
    kotlin("plugin.spring") version "<kotlin-version>"
    kotlin("plugin.jpa")    version "<kotlin-version>"
}
```

Also confirm `kotlin-reflect` is on the classpath (included by `spring-boot-starter`).

### Step 3 — Java version & runtime

Spring Boot 4.x requires **Java 17+** (Java 21+ recommended — first-class virtual thread support). Check `<java.version>` (Maven) or `java.toolchain` / `sourceCompatibility` (Gradle).

Virtual threads: enable via `spring.threads.virtual.enabled=true`. Don't use them unconditionally — harmful with `synchronized` blocks and `ThreadLocal`-heavy libraries.

**Undertow is no longer supported** in Boot 4 (dropped Servlet 6.1 compatibility). Use Tomcat (default) or Jetty.

### Step 4 — Jackson version

Spring Boot 4 defaults to **Jackson 3**. The package was renamed: `com.fasterxml.jackson` → `tools.jackson`. Any code importing Jackson classes directly will break. A `jackson-databind-compat` bridge module exists for gradual migration, but plan to update imports. If the project already uses Jackson 3 → proceed. If still on Jackson 2 → flag the migration before adding new Jackson-dependent code.

## Reference Guide

Load on demand — don't read all of these upfront.

| Topic | Reference | Load when |
|-------|-----------|-----------|
| Web Layer | `references/web.md` | Controllers, DTO boundary, validation, `ProblemDetail`, pagination, CORS, deprecations |
| Data Access | `references/data.md` | JPA / Hibernate pitfalls: N+1, `open-in-view`, `@Transactional` self-invocation, fetch-join + pagination, Hikari tuning |
| Security | `references/security.md` | Spring Security 7 `SecurityFilterChain`, CSRF rules, JWT resource server, method security, `/actuator/*` hardening |
| Testing | `references/testing.md` | Test slices (`@WebMvcTest` / `@DataJpaTest` / `@RestClientTest`), `@MockitoBean` migration, Testcontainers + `@ServiceConnection` |
| Migrations | `references/migrations.md` | Flyway / Liquibase, zero-downtime schema change (expand-contract), baseline-on-migrate, `CREATE INDEX CONCURRENTLY` |
| Scheduling & Observability | `references/scheduling-observability.md` | `@Scheduled` in a cluster (ShedLock), Actuator exposure, health probes, Micrometer cardinality, virtual threads trade-offs |
| Kotlin | `references/kotlin.md` | `kotlin-spring` / `kotlin-jpa` plugins, `@field:` validation, `suspend` controllers, `data class` vs `@Entity` |
| Event-Driven | `references/event-driven.md` | `@TransactionalEventListener`, `@Async` traps, Kafka idempotence, outbox pattern |
| Resilience | `references/resilience.md` | Resilience4j annotation order, `fallbackMethod` rules, breaker + retry interaction, distributed vs local rate-limit |
| Reactive (WebFlux) | `references/reactive.md` | When WebFlux is the right choice, `.block()` traps, `Schedulers.boundedElastic()`, context propagation, backpressure |
| Cloud Native | `references/cloud.md` | `spring.config.import` (not `bootstrap.yml`), `@RefreshScope` limits, Gateway on WebFlux, k8s vs Spring Cloud choice |

## Constraints

### MUST DO

| Rule | Correct pattern |
|------|-----------------|
| Constructor injection | `public MyService(Dep dep) { this.dep = dep; }` — never `@Autowired` on a field |
| Validate every mutating endpoint | `@Valid @RequestBody MyRequest req` + Bean Validation annotations on the DTO |
| DTOs at the web boundary | Java `record` or Kotlin `data class` — **never** return or accept JPA entities directly |
| Type-safe config | `@ConfigurationProperties(prefix = "app")` bound to a record/class, not `@Value("${…}")` scattered across the codebase |
| Correct stereotype | `@Service` for business logic, `@Repository` for data, `@RestController` for HTTP, `@Component` only when nothing else fits |
| Transaction scope | `@Transactional` only on `public` methods of a Spring-managed bean, called from outside the class (see MUST NOT below) |
| Read-only hint | `@Transactional(readOnly = true)` on queries — lets Hibernate skip dirty-checking |
| Rollback on checked exceptions | `@Transactional(rollbackFor = Exception.class)` when the method throws checked exceptions you want to roll back |
| Global error handling | `@RestControllerAdvice` + `ProblemDetail` (RFC 7807) — never leak stack traces to clients |
| Externalize secrets | Env vars or Spring Cloud Config — never commit secrets to `application.properties` / `application.yml` |
| Kotlin + Spring | `kotlin("plugin.spring")` always; `kotlin("plugin.jpa")` when JPA is used |
| Kotlin validation | `@field:NotBlank` on `data class` properties — bare `@NotBlank` is silently ignored |
| Post-commit side effects | `@TransactionalEventListener(phase = AFTER_COMMIT)` for email / Kafka / external calls — never inline after a `save()` inside the same transaction |

### MUST NOT — `@Transactional` pitfalls that break in production

- **Self-invocation.** Calling `this.methodWithTransactional()` from another method in the same bean bypasses the proxy — no transaction starts. If you need it, inject `self` (`@Lazy @Autowired MyService self`) or extract the method to a separate bean.
- **Private / package-private / `final` methods.** Proxies cannot intercept them. `@Transactional` must be on `public` non-`final` methods. (In Kotlin: add `kotlin-spring` plugin so classes/methods are open.)
- **Checked exceptions without `rollbackFor`.** By default Spring rolls back only on `RuntimeException` / `Error`. Declare `@Transactional(rollbackFor = IOException.class)` (or a common superclass) when you want checked exceptions to roll back.
- **`@Async` + `@Transactional` on the same method.** The async thread doesn't inherit the transaction context — entity becomes detached, you get `LazyInitializationException` or no transaction at all. Split into two beans or use `@TransactionalEventListener(phase = AFTER_COMMIT)`.
- **Writes inside `readOnly = true`.** Hibernate may skip the flush — your update silently disappears.
- **`@Transactional` on a `@PostConstruct` method.** Proxy isn't fully initialized yet; the annotation has no effect.

### MUST NOT — general

- Field injection (`@Autowired` on fields) — breaks testability and hides required dependencies.
- Skipping `@Valid` on API input — request bodies reach your service with whatever the client sent.
- Using `@Component` when a more specific stereotype fits.
- Mixing blocking and reactive code: no `.block()` / `.toFuture().get()` inside a `Mono` / `Flux` chain; no blocking JDBC inside a WebFlux controller. Wrap unavoidable blocking calls with `Mono.fromCallable(...).subscribeOn(Schedulers.boundedElastic())`.
- Storing secrets, connection strings or tokens in `application.properties` / `application.yml` committed to git.
- Hardcoding URLs / environment-specific values — use profiles (`application-dev.yml`, `application-prod.yml`) and env vars.
- Removed Boot 3.x deprecated APIs — all of these are gone in Boot 4 and will fail to compile:
  - `WebSecurityConfigurerAdapter` (use `SecurityFilterChain` bean)
  - `antMatchers(...)` (use `requestMatchers(...)`)
  - `WebMvcConfigurerAdapter` (implement `WebMvcConfigurer`)
  - `and()` in `HttpSecurity` DSL (use separate lambda calls)
  - `@MockBean` / `@SpyBean` (use `@MockitoBean` / `@MockitoSpyBean`)
  - `authorizeRequests()` (use `authorizeHttpRequests()`)
- **Jackson 3 imports**: `com.fasterxml.jackson.*` → `tools.jackson.*`. Don't write new code against Jackson 2 packages on a Boot 4 project.
- Undertow embedded server — not supported. Don't add `spring-boot-starter-undertow`.
- Returning or accepting JPA entities at the controller layer — leaks persistence details, causes lazy-loading blowups (`could not initialize proxy — no Session`), breaks API contracts on entity refactors.
- N+1 queries: `repository.findAll()` followed by accessing `@OneToMany` lazy associations in a loop. Use `@EntityGraph`, `JOIN FETCH`, or projections. See `references/data.md`.
- `spring.jpa.open-in-view=true` in production (the Spring Boot default!). Explicitly set it to `false` — OSIV hides lazy-loading bugs and holds the DB connection for the entire HTTP request.

## Output Format

When implementing a new feature, deliver in this order:
1. Migration (Flyway / Liquibase) if schema changes are needed.
2. Entity + Repository.
3. Service with `@Transactional` boundaries.
4. DTOs (request + response) as records / data classes.
5. Controller + `@RestControllerAdvice` entries for new exception types.
6. Tests: one `@DataJpaTest` for repository custom queries, one `@WebMvcTest` per controller, one `@SpringBootTest` for the full happy path.
7. One-line summary of the key architectural decisions (why this transaction boundary, why this projection, why this status code).
