# Fixing a Build

Classify and fix Gradle / compile / KSP / KAPT / resource errors. Run gradle tasks through the available build/test capabilities — do not invoke `gradlew` from a shell yourself, and do not parse a raw shell session for errors.

## Steps

1. **Run the build and capture errors.** Trigger a build with task `:app:assembleDebug` (or the relevant module/variant). For test failures, run tests with task `test`. Read the captured error output from the build result.

2. **Categorize the error.**

   **Kotlin / Java compile error** (`unresolved reference`, `type mismatch`, `cannot find symbol`):
   - Open the file and line from the error.
   - Check if an import is missing, a type signature changed, or a dependency is absent.

   **Gradle sync / dependency** (`Could not resolve`, `Plugin not found`, `version conflict`):
   - Read `build.gradle.kts` and `libs.versions.toml`.
   - Verify the version exists (e.g., on Maven Central / Google Maven).
   - Re-run the build with task `:app:dependencies` (or `dependencies`) to inspect resolution.

   **KSP / KAPT** (annotation processing): re-run the build with task `:app:assembleDebug` and the `--stacktrace` flag, then look for `Caused by:` in the output.
   Typical causes:
   - Room schema mismatch (version not bumped after schema change).
   - Missing `@Dao`, `@Database`, or `@Entity` annotation.
   - Hilt missing `@HiltAndroidApp`, `@AndroidEntryPoint`, or `@Inject`.
   - Dagger module not installed in a component.

   **Resource error** (`resource not found`, `duplicate value for resource`): re-run the build with task `:app:mergeDebugResources` and look for `error` in the output.
   - Duplicate names across modules/flavors.
   - Missing resource in one flavor.
   - Invalid XML in `res/values/*.xml`.

   **Manifest merger** (`Attribute application@... is also present at ...`):
   - Read the full merger report at `app/build/outputs/logs/manifest-merger-debug-report.txt`.
   - Use `tools:replace` or `tools:node="replace"` on the offending attribute.

3. **Fix minimally.** Apply the smallest change that resolves the error. Do not refactor surrounding code.

4. **Verify.** Re-build with task `:app:assembleDebug` and confirm `BUILD SUCCESSFUL`.

## Common Quick Fixes

- Missing import → IDE or manual `import com.example.Foo`.
- API level issue → guard with `if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.X)`.
- Room migration missing → bump DB version, add a `Migration(from, to)` in the builder.
- Compose compiler / Kotlin version mismatch → with Kotlin 2.0+ the Compose compiler is bundled and versioned automatically; just update Kotlin. For Kotlin < 2.0: update `compose-compiler` to match the Kotlin version matrix.
- `Duplicate class` → exclude transitive dep: `exclude(group = "com.foo", module = "bar")`.
- `Execution failed for task ':app:checkDebugDuplicateClasses'` → re-run with task `:app:dependencies` and find the double.
