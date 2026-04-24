# kotlin-engineer

Junie extension that turns the agent into a disciplined Kotlin 2.x engineer: enforces project-level policy and catches the subtle coroutine / Flow / API-design traps that LLMs get wrong by default — swallowed `CancellationException`, leaked `MutableStateFlow`, sequential `async`/`await`, misplaced `flowOn`, missing `kotlin-spring` / `kotlin-jpa` plugins.

## Philosophy

Baseline Kotlin knowledge is assumed — the extension does not re-teach data/sealed classes, scope functions, or `suspend`/`Flow` APIs. Instead it encodes:

- **Policy** — MUST / MUST NOT rules the agent should follow.
- **Pitfalls** — code that compiles, passes trivial tests, and misbehaves at runtime (cancellation, threading, exception transparency).
- **Setup awareness** — detect Kotlin version, JDK target, compiler plugins, lint config before writing non-trivial code.

## What it covers

- Language idioms: null-safety, sealed hierarchies, value / data / inline classes, scope functions, delegation, extension functions, generics & variance.
- Async: coroutine scopes, cancellation, dispatcher discipline, parallel fan-out, StateFlow vs SharedFlow, Flow correctness, `callbackFlow`, testing with `runTest` + `Turbine`.
- Build & tooling: Kotlin DSL, version catalogs, compiler plugins (`plugin.spring` / `plugin.jpa` / `kotlinx-serialization`), KSP vs kapt, JVM toolchain, multi-module layout.

## Files

- `skills/kotlin/SKILL.md` — hub: Setup Check, MUST DO / MUST NOT, Reference Guide, Output Format.
- `skills/kotlin/references/coroutines.md` — coroutines & Flow policy and pitfalls.
- `skills/kotlin/references/idioms.md` — API-design idioms (scope functions, class kinds, extensions, delegation, `Result<T>`, generics).
- `skills/kotlin/references/build-setup.md` — Gradle Kotlin DSL, version catalogs, compiler plugins, KSP/kapt, toolchain.

## Requirements

- Kotlin 2.x (policy works with late 1.9 as well).
- Project uses `./gradlew` wrapper.
- Optional: `detekt` / `ktlint` — respected if present.

## Installation

Drop the extension folder into your Junie extensions directory and enable it. Junie loads `SKILL.md` automatically and references on demand.
