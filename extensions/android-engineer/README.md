# android-engineer

Turns Junie into a senior Android engineer. Covers the full Android stack — Kotlin-first (Java legacy supported), Jetpack Compose and View system (XML + ViewBinding), MVVM, Coroutines/Flow, Room, Retrofit, Hilt — and adds a closed-loop workflow for running on real devices and emulators. Device interaction is layered: **plugin tools first** (device management, app lifecycle, logcat, crash/ANR reports, permissions, network, dark mode, Compose preview), **[@mobilenext/mobile-mcp](https://www.npmjs.com/package/@mobilenext/mobile-mcp)** for UI interaction (UI element tree, taps, swipes, type), and raw **ADB** as a last-resort fallback when neither tier exposes an operation.

## Features

- **Skills** for the full Android loop:
  - `android-implement` — implement a feature bottom-up (data → VM → UI).
  - `android-debug` — diagnose crashes from logcat and fix them.
  - `android-build-fix` — classify and fix Gradle / compile / KSP / resource errors.
  - `android-test` — unit + Compose/Espresso tests with MockK and coroutines-test.
  - `android-review` — Android-specific review: leaks, threading, lifecycle, perf.
  - `android-qa` — manual QA loop on the emulator (read UI tree → act → read UI tree → logcat).
- **Agent** `android-qa-agent` — autonomous QA engineer that runs scenarios on the emulator without modifying code.
- **Guidelines** with strict Kotlin/Compose/MVVM rules (no Java, no XML for new UI, no Context in ViewModels, etc.).
- **MCP** — registers `@mobilenext/mobile-mcp` to give the agent "eyes and hands": structured UI element tree and device interaction.

## Requirements

- `adb` in `PATH` (from Android SDK platform-tools).
- `emulator` in `PATH` (or under `$ANDROID_HOME/emulator/` / the Android Studio default SDK path) — optional, needed only for agent-driven emulator bootstrap (`references/device-setup.md`). Without it the agent will ask the user to start one from Android Studio.
- Android emulator running or a physical device attached (verify by listing connected devices through plugin tools or mobile-mcp).
- `npx` available for the `mobile-mcp` server.
- `./gradlew` in the target project.

> Not covered by this extension: physical device actions (USB, RSA prompts), `FLAG_SECURE` screens (black screenshots on banking/DRM/password fields), Android Studio internal actions (Apply Changes, Layout Inspector, Profiler), native (NDK) crash symbolication, Play Console / Firebase operations.

## How the device loop works

The agent uses three layers in priority order:

| Tier | Layer | Role | Typical operations |
|------|-------|------|--------------------|
| 1 | **Plugin tools** | Device management, app lifecycle, diagnostics, system tweaks | list devices/AVDs, start/stop emulator, build/install/launch, clear app data, logcat, last crash, ANR traces, permissions, network, dark mode, Compose preview |
| 2 | **mobile-mcp** | UI interaction (eyes & hands) | read UI element tree, tap, swipe, type, back/home, orientation, open-url, screenshot fallback |
| 3 | **ADB shell** | Last-resort fallback | only when neither plugin tools nor mobile-mcp expose the operation (`skills/android/references/adb.md`) |

The core pattern across all skills is a **closed observation loop**:

```
read UI element tree → action → read UI element tree → read logcat
```

That's what lets the QA agent actually catch silent crashes, not just tap in the dark.

## Installation

Enable this extension in Junie. The `mcp/.mcp.json` registers the `mobile` MCP server on first use.

