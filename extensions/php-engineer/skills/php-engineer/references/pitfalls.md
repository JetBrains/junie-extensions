# PHP pitfalls — subtle behavior that LLMs get wrong

Bugs here compile, pass trivial tests, and fail in production. Collected from real PHP 8.x review, not from the language manual.

## `declare(strict_types=1)` — what it does and doesn't

- Only affects **scalar type coercion on function calls made from the file where it's declared**. It does NOT propagate into libraries or called code.
- Does NOT affect return type coercion of the callee — each file decides its own strictness.
- Does NOT affect property assignments (typed properties always reject wrong types since 7.4).
- Conclusion: put it in **every** file, not just the entry point.

## Enums

- `Status::from('invalid')` throws `ValueError`. Use `Status::tryFrom('invalid')` when the input might be unknown — returns `null`.
- `Status::cases()` order is declaration order — don't rely on it for UI sorting.
- Enum values are compared by identity: `$a === Status::Active` works, `$a == 'active'` doesn't (an enum is not a string, even if backed by one).
- **Serialization pitfall**: `json_encode(Status::Active)` returns `"active"` (the backed value), but `var_export`/`serialize` produce `\Status::Active`. Don't round-trip through `serialize` if you deploy different app versions.
- Enums **cannot** have state (no properties). Don't try to emulate Java-style stateful enums.
- `const` inside an enum is fine; `static` properties are forbidden.
- Implementing an interface? Interface methods must be defined on all cases (via a single method on the enum itself).

## `readonly`

- `readonly` property can be written **only from the declaring class** and **only once** — not from a child constructor directly; the parent constructor must assign.
- **Direct reference to a readonly property throws on all PHP 8.1+ versions**: `$ref = &$obj->prop` → `Error: Cannot take reference of a readonly property`. PHP 8.3 additionally closed indirect bypass loopholes (e.g., via array references). Banned by policy regardless of version.
- `readonly class` (PHP 8.2+) implies `readonly` on all properties. You can't add a non-readonly property; you can't inherit a non-readonly class.
- `clone` copies the readonly values as-is. To "modify" — implement a `with*` method that returns a new instance.
- Readonly doesn't make nested mutable objects immutable: `readonly array $items` can still be mutated if the array contains objects (arrays themselves are by-value, but object references inside are by-identity).

## `match`

- Strict comparison (`===`). `match(1)` will NOT match `case "1"`.
- Exhaustive — missing `default` + unmatched input throws `UnhandledMatchError`. That's a feature: use it for sealed enum switches to get compile-time safety via PHPStan.
- `match(true) { $x > 10 => ..., $x > 0 => ... }` — pattern for range checks. First match wins; order matters.
- Each case is an **expression** (single statement). For multiple statements, call a method.

## Nullsafe `?->`

- Short-circuits on `null` for the whole chain: `$a?->b()->c->d()` returns `null` if any step is null.
- Cannot be used on the left side of an assignment: `$user?->name = 'x'` — syntax error.
- Does NOT work for array access: `$arr?['key']` is wrong. Use `$arr['key'] ?? null`.
- Method calls with nullsafe still evaluate arguments: `$obj?->log(expensive())` computes `expensive()` even if `$obj` is null. Move the call behind an `if`.

## Type coercion (even with `strict_types`)

- `strict_types` only affects **scalar parameter types**. Class types, array values, and property assignments were always strict.
- Without `strict_types`: `"42abc"` → `42` (with `E_WARNING` since 8.0), `"abc"` → `0`, `[]` → `false`, `null` → `0` / `""`.
- `is_numeric("42abc")` is `false` (not pure numeric); `(int)"42abc"` is `42`. Don't mix `is_numeric` with `(int)` cast intent.
- `(bool)"0"` is `false`. `(bool)"false"` is `true`. `(bool)" 0"` is `true`.

## Arrays

