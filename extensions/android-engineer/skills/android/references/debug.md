# Debugging a Crash

Diagnose a crash or unexpected behavior in an Android app using logcat + source reading + visual evidence.

## Steps

1. **Get recent errors from logcat.** Read logcat filtered by your app package and ERROR level. Look for: `FATAL`, `AndroidRuntime`, `Exception`, `Error`, `ANR in`.

2. **Parse the stacktrace.**
   - Identify exception type and message.
   - Find the first frame in the app's own package (e.g. `<package>.*`) — that's the origin.
   - Note file, class, method, line number.

3. **Read the relevant code.** Open the file from the stacktrace; read ±50 lines around the crash line, plus any classes/functions in the call chain.

4. **Read UI state.** Call `mobile_list_elements_on_screen` to see what is on screen at the moment of the crash. If the element tree is empty or unhelpful, fall back to `mobile_take_screenshot`.

5. **Classify the root cause.** Less obvious Android crashes:
   - `IllegalStateException: Can not perform this action after onSaveInstanceState` → fragment transaction after state save.
   - `WindowManager$BadTokenException` → showing dialog on a destroyed activity.
   - `ForegroundServiceStartNotAllowedException` → starting FGS from background (Android 12+).

6. **Fix and verify.**
   - Apply the fix.
   - `./gradlew assembleDebug` — must compile.
   - Run the app, reproduce the scenario, confirm logcat is clean.

## Notes

- Filter logcat by package name to reduce noise.
- For ANRs: use the ANR reader tool — it tries `/data/anr/` first, falls back to legacy traces and DropBox.
- Clear logcat before reproducing, then read it fresh after.
- If you see the crash but can't read logcat output, use the "last crash" reader — it parses logcat for the most recent `FATAL EXCEPTION` block automatically.
