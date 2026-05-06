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
- For any device-side operation, describe **what you need** (read recent ERROR logcat for the app's package, install a built APK, reset application data, read the on-screen UI, …) — the runtime resolves the right tool from what is currently available.
- **Prefer native** over shell. Don't reach for `adb` / `emulator` / `gradlew` as a first step. Direct shell is allowed only as a **declared fallback**: a needed capability is missing or the native tool failed in the current environment. When you fall back, say so explicitly (which capability failed and why) and keep the same observation discipline (re-read the element tree / logcat after the action).
- **UI interaction goes through the `mobile-mcp` MCP server** (`@mobilenext/mobile-mcp`), not `adb shell`. The on-screen element tree, tap / swipe / type, hardware buttons, orientation, screenshot, list-apps and launch / terminate are MCP tools. If those MCP tools are not visible in the current session, the server is not enabled — **request that it be enabled** via the available MCP-management capability instead of shelling out. Do **not** substitute UI work with `adb shell input tap/swipe/text/keyevent`, `adb shell uiautomator dump`, or `adb exec-out screencap`: these lose the structured element tree (no resource-ids, brittle pixel coords) and are not a valid fallback. If `mobile-mcp` cannot be enabled, mark affected scenarios as `BLOCKED — mobile-mcp not enabled` rather than driving the UI through shell.
- The **on-screen element tree** (text / resource-id / bounds) is the primary observation channel. Use the structured UI read; do not rely on screenshots or vision as your normal way to see the screen. Take a screenshot only when the tree genuinely cannot describe the screen — custom-drawn views, WebView, games, or a visual regression is suspected.
- Every UI action MUST follow the closed loop: **read the on-screen element tree → perform the action → read the element tree again → check recent ERROR-level logcat entries** (or fetch the last fatal-exception block). No blind taps.
- Do **not** compose ad-hoc deploy chains (manual `./gradlew assembleDebug` + `adb install` + `adb shell am start`) when the runtime's build-and-run / install / launch capabilities are working. Use the integrated path; shell-stitched deploys bypass the closed loop and the run-configuration's wiring.

## Compose Preview (visual feedback without an emulator)
- For pure "how does this `@Composable` look by code?" questions, **prefer rendering a `@Preview`-annotated function** through the available Compose-preview capability — it uses `layoutlib` on the IDE side, **no emulator or device required**, and the rendered PNG is returned directly to the agent.
- Use it as the first visual-feedback step when iterating on a Composable's layout / theming / state-less rendering: write code → render preview → inspect → adjust. Falling straight to `build_and_run` + emulator UI tree is correct only when you need **live state** or interaction (real ViewModel, navigation, animations driven by user input).
- The preview returns either an image (success) or a short text diagnostic (`Not a Compose preview file`, `No image: <status>`, `File not found`, `No open project`, etc.). Treat any non-image response as a failure to render and act on the diagnostic — do not retry blindly.
- Compose Preview does **not** replace the emulator-based closed loop for end-to-end QA; it is a faster pre-flight check. Once you need real state or want to verify a flow, switch back to the device-side closed loop above.

## Test discipline
- Never bypass failing tests with `@Ignore` / `@Disabled`, skip flags, weakened assertions, or stub mocks that hide the failure. Tests fail because either the test or the production code is wrong — fix the actual cause.
