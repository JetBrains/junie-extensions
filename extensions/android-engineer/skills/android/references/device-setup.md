# Device Setup

How to get a working Android device (emulator or physical) before running any skill that needs one (`qa.md`, `debug.md`, autonomous QA agent).

## Steps

1. **Check if a device is already connected** — list connected devices and emulators.
   - Returns a device → proceed with the task.
   - Returns empty → continue to step 2.

2. **List available AVDs** — list configured Android Virtual Devices.
   - Returns one or more AVDs → start the first one (`start_android_emulator`). The tool returns when boot completes — proceed immediately, do **not** insert `sleep`. Then retry step 1.
   - Returns empty → continue to step 3.

3. **Create an AVD** — run `create_android_avd` with just a name (it picks `pixel_7` + latest installed `google_apis` image by default). Then run `start_android_emulator` and retry step 1.
   - If it fails with a missing system image error → continue to step 4.

4. **Ask the user.**

> The required Android system image is not installed. Please install it via Android Studio → Tools → SDK Manager → SDK Platforms, select the system image, click Apply. Then let me know.

Do **not** try to download or install Android SDK system images autonomously.
