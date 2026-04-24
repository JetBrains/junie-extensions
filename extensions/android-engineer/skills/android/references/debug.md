# Debugging a Crash

Diagnose a crash or unexpected behavior in an Android app using logcat + source reading + visual evidence.

## Steps

1. **Get recent errors from logcat.**
   ```bash
   adb logcat -d -v brief *:E | tail -100
   ```
   Look for: `FATAL`, `AndroidRuntime`, `Exception`, `Error`, `ANR in`.

2. **Parse the stacktrace.**
   - Identify exception type and message.
   - Find the first frame in the app's own package (e.g. `<package>.*`) — that's the origin.
   - Note file, class, method, line number.

3. **Read the relevant code.** Open the file from the stacktrace; read ±50 lines around the crash line, plus any classes/functions in the call chain.

4. **Read UI state.** Call `mobile_list_elements_on_screen` to see what is on screen at the moment of the crash. If the element tree is empty or unhelpful, fall back to `mobile_take_screenshot`.

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
   - `./gradlew assembleDebug` — must compile.
   - Reinstall via mobile-mcp: `mobile_install_app` on the freshly built APK (typically under `app/build/outputs/apk/<flavor>/<buildType>/` — find it with `find app/build/outputs/apk -name '*.apk' -newer ...`), then `mobile_launch_app`.
   - Reproduce the scenario; `mobile_list_elements_on_screen` + `adb logcat -d *:E | tail -30` to confirm the crash is gone.

## Notes

- Filter by app PID to reduce noise:
  ```bash
  adb logcat -d --pid=$(adb shell pidof -s <package>)
  ```
- For ANRs: `adb pull /data/anr/traces.txt` and inspect thread states.
- For tombstones: `adb shell ls /data/tombstones` (requires rooted emulator or debug build).
- Clear logcat before reproducing: `adb logcat -c`, then reproduce, then dump.
