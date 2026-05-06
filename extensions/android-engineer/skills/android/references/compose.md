# Android & Jetpack Compose

Project-specific policy for Compose code. Generic Compose API knowledge (Material 3, `LazyColumn`, `LaunchedEffect`, Hilt boilerplate, animation APIs) is assumed — don't re-derive it here.

## State management

- Prefer a **sealed interface** for UI state (`Loading` / `Success(data)` / `Error(msg)`) — prevents invalid combinations like user + error both set.
- Use a flat `data class` only when the screen has several independent flags (multiple simultaneous loaders, filters, etc.).
- Canonical `UserUiState` + ViewModel + Composable example lives in `SKILL.md` → "MVVM + UDF (Compose)". Do not duplicate it.

## State hoisting

- Stateless composable takes `value` + `onValueChange`, owns nothing.
- Stateful wrapper holds `remember { mutableStateOf(...) }` and delegates to the stateless one.
- Use `rememberSaveable` for state that must survive process death (search query, expanded flags, selected tab).
- Use `SavedStateHandle` in the ViewModel for state that must survive navigation / config changes.

## Navigation

**Navigation 3** (`androidx.navigation:navigation-compose:3.x`) is stable as of November 2025 and is the recommended path for new Compose projects — it gives you full ownership of the back stack as Compose state, enabling adaptive layouts and multi-pane UIs. Patterns in the rest of this file use Navigation 2 (`NavHost` / `NavController`) which is still fully supported.

## Lifecycle & side effects

- Collect flows with `collectAsStateWithLifecycle()` — never bare `collectAsState()` (keeps collecting in background).
- Wrap `repeatOnLifecycle(STARTED)` around manual `flow.collect { }` in Activities / Fragments.
- Use `LaunchedEffect(key)` for one-shot suspend work, `DisposableEffect` when you need `onDispose` cleanup, `derivedStateOf` to memoize expensive derivations.

## Stability & recomposition

- **Primary approach (Compose 1.6+):** enable strong skipping mode in `composeCompiler {}` — the compiler skips recomposition for unstable parameters automatically without manual annotations.
- `@Immutable` / `@Stable` are a last resort: use them only when the compiler still can't infer stability after strong skipping is on. Misapplied, they suppress recomposition incorrectly.
- Always pass a stable `key` to `items(list, key = { it.id })` in `LazyColumn` / `LazyRow`.
- Read theme tokens (`MaterialTheme.colorScheme.*`, `MaterialTheme.typography.*`) — never hardcode dp / sp / colors.

## Pitfalls LLMs get wrong

**`remember` without a key when the input changes:**
```kotlin
// Wrong — memoized value never updates when userId changes
val profile = remember { loadProfile(userId) }

// Correct — recomputes when userId changes
val profile = remember(userId) { loadProfile(userId) }
```

**Side effects directly in composition body:**
```kotlin
// Wrong — runs on every recomposition, causes infinite loops, fires duplicates
@Composable
fun MyScreen(vm: MyViewModel) {
    vm.loadData()           // side effect in composition — never do this
    analyticsTracker.track("screen_view")  // same problem
}

// Correct — runs once (or when key changes), tied to lifecycle
@Composable
fun MyScreen(vm: MyViewModel) {
    LaunchedEffect(Unit) { vm.loadData() }
    LaunchedEffect(Unit) { analyticsTracker.track("screen_view") }
}
```

**Passing ViewModel down the tree (ViewModel drilling):**
```kotlin
// Wrong — creates tight coupling, breaks preview, complicates testing
@Composable
fun ParentScreen(vm: MyViewModel) {
    ChildWidget(vm = vm)
}

// Correct — hoist state, pass only what the child needs
@Composable
fun ParentScreen(vm: MyViewModel) {
    val state by vm.state.collectAsStateWithLifecycle()
    ChildWidget(items = state.items, onItemClick = vm::onItemClick)
}
```

**`CompositionLocal` for ordinary dependencies:**
```kotlin
// Wrong — abuses CompositionLocal as a service locator
val LocalRepo = compositionLocalOf<UserRepository> { error("no repo") }

// Correct — pass dependencies explicitly or inject via hiltViewModel()
@Composable
fun UserScreen(vm: UserViewModel = hiltViewModel()) { ... }
```
