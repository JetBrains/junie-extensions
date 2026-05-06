# android-engineer

Turns Junie into a senior Android engineer. Covers the full Android stack — Kotlin-first (Java legacy supported), Jetpack Compose and View system (XML + ViewBinding), MVVM, Coroutines/Flow, Room, Retrofit, Hilt — and adds a closed-loop workflow for running on real devices and emulators. UI interaction goes through the **[@mobilenext/mobile-mcp](https://www.npmjs.com/package/@mobilenext/mobile-mcp)** server, where the **structured on-screen element tree** is the primary observation channel (taps / swipes / type / app launch / terminate / orientation are resolved against it; screenshots are reserved for screens the tree cannot describe — custom-drawn views, WebView, games, visual regressions). Device-state and infrastructure (logcat, install, AVDs, emulator lifecycle, app data reset, runtime permissions, network, dark mode, ANR traces) go through Junie native tools. Direct `adb` / `gradlew` / `emulator` shell calls are reserved for declared fallbacks when a native capability is missing or fails.

## Features

- **Skills** for the full Android loop:
  - `android-implement` — implement a feature bottom-up (data → VM → UI).
  - `android-debug` — diagnose crashes from logcat and fix them.
  - `android-build-fix` — classify and fix Gradle / compile / KSP / resource errors.
  - `android-test` — unit + Compose/Espresso tests with MockK and coroutines-test.
  - `android-review` — Android-specific review: leaks, threading, lifecycle, perf.
  - `android-qa` — manual QA loop on the emulator: read the on-screen element tree → act → re-read the tree → check logcat. Screenshots are a fallback, not a default.
- **Agent** `android-qa-agent` — autonomous QA engineer that runs scenarios on the emulator without modifying code.
- **Guidelines** with strict Kotlin/Compose/MVVM rules (no Java, no XML for new UI, no Context in ViewModels, etc.).
- **MCP** — registers `@mobilenext/mobile-mcp` to give the agent "eyes and hands": structured UI element tree and device interaction.

## Requirements

- Android plugin enabled in the host IDE (Android Studio or IntelliJ Ultimate with the Android plugin) — Junie's native Android tools are gated on the IDE service exposed by this plugin.
- An installed Android SDK with at least one `google_apis` system image — required to start an emulator or create a new AVD.
- `npx` (Node.js v22+) available for the `mobile-mcp` server.
- A target project that builds via `gradlew` (Junie's build/test capabilities drive it).

> Not covered by this extension: physical device actions (USB, RSA prompts), `FLAG_SECURE` screens (black screenshots on banking/DRM/password fields), Android Studio internal actions (Apply Changes, Layout Inspector, Profiler), native (NDK) crash symbolication, Play Console / Firebase operations.

## How the device loop works

The agent uses two complementary layers:

| Layer | Role |
|-------|------|
| **mobile-mcp** | Eyes & hands (UI + app interaction). Primary channel: the **structured element tree** (text / resource-id / bounds). Actions: tap (resolved from the tree), swipe, type, orientation, app launch / terminate, open-url. Screenshots are kept as a fallback for screens the tree cannot describe. |
| **Junie native Android tools** | Device-state and infrastructure — device discovery, AVD listing, emulator lifecycle, AVD creation, APK install, headless build-install-launch, logcat (recent errors, last crash, ANR traces), application data reset, runtime permissions, Wi-Fi / mobile data toggle, system-wide dark mode, Compose preview rendering |

Skills and the QA agent describe **what they need** (read the on-screen UI, read recent ERROR logcat, install the rebuilt APK, reset app data, …) and let the runtime resolve the right tool. The core pattern is a **closed, structured observation loop**:

```
read on-screen element tree → act → read on-screen element tree → check recent ERROR logcat
```

Observation is **structured-first** — the agent reads the element tree, not screenshots. That's what lets the QA agent actually catch silent crashes, not just tap in the dark.

## Installation

Enable this extension in Junie. The `mcp/.mcp.json` registers the `mobile` MCP server on first use.
