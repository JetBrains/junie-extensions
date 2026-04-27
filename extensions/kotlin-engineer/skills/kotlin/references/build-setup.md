# Kotlin build setup — policy & pitfalls

Assumes basic Gradle knowledge. This file is the setup policy and the compiler-plugin traps.

## Build script style

- **Kotlin DSL (`build.gradle.kts`)** over Groovy. Type-safe, better IDE support, same syntax as the rest of the codebase.
- **Version catalogs (`gradle/libs.versions.toml`)** for dependency versions. Don't hard-code versions in module scripts.
  ```toml
  [versions]
  # Check latest stable at: https://kotlinlang.org/docs/releases.html
  kotlin = "<latest-stable>"
  # Check latest stable at: https://github.com/Kotlin/kotlinx.coroutines/releases
  coroutines = "<latest-stable>"
  [libraries]
  coroutines-core = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-core", version.ref = "coroutines" }
  [plugins]
  kotlin-jvm = { id = "org.jetbrains.kotlin.jvm", version.ref = "kotlin" }
  ```
- **`./gradlew`** always. If the wrapper is missing, generate it (`gradle wrapper --gradle-version X`) before anything else.

## Kotlin compiler plugins — which are mandatory, which break builds if missing

| Plugin | Needed when | Failure mode if missing |
|---|---|---|
| `kotlin("plugin.spring")` | Any Spring project | Final classes can't be CGLIB-proxied → `@Transactional` / `@Async` silently don't work |
| `kotlin("plugin.jpa")` | JPA entities | `InstantiationException: No default constructor for entity` at runtime |
| `kotlinx-serialization` | `@Serializable` data classes | `SerializationException: Serializer for class not found` |
| `kotlin("kapt")` / KSP | Annotation processors (Dagger, Room, Moshi codegen) | Processor simply doesn't run |
| `org.jlleitschuh.gradle.ktlint` / `io.gitlab.arturbosch.detekt` | If the project uses them | Lint noise in PRs |

- `all-open` plugin is the underlying mechanism of `plugin.spring` / `plugin.jpa`. Don't apply `all-open` directly unless you know exactly which annotations to mark open.
- `no-arg` plugin generates a synthetic no-arg constructor for annotated classes — that's how `plugin.jpa` works.

## KSP vs kapt

- **Prefer KSP (`com.google.devtools.ksp`)** — significantly faster than kapt (2–7× depending on the processor), avoids the stub generation round-trip.
- **Fall back to kapt only when** the processor doesn't have a KSP implementation (still a few legacy ones). Migrate when possible: Room, Moshi, Hilt all have KSP now.
- Don't mix KSP and kapt for the same processor in the same module — conflicts, build slowdown.
- kapt pitfall: `kapt` tasks ignore incremental compilation by default. Large multi-module projects waste minutes per build.

## JVM toolchain

- **Set `jvmToolchain(n)`** — Gradle downloads the right JDK if missing:
  ```kotlin
  kotlin {
      jvmToolchain(21)
  }
  ```
- This replaces `sourceCompatibility` / `targetCompatibility` / `kotlinOptions.jvmTarget`. Setting all three is redundant and error-prone (they drift).
- Virtual threads require JDK 21+. Records interop requires JDK 17+.

## `kotlinOptions` / `compilerOptions`

- In Kotlin 2.x use the DSL:
  ```kotlin
  kotlin {
      compilerOptions {
          jvmTarget = JvmTarget.JVM_21
          freeCompilerArgs.addAll(
              "-Xjsr305=strict",       // treat JSR-305 annotations as strict
              "-Xcontext-receivers",   // if you use context receivers
          )
      }
  }
  ```
- `-Xjsr305=strict` is strongly recommended when consuming Java APIs with `@Nullable` / `@NotNull` — turns platform types into proper Kotlin nullable types.
- Don't enable `-Werror` in library modules without a plan — breaks CI on benign warnings (deprecations you don't control).

## Multi-module layout

- **One-way dependencies.** `app` → `feature-*` → `core`. No `core` → `feature`.
- **Public API module boundary** — use `api(...)` in Gradle only when consumers need the type transitively; otherwise `implementation(...)`. `api` leaks the dependency and slows up compilation.
- Convention plugins (`buildSrc` or composite build `build-logic`) for shared config — don't duplicate `compilerOptions` / plugin ids across modules.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `@Transactional` silently doesn't start a transaction in Kotlin code | Class is `final` (Kotlin default) | Add `kotlin("plugin.spring")` — marks annotated classes `open` |
| `InstantiationException: No default constructor` on JPA entity | Kotlin class has no no-arg constructor | Add `kotlin("plugin.jpa")` |
| `SerializationException: Serializer for class X not found` | Missing `kotlinx-serialization` plugin or `@Serializable` on the class | Apply the plugin + annotation |
| `Duplicate class` from two versions of the same library | Transitive dependency conflict | `./gradlew :app:dependencies` → align via `constraints` block or version catalog |
| KSP / kapt not running | Plugin not applied OR task excluded in CI | Check `./gradlew :module:kspKotlin` runs standalone |
| Build suddenly slow after adding a library | kapt pulled in transitively | Check `./gradlew :module:dependencies` for `kapt` configuration; migrate to KSP |

## What NOT to put in a Kotlin build

- **Global `allprojects { kotlinOptions { ... } }`** — runs for every module, including those without Kotlin plugin applied → errors. Use a convention plugin.
- **`kotlin("jvm") version "..."` on subprojects** — declare the plugin at the root `plugins { }` block with `apply false`, then `plugins { alias(libs.plugins.kotlin.jvm) }` per module.
- **Absolute paths** in `gradle.properties` or scripts — breaks CI. Use project-relative paths.
- **`mavenLocal()`** as the first repository in CI — non-reproducible builds. Only for local debugging of a library you're developing.
