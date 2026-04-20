# Architecture Patterns

## Project Structure

```
app/
├── Http/
│   ├── Controllers/
│   │   └── Api/
│   ├── Requests/           # Form Requests (validation)
│   ├── Resources/          # API Resources (transformation)
│   └── Middleware/
├── Models/
├── Services/               # Business logic (stateful, multi-step)
├── Actions/                # Single-purpose operations
├── DTOs/                   # Data Transfer Objects
├── Events/
├── Listeners/
├── Jobs/
├── Notifications/
├── Observers/
├── Policies/
└── Exceptions/
```

## Services

Use for multi-step business operations that involve state or multiple models:

```php
// app/Services/OrderService.php
class OrderService
{
    public function __construct(
        private readonly InventoryService $inventory,
        private readonly PaymentGateway   $payment,
    ) {}

    public function create(array $data, User $user): Order
    {
        DB::transaction(function () use ($data, $user, &$order) {
            $order = Order::create([
                'user_id' => $user->id,
                'status'  => OrderStatus::Pending,
                'total'   => 0,
            ]);

            $total = 0;
            foreach ($data['items'] as $item) {
                $product = Product::findOrFail($item['product_id']);
                $this->inventory->reserve($product, $item['quantity']);

                $order->items()->create([
                    'product_id' => $product->id,
                    'quantity'   => $item['quantity'],
                    'price'      => $product->price,
                ]);

                $total += $product->price * $item['quantity'];
            }

            $order->update(['total' => $total]);
            event(new OrderCreated($order));
        });

        return $order;
    }

    public function cancel(Order $order): void
    {
        if (! in_array($order->status, [OrderStatus::Pending, OrderStatus::Paid])) {
            throw new \DomainException("Cannot cancel order with status: {$order->status->value}");
        }

        DB::transaction(function () use ($order) {
            foreach ($order->items as $item) {
                $this->inventory->release($item->product, $item->quantity);
            }

            if ($order->status === OrderStatus::Paid) {
                $this->payment->refund($order->payment_id);
            }

            $order->update(['status' => OrderStatus::Cancelled]);
            event(new OrderCancelled($order));
        });
    }
}
```

## Actions

Use for single, focused operations — simpler than Services:

```php
// app/Actions/CreateOrderAction.php
class CreateOrderAction
{
    public function handle(User $user, CreateOrderData $data): Order
    {
        return DB::transaction(function () use ($user, $data): Order {
            $order = Order::create([
                'user_id' => $user->id,
                'status'  => OrderStatus::Pending,
                'total'   => $data->total(),
            ]);

            foreach ($data->items as $item) {
                $order->items()->create($item->toArray());
            }

            return $order;
        });
    }
}

// In controller
class OrderController extends Controller
{
    public function __construct(
        private readonly CreateOrderAction $createOrder,
    ) {}

    public function store(StoreOrderRequest $request): OrderResource
    {
        $data  = CreateOrderData::fromRequest($request);
        $order = $this->createOrder->handle($request->user(), $data);

        return new OrderResource($order);
    }
}
```

## DTOs (Data Transfer Objects)

Use readonly classes to pass structured data between layers:

```php
// app/DTOs/CreateOrderData.php
readonly class CreateOrderData
{
    /** @param list<OrderItemData> $items */
    public function __construct(
        public array  $items,
        public string $shippingAddress,
        public ?string $notes = null,
    ) {}

    public static function fromRequest(StoreOrderRequest $request): self
    {
        return new self(
            items:           array_map(
                fn(array $item) => new OrderItemData(
                    productId: $item['product_id'],
                    quantity:  $item['quantity'],
                ),
                $request->validated('items'),
            ),
            shippingAddress: $request->validated('shipping_address'),
            notes:           $request->validated('notes'),
        );
    }

    public function total(): float
    {
        return array_sum(array_map(
            fn(OrderItemData $item) => $item->subtotal(),
            $this->items,
        ));
    }
}

readonly class OrderItemData
{
    public function __construct(
        public int $productId,
        public int $quantity,
    ) {}
}
```

## Repository Pattern

Use when you need to abstract complex query logic or support multiple data sources:

```php
// app/Repositories/OrderRepository.php
interface OrderRepositoryInterface
{
    public function findForUser(int $userId, array $filters = []): LengthAwarePaginator;
    public function findWithItems(int $orderId): ?Order;
    public function totalRevenueForPeriod(Carbon $from, Carbon $to): float;
}

class EloquentOrderRepository implements OrderRepositoryInterface
{
    public function findForUser(int $userId, array $filters = []): LengthAwarePaginator
    {
        return Order::with('items')
            ->where('user_id', $userId)
            ->when(isset($filters['status']), fn($q) => $q->where('status', $filters['status']))
            ->when(isset($filters['from']), fn($q) => $q->where('created_at', '>=', $filters['from']))
            ->latest()
            ->paginate(20);
    }

    public function findWithItems(int $orderId): ?Order
    {
        return Order::with(['items.product', 'user'])->find($orderId);
    }

    public function totalRevenueForPeriod(Carbon $from, Carbon $to): float
    {
        return Order::whereBetween('created_at', [$from, $to])
            ->where('status', OrderStatus::Paid)
            ->sum('total');
    }
}
```

> Use Repository only when query logic is complex or reused. For simple CRUD, Eloquent directly in the service is fine.

## Value Objects

```php
readonly class Money
{
    public function __construct(
        public int    $amount,     // in cents
        public string $currency,
    ) {}

    public function add(Money $other): self
    {
        if ($this->currency !== $other->currency) {
            throw new \DomainException("Currency mismatch: {$this->currency} vs {$other->currency}");
        }

        return new self($this->amount + $other->amount, $this->currency);
    }

    public function format(): string
    {
        return number_format($this->amount / 100, 2) . ' ' . $this->currency;
    }
}

readonly class Email
{
    public readonly string $value;

    public function __construct(string $email)
    {
        if (! filter_var($email, FILTER_VALIDATE_EMAIL)) {
            throw new \InvalidArgumentException("Invalid email: {$email}");
        }
        $this->value = strtolower($email);
    }
}
```

## Service Provider Bindings

```php
// app/Providers/AppServiceProvider.php
public function register(): void
{
    $this->app->bind(
        OrderRepositoryInterface::class,
        EloquentOrderRepository::class,
    );

    $this->app->singleton(
        PaymentGateway::class,
        fn() => new StripeGateway(config('services.stripe.secret')),
    );
}
```
