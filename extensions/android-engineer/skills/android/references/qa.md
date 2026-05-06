# Manual QA on Emulator

Run scenarios on a connected emulator (or device) by inspecting the structured UI state and verifying via logcat. Describe **what you need** at each step — the runtime picks the right tool.

Device-layer rules (UI through `mobile-mcp`, prefer native over shell, declared fallback, element tree as primary observation channel) are defined in `guidelines/android.md` and apply throughout this workflow — not repeated here. If `mobile-mcp` cannot be enabled when a scenario needs UI driving, mark it `BLOCKED — mobile-mcp not enabled` and continue with the rest of the report.

## Steps

1. **Understand what to test.** Identify the screen / feature. List the scenarios you will cover.

2. **Make sure a device is available.** If no device is currently visible to the IDE, follow `references/device-setup.md` to bring up an emulator (or ask the user to attach a physical device).

3. **Clear the logcat ring buffer** so subsequent reads only contain the new run.

4. **Launch the app** by package name.

5. **Reset state if needed** — terminate the app, clear its application data, then launch it again. Use this whenever you need a clean first-run state, or whenever the previous scenario left the app in an unexpected state.

6. **For each scenario, follow the closed loop:**
   1. Read the on-screen element tree to capture the current UI state.
   2. Perform an action — tap (use coordinates resolved from the tree by resource-id or text, never hardcoded pixels), swipe, type text, press a hardware button (BACK / HOME / ENTER), or set orientation.
   3. Read the element tree again to verify the screen actually changed as expected.
   4. Check recent errors in logcat (last ~20 ERROR-level entries) — or fetch the last fatal-exception block — to catch silent crashes.
   5. Mark: **PASS / FAIL / BUG**.

   If an expected element is genuinely not visible in the tree (custom-drawn UI, WebView, suspected visual regression) → take a screenshot as a fallback. Otherwise stay on the tree.

7. **Document bugs.** For each bug:
   - The element tree of the broken state (copy from the observation step).
   - Exact steps to reproduce.
   - Expected vs actual behavior.
   - Relevant logcat lines (recent errors or the last fatal-exception block).

## Common scenarios

- **Happy path** — complete the main flow successfully.
- **Empty state** — what shows with no data?
- **Error state** — disconnect the network (toggle Wi-Fi off, toggle mobile data off).
- **Edge input** — very long text, special characters, empty fields.
- **Back navigation** — press BACK throughout the flow; does it work correctly?
- **Rotation** — switch orientation between landscape and portrait — does state persist?
- **Permissions** — revoke a runtime permission (e.g. CAMERA) to test the deny path; grant it back to test the granted path.
- **Dark mode** — enable system-wide dark mode (note: it affects all apps on the device).
- **Deep links** — open a `myapp://...` URL on the device.
- **ANR diagnosis** — when an ANR is suspected, read ANR traces (only available on debuggable / userdebug builds).

## Notes

- Don't hardcode pixel coordinates: resolve elements through the on-screen element tree (by resource-id or text) and tap their bounds-center. This is resilient to screen size and rotation.
- For text input: first tap the field to focus it, confirm focus via the element tree, then type.
- For actions that are deliberately not covered by a native tool (`bugreport` dumps, arbitrary file push/pull on the device, port forwarding, raw `dumpsys`), prefer to note them as a tool gap and continue with the rest of the scenario. If the scenario truly cannot proceed without one, a direct `adb` call is acceptable as a declared fallback — record what you ran and why in the scenario notes.
