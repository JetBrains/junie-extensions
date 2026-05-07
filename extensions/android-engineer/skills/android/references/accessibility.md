# Accessibility

Android accessibility rules for Jetpack Compose and View system. Generic a11y theory is assumed — this covers Android-specific APIs and common mistakes.

## Compose

### Semantics basics

Every interactive element must have a meaningful label. The compiler won't warn you when it's missing.

```kotlin
// Wrong — icon button with no label, TalkBack says "Button"
IconButton(onClick = { }) {
    Icon(Icons.Default.Favorite, contentDescription = null)
}

// Correct
IconButton(onClick = { }) {
    Icon(Icons.Default.Favorite, contentDescription = "Add to favourites")
}
```

```kotlin
// Wrong — image conveys meaning but has no description
Image(painter = painterResource(R.drawable.banner), contentDescription = null)

// Correct — or null only when image is purely decorative
Image(painter = painterResource(R.drawable.banner), contentDescription = "Summer sale banner")
```

### Merge vs. clear semantics

Use `Modifier.semantics(mergeDescendants = true)` to group related elements into a single focusable node:

```kotlin
// Single TalkBack focus for the whole card, reads "John Doe, Senior Engineer"
Row(modifier = Modifier.semantics(mergeDescendants = true) {}) {
    Text("John Doe")
    Text("Senior Engineer")
}
```

Use `clearAndSetSemantics` when you want to replace all descendant semantics with a single custom description:

```kotlin
// Replaces "47" and progress bar semantics with one coherent sentence
LinearProgressIndicator(
    progress = { 0.47f },
    modifier = Modifier.clearAndSetSemantics {
        contentDescription = "Upload progress: 47%"
    }
)
```

### Roles and state

Set the `Role` when a composable acts as a specific control but isn't one natively:

```kotlin
Row(
    modifier = Modifier
        .toggleable(value = checked, onValueChange = onCheckedChange)
        .semantics { role = Role.Checkbox }
) { ... }
```

Expose dynamic state:

```kotlin
Modifier.semantics {
    stateDescription = if (isExpanded) "Expanded" else "Collapsed"
}
```

### Touch targets

Minimum touch target is **48×48dp**. Compose doesn't enforce this automatically.

```kotlin
// Small icon — pad it so TalkBack focus area is large enough
Icon(
    ...,
    modifier = Modifier
        .size(24.dp)
        .padding(12.dp)   // effective touch target = 48dp
)
```

Or use `Modifier.minimumInteractiveComponentSize()` (Compose 1.3+) which applies the 48dp minimum automatically.

### Headings

Mark section headers so TalkBack users can navigate by heading:

```kotlin
Text(
    text = "Recent Orders",
    modifier = Modifier.semantics { heading() }
)
```

## View system

- Every `ImageView` and `ImageButton` needs `android:contentDescription` or `tools:ignore="ContentDescription"` (decorative only).
- Every interactive `View` without visible text needs `android:contentDescription`.
- `android:importantForAccessibility="no"` for purely decorative views.
- `android:labelFor` on a `TextView` label pointing to its associated input field.
- `RecyclerView` items: set `itemView.contentDescription` in `onBindViewHolder` when the row's meaning depends on data.

## Verification

- Enable TalkBack and navigate through the feature with eyes closed — every element must announce something meaningful.
- Use the Accessibility Scanner app (Google) to catch missing labels and small touch targets automatically.
- In Compose: use `onNodeWithContentDescription(...)` in tests to assert labels exist.

```kotlin
composeTestRule.onNodeWithContentDescription("Add to favourites").assertIsDisplayed()
```
