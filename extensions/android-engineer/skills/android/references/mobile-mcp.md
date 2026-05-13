# Mobile MCP (mobile-mcp)

How to use the `@mobilenext/mobile-mcp` server — the agent's "eyes and hands" on the device.

Source: https://github.com/mobile-next/mobile-mcp

## What it is

An MCP server (registered in `mcp/.mcp.json`) that exposes mobile-automation tools for Android devices and emulators.

- **Primary observation:** `mobile_list_elements_on_screen` returns a structured UI tree (text, resource-id, bounds) — use this first, no vision needed.
- **Fallback observation:** `mobile_take_screenshot` — only when expected elements are absent from the tree (custom-drawn views, games, WebView, visual layout regressions).

## Where mobile-mcp fits in the three-tier model

Plugin tools for device/app management → mobile-mcp for UI interaction → ADB shell as last resort. Full breakdown in `SKILL.md → Tool priority`.

The mapping below lists the mobile-mcp tools that cover each UI-side operation, so the agent picks mobile-mcp first and only falls back to raw ADB shell when mobile-mcp is unavailable:

| Action | mobile-mcp tool | ADB fallback (only if mobile-mcp is unavailable) |
|--------|-----------------|--------------------------------------------------|
| List devices | `mobile_list_available_devices` | `adb devices` |
| Install APK | `mobile_install_app` | `adb install` |
| Uninstall app | `mobile_uninstall_app` | `adb uninstall` |
| Launch app | `mobile_launch_app` | `adb shell am start` |
| Force-stop app | `mobile_terminate_app` | `adb shell am force-stop` |
| List installed apps | `mobile_list_apps` | `adb shell pm list packages` |
| UI state / elements | `mobile_list_elements_on_screen` | `adb shell uiautomator dump` |
| Screenshot (fallback) | `mobile_take_screenshot` | `adb exec-out screencap` |
| Tap | `mobile_click_on_screen_at_coordinates` | `adb shell input tap` |
| Swipe | `mobile_swipe_on_screen` | `adb shell input swipe` |
| Type text | `mobile_type_keys` | `adb shell input text` |
| Back / Home | `mobile_press_button BACK` / `HOME` | `adb shell input keyevent 4/3` |
| Open URL / deep link | `mobile_open_url` | `adb shell am start -a VIEW -d` |
| Read screen size | `mobile_get_screen_size` | `adb shell wm size` |
| Rotate device | `mobile_set_orientation` | `adb shell settings put system user_rotation` |

> Note: when an Android device-management plugin tool exposes an operation directly (e.g. listing devices, installing/launching the app, clearing app data), prefer the plugin tool over both mobile-mcp and ADB.

## Troubleshooting

- **No device found** → `mobile_list_available_devices` returned empty. See `references/device-setup.md` to bring up an emulator, or ask the user to attach a physical device.
- **Element not found by label** → call `mobile_list_elements_on_screen`, pick by resource-id / content-desc; fall back to coordinates.
- **Typing lands in wrong field** → tap the field first to focus, verify it's focused via `mobile_list_elements_on_screen`, then `mobile_type_keys`.
- **Screenshot is black** → content uses `FLAG_SECURE` (DRM, banking, password fields); nothing the agent can do.
- **Multiple devices attached** → select explicitly; for ADB-fallback commands pass `-s <serial>`.
