# Manual QA on Emulator

Run scenarios on the emulator by visually inspecting the UI and verifying via logcat.

**Rule of thumb:** UI interaction goes through `mobile-mcp`; device management, logs, and system state go through plugin tools.

**Observation:** use `mobile_list_elements_on_screen` (structured UI tree) as the primary way to read screen state — it returns element text, resource-ids, and bounds without needing vision. Fall back to `mobile_take_screenshot` only when an element is missing from the tree (custom views, WebView, visual glitches).

## Steps

1. **Understand what to test.** Identify the screen / feature. List scenarios to cover.

2. **Check a device is available.** If none found, follow `references/device-setup.md` to bring up an emulator (or ask the user to attach a physical device), then retry.

3. **Launch the app** via `mobile_launch_app` with the app's package name.

4. **Reset state if needed** — clear app data for the package, then relaunch.

5. **For each scenario, follow the closed loop:**
   1. `mobile_list_elements_on_screen` — read current UI state (elements, texts, resource-ids).
   2. Action via mobile-mcp:
      - `mobile_click_on_screen_at_coordinates` (use coords from `mobile_list_elements_on_screen` for a given resource-id / text)
      - `mobile_swipe_on_screen`
      - `mobile_type_keys`
      - `mobile_press_button BACK` / `HOME` / `ENTER`
   3. `mobile_list_elements_on_screen` — verify UI changed as expected.
   4. Check logcat for errors — catch silent crashes.
   5. Mark: **PASS / FAIL / BUG**.

   If an expected element is not visible in the tree → call `mobile_take_screenshot` to check for custom-drawn UI or visual regressions.

6. **Document bugs.** For each bug:
   - UI element tree of the broken state (copy from `mobile_list_elements_on_screen` output).
   - Exact steps to reproduce.
   - Expected vs actual behavior.
   - Relevant logcat lines.

## Common scenarios

- **Happy path** — complete the main flow successfully.
- **Empty state** — what shows with no data?
- **Error state** — disable network, then reproduce the flow.
- **Edge input** — very long text, special characters, empty fields (via `mobile_type_keys`).
- **Back navigation** — `mobile_press_button BACK` throughout the flow; does it work correctly?
- **Rotation** — `mobile_set_orientation landscape` / `portrait` — does state persist?
- **Permissions** — revoke the relevant permission, then try the flow that needs it.
- **Low memory** — send a trim-memory signal to the app process.
- **Dark mode** — switch to dark mode, verify theming.
- **Deep links** — `mobile_open_url "myapp://some/path"`.

## Notes

- Don't hardcode pixel coordinates: call `mobile_list_elements_on_screen` to resolve the element by resource-id or text, then pass its bounds center to `mobile_click_on_screen_at_coordinates`. This is resilient to screen size and rotation.
- For text input: first tap the field to focus it, confirm it's focused via `mobile_list_elements_on_screen`, then `mobile_type_keys`.