- `foreach ($arr as &$v) { ... } ` — the `$v` reference persists after the loop. A subsequent `foreach ($arr as $v)` silently overwrites the last element. Always `unset($v)` after reference loops.
- `array_merge([1=>'a'], [1=>'b'])` — string/int keys behave differently: numeric keys are renumbered, string keys are overwritten. Use `$a + $b` for "first wins" on integer keys.
- `array_map(null, $a, $b)` → zips arrays. `array_map(fn, $a, $b)` → calls `fn($a[i], $b[i])`. Subtle.
- `in_array('1', [1, 2])` is `true` in loose mode. Always `in_array('1', [1, 2], true)` (3rd arg = strict).
- `array_unique` uses loose comparison by default. `array_unique($arr, SORT_REGULAR)` differs from `SORT_STRING`.
- `array_keys($m)` preserves order; `ksort`/`asort`/`sort` don't — `ksort` sorts in-place and returns `true` (not the sorted array).
- `list($a, $b) = $arr` / `[$a, $b] = $arr` — missing keys give `null` + `E_WARNING`. Use `$a = $arr[0] ?? null`.

## Dates

- `DateTime` is mutable. `$d->modify('+1 day')` changes `$d`. Any other variable holding the same instance sees the change. Use `DateTimeImmutable`.
- `DateTimeImmutable::createFromFormat('Y-m-d', $s)` returns `false` on failure — not an exception. Check with `!== false` and inspect `DateTimeImmutable::getLastErrors()`.
- Default `DateTime('2024-01-01')` uses the server timezone. For deterministic code always pass a `DateTimeZone`: `new DateTimeImmutable('2024-01-01', new DateTimeZone('UTC'))`.
- `date('Y-m-d', $ts)` formats in the server timezone. For UTC: `gmdate` or `DateTimeImmutable::setTimezone(new DateTimeZone('UTC'))`.

## Strings

- `strlen($utf8)` returns the byte count, not character count. Use `mb_strlen($utf8, 'UTF-8')`.
- `substr`, `str_replace`, `strpos` — byte-oriented. Prefer `mb_*` variants for multi-byte safety.
- `sprintf('%s', $obj)` calls `__toString` only if the object implements `Stringable`. Otherwise TypeError.
- `implode(',', $items)` where `$items` contains a `null` → `""`; with objects without `Stringable` → TypeError. Cast or filter first.
- `number_format(1234.5, 2, '.', ',')` is locale-agnostic; `money_format` is removed (PHP 8.0).

## Comparison

- `0 == 'abc'` — `false` on PHP 8+ (finally), `true` on 7.x. Use `===` everywhere anyway.
- `'0' == false` → `true`. `'0' == null` → `false`. Never trust `==`.
- `spl_object_id($a) === spl_object_id($b)` — for object identity; `$a === $b` checks that they're the same instance (identical). Not the same as `==` (value-equal by property).
- `NAN == NAN` → `false`. `NAN === NAN` → `false`. Use `is_nan()`.

## Fibers

- `Fiber::suspend($x)` can only be called from **within a fiber**. Outside → Error.
- `$fiber->resume()` on a fiber that returned (not suspended) → FiberError. Check `$fiber->isTerminated()` first.
- `$fiber->getReturn()` throws if the fiber is not terminated or threw an exception. Wrap in `try { $fiber->getReturn(); } catch (Throwable $e) { ... }`.
- Fibers are cooperative — they do NOT run in parallel. For real concurrency use Swoole, ReactPHP, or AMPHP.

## Generators

- `yield from $iterable` delegates — faster than manual loop + yield.
- A generator can be iterated only once. `iterator_to_array` drains it; calling `foreach` again → nothing.
- `iterator_to_array($gen)` by default uses string/int yield keys, so duplicate keys overwrite. Pass `preserve_keys: false` if you want a list.

## Exceptions

