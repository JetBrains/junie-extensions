# Device setup

How to get a working Android device (emulator or physical) before running any skill that needs one (`qa.md`, `debug.md`, autonomous QA agent).

Describe what you need at each step — the runtime picks the right tool. Prefer native capabilities over `adb` / `emulator`; a direct shell call is acceptable only as a **declared fallback** when a needed capability is missing or fails in the current environment (say which one and why).

## 1. Preflight check

List the devices currently visible to the IDE.

- At least one online device → use it for the task.
- No device → continue to step 2.

## 2. Pick an AVD to start

List available AVDs on the host.

- At least one AVD → take the first one (or one explicitly chosen by the user) and continue to step 3.
- None → continue to step 4.

## 3. Start the emulator

Start the chosen AVD. On success the result includes the adb serial of the freshly booted emulator (e.g. `emulator-5554`); use that serial for subsequent device-targeted actions.

On failure, the result contains a diagnostic message (SDK not configured, emulator binary missing, AVD not found, boot timeout). Surface it to the user — do not retry blindly.

## 4. No AVDs available

Create a new Pixel-class AVD with the latest installed `google_apis` system image matching the host architecture, then go to step 3 with the freshly created AVD.

If creation fails with a message like *"No installed 'google_apis' system image found ..."*, fall through to step 5: the host has no usable system image, and the agent does **not** download SDK packages on its own.

## 5. Fallback — ask the user

> No AVD is available and no `google_apis` system image is installed on this host. Please open Android Studio → Tools → SDK Manager and install a system image (e.g. `Google APIs Intel x86_64 Atom System Image` for the latest API level), then let me know — or attach a physical device with USB debugging enabled.

Do **not** try to install the Android SDK, accept licenses, or download system images autonomously — it's heavy, interactive, and usually fails without human input.
