# ADB Fallback Cheat Sheet

ADB shell commands are a **last-resort fallback**. Use them only when neither plugin tools (device management, app lifecycle, logcat, crash/ANR readers, permissions, network, dark mode, Compose preview) nor mobile-mcp (UI element tree, taps, swipes, type, orientation, open-url, screenshot fallback) are available — for example, on a plugin version that doesn't yet expose a particular operation, or when an MCP server failed to start.

> **IMPORTANT:** `adb logcat` MUST always be invoked with `-d` — without it the command streams forever and hangs the agent session.

## When to reach for ADB (fallback only)

Reach for ADB shell only when the corresponding plugin tool / MCP tool is not available:

- Reading logs (`logcat`, ANR traces, tombstones, bugreport).
- Resetting app state without uninstall (`pm clear`).
- Runtime permissions (`pm grant` / `pm revoke`).
- System-level settings (network, locale, dark mode, airplane mode, user rotation).
- File transfer to/from the device (`push` / `pull`).
- Port forwarding (`forward` / `reverse`).
- Device properties and diagnostics (`getprop`, `dumpsys`, `pidof`).

If a plugin tool or mobile-mcp tool already covers the operation, prefer it — ADB is the slowest and least-structured option.

## Multi-device

```bash
adb -s <serial> <cmd>               # target a specific device
adb start-server / kill-server      # restart adb daemon (if MCP loses connection)
```

When more than one device is attached, always pass `-s <serial>` on ADB commands.

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
adb shell am send-trim-memory com.example.app MODERATE  # requires app's android:debuggable="true" OR `adb root`; otherwise silently ignored. Verify via `adb logcat -d | grep onTrimMemory`.
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

- To clear logcat, reproduce, then dump: `adb logcat -c && <reproduce> && adb logcat -d *:E | tail -50`.
- When multiple devices are attached, always pass `-s <serial>`.
- If `adb` itself is missing: `brew install --cask android-platform-tools` (macOS) or install via Android Studio → SDK Manager → Platform-Tools.
