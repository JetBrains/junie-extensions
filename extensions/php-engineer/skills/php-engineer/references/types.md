# PHP Type System

## Scalar and Built-in Types

```php
// Scalar
function process(int $id, float $price, string $name, bool $active): void {}

// Compound
function handle(array $items, callable $fn, object $obj): void {}

// Special
function maybeNull(?string $value): ?int {}  // nullable shorthand

// void — function returns nothing
function log(string $message): void {}

// never — function never returns (throws or exits)
function fail(string $msg): never
{
    throw new \RuntimeException($msg);
}

// mixed — explicit opt-out of typing (document why)
/** @param mixed $value Raw decoded JSON value */
function decode(mixed $value): string {}
```

## Union Types

```php
// PHP 8.0+
function formatId(int|string $id): string
{
    return (string) $id;
}

// Nullable is shorthand for T|null
function find(int|null $id): User|null {}
// same as:
function find(?int $id): ?User {}

// Multiple types
function accept(int|float|string $value): string {}
```

## Intersection Types

```php
// PHP 8.1+ — value must satisfy ALL types
function log(Stringable&Countable $value): void {}

// Common use: combining interfaces
interface Repository {}
interface Cacheable {}

function cache(Repository&Cacheable $repo): void {}
```

## DNF Types (Disjunctive Normal Form)

```php
// PHP 8.2+ — union of intersection types
function handle((Traversable&Countable)|array $items): int
{
    return count($items);
}
```

## Return Types

```php
// Static — returns same class, useful for fluent builders
class Builder
{
    public function set(string $key, mixed $value): static
    {
        $this->data[$key] = $value;
        return $this;
    }
}

// self — returns declaring class (not subclasses)
class Singleton
{
    private static self $instance;

    public static function getInstance(): self
    {
        return self::$instance ??= new self();
    }
}
```

## Property Types

```php
class Order
{
    // Typed properties must be initialized before access
    public int      $id;
    public string   $status;
    public ?Address $address = null;  // nullable with default

    // Readonly (PHP 8.1+) — set once in constructor
    public readonly float $total;

    public function __construct(float $total)
    {
        $this->total = $total;
    }
}
```

## Generic-style PHPDoc Types

PHPStan and IDE tooling understand these annotations:

```php
/** @var array<string, int> */
private array $scores = [];

/** @var list<User> */  // list = sequential array from 0
private array $users = [];

/** @var array<int, array{name: string, age: int}> */
private array $records = [];

/**
 * @template T
 * @param class-string<T> $class
 * @return T
 */
public function make(string $class): object
{
    return new $class();
}

/**
 * @param array<string, mixed> $data
 * @return array{id: int, name: string}
 */
public function normalize(array $data): array {}
```

## Type Coercion and Strict Mode

```php
// At the top of every file — enforces strict types
declare(strict_types=1);

// Without strict_types, PHP coerces:
// "42" → 42 for int params
// 3.7 → 3 for int params

// With strict_types=1, these throw TypeError
```

## instanceof and Type Narrowing

```php
function process(int|string|User $value): string
{
    if ($value instanceof User) {
        return $value->getName(); // PHPStan knows it's User here
    }

    if (is_int($value)) {
        return (string) $value;
    }

    return $value; // PHPStan knows it's string here
}
```

## Casting

```php
// Explicit casts — prefer type-safe alternatives when possible
$int    = (int) $value;
$float  = (float) $value;
$string = (string) $value;
$bool   = (bool) $value;
$array  = (array) $value;

// ✅ Safer for user input
$id = filter_var($input, FILTER_VALIDATE_INT);
if ($id === false) {
    throw new \InvalidArgumentException('Invalid ID');
}
```

## PHPStan Level Guide

| Level | What it checks |
|-------|---------------|
| 0 | Basic syntax errors |
| 1 | Unknown classes, functions |
| 2 | Unknown methods, properties |
| 3 | Return type mismatches |
| 4 | Dead code, unknown parameter types |
| 5 | Checking types of all passed args |
| 6 | Report missing typehints |
| 7 | Report partially wrong union types |
| 8 | Report nullable type issues |
| 9 | Be strict about mixed type |

**Minimum target: level 8.** Add to `phpstan.neon`:

```yaml
parameters:
    level: 8
    paths:
        - src
        - app
```
