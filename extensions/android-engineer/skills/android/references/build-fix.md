# Fixing a Build

Classify and fix Gradle / compile / KSP / KAPT / resource errors.

> **Google Android skills-pack:** for build-tooling upgrades (AGP, R8, Play Services, etc.) check `npx android-skills-pack list` first and install a matching skill with `npx android-skills-pack install --target junie --skill <name>`. If no exact match, pick the closest one from the list or proceed without.

## Steps

1. **Run the build and capture errors:**
   ```bash
   ./gradlew assembleDebug 2>&1 | grep -A 5 "error:"
   # For test failures:
   ./gradlew test 2>&1 | grep -A 10 "FAILED"
   ```

2. **Categorize the error.**

   **Kotlin / Java compile error** (`unresolved reference`, `type mismatch`, `cannot find symbol`):
   - Open the file and line from the error.
   - Check if an import is missing, a type signature changed, or a dependency is absent.

   **Gradle sync / dependency** (`Could not resolve`, `Plugin not found`, `version conflict`):
   - Read `build.gradle.kts` and `libs.versions.toml`.
   - Verify version exists (e.g., on Maven Central / Google Maven).
   - Run `./gradlew dependencies | grep -i conflict` to see resolution issues.

   **KSP / KAPT** (annotation processing):
   ```bash
   ./gradlew assembleDebug --stacktrace 2>&1 | grep -A 20 "Caused by"
   ```
   Typical causes:
   - Room schema mismatch (version not bumped after schema change).
   - Missing `@Dao`, `@Database`, or `@Entity` annotation.
   - Hilt missing `@HiltAndroidApp`, `@AndroidEntryPoint`, or `@Inject`.
   - Dagger module not installed in a component.

   **Resource error** (`resource not found`, `duplicate value for resource`):
   ```bash
   ./gradlew mergeDebugResources 2>&1 | grep "error"
   ```
   - Duplicate names across modules/flavors.
   - Missing resource in one flavor.
   - Invalid XML in `res/values/*.xml`.

   **Manifest merger** (`Attribute application@... is also present at ...`):
   - Read the full merger report: `app/build/outputs/logs/manifest-merger-debug-report.txt`.
   - Use `tools:replace` or `tools:node="replace"` on the offending attribute.

3. **Fix minimally.** Apply the smallest change that resolves the error. Do not refactor surrounding code.

4. **Verify.**
   ```bash
   ./gradlew assembleDebug
   ```
   Confirm `BUILD SUCCESSFUL`.

## Common Quick Fixes

- Missing import → IDE or manual `import com.example.Foo`.
- API level issue → guard with `if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.X)`.
- Room migration missing → bump DB version, add a `Migration(from, to)` in the builder.
- Compose compiler / Kotlin version mismatch → with Kotlin 2.0+ the Compose compiler is bundled and versioned automatically; just update Kotlin. For Kotlin < 2.0: update `compose-compiler` to match the Kotlin version matrix.
- `Duplicate class` → exclude transitive dep: `exclude(group = "com.foo", module = "bar")`.
- `Execution failed for task ':app:checkDebugDuplicateClasses'` → run `./gradlew :app:dependencies` and find the double.
