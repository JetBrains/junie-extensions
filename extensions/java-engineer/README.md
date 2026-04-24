# java-engineer

Junie extension that turns the agent into a disciplined Java (17–21) engineer: enforces project-level policy and catches the subtle language traps that LLMs get wrong by default — `Optional` misuse, `Stream.toList` mutability, `orElse` vs `orElseGet`, pattern-matching null, virtual-thread carrier pinning, `ExecutorService` lifecycle.

## Philosophy

Baseline Java knowledge is assumed — the extension does not re-teach records, sealed classes, streams, or `switch`. Instead it encodes:

- **Policy** — MUST / MUST NOT rules the agent should follow.
- **Pitfalls** — behaviors that compile, pass trivial tests, and fail in production.
- **Setup awareness** — detect JDK version, build wrapper, Lombok, static analysis before writing non-trivial code.

## What it covers

- Language idioms: `Optional`, `record`, `sealed`, pattern matching, `var`.
- API traps: `Stream`, `switch`, generics, equality, I/O, numbers, date/time.
- Concurrency: virtual threads (when they help / when they pin), `StructuredTaskScope`, `ExecutorService` lifecycle, `CompletableFuture` exception propagation, race conditions in "simple" code.

## Files

- `skills/java/SKILL.md` — hub: Setup Check, MUST DO / MUST NOT, Reference Guide, Output Format.
- `skills/java/references/pitfalls.md` — subtle language / API gotchas.
- `skills/java/references/concurrency.md` — virtual threads, structured concurrency, executors, thread-locals.

## Requirements

- JDK 17+ (policy targets 17–21).
- Project uses `./mvnw` or `./gradlew` (wrappers — don't rely on a global `mvn` / `gradle`).
- Optional: Lombok, `error-prone` / `checkstyle` / `spotbugs` / `pmd` — the agent will respect them if present.

## Installation

Drop the extension folder into your Junie extensions directory and enable it. Junie picks up `SKILL.md` automatically and loads references on demand.
