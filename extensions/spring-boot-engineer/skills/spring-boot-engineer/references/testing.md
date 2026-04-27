# Testing — policy & pitfalls

Generic knowledge of JUnit 5, Mockito, MockMvc, `@SpringBootTest` is assumed. This file covers which test slice to use, and the Spring-specific traps.

## Pick the right slice — avoid `@SpringBootTest` by default

| Goal | Annotation | Loads |
|---|---|---|
| Controller + filters + `@RestControllerAdvice` | `@WebMvcTest(MyController.class)` | Web layer only, no repositories |
| Repository queries + Flyway migrations | `@DataJpaTest` | JPA + embedded / Testcontainers DB |
| `WebClient` / `@HttpExchange` mock | `@RestClientTest` | `MockRestServiceServer`, no full context |
| JSON serialization | `@JsonTest` | Just `ObjectMapper` + custom serializers |
| Full happy path through real beans | `@SpringBootTest` | Everything — slow, use sparingly |

Rule: one `@SpringBootTest` per critical end-to-end flow, not per test class.

## `@MockBean` / `@SpyBean` removed (Spring Boot 4.0)

- **Removed** in Boot 4.0 — will not compile. Use `@MockitoBean` / `@MockitoSpyBean` (from `org.springframework.test.context.bean.override.mockito`).
- Were deprecated in Boot 3.4; fully removed in Boot 4.0.
- In Kotlin, if your production class is `final`, Mockito needs `mockito-inline` (and `kotlin-spring` plugin if the class is Spring-managed).

Each unique combination of `@MockitoBean` + other context customizers produces a **new ApplicationContext**. That's why tests suddenly start at 60s — keep mock beans consistent across test classes or suites get slow.

## MockMvc vs WebTestClient

- MVC app → `MockMvc` (via `@AutoConfigureMockMvc` or injected into `@WebMvcTest`).
- WebFlux app → `WebTestClient`.
- Don't use `TestRestTemplate` in new code for most cases — `WebTestClient` works against MVC too (just set `bindToServer()`) and has a better assertion DSL.

## Testcontainers — do it right

- Use `@Testcontainers` + `@Container` for one-off tests; use `@ServiceConnection` (Spring Boot 3.1+) to auto-wire container URL into `spring.datasource.*` — no more manual `@DynamicPropertySource`.
- Reuse containers across runs: `.withReuse(true)` + `~/.testcontainers.properties` with `testcontainers.reuse.enable=true`. Cuts test time dramatically on local runs.
- Don't mix Flyway with `spring.jpa.hibernate.ddl-auto=create` in tests — one of them will win silently and you test the wrong schema.

## Common pitfalls

- `@Transactional` on a test method rolls back by default — great for isolation, **but** it hides bugs where you rely on post-commit side effects (`@TransactionalEventListener(AFTER_COMMIT)` never fires). For those tests: `@Commit` or explicit `TransactionTemplate`.
- `@DirtiesContext` on many tests → each test class rebuilds the context. Use only when you actually mutate singleton state; otherwise remove.
- Tests that pass locally but fail in CI: usually caused by unstable context (random `@MockitoBean` combinations) or port collisions (`SpringBootTest.WebEnvironment.DEFINED_PORT`). Prefer `RANDOM_PORT` + `@LocalServerPort`.
- `@SpyBean` / `@MockitoSpyBean` on a bean that's `@Transactional`: the spy wraps the proxy, so method calls still go through the transactional advice. Usually what you want, but surprising if you forget.
- Asserting on `List` equality when DB order isn't guaranteed — add `ORDER BY` in the query, not `Collections.sort` in the test.

## Integration test hygiene

- Seed data via SQL scripts (`@Sql("/seed.sql")`) or Testcontainers init scripts — not by calling repositories from `@BeforeEach`, which couples tests to JPA/caching behavior.
- One assertion theme per test. "Test reads like a sentence": `given / when / then`.
- Clock-dependent tests: inject `Clock` as a bean, stub with `Clock.fixed(...)` in the test context. Don't call `Instant.now()` directly in production code.

## `@DataJpaTest` specifics

- By default `@DataJpaTest` **replaces your datasource with an embedded H2**. On a project running Postgres in prod, your queries (native SQL, JSONB, window functions, `ON CONFLICT`) may silently succeed on H2 and blow up in prod. Disable the replacement: `@AutoConfigureTestDatabase(replace = Replace.NONE)` + `@ServiceConnection PostgreSQLContainer<?>`.
- `@DataJpaTest` wraps every test in a transaction and rolls back. `entityManager.flush()` is needed to make Hibernate actually emit SQL; without it `.persist()` is a no-op at the DB level.
- `@DataJpaTest` imports **only JPA-related beans**. Your `@Component`-annotated services won't be in the context — use `@Import(MyService.class)` explicitly.

## `@WebMvcTest` security gotchas

- `@WebMvcTest` **applies your security config** by default. Every request in the test must pass authentication — use `@WithMockUser` or disable security for the slice (`@AutoConfigureMockMvc(addFilters = false)`) when testing non-auth concerns.
- CSRF: POST/PUT/DELETE tests need `.with(csrf())` from `SecurityMockMvcRequestPostProcessors` when CSRF is enabled.
- `@WebMvcTest` does not load `@ControllerAdvice` from libraries unless you `@Import` it. Tests claiming "exception handling works" while the advice isn't wired are a classic false positive.

## Testcontainers performance

- `@Testcontainers(parallel = true)` starts containers in parallel within a test class.
- Global singleton pattern: declare `static final PostgreSQLContainer<?> DB = new PostgreSQLContainer<>("postgres:17").withReuse(true); static { DB.start(); }` and point `@ServiceConnection` / `@DynamicPropertySource` at it. One container for the entire suite.
- Ryuk cleanup can be disabled for CI where the runner itself is ephemeral (`TESTCONTAINERS_RYUK_DISABLED=true`) — saves 2–3s per test class.
