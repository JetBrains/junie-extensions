# Writing & Running Tests

Unit tests (VM / UseCase / Repository) and UI tests (Compose / Espresso).

## Choose the right test type

| Type | Location | Tools | Run |
|------|----------|-------|-----|
| Unit (logic) | `src/test/` | JUnit5 (requires `de.mannodermaus.junit5` Gradle plugin — not built into AGP; if the project uses JUnit4, skip the plugin), MockK, kotlinx-coroutines-test, Turbine | `./gradlew test` |
| UI / Integration | `src/androidTest/` | Compose Testing, Espresso, Hilt test rules | `./gradlew connectedAndroidTest` |
| Screenshot | `src/androidTest/` or Paparazzi | Paparazzi / Showkase / Shot | `./gradlew verifyPaparazziDebug` |

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
- For UI tests that require visual confirmation, read the UI element tree after the test and assert expected elements are present.

## Examples

### MainDispatcherRule (required for `viewModelScope` in unit tests)

```kotlin
class MainDispatcherRule(
    val dispatcher: TestDispatcher = UnconfinedTestDispatcher(),
) : TestWatcher() {
    override fun starting(d: Description) { Dispatchers.setMain(dispatcher) }
    override fun finished(d: Description) { Dispatchers.resetMain() }
}
```

### ViewModel test (MockK + Turbine)

```kotlin
@ExtendWith(MockKExtension::class)
class UserViewModelTest {
    @get:Rule val dispatcherRule = MainDispatcherRule()

    @MockK lateinit var repo: UserRepository
    private lateinit var vm: UserViewModel

    @BeforeEach fun setUp() { vm = UserViewModel(repo) }

    @Test
    fun `given repo returns user when load then state is Success`() = runTest {
        val user = User(id = "1", name = "Alice")
        coEvery { repo.user("1") } returns user

        vm.state.test {
            assertEquals(UserUiState.Loading, awaitItem())
            vm.load("1")
            assertEquals(UserUiState.Success(user), awaitItem())
            cancelAndIgnoreRemainingEvents()
        }
    }
}
```

### Repository test — mock at ApiService/Dao boundary

```kotlin
class UserRepositoryTest {
    private val api = mockk<UserApi>()
    private val dao = mockk<UserDao>()
    private val repo = UserRepository(api, dao)

    @Test
    fun `given api throws when getUser then returns cached entity`() = runTest {
        val cached = UserEntity(id = "1", name = "Alice")
        coEvery { dao.getUser("1") } returns cached
        coEvery { api.getUser("1") } throws IOException()

        val result = repo.user("1")

        assertEquals("Alice", result.name)
    }
}
```
