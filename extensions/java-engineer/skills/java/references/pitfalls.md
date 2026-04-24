# Java pitfalls — subtle behavior that LLMs get wrong

Bugs in this file compile, pass basic tests, and fail in production. They're collected from real code review, not from the language tutorial.

## `Optional`

- `Optional.orElse(expensiveCall())` **always evaluates the argument**, even if the Optional is present. For lazy defaults use `.orElseGet(() -> expensiveCall())`.
- `Optional.of(nullable)` throws NPE if the argument is null — use `Optional.ofNullable(...)`.
- `Optional<List<T>>` is almost always the wrong shape. Return `List<T>` (possibly empty).
- `Optional` is not `Serializable` — don't put it in a `record` that's serialized, and don't put it in JPA entities.
- Chains that end in `.orElse(null)` defeat the purpose. Either return `Optional` to the caller, or `.orElseThrow(...)` to fail fast.

## `Stream`

- `Stream.toList()` (JDK 16+) ≠ `Collectors.toList()`. The first is **unmodifiable**; mutating it throws `UnsupportedOperationException`. The second is modifiable but with no guaranteed implementation class.
- `stream.sorted()` on an unbounded / infinite stream hangs forever — must be preceded by `.limit(n)`.
- `peek(...)` is **not** guaranteed to run on every element in a short-circuited pipeline (`.findFirst()` / `.anyMatch()`). Don't use it for side effects.
- `map(f)` on a stream of `Stream<T>` collapses types only if you use `flatMap`. Nested `.map(s -> s.stream())` yields `Stream<Stream<T>>`, not what you want.
- Collecting to a `Map` with duplicate keys: `Collectors.toMap(k, v)` throws `IllegalStateException`. Use the 3-arg form with a merge function: `Collectors.toMap(k, v, (a, b) -> a)`.
- `parallelStream()` uses the shared `ForkJoinPool.commonPool()`. One blocking element starves the rest of the JVM. For blocking I/O use a virtual-thread executor instead.
- `Stream` is single-use — a `IllegalStateException: stream has already been operated upon` means someone tried to reuse it.

## `switch` / pattern matching

- In a pattern-matching `switch` over a sealed hierarchy, **don't add `default`** — the exhaustiveness check stops protecting you when new subtypes are added.
- `null` is NOT matched by any pattern by default. Add a `case null -> ...` if the input may be null; otherwise you'll get `NullPointerException` at runtime.
- `case Integer i when i > 0 -> ...` — the guard uses `when`, not `&&` directly on the pattern.
- Arrow cases (`->`) don't fall through. Colon cases (`:`) do — don't mix syntaxes in one switch.

## `record`

- Compact constructors validate / normalize — they can't assign to `this.field` directly; assignments to the parameter names are implicit.
- Records are `final` — no subclassing. Can implement interfaces (including `sealed interface`).
- `equals` / `hashCode` / `toString` are auto-generated based on **all components** in declaration order. If you override them, you usually regret it.
- No no-arg constructor → incompatible with frameworks that require one (Hibernate `@Entity`, legacy Jackson configs — use `@JsonCreator` or the record module).
- A record component of a mutable type (`List<...>`, array) leaks mutability. Wrap in `List.copyOf(...)` inside the compact constructor, or accept it as a design choice.

## Generics

- `List<? extends Foo>` is read-only (can't `.add(...)` except null). `List<? super Foo>` accepts writes but reads are `Object`. Mnemonic: PECS — Producer Extends, Consumer Super.
- `new ArrayList<>()` (diamond) is fine; `new ArrayList()` is a raw type — compiler warning is not cosmetic, it disables type checks for the whole reference.
- Generic arrays can't be created directly: `new T[n]` → compile error. Use `List<T>` or `(T[]) Array.newInstance(clazz, n)` with a class token.

## Equality & hashing

- `a.equals(b)` on floating point is almost always wrong. Use `Double.compare(a, b)` or `BigDecimal` with `compareTo` (not `equals` — `BigDecimal.equals` differentiates `2.0` and `2.00`).
- `HashSet<MyClass>` silently misbehaves if `MyClass` overrides `equals` but not `hashCode` (or vice versa). Always override both together.
- `String.intern()` is a footgun — GC behavior is JVM-specific. Don't use it to "speed up equality".

## Concurrency traps

- `ConcurrentHashMap.computeIfAbsent` holds a bin-level lock. Calling another `computeIfAbsent` on the same map from within the lambda can deadlock.
- `Collections.synchronizedMap(new HashMap<>())` synchronizes single operations, **not** iteration. Iterating without external synchronization → `ConcurrentModificationException`.
- `AtomicInteger` != thread-safe counter + condition. `if (counter.get() < N) counter.incrementAndGet()` is a race — use `updateAndGet` / `accumulateAndGet`.
- `volatile` provides visibility but not atomicity of compound ops. `counter++` on a `volatile int` is still a race.

## Exceptions

- `catch (IOException | SQLException e)` — multi-catch variable is effectively final; can't reassign `e`.
- `throw new RuntimeException(cause)` without a message loses context in logs — prefer `throw new RuntimeException("failed to X for id=" + id, cause)`.
- `finally` can swallow exceptions: a `return` or `throw` inside `finally` overrides the one from `try`. Avoid.
- `Throwable.addSuppressed(...)` is already done by `try-with-resources` — don't duplicate.

## `var`

- `var` only for locals. Not for fields, method parameters, or return types.
- `var list = new ArrayList<>();` → `ArrayList<Object>`. Always give the diamond a type: `var list = new ArrayList<String>()`.
- Don't use `var` when it hides the type of a non-obvious expression (a stream chain, a method whose name doesn't imply the type). It's a readability tool, not a line-shortener.

## I/O & resources

- `Files.lines(path)` returns a `Stream<String>` that must be closed (`try (var stream = Files.lines(path)) { ... }`) — the file handle leaks otherwise.
- `InputStream.read(byte[])` does **not** fill the whole buffer. Loop until `-1` or use `in.readAllBytes()` / `in.readNBytes(n)` for bounded reads (JDK 11+).
- Don't use `new FileReader(file)` — uses the default platform charset. Always `Files.newBufferedReader(path, StandardCharsets.UTF_8)`.

## Numbers

- Integer overflow is silent: `Integer.MAX_VALUE + 1 == Integer.MIN_VALUE`. Use `Math.addExact(...)` / `Math.multiplyExact(...)` when overflow is a bug, not a feature.
- `BigDecimal bd = new BigDecimal(0.1)` — not `0.1`. Use `BigDecimal.valueOf(0.1)` or `new BigDecimal("0.1")`.
- Integer division truncates toward zero: `-7 / 2 == -3`, not `-4`. For floor division use `Math.floorDiv`.

## Miscellaneous

- `String.split(regex)` — the argument is a regex, not a literal. `split(".")` returns empty array. Use `split("\\.", -1)` (the `-1` preserves trailing empty strings).
- `new SimpleDateFormat` is **not thread-safe** and deprecated in style. Use `DateTimeFormatter` (immutable, thread-safe).
- `Date`, `Calendar` → `java.time.Instant` / `LocalDate` / `LocalDateTime` / `ZonedDateTime`. Mixing old and new APIs in the same call chain is a smell.
- `Object.finalize()` — deprecated for removal. Use `Cleaner` + `AutoCloseable` instead.
