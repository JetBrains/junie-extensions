# ADB Cheat Sheet

ADB (Android Debug Bridge) is used **only for things `mobile-mcp` cannot do**. For device listing, install/uninstall, launch/terminate, taps, swipes, text input, UI element tree, orientation, open-url and app listing — use `mobile-mcp` tools instead (see `mobile-mcp.md`).

> **IMPORTANT:** `adb logcat` MUST always be invoked with `-d` — without it the command streams forever and hangs the agent session.

## When to reach for ADB

Use ADB shell commands only for:

- Reading logs (`logcat`, ANR traces, tombstones, bugreport).
- Resetting app state without uninstall (`pm clear`).
- Runtime permissions (`pm grant` / `pm revoke`).
- System-level settings (network, locale, dark mode, airplane mode, user rotation).
- File transfer to/from the device (`push` / `pull`).
- Port forwarding (`forward` / `reverse`).
- Device properties and diagnostics (`getprop`, `dumpsys`, `pidof`).

Everything else → `mobile-mcp` tool.

## Multi-device

```bash
adb -s <serial> <cmd>               # target a specific device
adb start-server / kill-server      # restart adb daemon (if mobile-mcp loses connection)
```

(Use `mobile_list_available_devices` to get device serials; pass the serial with `-s` on ADB commands when more than one is attached.)

## Logcat

```bash
adb logcat -c                                        # clear buffer (before reproducing)
adb logcat -d *:E | tail -100                        # dump errors only
adb logcat -d -v brief *:E | tail -100               # brief format
adb logcat -d --pid=$(adb shell pidof -s com.example.app) | tail -200
adb logcat -d -v time MyTag:D *:S                    # only MyTag debug
adb logcat -d -T 1000                                # last 1000 lines
```

## App state reset

```bash
adb shell pm clear com.example.app                   # wipe app data (keeps APK installed)
```

(`mobile-mcp` can uninstall/reinstall via `mobile_uninstall_app` + `mobile_install_app`, but has no `pm clear`.)

## Runtime permissions

```bash
adb shell pm grant  com.example.app android.permission.CAMERA
adb shell pm revoke com.example.app android.permission.CAMERA
adb shell pm reset-permissions com.example.app
```

## System tweaks (for QA scenarios)

```bash
adb shell svc wifi disable / enable
adb shell svc data disable / enable
adb shell settings put global airplane_mode_on 1 && \
  adb shell am broadcast -a android.intent.action.AIRPLANE_MODE
adb shell "cmd uimode night yes"                     # dark mode
adb shell settings put system user_rotation 1        # landscape (0/1/2/3)
adb shell am send-trim-memory com.example.app MODERATE
```

## Files

```bash
adb push  local.txt /sdcard/
adb pull  /sdcard/remote.txt .
adb pull  /data/anr/traces.txt                       # ANR traces
adb shell ls /sdcard/Download
```

## Port forwarding (debug / dev server)

```bash
adb forward tcp:8080 tcp:8080                        # host → device
adb reverse tcp:3000 tcp:3000                        # device → host (e.g. Metro / dev server)
```

## Diagnostics

```bash
adb shell getprop ro.build.version.release           # Android version
adb shell getprop ro.product.model                   # device model
adb shell dumpsys package com.example.app | grep versionName
adb shell dumpsys activity top | head -40            # current activity/fragment stack
adb shell dumpsys window windows | grep mCurrentFocus
adb shell pidof -s com.example.app                   # PID of the app process
adb bugreport bugreport.zip                          # full system snapshot
```

## Tips

- To clear logcat, reproduce, then dump: `adb logcat -c && <action via mobile-mcp> && adb logcat -d *:E | tail -50`.
- When multiple devices attached, always pass `-s <serial>` on ADB commands.
- If `adb` itself is missing: `brew install --cask android-platform-tools` (macOS) or install via Android Studio → SDK Manager → Platform-Tools.
