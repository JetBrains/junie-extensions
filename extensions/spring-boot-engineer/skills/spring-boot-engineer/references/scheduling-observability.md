# Scheduling, Actuator & Virtual Threads — policy & pitfalls

Generic knowledge of `@Scheduled`, Actuator endpoints, and Micrometer is assumed. This file covers the traps.

## `@Scheduled` in a multi-instance deployment

- `@Scheduled` fires on **every** instance. In a clustered app (≥2 replicas) that means the job runs N times.
- Options:
  1. **ShedLock** (`net.javacrumbs.shedlock`) — DB-backed distributed lock; easiest fix. One line: `@SchedulerLock(name = "reportJob", lockAtMostFor = "5m")`.
  2. Leader election via Spring Integration / Zookeeper / Kubernetes lease — heavier, for complex cases.
  3. Only run scheduler on a dedicated "worker" profile (`@Profile("worker")` + 1 replica). Simple but fragile.
- Never assume "my cron runs on only one instance" — always make it explicit.

## Required setup

- `@EnableScheduling` on a `@Configuration` class (or the main app class).
- Default: tasks run on a **single-threaded** scheduler. A long job blocks all other schedules. Configure:
  ```java
  @Bean
  public ThreadPoolTaskScheduler taskScheduler() {
      var s = new ThreadPoolTaskScheduler();
      s.setPoolSize(Runtime.getRuntime().availableProcessors());
      s.setThreadNamePrefix("sched-");
      return s;
  }
  ```
- `@Async` tasks need their own `ThreadPoolTaskExecutor` (see `event-driven.md`). Don't share the scheduler pool for async work.

## `@Scheduled` on a proxied method

Same proxy rules as `@Transactional`:

- Public, non-final, not called via `this.` from another method in the same bean.
- Kotlin: `kotlin-spring` plugin so the class is `open`.
- `@Scheduled` + `@Transactional` on the same method is fine, but remember it opens a tx for the entire job — keep the job short.

## Actuator — what to expose

Default exposure (since Spring Boot 2+): only `/actuator/health` and `/actuator/info`. That's deliberate.

- **Expose only what you use.** `management.endpoints.web.exposure.include=health,info,metrics,prometheus` — never `*` in prod.
- Put actuator behind auth and/or a separate port:
  ```properties
  management.server.port=9090
  management.server.address=127.0.0.1
  ```
- `/actuator/env`, `/actuator/configprops`, `/actuator/heapdump`, `/actuator/threaddump` leak secrets / can crash a JVM if exposed publicly.

## Health checks

- Liveness vs readiness:
  - `/actuator/health/liveness` — is the process alive? Restart if failing.
  - `/actuator/health/readiness` — can it serve traffic? Temporarily drop from LB.
- Don't mix DB health into liveness. If DB is down, restarting your pod won't help — only readiness should drop. Spring Boot auto-configures this correctly for Kubernetes; for other platforms, check your probe mapping.
- Custom `HealthIndicator` beans must be fast (< 1s) — if slow, your liveness probe times out and the pod gets killed.

## Metrics (Micrometer)

- Micrometer is auto-wired; publish to Prometheus via `micrometer-registry-prometheus` + expose `/actuator/prometheus`.
- Tag cardinality kills Prometheus. **Never tag with user-id, request-id, or anything unbounded.** Metric labels must be low-cardinality (method, endpoint, status code, tenant tier).
- `@Timed` on a service method = Micrometer timer. Useful, but prefer wiring timers explicitly for custom metrics.
- Include `http.server.requests` (auto-instrumented). Alert on `p99` > budget, `5xx` rate, saturation (thread pool queue size).

## OpenTelemetry (Spring Boot 4.x)

Spring Boot 4 ships a dedicated starter: `spring-boot-starter-opentelemetry`. It brings OTLP metrics and trace export out of the box without manual Micrometer OTLP bridge wiring.

- Use when the stack uses an OpenTelemetry Collector (common in k8s / CNCF environments).
- For Prometheus-only setups `micrometer-registry-prometheus` is still the simpler choice.
- Both can coexist, but configure one exporter per signal type to avoid duplicate data.

## Virtual threads

- Enable with `spring.threads.virtual.enabled=true`. Spring Boot rewires Tomcat / Jetty to use virtual threads for request handling. (Available since Boot 3.2; recommended in Boot 4.x for I/O-heavy MVC apps.)
- **Helpful for**: blocking I/O-heavy apps (lots of DB / HTTP calls per request) where you'd otherwise need a huge thread pool.
- **Harmful for / doesn't help**:
  - CPU-bound workloads (virtual threads pin a carrier thread — no benefit vs platform threads).
  - Code using `synchronized` blocks (pins the carrier thread until the monitor is released; defeats the scalability win). Prefer `ReentrantLock`.
  - Heavy use of `ThreadLocal` that isn't cleared per request — memory explodes because there are now millions of threads.
  - JNI / native code that assumes a 1:1 thread binding.
- Don't enable blindly on WebFlux — WebFlux is already non-blocking. Virtual threads are the MVC alternative.

## Common mistakes

- `@Scheduled` fires on every pod, no lock → duplicate emails, double charges.
- Single-threaded default scheduler, one job hangs for 10 min → all crons miss their windows.
- Exposing `/actuator/*` publicly → env vars, heap dumps, config leaked.
- High-cardinality Prometheus labels → registry explodes, scrape times out.
- Enabling virtual threads + keeping `synchronized` blocks in hot paths → no throughput improvement, sometimes worse.
