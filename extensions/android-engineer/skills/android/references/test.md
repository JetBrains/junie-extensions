# Writing & Running Tests

Unit tests (VM / UseCase / Repository) and UI tests (Compose / Espresso). Run gradle test tasks through the available build/test capabilities — do not invoke `gradlew` from a shell yourself.

## Choose the right test type

| Type | Location | Tools | Gradle task |
|------|----------|-------|-------------|
| Unit (logic) | `src/test/` | JUnit5 (requires `de.mannodermaus.junit5` Gradle plugin — not built into AGP; if the project uses JUnit4, skip the plugin), MockK, kotlinx-coroutines-test, Turbine | `test` |
| UI / Integration | `src/androidTest/` | Compose Testing, Espresso, Hilt test rules | `connectedAndroidTest` |
| Screenshot | `src/androidTest/` or Paparazzi | Paparazzi / Showkase / Shot | `verifyPaparazziDebug` |

## What to cover

- **Happy path** — normal success.
- **Error path** — network error, null / empty inputs, timeouts.
- **Edge cases** — empty list, zero / max values, very long strings, rapid-fire calls.
- **State transitions** — Loading → Success, Loading → Error, retry after Error.

## Running

Use the available test capability and pass the gradle task plus an optional filter:

- task `test` — all JVM unit tests.
- task `test --tests "*.UserViewModelTest"` — single class.
- task `connectedAndroidTest` — instrumented tests on the currently connected device / emulator.
- task `:app:connectedDebugAndroidTest --tests "*.UserScreenTest"` — single instrumented class.

HTML report: `app/build/reports/tests/test/index.html`.

## Rules

- Name tests: `` `given [precondition] when [action] then [expected result]` ``.
- **Mock at the `ApiService` / `Dao` boundary — test the Repository itself.** The Repository contains real logic (cache-first, API fallback, error mapping); mocking it whole hides that logic. Mock Retrofit services and Room DAOs, then exercise `UserRepository` as a unit.
- When testing a **ViewModel** in isolation, mocking the Repository is fine — the Repository has its own dedicated test.
- Use `UnconfinedTestDispatcher` for simple cases, `StandardTestDispatcher` when you need manual control.
- For Flow, use **Turbine** (`flow.test { ... awaitItem() }`).
- For UI tests that require visual confirmation on a running emulator, read the on-screen element tree after the test and assert the expected elements are present.
