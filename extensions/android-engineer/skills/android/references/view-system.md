# View System / XML UI

Project-specific policy for Android projects using XML layouts, ViewBinding, RecyclerView and Fragments. Generic API knowledge (`ViewBinding.inflate`, `ListAdapter`, `supportFragmentManager.commit`, `MaterialAlertDialogBuilder`) is assumed.

## When this applies

- Project has `res/layout/*.xml` and no `setContent {}` in activities.
- `buildFeatures { viewBinding = true }` in `build.gradle.kts`, or task explicitly says "don't add Compose".
- Compose dependency is absent from `libs.versions.toml`.

## Java → Kotlin migration

If migrating Java files to Kotlin and `kotlin-tooling-java-to-kotlin` skill is not installed:
`npx skills add Kotlin/kotlin-agent-skills --skill kotlin-tooling-java-to-kotlin -a junie -y`

## Review checklist for View system code

- `_binding = null` in `onDestroyView()` — prevents leaking the view hierarchy into the Fragment.
- No `binding.*` access after `onDestroyView` — crashes with NPE.
- Fragment transactions only when `isAdded && !isDetached`.
- `RecyclerView` uses `ListAdapter` + `DiffUtil.ItemCallback`, never plain `RecyclerView.Adapter` with `notifyDataSetChanged`.
- No `Context` / `View` stored in ViewModel.
- `LiveData.observe` is called with `viewLifecycleOwner`, not `this` (Fragment).
- `StateFlow` is collected inside `viewLifecycleOwner.lifecycleScope` + `repeatOnLifecycle(STARTED)` — never bare `launch { collect }`.
- Prefer `StateFlow` even in View system projects; keep `LiveData` only if the project already uses it.
- Use `isVisible` / `isGone` (androidx ktx) instead of `View.VISIBLE` / `GONE`.
