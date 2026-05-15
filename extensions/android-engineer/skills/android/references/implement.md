# Implementing a Feature

Step-by-step workflow for adding a new feature or screen to an Android app.

> **Google Android skills-pack:** for domain tasks (edge-to-edge for SDK 35+, Play Billing upgrades, etc.) check `npx android-skills-pack list` first and install a matching skill with `npx android-skills-pack install --target junie --skill <name>`. If no exact match, pick the closest one from the list or proceed without.

## Steps

1. **Restate the task in one sentence.** Identify which layers are affected: UI only, ViewModel, Repository, or all layers.

2. **Explore the existing code** before writing anything new:
   - Find the most relevant existing screen/feature and read it as a reference.
   - Read its ViewModel, Repository, UseCases.
   - Check `AndroidManifest.xml` if a new Activity, Service, BroadcastReceiver, or Permission is needed.
   - Read `libs.versions.toml` if a new dependency is required.

3. **List every file that will be created or modified** before writing code.

4. **Implement bottom-up** — data → domain → UI:
   1. Entity / Model (domain types, Room `@Entity`).
   2. DAO and API interface (`suspend` functions, `Flow` returns).
   3. Repository / UseCase — business logic. Handle errors **at the Repository boundary**: wrap API/DAO calls in `runCatching`, fall back to cache on failure, and only rethrow once no recovery is possible (see the `UserRepository` example in `SKILL.md`). Do not leak `IOException` / `HttpException` upward — the ViewModel should map a thrown `Throwable` into `UiState.Error`, nothing lower-level. **Important**: always rethrow `CancellationException` from `runCatching`: `.onFailure { if (it is CancellationException) throw it }` — swallowing it disables coroutine cancellation.
   4. ViewModel — exposes `StateFlow<UiState>`, no `Context`.
   5. UI layer — pick based on what the project uses:
      - **Compose**: Composable that handles loading / error / empty / content states (`references/compose.md`).
      - **View system (XML)**: Fragment + ViewBinding + `repeatOnLifecycle` collection (`references/view-system.md`).
      - **Mixed**: follow the existing pattern of the screen being changed.
   6. Navigation wiring (`NavHost` for Compose, `nav_graph.xml` or fragment transactions for View system).

5. **Follow project conventions strictly:**
   - Match the existing architecture pattern — do not introduce a new one.
   - Reuse theme tokens (`MaterialTheme.colorScheme`, `MaterialTheme.typography`, dimen resources).
   - Add strings to `strings.xml`, never inline.

6. **Build & check.** Run `./gradlew assembleDebug`. Fix all compilation errors before continuing.

7. **Verify the UI via headless preview (Compose).** Before running on a device, render the relevant `@Preview` composables with the headless preview renderer — it visualizes the layout instantly without building or running on a device. Iterate on the preview until the layout looks correct.

8. **Verify on emulator.** Run `run_android_app` with the absolute path to the entry-point file (e.g. `.../app/src/main/java/com/example/MainActivity.kt`) — it builds, installs, and launches in one step, returning only when the app is running. Do not insert `sleep`. On failure, fall back: `./gradlew assembleDebug` → `install_android_apk` → `launch_android_app` → `wait_for_android_app_launch`. Navigate to the screen, read the UI element tree, and confirm the expected elements are present.

## Notes

- If unsure about the architecture, read 2–3 existing similar features first — don't guess.
- Prefer extending existing patterns over introducing new ones.
- For new libraries: add to `libs.versions.toml` first, reference by alias in `build.gradle.kts`. If the library uses reflection, serialization, or class-name lookups (Retrofit converters, custom Gson/Moshi adapters, Room entities accessed by name) — check `proguard-rules.pro`: R8 may strip or rename these classes in release builds.
- For new Hilt bindings: add a `@Module` with `@InstallIn(SingletonComponent::class)` next to related code.
