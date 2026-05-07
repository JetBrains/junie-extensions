# Device Setup

How to get a working Android device (emulator or physical) before running any skill that needs one (`qa.md`, `debug.md`, autonomous QA agent).

## Steps

1. **Check if a device is already connected** — list connected devices and emulators.
   - Returns a device → proceed with the task.
   - Returns empty → continue to step 2.

2. **List available AVDs** — list configured Android Virtual Devices.
   - Returns one or more AVDs → start the first one, wait for it to boot (typically 30–120 s), then retry step 1.
   - Returns empty → go to step 3.

3. **Ask the user.**

> Please start an emulator from Android Studio (Device Manager → ▶) or attach a physical device with USB debugging enabled, then let me know.

Do **not** try to install the Android SDK, download system images, or create AVDs autonomously — it's heavy, interactive, and usually fails without human input.
