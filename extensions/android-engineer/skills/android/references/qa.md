# Manual QA on Emulator

Run scenarios on the emulator by visually inspecting the UI and verifying via logcat.

**Observation:** use the structured UI element tree (via mobile-mcp) as the primary way to read screen state — it returns element text, resource-ids, and bounds without needing vision. Fall back to a screenshot only when an element is missing from the tree (custom views, WebView, visual glitches). Never use `sleep` or arbitrary delays between observations — if a screen looks unsettled, re-read the element tree.

**For UI / layout regressions:** before reproducing on the emulator, render the relevant `@Preview` composables via the headless preview renderer — it visualizes the layout instantly without a device run and often surfaces layout bugs (clipped text, wrong padding, missing previews) without any QA-loop iterations.

## Steps

1. **Understand what to test.** Identify the screen / feature. List scenarios to cover.

2. **Check a device is available.** If none found, follow `references/device-setup.md` to bring up an emulator (or ask the user to attach a physical device), then retry.

3. **Launch the app** via `run_android_app` (pass the absolute path to the entry-point file — it builds, installs, and launches in one step). If `run_android_app` is unavailable, use `launch_android_app` followed by `wait_for_android_app_launch` to confirm the process started. Proceed immediately after the tool returns — do not insert `sleep`.

4. **Reset state if needed** — clear app data for the package via the plugin tool, then relaunch.

5. **For each scenario, follow the closed loop:**
   1. Read the UI element tree (via mobile-mcp) — capture current elements, texts, resource-ids.
   2. Act via mobile-mcp using coordinates resolved from the element tree:
      - tap on element coordinates
      - swipe
      - type text
      - press button (`BACK` / `HOME` / `ENTER`)
   3. Read the UI element tree again — verify the UI changed as expected.
   4. Check logcat (via the plugin tool) for errors — catch silent crashes.
   5. Mark: **PASS / FAIL / BUG**.

   If an expected element is not visible in the tree → take a screenshot to check for custom-drawn UI or visual regressions.

6. **Document bugs.** For each bug:
   - UI element tree of the broken state (copy from the element-tree output).
   - Exact steps to reproduce.
   - Expected vs actual behavior.
   - Relevant logcat lines.

## Common scenarios

- **Happy path** — complete the main flow successfully.
- **Empty state** — what shows with no data?
- **Error state** — disable network (via the plugin tool), then reproduce the flow.
- **Edge input** — very long text, special characters, empty fields.
- **Back navigation** — press `BACK` throughout the flow; does it work correctly?
- **Rotation** — switch orientation between landscape and portrait — does state persist?
- **Permissions** — revoke the relevant permission via the plugin tool, then try the flow that needs it.
- **Low memory** — send a trim-memory signal to the app process.
- **Dark mode** — switch to dark mode via the plugin tool, verify theming.
- **Deep links** — open a `myapp://some/path` URL via mobile-mcp.

## Notes

- Don't hardcode pixel coordinates: read the UI element tree to resolve the element by resource-id or text, then tap its bounds center. This is resilient to screen size and rotation.
- For text input: first tap the field to focus it, confirm it's focused via the element tree, then type.
- Never insert `sleep` between actions — always re-read the element tree to confirm the UI is in the expected state and proceed.
