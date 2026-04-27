---
name: java-engineer
description: Java 17–25 policy and pitfalls. Use when writing, reviewing, or refactoring Java code — enforces idioms around records, sealed types, switch exhaustiveness, Optional, virtual threads, and null-safety that LLMs frequently get wrong.
---

# Java — policy & pitfalls

Baseline knowledge of the Java language (records, sealed, pattern matching, text blocks, streams, `var`, generics, Optional API) is assumed — this skill does not teach the language. It encodes the project policy and the traps that keep appearing in code review.

## Setup Check (run first)

Before writing non-trivial code, verify:

1. **JDK version** — `java --version`, and target version in `pom.xml` (`<maven.compiler.release>`) or `build.gradle(.kts)` (`java { toolchain { languageVersion = JavaLanguageVersion.of(21) } }`). Adjust feature use if < 17. Current LTS: Java 25 (released Sept 2025); Java 21 is the previous LTS. Prefer LTS releases for new projects.
2. **Build tool wrapper** — use `./mvnw` / `./gradlew`, never a globally installed `mvn` / `gradle`.
3. **Lombok** — look for `lombok` in dependencies. If present, prefer `@RequiredArgsConstructor` / `@Slf4j` / `@Builder`; if absent, do not introduce Lombok unless asked.
4. **Static analysis** — `error-prone`, `checkstyle`, `spotbugs`, `pmd`. Respect existing rules; do not add new violations.
5. **Preview features** — if build uses `--enable-preview`, some features behave differently. Check flag before relying on preview syntax.

## MUST DO

- **`Optional` is a return type only.** Never a parameter, field, or element of a collection.
- **Value classes → `record`.** DTOs, events, results, config snapshots. Not JPA entities (records are final and have no no-arg constructor).
- **Closed hierarchies → `sealed`** + exhaustive `switch`. Compiler catches new cases.
- **`switch` expression over `if / else if` chains.** Pattern-matching `switch` over `instanceof` chains.
- **Fields `final`** unless you have a reason to reassign.
- **Fail fast at boundaries** — `Objects.requireNonNull` in public-API constructors; validate invariants in record compact constructors.
- **`try-with-resources`** for anything `AutoCloseable` — including `ExecutorService` (Java 19+).
- **Virtual threads for blocking I/O** (`Executors.newVirtualThreadPerTaskExecutor()`). Not for CPU-bound work.
- **Structured concurrency** for multi-call fan-out: `try (var scope = new StructuredTaskScope.ShutdownOnFailure()) { ... }`.
- **Parameterized logging**: `log.info("user_updated userId={} status={}", id, status)`.

## MUST NOT DO

- **No `Optional.get()`** without prior `isPresent()` — use `.map(...).orElseThrow(...)` or `.orElse(default)`.
- **No raw types** (`List` instead of `List<Foo>`), no `@SuppressWarnings("rawtypes")` to silence warnings.
- **No returning `null` from a collection-returning method.** Return `List.of()` / `Collections.emptyList()`.
- **No checked exceptions leaking into `Stream` / lambda**. Wrap into an unchecked domain exception at the boundary.
- **No catching `Exception` / `Throwable`** to "make the compiler happy". Handle a specific type or propagate.
- **No mutating input collections.** Make a defensive copy: `List.copyOf(input)`.
- **No `synchronized` around a blocking call on a virtual thread** — it pins the carrier thread. Use `ReentrantLock`.
- **No `Thread.sleep` / blocking I/O on `parallelStream()`** — shared common pool, starves other work.
- **No mutation of `Stream.toList()` result** — it's unmodifiable (JDK 16+).
- **No PII / tokens / raw passwords in logs.**

## Reference Guide

| Load when | File |
|---|---|
| Debugging subtle language / API behavior (Optional, Stream, switch, records, generics) | `references/pitfalls.md` |
| Records, sealed hierarchies, pattern-matching switch, preview features (pitfalls & traps, not syntax tutorials) | `references/modern-java.md` |
| Writing concurrent code (virtual threads, structured concurrency, `ExecutorService` lifecycle, `ThreadLocal` traps) | `references/concurrency.md` |
| File / stream / socket I/O, charsets, partial reads, NIO buffers | `references/io.md` |

## Output Format

When producing code:

1. A short plan (1–3 bullets) of what's changing.
2. The code.
3. A checklist of the non-obvious MUST rules applied.

When reviewing code: call out MUST-DO / MUST-NOT violations explicitly and suggest the minimal fix.
