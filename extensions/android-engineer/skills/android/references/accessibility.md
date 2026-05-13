# Accessibility

Android-specific accessibility policy. Generic a11y theory and Compose/View-system API surface are assumed knowledge — this file lists only the rules the agent must enforce.

## Rules

- **Every interactive element has a meaningful label.** Icon buttons, image buttons, custom-toggleable rows: `contentDescription` (View) or `Icon(..., contentDescription = "...")` / `Modifier.semantics { contentDescription = "..." }` (Compose). `null` is allowed **only** for purely decorative imagery.
- **Minimum touch target is 48×48dp.** Pad small icons or apply `Modifier.minimumInteractiveComponentSize()`; in XML use `minWidth` / `minHeight` 48dp or extend hit-rect via `TouchDelegate`.
- **Group related elements** that read as one unit (avatar + name + subtitle, list rows) using `Modifier.semantics(mergeDescendants = true) {}` — TalkBack focuses the group, not each child.
- **Use `clearAndSetSemantics`** to replace descendant semantics with a single coherent description (e.g. progress bars).
- **Set `Role`** when a composable acts as a control it isn't natively (`Role.Checkbox`, `Role.Switch`, `Role.RadioButton`, `Role.Tab`).
- **Expose dynamic state** via `stateDescription` (expanded/collapsed, selected, loading) — never rely on a visual cue alone.
- **Mark section headers** with `Modifier.semantics { heading() }` (Compose) or `android:accessibilityHeading="true"` (View) so users can navigate by heading.
- **`labelFor`** on standalone label `TextView`s pointing to their input field.
- **Decorative views** must be marked `importantForAccessibility="no"` (or use `tools:ignore="ContentDescription"` when the lint warning is intentional).
- **RecyclerView rows** whose meaning depends on data must set `itemView.contentDescription` in `onBindViewHolder`.

## Verification

- TalkBack pass: navigate the screen with TalkBack on — every element announces something meaningful, no "Button" / "Image" / silent focus.
- Accessibility Scanner (Google) — run on the screen for missing labels and small touch targets.
- Compose tests: assert labels exist via `onNodeWithContentDescription("...").assertIsDisplayed()`.
