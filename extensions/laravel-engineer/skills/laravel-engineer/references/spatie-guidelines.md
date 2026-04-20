# Spatie Laravel Guidelines

Spatie's coding standards for Laravel, adapted from https://spatie.be/guidelines/laravel-php.
These are battle-tested conventions from the most prolific Laravel package maintainer.

## General Principles

- **Explicit over magic** — prefer clear, readable code over clever shortcuts
- **Single responsibility** — one class, one purpose
- **Thin controllers** — controllers only delegate; logic lives in services or actions
- **No abbreviations** — write `$userGroups` not `$usrGrps`, `getUserById` not `getUsrById`

## Naming

```php
// Controllers — singular, PascalCase
class UserController {}        // ✅
class UsersController {}       // ❌

// Models — singular, PascalCase
class Order {}                 // ✅
class Orders {}                // ❌

// Migrations — descriptive
create_orders_table            // ✅
orders                         // ❌
add_status_to_orders_table     // ✅

// Blade views — dot notation, kebab-case
resources/views/orders/index.blade.php      // ✅
resources/views/ordersIndex.blade.php       // ❌

// Methods — camelCase, verb-first
public function getActiveUsers(): Collection {}   // ✅
public function activeUsers(): Collection {}      // ✅ (readable alternative)
public function active_users(): Collection {}     // ❌

// Booleans — is/has/can prefix
public bool $isVerified;
public function hasCompletedProfile(): bool {}
public function canPublish(): bool {}

// Events — past tense
class OrderPaid {}             // ✅
class PayOrder {}              // ❌

// Listeners — present tense, describes what it does
class SendOrderPaidNotification {}   // ✅

// Jobs — describe what the job does
class ProcessOrderPayment {}   // ✅
class PaymentJob {}            // ❌

// Commands — verb + noun
php artisan orders:process-pending     // ✅
php artisan process                    // ❌
```

## Classes and Methods

```php
// ✅ Constructor injection, not property injection
class OrderService
{
    public function __construct(
        private readonly InventoryService $inventory,
        private readonly PaymentGateway   $payment,
    ) {}
}

// ✅ Return early to reduce nesting
public function cancel(Order $order): void
{
    if ($order->status === OrderStatus::Cancelled) {
        return;
    }

    if (! $order->canBeCancelled()) {
        throw new \DomainException('Order cannot be cancelled.');
    }

    // proceed with cancellation...
}

// ❌ Deep nesting
public function cancel(Order $order): void
{
    if ($order->status !== OrderStatus::Cancelled) {
        if ($order->canBeCancelled()) {
            // proceed...
        } else {
            throw new \DomainException('...');
        }
    }
}
```

## Whitespace and Formatting

```php
// ✅ Blank line before return (when there are statements above it)
public function getTotal(): float
{
    $subtotal = $this->calculateSubtotal();
    $tax      = $this->calculateTax();

    return $subtotal + $tax;
}

// ✅ Align assignments in a block for readability
$name    = 'John';
$email   = 'john@example.com';
$country = 'US';

// ✅ No blank line after opening brace
public function handle(): void
{
    $this->doSomething();  // ✅ immediately after opening brace
}
```

## Arrays

```php
// ✅ Short syntax, trailing comma
$order = [
    'user_id' => 1,
    'status'  => 'pending',
    'total'   => 99.99,    // trailing comma
];

// ✅ Single-item arrays on one line
$statuses = ['pending', 'paid', 'cancelled'];

// ✅ Align double-arrows when it aids readability
$map = [
    'user_id'    => $user->id,
    'order_id'   => $order->id,
    'product_id' => $product->id,
];
```

## Strings

```php
// ✅ Use string interpolation
$message = "Hello, {$user->name}!";

// ✅ Multiline strings
$query = "
    SELECT *
    FROM orders
    WHERE user_id = {$userId}
      AND status = 'pending'
";

// ❌ String concatenation when interpolation is cleaner
$message = 'Hello, ' . $user->name . '!';
```

## Eloquent

```php
// ✅ Scope names are descriptive, chainable
Order::pending()->forUser($userId)->recent(30)->paginate(20);

// ✅ Load relations with with() — never lazy-load in a loop
$orders = Order::with('user', 'items')->get();

// ✅ Use attribute casting — no manual casting in code
protected $casts = ['is_verified' => 'boolean', 'metadata' => 'array'];

// ❌ Manual casting everywhere
$isVerified = (bool) $user->is_verified;

// ✅ Use firstOrCreate / updateOrCreate for upserts
User::updateOrCreate(['email' => $email], ['name' => $name]);

// ✅ Declare fillable explicitly
protected $fillable = ['name', 'email', 'status'];

// ❌ Disable guarding entirely
protected $guarded = [];
```

## Routing

```php
// ✅ Use route names consistently
Route::get('/orders', [OrderController::class, 'index'])->name('orders.index');
Route::post('/orders', [OrderController::class, 'store'])->name('orders.store');

// ✅ Use route model binding
Route::get('/orders/{order}', [OrderController::class, 'show']);
// Controller receives Order $order automatically

// ✅ Group related routes
Route::prefix('admin')->name('admin.')->middleware('can:access-admin')->group(function () {
    Route::apiResource('users', Admin\UserController::class);
});
```

## Exceptions

```php
// ✅ Domain exceptions are expressive
throw new InsufficientStockException($product, $requested, $available);

// ✅ Catch specific exceptions
try {
    $this->payment->charge($amount);
} catch (PaymentDeclinedException $e) {
    // handle gracefully
} catch (PaymentGatewayException $e) {
    Log::error('Payment gateway error', ['exception' => $e]);
    throw $e;
}

// ❌ Catch-all
try {
    //
} catch (\Exception $e) {
    // don't do this
}
```

## Comments

```php
// ✅ Comments explain WHY, not WHAT
// Stripe requires amounts in cents
$amount = (int) round($total * 100);

// ❌ Comments that just restate the code
// multiply by 100
$amount = $total * 100;
```
