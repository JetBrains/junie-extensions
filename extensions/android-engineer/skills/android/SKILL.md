---
name: android
description: Senior Android engineer workflows — Kotlin-first (Java legacy supported), Jetpack Compose + View system, MVVM, Coroutines/Flow, Room, Retrofit, Hilt. Use when implementing features, debugging crashes, fixing builds, writing tests, reviewing Android code, or running QA on an emulator.
---

# Android

Senior Android developer workflows. Covers both the **codebase layer** (Kotlin / Compose / MVVM / Coroutines / Room / Retrofit) and the **device layer** — interacting with a real device or emulator, reading logs, managing app state, running QA scenarios.

This skill provides **workflows and code patterns**. The non-negotiable rules (architecture, async, UI, testing, device discipline, prefer-native-over-shell, mobile-mcp for UI, closed loop, no-bypass for tests) live in `guidelines/android.md` and apply unconditionally — this file does not repeat them.

## Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Implement a feature | `references/implement.md` | Adding new screen / feature / data layer |
| Jetpack Compose patterns | `references/compose.md` | Compose UI, state, navigation, animation, Hilt, side effects |
| View system / XML UI | `references/view-system.md` | XML layouts, ViewBinding, RecyclerView, Fragments (legacy / mixed projects) |
| Debug a crash | `references/debug.md` | Crash, unexpected behavior, stacktrace in logcat |
| Fix a build | `references/build-fix.md` | Gradle error, compile error, KSP/KAPT failure, resource error |
| Write & run tests | `references/test.md` | Unit tests (VM/UseCase) or Compose/Espresso UI tests |
| Code review | `references/review.md` | Reviewing diff for leaks, threading, lifecycle, perf |
| Manual QA on emulator | `references/qa.md` | Running scenarios on device, visual verification |
| Device setup / emulator bootstrap | `references/device-setup.md` | No device is currently available, need to bring up an emulator |

## The core loop

Whenever the agent touches the device, it follows the same loop — no blind actions:

1. **Observe** the current UI state by reading the structured **on-screen element tree** (text, resource-ids, bounds). This is the primary — and usually the only — observation channel; do not rely on screenshots / vision.
2. **Act** on the device (tap an element resolved from the tree, swipe, type, press a hardware button, etc.).
3. **Re-observe** by reading the element tree again to verify the screen actually changed as expected.
4. **Check recent errors** in logcat (recent error-level entries, or the latest fatal-exception block) to catch silent crashes that did not visibly fail the UI.

A screenshot is **not** a normal observation step. Take one only when the element tree genuinely cannot describe the screen — custom-drawn views, WebView content, games, or a visual regression suspected (mis-rendered colors / layout). Default to the tree.

## Key Patterns

### MVVM + UDF (Compose)

```kotlin
// State — what's on screen right now
sealed interface UserUiState {
    data object Loading : UserUiState
    data class Success(val user: User) : UserUiState
    data class Error(val message: String) : UserUiState
}

// ViewModel — no Context, no View, no Activity
class UserViewModel(
    private val repo: UserRepository,
) : ViewModel() {
    private val _state = MutableStateFlow<UserUiState>(UserUiState.Loading)
    val state: StateFlow<UserUiState> = _state.asStateFlow()

    fun load(id: String) = viewModelScope.launch {
        _state.value = UserUiState.Loading
        _state.value = runCatching { repo.user(id) }
            .onFailure { if (it is CancellationException) throw it }  // never swallow cancellation
            .fold({ UserUiState.Success(it) }, { UserUiState.Error(it.message ?: "Error") })
    }
}

// Composable — observes state with lifecycle awareness
@Composable
fun UserScreen(vm: UserViewModel = hiltViewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()
    when (val s = state) {
        UserUiState.Loading     -> LoadingIndicator()
        is UserUiState.Error    -> ErrorView(s.message) { vm.load("me") }
        is UserUiState.Success  -> UserContent(s.user)
    }
}
```

Full Repository / Retrofit / Fragment examples → `references/implement.md`.

## Device-side capabilities (intent, not commands)

Express what you need; the runtime picks the right tool. Rules for the device layer (UI through `mobile-mcp`, prefer native, declared fallback, element tree as primary observation, closed loop) are in `guidelines/android.md`.

The runtime can:

- **Discover devices** that the IDE can talk to, including emulators, with API level / model.
- **Bring up an emulator** — list AVDs, start one, create a new one if none exist (see `references/device-setup.md`).
- **Deploy a built APK** to a device, then **launch** the app and wait until its process is actually running.
- **Build, install, and run** the app in one shot when an IDE Run Configuration is already set up.
- **Read recent errors from logcat** (filtered by package and/or severity), **clear the logcat ring buffer** between runs, **fetch the last fatal-exception block** as a single aggregated stack, **read ANR traces** on debuggable / userdebug builds.
- **Reset app data** between scenarios; **grant or revoke a runtime permission**; **toggle Wi-Fi or mobile data**; **toggle system-wide dark mode** for QA.
- **Render a Compose preview** of a `@Preview`-annotated function and read its output.
- **Drive the UI**: read the on-screen element tree, tap by coordinates resolved from the tree, swipe, type text, press hardware buttons, set orientation, open a deep link. A screenshot is available only as a fallback for screens the tree can't describe.

For builds and tests, prefer the available build/test capabilities (pass the gradle task name, e.g. `:app:assembleDebug`, `test`, `connectedAndroidTest`, plus an optional test filter). If that capability is unavailable in the current environment, calling `./gradlew <task>` from the project root is an acceptable declared fallback.

## Output Format

When implementing a feature:

1. **Plan** — one sentence stating what changes and which layers are touched (UI / ViewModel / Repository / data).
2. **Code** — implement bottom-up: data layer → domain → ViewModel → UI. Follow existing architecture patterns.
3. **Checklist** — confirm: no `Context` in ViewModel, flows collected with `collectAsStateWithLifecycle`, `runBlocking` not used on main thread, no hardcoded colors/dp.

When reviewing code: call out MUST-DO / MUST-NOT violations, lifecycle leaks, threading issues, and N+1 data fetches. Suggest minimal fixes.

When running QA: follow the core loop — observe → act → re-observe → check logs. Delegate long scenarios to `android-qa-agent`.

## Skill-specific reminders

These complement the always-on rules in `guidelines/android.md` (don't duplicate them here):

- **Reuse existing architecture patterns** — read 2–3 similar features before adding a new one; match the project's existing conventions over importing fresh ones.
- **Mock at the `ApiService` / `Dao` boundary**, not at the Repository — the Repository's cache-first / fallback / error-mapping logic must actually be exercised by tests. Mocking the Repository is fine inside ViewModel tests. See `references/test.md`.

## Dedicated agent

For autonomous QA loops, delegate to the `android-qa-agent` — it runs scenarios on the emulator and produces a structured PASS/FAIL/BLOCKED report without modifying source code.