- Catching `\Throwable` catches `Error` too (type errors, parse errors). Almost always wrong — catch `\Exception` at most, usually a specific subclass.
- `finally` blocks that `return` or `throw` **override** the original exception/return. Avoid.
- Chained exceptions: `new RuntimeException($msg, previous: $cause)` (named arg is clearer than positional `0, $cause`).
- `set_error_handler` converts warnings to exceptions — don't use it globally; scope it to the specific call with try/finally.

## I/O & file handling

- `file_get_contents($url)` needs `allow_url_fopen=1` and doesn't verify TLS well. Use cURL or Guzzle.
- `fopen($path, 'w')` truncates. `'x'` fails if file exists (safe for "create new"). `'a'` appends. Know the mode before writing.
- `file_put_contents` with `LOCK_EX` + `FILE_APPEND` gives atomic append. Without `LOCK_EX` → interleaved writes under load.
- Never `include` / `require` a path derived from user input. Even with `realpath`: `realpath('/safe/' . $userInput)` can escape with `../`.

## Numeric & math

- PHP `int` is platform-dependent: 64-bit on most modern systems, 32-bit on 32-bit PHP builds. For large integers use `GMP` or string arithmetic (`bcmath`).
- Integer overflow converts to `float` silently, losing precision above `2^53`.
- `intdiv(7, 2)` → `3` (integer division); `7 / 2` → `3.5` (float). Don't mix.
- `round(0.5)` → `1` (half-up); `round(-0.5)` → `-1` (not zero). Banker's rounding: `round($x, 0, PHP_ROUND_HALF_EVEN)`.
- Floating point: `0.1 + 0.2 === 0.3` → `false`. Compare with epsilon or use `bcmath` for money.

## `null` and `??`

- `??` (null coalescing) fires on `null` OR missing-array-key. `??` does NOT fire on empty string or `0` — use `?:` (Elvis) or explicit check.
- `$a ??= 'default'` — null-coalescing assignment. Assigns only if `$a` is null or undefined.
- `isset($arr['key'])` is `false` if the value is `null`. Use `array_key_exists('key', $arr)` when you need to distinguish "absent" from "null".

## `final class` by default

- Default to `final class Foo` for application code. Inheritance across module boundaries is almost always a mistake — it couples consumers to internals and blocks safe refactoring.
- Exceptions: framework-required base classes (`Eloquent Model`, `AbstractController`), abstract templates you explicitly design for extension, and value objects meant as a hierarchy (in which case use `sealed`-style comment + PHPStan rule).
- `final` plays well with readonly DTOs: `final readonly class Money(...)`. Test doubles via composition, not `extends` — don't remove `final` to make mocking easier, inject an interface.
- For libraries distributed publicly: `final` is a stronger API contract than docblock `@internal`. Favor `final` + explicit extension points (hooks, events, interfaces).

## `static` vs `self`

- `self` binds at declaration; `static` uses late static binding. In `self::create()` inside a parent class, a child class call returns a parent instance. Use `static::create()` for fluent builders.
- `new static()` respects the caller's class; `new self()` hardcodes the declaring class.

## Closures

- `fn($x) => $x + $captured` — arrow functions auto-capture `$captured` by value. For reference capture use `function` + `use (&$captured)`.
- `Closure::bind($fn, $obj, $class)` can access private members — powerful for testing, dangerous for production.
- `$this` inside an arrow function refers to the enclosing `$this`. Inside `fn() => ...` defined outside a class → FatalError.

## Objects & cloning

- `clone $obj` is shallow: nested objects are still shared. Implement `__clone` to deep-copy if needed.
- `(array)$obj` keys private as `"\0ClassName\0prop"`, protected as `"\0*\0prop"`. Don't use to "serialize" — implement `JsonSerializable` or a method.
- `$obj::class` (PHP 8.0+) → class name as string. Cheaper than `get_class($obj)`.
- Iterating `foreach ($obj as $k => $v)` yields public properties. For custom iteration implement `IteratorAggregate`.
