# Android Development Guidelines

Project-level conventions for Android codebases. Junie MUST follow these rules when working on Android projects.

## Language & Syntax
- Use **Kotlin** for all new files.
- In mixed or legacy Java projects: keep existing Java files in Java unless the task explicitly asks to migrate. Do not force-convert Java to Kotlin when touching unrelated code.
- Use `@SerializedName` / `@SerialName` on all DTO / Retrofit classes — code gets obfuscated in release builds.

## Architecture
- Follow **MVVM**: ViewModel + Repository + UseCases.
- ViewModels **MUST NOT** hold references to `Context`, `View`, `Activity`, or `Fragment`.
- Use **unidirectional data flow**: UI observes state, sends events to ViewModel.
- Separate UI **state** (current screen data) from UI **events** (one-time actions like navigation).
- Repository is the mocking boundary — ViewModels never touch Room DAOs or Retrofit directly.

## Async
- Use **Kotlin Coroutines and Flow** for all async operations.
- Never use `runBlocking` on the main thread.
- Collect flows with `repeatOnLifecycle(Lifecycle.State.STARTED)` or inside `lifecycleScope`.
- Use `viewModelScope` for coroutines in ViewModels.
- Expose `StateFlow` / `SharedFlow` from ViewModels — never raw `MutableStateFlow`.

## UI
- Use **Jetpack Compose** for all new UI screens.
- In projects using the **View system** (XML layouts): keep existing screens in XML + ViewBinding. Add new screens in Compose only if the project already has Compose set up; otherwise use XML + ViewBinding.
- Follow **Material Design 3** guidelines and components.
- Never hardcode `dp`/`sp` values — use theme dimensions or `MaterialTheme.typography` / dimension resources.
- Never hardcode colors — use `MaterialTheme.colorScheme` or color resources.
- Handle **all screen states**: loading, error, empty, content.

## Data & Storage
- Use **Room** for local database; define `Entity`, `DAO`, and `Database` classes separately.
- Use **Repository pattern** — ViewModels never access Room DAOs directly.
- Use **Retrofit** for network; define interfaces with `suspend` functions.
- Handle network errors explicitly — never swallow exceptions silently.

## DI
- Use **Hilt** (or Koin if already established). Do not mix frameworks.
- Inject at construction site; do not use service locators in production code.

## Testing
- Unit-test ViewModels and UseCases with **JUnit5 + MockK + kotlinx-coroutines-test**.
- UI-test critical flows with **Compose Testing** or Espresso.
- Mock at the **`ApiService` / `Dao` boundary** and exercise the Repository as a unit — its cache-first / fallback / error-mapping logic must be tested, not stubbed. Mocking the Repository is only acceptable inside ViewModel tests.
- Test name convention: `` `given [precondition] when [action] then [expected result]` ``.

## Build & Dependencies
- Use `build.gradle.kts` (Kotlin DSL), not Groovy.
- Use **version catalogs** (`libs.versions.toml`) for dependency management.
- Never commit API keys or secrets — use `local.properties` or environment variables.

## Device / Emulator Work
- The agent has two layers for device interaction:
  - **mobile-mcp** (UI + app lifecycle) — device listing, install/uninstall, launch/terminate, UI element tree, taps, swipes, text input, orientation, open-url.
  - **ADB** via shell (system layer only) — `logcat`, `pm clear`, `pm grant`/`revoke`, `svc wifi/data`, `settings put`, ANR/file `pull`, `forward`/`reverse`, `getprop`/`dumpsys`.
- Device listing, install, launch, taps, swipes, text input, back/home, orientation and URL opening MUST go through mobile-mcp — never `adb shell input …`, `am start`, `adb install`, `pm list packages`, `adb devices`, `screencap` or `uiautomator dump`.
- Every UI action MUST be wrapped with: **`mobile_list_elements_on_screen` → action → `mobile_list_elements_on_screen` → `adb logcat -d *:E | tail -N`**. No blind taps.
- Use `mobile_take_screenshot` only as a fallback when elements are absent from the tree (custom-drawn views, WebView, games).
- `adb logcat` MUST always be invoked with `-d` — without it the command streams forever and hangs the agent session.
