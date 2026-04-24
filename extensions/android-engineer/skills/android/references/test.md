# Writing & Running Tests

Unit tests (VM / UseCase / Repository) and UI tests (Compose / Espresso).

## Choose the right test type

| Type | Location | Tools | Run |
|------|----------|-------|-----|
| Unit (logic) | `src/test/` | JUnit5 (requires `de.mannodermaus.junit5` Gradle plugin — not built into AGP; if the project uses JUnit4, skip the plugin), MockK, kotlinx-coroutines-test, Turbine | `./gradlew test` |
| UI / Integration | `src/androidTest/` | Compose Testing, Espresso, Hilt test rules | `./gradlew connectedAndroidTest` |
| Screenshot | `src/androidTest/` or Paparazzi | Paparazzi / Showkase / Shot | `./gradlew verifyPaparazziDebug` |

## What to cover

- **Happy path** — normal success.
- **Error path** — network error, null / empty inputs, timeouts.
- **Edge cases** — empty list, zero / max values, very long strings, rapid-fire calls.
- **State transitions** — Loading → Success, Loading → Error, retry after Error.

## Running

```bash
./gradlew test                                    # all unit tests
./gradlew test --tests "*.UserViewModelTest"      # single class
./gradlew connectedAndroidTest                    # instrumented tests
./gradlew :app:connectedDebugAndroidTest --tests "*.UserScreenTest"
```

Report: `app/build/reports/tests/test/index.html`.

## Rules

- Name tests: `` `given [precondition] when [action] then [expected result]` ``.
- **Mock at the `ApiService` / `Dao` boundary — test the Repository itself.** The Repository contains real logic (cache-first, API fallback, error mapping); mocking it whole hides that logic. Mock Retrofit services and Room DAOs, then exercise `UserRepository` as a unit.
- When testing a **ViewModel** in isolation, mocking the Repository is fine — the Repository has its own dedicated test.
- Use `UnconfinedTestDispatcher` for simple cases, `StandardTestDispatcher` when you need manual control.
- For Flow, use **Turbine** (`flow.test { ... awaitItem() }`).
- For UI tests that require visual confirmation, call `mobile_list_elements_on_screen` after the test and assert expected elements are present.
