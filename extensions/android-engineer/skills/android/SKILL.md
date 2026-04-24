---
name: android
description: Senior Android engineer workflows — Kotlin-first (Java legacy supported), Jetpack Compose + View system, MVVM, Coroutines/Flow, Room, Retrofit, Hilt, plus device orchestration via mobile-mcp (UI element tree, taps, swipes, install, launch) with ADB as fallback for logcat, pm clear, permissions and system settings. Use when implementing features, debugging crashes, fixing builds, writing tests, reviewing Android code, or running QA on an emulator.
---

# Android

Senior Android developer workflows. Covers both the **codebase layer** (Kotlin / Compose / MVVM / Coroutines / Room / Retrofit) and the **device layer** (mobile-mcp for UI and app lifecycle, ADB as fallback for system state).

> **Self-contained.** This skill does not require `kotlin-engineer`. All Kotlin/coroutine rules relevant for Android are included here.

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
| Device setup / emulator bootstrap | `references/device-setup.md` | `mobile_list_available_devices` returns empty, need to bring up an emulator |
| ADB cheat sheet | `references/adb.md` | Need logcat, `pm clear`, permissions, pull, system settings |
| Mobile MCP usage | `references/mobile-mcp.md` | Reading UI element tree, taps, swipes, text input via mobile-mcp |

## Google Official Skills

For specific migration or upgrade tasks, install the relevant Google Android skill into the project:

```bash
# See all available skills and their descriptions
npx android-skills-pack list

# Install only if the skill is not already installed
npx android-skills-pack install --target junie --skill <name>
```

Relevant hints are in each reference file. When a task matches a Google skill, install it only if not already present.

## The core loop

Whenever the agent touches the device, it follows this loop — no blind actions:

```
mobile_list_elements_on_screen        → read current UI state (text, ids, bounds)
     ↓
action (mobile-mcp: mobile_click_on_screen_at_coordinates / mobile_swipe_on_screen / mobile_type_keys)
     ↓
mobile_list_elements_on_screen        → verify UI changed as expected
     ↓
adb logcat -d *:E | tail -30          → catch silent crashes
```

Use `mobile_list_elements_on_screen` as the primary observation tool — it returns structured element data (text, resource-id, bounds) that the agent can read directly without vision.

`mobile_take_screenshot` is a **fallback only**: use it when elements are missing from the tree (custom views, games, WebView content, visual layout issues).

`mobile-mcp` = eyes & hands + app lifecycle (UI, install, launch). `adb` = system access only (logs, permissions, system state).

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

## Quick device commands

**Prefer mobile-mcp** for everything UI / app lifecycle:

- `mobile_list_available_devices` — list devices / emulators.
- `mobile_install_app <path-to.apk>` — install build output.
- `mobile_launch_app com.example.app` / `mobile_terminate_app com.example.app`.
- `mobile_list_elements_on_screen` — **primary observation tool**: structured UI tree (text, resource-id, bounds).
- `mobile_click_on_screen_at_coordinates`, `mobile_swipe_on_screen`, `mobile_type_keys`, `mobile_press_button BACK|HOME|ENTER`, `mobile_set_orientation`, `mobile_open_url`.
- `mobile_take_screenshot` — fallback only when elements are not visible in the tree.

**ADB only for what mobile-mcp can't do:**

```bash
adb shell pm clear com.example.app           # reset app state (no mobile-mcp equivalent)
adb logcat -d -v brief *:E | tail -100       # recent errors only (always -d)
adb logcat -d --pid=$(adb shell pidof -s com.example.app)  # logs for app process
adb pull /data/anr/traces.txt                # ANR traces
adb shell pm grant com.example.app android.permission.CAMERA
adb shell svc wifi disable                   # toggle network for QA
```

**Gradle (not device-related):**

```bash
./gradlew assembleDebug                      # build the app
./gradlew test                               # unit tests
./gradlew connectedAndroidTest               # instrumented tests on device
```

## Output Format

When implementing a feature:

1. **Plan** — one sentence stating what changes and which layers are touched (UI / ViewModel / Repository / data).
2. **Code** — implement bottom-up: data layer → domain → ViewModel → UI. Follow existing architecture patterns.
3. **Checklist** — confirm: no `Context` in ViewModel, flows collected with `collectAsStateWithLifecycle`, `runBlocking` not used on main thread, no hardcoded colors/dp.

When reviewing code: call out MUST-DO / MUST-NOT violations, lifecycle leaks, threading issues, and N+1 data fetches. Suggest minimal fixes.

When running QA: follow the core loop — observe → act → verify. Delegate long scenarios to `android-qa-agent`.

## Constraints

**MUST DO:**
- Use Kotlin, Jetpack Compose, MVVM, Coroutines/Flow.
- Use **mobile-mcp** for device listing, install/uninstall, launch/terminate, UI element tree, taps, swipes, text input, back/home, orientation, open-url — never shell out to `adb` for those.
- Use **ADB** only for: `logcat`, `pm clear`, `pm grant`/`revoke`, `svc wifi`/`data`, `settings put`, ANR `pull`, `forward`/`reverse`, `push`/`pull`, `getprop`/`dumpsys`.
- Wrap every UI action with `mobile_list_elements_on_screen` before and after, plus `adb logcat -d *:E | tail -30` after.
- Always pass `-d` to `adb logcat` in agent contexts — without it the command streams forever and hangs the agent session.
- When unit-testing, mock at the `ApiService` / `Dao` boundary so the Repository logic (cache-first, API fallback, error mapping) is actually exercised. See `references/test.md`.
- Reuse existing architecture patterns; read 2–3 similar features before adding a new one.

**MUST NOT DO:**
- Write new files in Java (Kotlin for all new code; keep existing Java files in Java).
- Hold `Context`, `View`, `Activity` references in a ViewModel.
- Call `runBlocking` on the main thread.
- Swallow exceptions with empty `catch` blocks.
- Hardcode dp/sp/colors — use `MaterialTheme` / theme tokens.
- Run `adb logcat` without `-d` — it streams forever and hangs the agent session.
- Shell out to `adb shell input tap|swipe|text|keyevent`, `adb install`, `adb shell am start`, `adb shell am force-stop`, `pm list packages`, `screencap`, `uiautomator dump`, `adb devices` — use the corresponding mobile-mcp tool instead.
- Bypass failing tests with `@Ignore`, skip flags, or weakened assertions.

## Dedicated agent

For autonomous QA loops, delegate to the `android-qa-agent` — it runs scenarios on the emulator and produces a structured PASS/FAIL/BLOCKED report without modifying source code.
