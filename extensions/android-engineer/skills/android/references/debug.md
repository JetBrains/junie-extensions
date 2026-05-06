# Debugging a Crash

Diagnose a crash or unexpected behavior using logcat + source reading + the on-screen UI state. Describe what you need at each step (read recent errors, fetch the last fatal-exception block, install the rebuilt APK, …) — the runtime picks the right tool. Prefer native capabilities over `adb`; a direct shell call is acceptable only as a **declared fallback** when a needed capability is missing or fails in the current environment.

## Steps

1. **Get recent errors from logcat.** Read the last ~100 ERROR-level entries on the target device. Look for: `FATAL`, `AndroidRuntime`, `Exception`, `Error`, `ANR in`. For a single fatal-exception block, fetch the last crash for the app's package — it returns the aggregated stack trace already.

2. **Parse the stacktrace.**
   - Identify exception type and message.
   - Find the first frame in the app's own package — that's the origin.
   - Note file, class, method, line number.

3. **Read the relevant code.** Open the file from the stacktrace; read ±50 lines around the crash line, plus any classes/functions in the call chain.

4. **Read UI state at the moment of the crash.** Read the on-screen element tree to see what was displayed — this is the primary, default channel. Take a screenshot only as a fallback when the tree genuinely cannot describe the screen (custom-drawn UI, WebView, game, suspected visual regression).

5. **Classify the root cause.** Common Android crashes:
   - `NullPointerException` → missing null check, `lateinit` not initialized.
   - `NetworkOnMainThreadException` → network call outside coroutine / `Dispatchers.IO`.
   - `IllegalStateException: Can not perform this action after onSaveInstanceState` → fragment transaction after state save.
   - `OutOfMemoryError` → unrecycled bitmap, leaked activity holding memory.
   - `ClassCastException` → wrong `ViewHolder` type in `RecyclerView`.
   - `WindowManager$BadTokenException` → showing dialog on a destroyed activity.
   - `ForegroundServiceStartNotAllowedException` → starting FGS from background (Android 12+).

6. **Fix and verify.**
   - Apply the fix.
   - Rebuild the debug APK (gradle task `:app:assembleDebug`).
   - Deploy: prefer the IDE-driven build-and-run path when a Run Configuration exists; otherwise install the rebuilt APK, launch the app by package + main activity, and wait for the app process to actually appear.
   - Reproduce the scenario; read the element tree and recent ERROR logcat entries (or the last fatal-exception block) to confirm the crash is gone.

## Notes

- To reduce noise, narrow the logcat read to the app's package — the runtime resolves the process pid internally, no need to look it up by hand.
- For ANRs: read ANR traces from the device (only available on debuggable / userdebug builds; production retail devices block this path).
- Always clear the logcat ring buffer before reproducing, then read again — that way the captured output is exactly the new run.
- Diagnostics that are intentionally **not** exposed (`bugreport` dumps, raw `dumpsys`, tombstone files, arbitrary file push/pull) are usually noise for an LLM-driven debug loop — prefer to raise them as a tool gap. If one is genuinely required to make progress, a direct `adb` call is acceptable as a declared fallback; say what you ran and why.
