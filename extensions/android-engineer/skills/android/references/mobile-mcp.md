# Mobile MCP (mobile-mcp)

How to use the `@mobilenext/mobile-mcp` server — the agent's "eyes and hands" on the device.

Source: https://github.com/mobile-next/mobile-mcp

## What it is

An MCP server (registered in `mcp/.mcp.json`) that exposes mobile-automation tools for Android devices and emulators.

- **Primary observation:** `mobile_list_elements_on_screen` returns a structured UI tree (text, resource-id, bounds) — use this first, no vision needed.
- **Fallback observation:** `mobile_take_screenshot` — only when expected elements are absent from the tree (custom-drawn views, games, WebView, visual layout regressions).

## Mapping: prefer mobile-mcp over ADB

The following actions MUST go through mobile-mcp — **do not shell out to `adb`** for them:

| Action | mobile-mcp tool | (old adb equivalent — **don't use**) |
|--------|-----------------|--------------------------------------|
| List devices | `mobile_list_available_devices` | ~~`adb devices`~~ |
| Install APK | `mobile_install_app` | ~~`adb install`~~ |
| Uninstall app | `mobile_uninstall_app` | ~~`adb uninstall`~~ |
| Launch app | `mobile_launch_app` | ~~`adb shell am start`~~ |
| Force-stop app | `mobile_terminate_app` | ~~`adb shell am force-stop`~~ |
| List installed apps | `mobile_list_apps` | ~~`adb shell pm list packages`~~ |
| UI state / elements | `mobile_list_elements_on_screen` | ~~`adb shell uiautomator dump`~~ |
| Screenshot (fallback) | `mobile_take_screenshot` | ~~`adb exec-out screencap`~~ |
| Tap | `mobile_click_on_screen_at_coordinates` | ~~`adb shell input tap`~~ |
| Swipe | `mobile_swipe_on_screen` | ~~`adb shell input swipe`~~ |
| Type text | `mobile_type_keys` | ~~`adb shell input text`~~ |
| Back / Home | `mobile_press_button BACK` / `HOME` | ~~`adb shell input keyevent 4/3`~~ |
| Open URL / deep link | `mobile_open_url` | ~~`adb shell am start -a VIEW -d`~~ |
| Read screen size | `mobile_get_screen_size` | ~~`adb shell wm size`~~ (reads dimensions) |
| Rotate device | `mobile_set_orientation` | ~~`adb shell settings put system user_rotation`~~ |

## What mobile-mcp does NOT do — use ADB

mobile-mcp has no tool for any of these, so the agent must fall back to `adb` via shell:

| Need | ADB command |
|------|-------------|
| Read crashes / errors | `adb logcat -d *:E \| tail -N` |
| Logs by app PID | `adb logcat -d --pid=$(adb shell pidof -s com.pkg)` |
| Clear buffer before reproducing | `adb logcat -c` |
| Reset app data (no uninstall) | `adb shell pm clear com.pkg` |
| ANR traces | `adb pull /data/anr/traces.txt` |
| Grant / revoke runtime permissions | `adb shell pm grant \| pm revoke com.pkg <permission>` |
| Toggle Wi-Fi / data | `adb shell svc wifi disable\|enable` / `svc data …` |
| System settings (dark mode, airplane, locale) | `adb shell cmd uimode night yes`, `settings put …` |
| Port forwarding | `adb forward tcp:… tcp:…` / `adb reverse …` |
| Push / pull arbitrary files | `adb push`, `adb pull` |
| Device build info | `adb shell getprop ro.build.version.release` |
| Bug report | `adb bugreport bugreport.zip` |
| Running `./gradlew` | not device-related, but part of the same flow |

## Troubleshooting

- **No device found** → `mobile_list_available_devices` returned empty. See `references/device-setup.md` to bring up an emulator (tries to find the `emulator` binary in `PATH` / `$ANDROID_HOME` / Android Studio default SDK path, then launches the first AVD), or ask the user to attach a physical device.
- **Element not found by label** → call `mobile_list_elements_on_screen`, pick by resource-id / content-desc; fall back to coordinates.
- **Typing lands in wrong field** → tap the field first to focus, verify it's focused via `mobile_list_elements_on_screen`, then `mobile_type_keys`.
- **Screenshot is black** → content uses `FLAG_SECURE` (DRM, banking, password fields); nothing the agent can do.
- **Multiple devices attached** → select explicitly; for ADB commands pass `-s <serial>`.
