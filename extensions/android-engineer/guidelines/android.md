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

## Security
- Set `android:exported` explicitly (`true` or `false`) on every Activity, Service, and BroadcastReceiver that has an `<intent-filter>` — required on Android 12+ (targetSdk 31+), the build fails without it.
- On Android 14+ (targetSdk 34+): `android:foregroundServiceType` is mandatory on every Foreground Service — missing it causes `SecurityException` at runtime.
- Never hardcode API keys or secrets in source code — use `local.properties` or environment variables.
- Set `usesCleartextTraffic="false"` unless explicitly required.

## Build & Dependencies
- Use `build.gradle.kts` (Kotlin DSL), not Groovy.
- Use **version catalogs** (`libs.versions.toml`) for dependency management.
- Never commit generated files or build artifacts.

## Device / Emulator Work

Three layers for device interaction, in fallback order — use the first that's available:

1. **Plugin tools — first choice** (device management, app lifecycle, diagnostics, system tweaks): listing devices and AVDs, starting/stopping emulators, building and running the app, reading logcat, getting crash reports and ANR traces, clearing app data, granting/revoking permissions, toggling network and dark mode, rendering Compose previews.
2. **mobile-mcp — UI interaction only**: reading the UI element tree, tapping, swiping, text input, back/home buttons, orientation changes, opening URLs, screenshot fallback.
3. **ADB shell — last-resort fallback**: only when neither plugin tools nor mobile-mcp expose the operation (older plugin version, MCP unavailable, exotic shell case). See `skills/android/references/adb.md`.

Never use `sleep` or manual delays after starting an emulator, launching an app, reproducing a bug, or running a QA scenario — plugin tools handle boot and launch completion internally, and other tools return when the action is done. Proceed to the next step immediately after the tool returns.

When implementing or changing Compose UI, use the headless preview renderer to verify layout before running the app on device — it renders all `@Preview` composables in the file instantly without a full build or device run.

Every UI action MUST be wrapped: **read the UI element tree → action → read the UI element tree**. No blind taps. Use a screenshot only as a fallback when elements are absent from the tree (custom-drawn views, WebView, games).
