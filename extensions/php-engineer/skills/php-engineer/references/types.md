# PHP type system — policy & PHPStan discipline

Baseline union / intersection / DNF / nullable / `never` / `void` syntax is assumed. This file is about project policy and the type-design choices LLMs get wrong.

## Strict types are the baseline

- `declare(strict_types=1);` on line 1 of every file. Not optional.
- File-level — it does NOT propagate into called libraries. Libraries may be non-strict; your code still must be.
- Does NOT affect typed property assignments, return coercion of callee, or implicit `(int)`/`(string)` cast expressions in your own code. Still avoid implicit casts.

## `mixed` — the type-check escape hatch

- Every `mixed` is a policy concession — document it with a PHPDoc comment explaining why.
- Common legitimate uses: `json_decode` raw output, framework-provided `$request->input($key)`, deserialization boundary.
- Almost never legitimate: service methods, repositories, domain models. If you're tempted to use `mixed` there, you're missing a value object.
- `mixed` disables PHPStan checking on that value. Narrow it back immediately with `is_string` / `is_int` / `instanceof`.

## Generics via PHPDoc (PHPStan / Psalm)

PHP has no runtime generics — PHPStan reads PHPDoc annotations and enforces them at analysis time.

- **Prefer `list<T>` over `array<int, T>`** when the array is sequential from 0. `list<T>` catches "looks sequential but has gaps" bugs.
- **Use `array{name: string, age: int}`** (array shapes) for fixed-key maps. More precise than `array<string, mixed>`.
- **Template classes** — `@template T` on the class, `@var T` on properties, `@return T` on methods. Needed for generic collections / repositories.
- **`class-string<T>`** for methods that take a class name and return `T`: `public function make(string $class): object` → `@param class-string<T> $class, @return T`.
- PHPStan baseline (`phpstan-baseline.neon`) — commit it to freeze current violations; new code must pass at the project's level without adding new baseline entries.

## Union types

- `int|string $id` is fine at boundaries (IDs, route params). Internally narrow immediately.
- Returning `User|null` is PHP-idiomatic. Returning `User|false` is NOT — it's a legacy habit from `strpos` and similar. Throw an exception or return `null`.
- `int|bool` almost always means "I'm using `false` as an error sentinel". Don't. Throw or use `null`.

## Intersection & DNF types

- `Countable&Iterator` — value must satisfy BOTH. Useful for cross-cutting interfaces; otherwise it's an architecture smell (too many interfaces on one param).
- DNF (PHP 8.2+): `(A&B)|null`, `(Countable&Iterator)|array`. Use sparingly — when you need it, the alternatives (union wrapper, adapter) are usually worse.

## Nullable

- `?Foo` is sugar for `Foo|null`. Prefer the shorthand in signatures.
- For properties: `?Foo $prop = null` — must have `= null` default, otherwise accessing before construction throws.
- For parameters with defaults: `?Foo $foo = null` is more honest than `Foo $foo = null` (deprecated implicit nullable in PHP 8.4+).

## `never` and `void`

- `never` — function must throw or exit. Enables exhaustiveness: `match` on a union can have a `default => throw new Unexpected()` of type `never`, and PHPStan narrows the remaining branches.
- `void` — returns no value. Calling code that tries `$x = voidFn()` → error.
- Don't use `void` when the function might in the future return something. Use `?T` from the start.

## Property types

- All properties typed. Untyped property = implicit `mixed` = policy violation.
- `readonly` implies it will be set in the constructor exactly once — don't add `= null` default (then it could be read-before-write).
- Properties with complex defaults (`private array $config = [...]`) — consider moving to the constructor for clarity.

## Narrowing

PHPStan narrows types through:

- `instanceof`
- `is_string`, `is_int`, `is_array`, `is_object`, `is_a`
- `!== null` (not `!= null`)
- `assert()` — included in type narrowing (Psalm / PHPStan read `assert` conditions)
- `@phpstan-assert` PHPDoc on user-defined guard functions

Do NOT use early-return `throw` without proper typing — write the guard as a method with `@phpstan-assert Foo $value` so callers narrow.

## Type coverage pitfalls

- `/** @return User[] */` vs `/** @return list<User> */` — the first doesn't catch gaps. Use `list<User>`.
- `/** @return array */` with no item type — PHPStan treats as `array<mixed>`, defeats type checking. Always parameterize.
- `@var` on a local variable — works but is a code smell. If PHPStan can't infer the type, either the upstream signature is wrong or you need a helper.
- Generic methods returning `T` from `class-string<T>` — without `@template`, PHPStan returns `object`. Add `@template T of object`.
- `mixed[]` / `array<mixed>` — banned by policy. Either type it or use a value object.

## Casting

- `(int) "42"` — always works but silently converts `"abc"` to `0`. For user input prefer `filter_var($in, FILTER_VALIDATE_INT)` + null-check.
- `(array) $object` leaks null-byte-mangled keys. Don't use to introspect; use `get_object_vars` (still exposes private when called inside the class) or `JsonSerializable`.
- `settype($var, 'int')` mutates in place and returns `bool`. Avoid — use explicit `$var = (int)$var`.

## Enum vs class hierarchy

- Closed, value-like sets → `enum`. `UserRole`, `OrderStatus`.
- Open hierarchies with behavior → abstract class / interface + classes.
- Don't mix: a `BillingMode` enum with `calculate(Money $m): Money` methods is OK if behavior is trivial; if logic is substantial, move to a strategy class keyed by the enum.

## Value objects

- Policy: wrap primitives used as domain identifiers in `readonly class` value objects (`UserId`, `Email`, `Money`).
- Cheap: single readonly `value` property + factory + self-equality method.
- Prevents `function findUser(int $id)` from accepting `productId` silently.

## PHPStan / Psalm runtime

- `vendor/bin/phpstan analyse` — target level 8 (or 9 for new projects, which is strict about `mixed`; level 10 = "bleeding edge" rules, opt-in for projects that want maximum strictness).
- Ignore errors only via `@phpstan-ignore-next-line` with a comment explaining why — never silent via config-wide `ignoreErrors`.
- Baseline allowed only for legacy code; new code must not add lines to the baseline.
- On CI: `phpstan analyse --no-progress --error-format=github` + fail on error.
