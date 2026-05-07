---
name: android
description: Senior Android engineer workflows — Kotlin-first (Java legacy supported), Jetpack Compose + View system, MVVM, Coroutines/Flow, Room, Retrofit, Hilt, plus device orchestration via plugin tools (device management, logcat, crash reports, app run) and mobile-mcp for UI interaction (element tree, taps, swipes). Use when implementing features, debugging crashes, fixing builds, writing tests, reviewing Android code, or running QA on an emulator.
---

# Android

Senior Android developer workflows. Covers both the **codebase layer** (Kotlin / Compose / MVVM / Coroutines / Room / Retrofit) and the **device layer** (plugin tools for device management and diagnostics, mobile-mcp for UI interaction).

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
| Device setup / emulator bootstrap | `references/device-setup.md` | No device available, need to bring up an emulator |
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
read logcat                           → catch silent crashes
```

Use `mobile_list_elements_on_screen` as the primary observation tool — it returns structured element data (text, resource-id, bounds) that the agent can read directly without vision.

`mobile_take_screenshot` is a **fallback only**: use it when elements are missing from the tree (custom views, games, WebView content, visual layout issues).

Plugin tools = device management + app lifecycle + diagnostics. mobile-mcp = UI interaction.

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
- Use **plugin tools** for device management (list/start/stop emulator), app lifecycle (run/install/clear), diagnostics (logcat, crashes, ANR), permissions, and system settings.
- Use **mobile-mcp** for UI interaction: element tree, taps, swipes, text input, back/home, orientation, open-url.
- Wrap every UI action with `mobile_list_elements_on_screen` before and after, plus log check after.
- When unit-testing, mock at the `ApiService` / `Dao` boundary so the Repository logic (cache-first, API fallback, error mapping) is actually exercised. See `references/test.md`.
- Reuse existing architecture patterns; read 2–3 similar features before adding a new one.

**MUST NOT DO:**
- Write new files in Java (Kotlin for all new code; keep existing Java files in Java).
- Hold `Context`, `View`, `Activity` references in a ViewModel.
- Call `runBlocking` on the main thread.
- Swallow exceptions with empty `catch` blocks.
- Hardcode dp/sp/colors — use `MaterialTheme` / theme tokens.
- Bypass failing tests with `@Ignore`, skip flags, or weakened assertions.

## Dedicated agent

For autonomous QA loops, delegate to the `android-qa-agent` — it runs scenarios on the emulator and produces a structured PASS/FAIL/BLOCKED report without modifying source code.
