# PHP 8.x Features

## PHP 8.1

### Enums

```php
// Pure enum (no backing type)
enum Direction
{
    case North;
    case South;
    case East;
    case West;
}

// Backed enum (string)
enum Color: string
{
    case Red   = 'red';
    case Green = 'green';
    case Blue  = 'blue';
}

// Backed enum (int)
enum Priority: int
{
    case Low    = 1;
    case Medium = 2;
    case High   = 3;
}

// Enums can implement interfaces
interface HasLabel
{
    public function label(): string;
}

enum Status: string implements HasLabel
{
    case Active   = 'active';
    case Inactive = 'inactive';

    public function label(): string
    {
        return ucfirst($this->value);
    }
}

// Enums can have constants
enum Suit: string
{
    case Hearts   = 'H';
    case Diamonds = 'D';
    case Clubs    = 'C';
    case Spades   = 'S';

    const DEFAULT = self::Hearts;
}

// From/tryFrom
$color = Color::from('red');         // Color::Red
$color = Color::tryFrom('invalid');  // null (no exception)

// Cases list
$all = Color::cases(); // [Color::Red, Color::Green, Color::Blue]
```

### Readonly Properties

```php
class User
{
    public function __construct(
        public readonly int    $id,
        public readonly string $name,
        public readonly string $email,
    ) {}
}

// PHP 8.2+: readonly classes
readonly class Point
{
    public function __construct(
        public float $x,
        public float $y,
        public float $z = 0.0,
    ) {}
}
```

### Fibers

```php
$fiber = new Fiber(function (): string {
    $input = Fiber::suspend('ready');
    return "Processed: {$input}";
});

$yielded = $fiber->start();          // 'ready'
$result  = $fiber->resume('hello');  // null (fiber returned)
$return  = $fiber->getReturn();      // 'Processed: hello'

// Check state
$fiber->isStarted();
$fiber->isRunning();
$fiber->isSuspended();
$fiber->isTerminated();
```

### Intersection Types

```php
function processRequest(ServerRequestInterface&LoggableInterface $request): void
{
    $request->log();
    // process...
}
```

### never Return Type

```php
function throwException(string $message): never
{
    throw new RuntimeException($message);
}

function redirect(string $url): never
{
    header("Location: {$url}");
    exit;
}
```

### Array Unpacking with String Keys

```php
$defaults = ['color' => 'red', 'size' => 'M'];
$custom   = ['size' => 'L', 'weight' => '200g'];

$merged = [...$defaults, ...$custom];
// ['color' => 'red', 'size' => 'L', 'weight' => '200g']
```

---

## PHP 8.0

### Named Arguments

```php
// ✅ Clear intent, order-independent
$result = array_slice(array: $items, offset: 0, length: 5, preserve_keys: true);

// ✅ Skip optional params
htmlspecialchars(string: $input, double_encode: false);
```

### Match Expression

```php
// Strict comparison (===), exhaustive, returns value
$label = match($status) {
    Status::Active             => 'Active',
    Status::Inactive, Status::Pending => 'Inactive or Pending',
    default                    => throw new \UnhandledMatchError($status),
};

// match(true) for range checks
$tier = match(true) {
    $score >= 90 => 'A',
    $score >= 80 => 'B',
    $score >= 70 => 'C',
    default      => 'F',
};
```

### Nullsafe Operator

```php
// Chain of nullable calls
$country = $order?->getUser()?->getAddress()?->getCountry();

// With method calls returning nullable
$formatted = $user?->getProfile()?->formatName();
```

### Constructor Promotion

```php
class Product
{
    public function __construct(
        private readonly string $name,
        private readonly float  $price,
        private int             $stock = 0,
    ) {}
}
```

### Union Types

```php
function formatId(int|string $id): string
{
    return (string) $id;
}

// Nullable shorthand
function find(?int $id): ?User  // same as int|null and User|null
{
    // ...
}
```

### First-Class Callables (PHP 8.1)

```php
// Replace closures with callable syntax
$strlen    = strlen(...);
$trimmed   = array_map(trim(...), $strings);
$validated = array_filter($items, $this->validate(...));

// Bound to instance methods
$handler = $this->handleRequest(...);
```

### Throw Expression

```php
// In match
$value = $input ?? throw new \InvalidArgumentException('Input required');

// In arrow functions
$fn = fn($x) => $x > 0 ? $x : throw new \RangeException('Must be positive');
```

---

## PHP 8.2

### Readonly Classes

```php
readonly class Money
{
    public function __construct(
        public int    $amount,
        public string $currency,
    ) {}

    public function add(Money $other): self
    {
        assert($this->currency === $other->currency);
        return new self($this->amount + $other->amount, $this->currency);
    }
}
```

### Disjunctive Normal Form (DNF) Types

```php
function process((Countable&Iterator)|null $input): void
{
    // $input is either (Countable AND Iterator) or null
}
```

### `true`, `false`, `null` Standalone Types

```php
function alwaysFails(): false
{
    return false;
}

function getNothing(): null
{
    return null;
}
```

---

## PHP 8.3

### Typed Class Constants

```php
class Config
{
    const string VERSION = '1.0.0';
    const int    MAX_RETRIES = 3;
    const bool   DEBUG = false;
}
```

### `json_validate()`

```php
if (json_validate($input)) {
    $data = json_decode($input, true);
}
```

### `#[\Override]` Attribute

```php
class Child extends Parent
{
    #[\Override]
    public function method(): void  // Error if parent doesn't have this method
    {
        // ...
    }
}
```
