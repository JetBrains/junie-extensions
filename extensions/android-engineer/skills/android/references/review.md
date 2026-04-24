# Android Code Review

Review code or a git diff for Android-specific quality issues.

> **Reviewing R8/ProGuard keep rules?** If `r8-analyzer` skill is not already installed: `npx android-skills-pack install --target junie --skill r8-analyzer`

## Steps

1. **Get the code to review.**
   - Recent changes: `git diff main...HEAD`
   - Specific file: read it directly.

2. **Correctness.**
   - Does the logic actually implement what was intended?
   - Off-by-one, null risks, race conditions?
   - Are all error cases handled — not swallowed in empty `catch`?

3. **Android-specific checks.**

   **Memory leaks:**
   - Anything holding `Activity` / `Fragment` / `Context` beyond its lifecycle?
   - Listeners / callbacks unregistered in `onDestroy`?
   - Coroutines scoped to `viewModelScope` / `lifecycleScope` (not `GlobalScope`)?
   - Inner classes holding implicit outer-class references?

   **Threading:**
   - Network / disk off main thread (`Dispatchers.IO`)?
   - UI updated only on main thread?
   - Shared mutable state protected (`Mutex`, `StateFlow`)?
   - No `runBlocking` on main thread?

   **Lifecycle:**
   - Handles configuration changes (rotation, dark mode)?
   - State stored in `ViewModel`, not `Fragment` / `Activity`?
   - Fragment transactions safe (not after `onSaveInstanceState`)?
   - `collectAsStateWithLifecycle` used in Compose instead of plain `collectAsState`?

   **Performance:**
   - Bitmaps loaded via Coil / Glide with proper sizing?
   - `RecyclerView` using `DiffUtil` / `ListAdapter`?
   - Expensive ops off main thread?
   - Compose: `remember` used where needed; no unnecessary recompositions (stable / immutable types)?

   **Security:**
   - No hardcoded API keys, secrets, tokens?
   - `android:exported` explicitly set (`true` or `false`) on **every** Activity, Service and BroadcastReceiver that declares an `<intent-filter>` — required on Android 12+ (targetSdk 31+), the build will fail otherwise. Non-exported components that have no intent-filter don't need it, but setting it explicitly is still preferred.
   - `usesCleartextTraffic="false"` unless explicitly needed?
   - WebView `setJavaScriptEnabled(true)` only if strictly required?

4. **Code quality.**
   - Naming follows Kotlin / Android conventions?
   - Duplicated logic that should be extracted?
   - Magic numbers / hardcoded strings (use resources)?
   - Meaningful error handling (not `catch (e: Exception) {}`)?

5. **Output the review.** Severity-bucketed:
   - **Critical** — bugs, crashes, data-loss risks, security. MUST fix.
   - **Major** — perf issues, memory leaks, bad patterns. SHOULD fix.
   - **Minor** — naming, style, nitpicks. Optional.

   For each issue: `file:line` — description — suggested fix.
