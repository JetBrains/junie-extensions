# Device setup

How to get a working Android device (emulator or physical) before running any skill that needs one (`qa.md`, `debug.md`, autonomous QA agent).

## 1. Preflight check

Call **`mobile_list_available_devices`**.

- Returns a device → proceed with the task.
- Returns empty → continue to step 2.

## 2. Find the `emulator` binary

Try these in order, stop on the first that works:

1. `emulator -list-avds` — works if `emulator` is in `PATH`.
2. `$ANDROID_HOME/emulator/emulator -list-avds` — if `$ANDROID_HOME` is set.
3. `~/Library/Android/sdk/emulator/emulator -list-avds` — macOS default Android Studio path.
4. `~/Android/Sdk/emulator/emulator -list-avds` — Linux default Android Studio path.

If all four fail (`command not found` / no such file) → go to step 4.

## 3. Launch the first AVD

Take the first line from the `-list-avds` output of step 2 — that's `<avd-name>`. Launch it in the background using the same `emulator` path that worked:

```
<emulator-path> -avd <avd-name> >/dev/null 2>&1 &
```

Then retry `mobile_list_available_devices` every few seconds until it returns a device (boot typically takes 30–120 s on first launch).

If `-list-avds` returned empty (no AVD configured) → go to step 4.

## 4. Fallback — ask the user

> Please start an emulator from Android Studio (Device Manager → ▶) or attach a physical device with USB debugging enabled, then let me know.

Do **not** try to install the Android SDK, create AVDs, or download system images autonomously — it's heavy, interactive, and usually fails without human input.
