# Testing with Pest and PHPUnit

## Pest Setup

```php
// tests/Pest.php
uses(Tests\TestCase::class)->in('Feature');
uses(Tests\TestCase::class, RefreshDatabase::class)->in('Feature');

// Custom helpers
expect()->extend('toBeActive', function () {
    return $this->toBe('active');
});
```

## Feature Tests (HTTP)

```php
// tests/Feature/OrderTest.php
use App\Models\Order;
use App\Models\User;

it('creates an order', function () {
    $user = User::factory()->create();
    $products = Product::factory()->count(2)->create();

    $response = $this
        ->actingAs($user)
        ->postJson('/api/v1/orders', [
            'items' => [
                ['product_id' => $products[0]->id, 'quantity' => 2],
                ['product_id' => $products[1]->id, 'quantity' => 1],
            ],
            'shipping_address' => '123 Main St',
        ]);

    $response
        ->assertCreated()
        ->assertJsonPath('data.status', 'pending')
        ->assertJsonCount(2, 'data.items');

    $this->assertDatabaseHas('orders', [
        'user_id' => $user->id,
        'status'  => 'pending',
    ]);
});

it('requires authentication to create an order', function () {
    $this->postJson('/api/v1/orders', [])
        ->assertUnauthorized();
});

it('validates order items', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->postJson('/api/v1/orders', ['items' => []])
        ->assertUnprocessable()
        ->assertJsonValidationErrors(['items']);
});
```

## Database Testing

```php
// Use RefreshDatabase in TestCase or per-test
uses(RefreshDatabase::class);

// Or via Pest uses() in Pest.php
// uses(Tests\TestCase::class, RefreshDatabase::class)->in('Feature');

it('lists only current user orders', function () {
    $user  = User::factory()->create();
    $other = User::factory()->create();

    Order::factory()->count(3)->for($user)->create();
    Order::factory()->count(2)->for($other)->create();

    $this->actingAs($user)
        ->getJson('/api/v1/orders')
        ->assertOk()
        ->assertJsonCount(3, 'data');
});
```

## Unit Tests (Pure Business Logic)

```php
// tests/Unit/OrderServiceTest.php
use App\Services\OrderService;

it('calculates order total correctly', function () {
    $service = new OrderService();

    $total = $service->calculateTotal([
        ['price' => 10.00, 'quantity' => 2],
        ['price' => 5.50,  'quantity' => 3],
    ]);

    expect($total)->toBe(36.50);
});

it('throws when product is out of stock', function () {
    $service = app(OrderService::class);

    expect(fn() => $service->create(['product_id' => 999, 'quantity' => 1]))
        ->toThrow(InsufficientStockException::class);
});
```

## Factories

```php
// Complex factory setup
it('cancels a paid order and refunds', function () {
    $order = Order::factory()
        ->paid()
        ->withItems(3)
        ->for(User::factory()->withCreditCard())
        ->create();

    $this->actingAs($order->user)
        ->postJson("/api/v1/orders/{$order->id}/cancel")
        ->assertOk();

    expect($order->fresh())
        ->status->toBe(OrderStatus::Cancelled)
        ->refunded_at->not->toBeNull();
});
```

## Mocking and Faking

```php
it('sends confirmation email after order creation', function () {
    Mail::fake();
    Event::fake();
    Queue::fake();

    $user = User::factory()->create();

    $this->actingAs($user)
        ->postJson('/api/v1/orders', $this->validPayload())
        ->assertCreated();

    Mail::assertSent(OrderConfirmationMail::class, function ($mail) use ($user) {
        return $mail->hasTo($user->email);
    });

    Event::assertDispatched(OrderCreated::class);

    Queue::assertPushed(ProcessPaymentJob::class);
});

// HTTP faking for external services
it('handles payment gateway failure', function () {
    Http::fake([
        'api.payment.com/*' => Http::response(['error' => 'declined'], 402),
    ]);

    // ...test behavior when payment fails
});
```

## Dataset-Driven Tests

```php
it('validates price range', function (float $price, bool $valid) {
    $user = User::factory()->create();

    $response = $this->actingAs($user)->postJson('/api/v1/products', [
        'name'  => 'Widget',
        'price' => $price,
    ]);

    $valid
        ? $response->assertCreated()
        : $response->assertUnprocessable();
})->with([
    'zero price'     => [0.0,    false],
    'negative price' => [-1.0,   false],
    'valid price'    => [9.99,   true],
    'large price'    => [9999.0, true],
]);
```

## Testing Authorization

```php
it('prevents users from viewing other users orders', function () {
    $owner = User::factory()->create();
    $other = User::factory()->create();
    $order = Order::factory()->for($owner)->create();

    $this->actingAs($other)
        ->getJson("/api/v1/orders/{$order->id}")
        ->assertForbidden();
});

it('allows admin to view any order', function () {
    $admin = User::factory()->admin()->create();
    $order = Order::factory()->create();

    $this->actingAs($admin)
        ->getJson("/api/v1/orders/{$order->id}")
        ->assertOk();
});
```

## Assertions Quick Reference

```php
// HTTP status
->assertOk()            // 200
->assertCreated()       // 201
->assertNoContent()     // 204
->assertUnauthorized()  // 401
->assertForbidden()     // 403
->assertNotFound()      // 404
->assertUnprocessable() // 422

// JSON structure
->assertJson(['key' => 'value'])
->assertJsonPath('data.id', 1)
->assertJsonCount(3, 'data')
->assertJsonStructure(['data' => ['id', 'name', 'email']])
->assertJsonMissing(['password'])
->assertJsonValidationErrors(['email', 'name'])

// Database
$this->assertDatabaseHas('orders', ['status' => 'paid']);
$this->assertDatabaseMissing('orders', ['id' => $deletedId]);
$this->assertDatabaseCount('orders', 5);
$this->assertSoftDeleted('orders', ['id' => $order->id]);
```
