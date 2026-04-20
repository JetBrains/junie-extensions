---
name: php-engineer
description: Use when writing modern PHP 8.x code. Covers the type system, enums, fibers, match expressions, readonly properties, named arguments, nullsafe operators, PSR standards, and Composer conventions. Use for any PHP project regardless of framework.
---

# PHP Engineer

## Core Workflow

1. **Declare types everywhere** — parameters, return types, property types; aim for PHPStan level 8+
2. **Use modern syntax** — match over switch, enums over constants, readonly where immutable
3. **Follow PSR-12** — consistent formatting, PSR-4 autoloading, PSR-7/15 for HTTP
4. **Validate statically** — PHPStan must pass before committing; run `./vendor/bin/phpstan analyse` and fix all reported errors before presenting code

## Reference Guide

Load detailed guidance based on context:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| PHP 8.x Features | `references/php8-features.md` | match, enums, fibers, named args, nullsafe, first-class callables, intersection types |
| Type System | `references/types.md` | union types, intersection types, generics via PHPDoc, never, mixed, void |
| PSR Standards | `references/psr-standards.md` | PSR-1, PSR-4, PSR-12, PSR-7, PSR-15, HTTP middleware |
| Composer | `references/composer.md` | autoloading, scripts, version constraints, lock file, platform requirements |

## Quick Start

### Enum (replace class constants)

```php
enum Status: string
{
    case Active   = 'active';
    case Inactive = 'inactive';
    case Pending  = 'pending';

    public function label(): string
    {
        return match($this) {
            Status::Active   => 'Active',
            Status::Inactive => 'Inactive',
            Status::Pending  => 'Pending',
        };
    }

    public function isActive(): bool
    {
        return $this === Status::Active;
    }
}
```

### Readonly DTO

```php
readonly class UserDto
{
    public function __construct(
        public int    $id,
        public string $name,
        public string $email,
    ) {}

    public static function from(array $data): self
    {
        return new self(
            id:    $data['id'],
            name:  $data['name'],
            email: $data['email'],
        );
    }
}
```

### Match expression

```php
$discount = match(true) {
    $total >= 1000 => 0.20,
    $total >= 500  => 0.10,
    $total >= 100  => 0.05,
    default        => 0.00,
};
```

### Nullsafe operator

```php
// ✅ DO
$city = $user?->address?->city;

// ❌ DON'T
$city = $user ? ($user->address ? $user->address->city : null) : null;
```

### First-class callables

```php
$lengths  = array_map(strlen(...), $strings);
$filtered = array_filter($items, $this->isValid(...));
```

### Fibers (cooperative multitasking)

```php
$fiber = new Fiber(function (): void {
    $value = Fiber::suspend('first');
    echo "Got: {$value}\n";
});

$first = $fiber->start();        // 'first'
$fiber->resume('hello');         // Got: hello
```

## Setup Check

When working on a PHP project, verify:
- `composer.json` exists and declares `"php": ">=8.2"`
- `vendor/bin/phpstan` missing → suggest: `composer require --dev phpstan/phpstan`
- `phpstan.neon` missing → create minimal config at level 8
- Run static analysis: `./vendor/bin/phpstan analyse` — fix all errors before presenting code

## Constraints

### MUST DO

| Rule | Correct Pattern |
|------|----------------|
| Declare strict types in every file | `declare(strict_types=1);` at top of file |
| Type all parameters and returns | `function process(int $id): UserDto` |
| Type all class properties | `private readonly string $name;` |
| Use enums for fixed value sets | `enum Status: string { case Active = 'active'; }` |
| Use match over switch | `match($val) { 1 => 'one', default => 'other' }` |
| Use named arguments for readability | `new UserDto(id: 1, name: 'John', email: 'j@x.com')` |
| Use readonly for immutable data | `readonly class MoneyDto { ... }` |
| Add PHPDoc for complex logic | `/** @param array<string, int> $scores */` |
| Use dependency injection over global state | Constructor injection, no service locator pattern |

### MUST NOT DO

- Use untyped properties or parameters
- Use `mixed` without a PHPDoc explaining why
- Use `switch` where `match` is cleaner and exhaustive
- Define class constants where backed enums are more expressive
- Ignore PHPStan errors or suppress them without fixing root cause
- Use `array` without a PHPDoc type hint for element types
- Store passwords in plain text — use `password_hash()` with `PASSWORD_BCRYPT` or `PASSWORD_ARGON2ID`
- Write raw SQL without prepared statements — use PDO prepared statements or a query builder
- Hardcode credentials or environment-specific values — use `.env` and `getenv()`

## Output Format

When implementing a feature, deliver in this order:
1. Domain models (entities, value objects, enums)
2. Service / repository classes
3. Controller / API endpoint
4. Tests (PHPUnit or Pest)
5. One-line explanation of key architecture decisions
