# Queues & Events

## Jobs

```php
// app/Jobs/ProcessOrderPayment.php
class ProcessOrderPayment implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;
    public int $timeout = 60;
    public int $backoff = 30;  // seconds between retries

    public function __construct(
        private readonly Order $order,
        private readonly string $paymentToken,
    ) {}

    public function handle(PaymentGateway $gateway): void
    {
        $result = $gateway->charge($this->order->total, $this->paymentToken);

        $this->order->update([
            'status'       => OrderStatus::Paid,
            'payment_id'   => $result->id,
            'paid_at'      => now(),
        ]);

        event(new OrderPaid($this->order));
    }

    public function failed(\Throwable $exception): void
    {
        $this->order->update(['status' => OrderStatus::PaymentFailed]);
        Log::error('Payment failed', [
            'order_id'  => $this->order->id,
            'exception' => $exception->getMessage(),
        ]);
    }

    // Prevent duplicate jobs for same order
    public function uniqueId(): string
    {
        return (string) $this->order->id;
    }
}
```

### Dispatching Jobs

```php
// Dispatch to default queue
ProcessOrderPayment::dispatch($order, $token);

// Dispatch with delay
ProcessOrderPayment::dispatch($order, $token)->delay(now()->addMinutes(5));

// Dispatch to specific queue
ProcessOrderPayment::dispatch($order, $token)->onQueue('payments');

// Dispatch synchronously (testing / urgent)
ProcessOrderPayment::dispatchSync($order, $token);

// Conditional dispatch
ProcessOrderPayment::dispatchIf($order->requiresPayment(), $order, $token);

// Chain: run sequentially
Bus::chain([
    new ProcessOrderPayment($order, $token),
    new SendOrderConfirmation($order),
    new UpdateInventory($order),
])->dispatch();
```

### Queue Configuration

```php
// config/queue.php — use Redis for production
'default' => env('QUEUE_CONNECTION', 'redis'),

// Run workers
php artisan queue:work --queue=payments,default --tries=3
php artisan queue:work --sleep=3 --timeout=60
```

---

## Events

```php
// app/Events/OrderPaid.php
class OrderPaid
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    public function __construct(
        public readonly Order $order,
    ) {}
}
```

### Listeners

```php
// app/Listeners/SendOrderPaidNotification.php
class SendOrderPaidNotification implements ShouldQueue
{
    use InteractsWithQueue;

    public function handle(OrderPaid $event): void
    {
        Mail::to($event->order->user)->send(
            new OrderPaidMail($event->order)
        );
    }

    // Only handle if condition met
    public function shouldHandle(OrderPaid $event): bool
    {
        return $event->order->user->wantsEmailNotifications();
    }
}
```

### Registering Events

```php
// app/Providers/EventServiceProvider.php
// Laravel auto-discovers listeners — but explicit is cleaner for large apps:
protected $listen = [
    OrderPaid::class => [
        SendOrderPaidNotification::class,
        UpdateSalesReport::class,
        NotifyWarehouse::class,
    ],

    OrderCancelled::class => [
        RefundPayment::class,
        RestoreInventory::class,
    ],
];
```

### Dispatching Events

```php
event(new OrderPaid($order));

// Or via model dispatch
OrderPaid::dispatch($order);

// Model events (automatic via $dispatchesEvents)
class Order extends Model
{
    protected $dispatchesEvents = [
        'created' => OrderCreated::class,
        'updated' => OrderUpdated::class,
    ];
}
```

---

## Observers

For model lifecycle hooks — keep logic out of the model:

```php
// app/Observers/OrderObserver.php
class OrderObserver
{
    public function created(Order $order): void
    {
        event(new OrderCreated($order));
    }

    public function updated(Order $order): void
    {
        if ($order->wasChanged('status')) {
            event(new OrderStatusChanged($order, $order->getOriginal('status')));
        }
    }

    public function deleting(Order $order): void
    {
        // Cancel pending jobs before deletion
        $order->jobs()->delete();
    }
}

// Register in AppServiceProvider
Order::observe(OrderObserver::class);
```

---

## Notifications

```php
// app/Notifications/OrderShipped.php
class OrderShipped extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(
        private readonly Order $order,
    ) {}

    public function via(object $notifiable): array
    {
        return ['mail', 'database'];  // channels
    }

    public function toMail(object $notifiable): MailMessage
    {
        return (new MailMessage)
            ->subject("Your order #{$this->order->id} has shipped")
            ->line('Your order is on its way!')
            ->action('Track Order', url("/orders/{$this->order->id}"))
            ->line('Thank you for your purchase.');
    }

    public function toArray(object $notifiable): array
    {
        return [
            'order_id'     => $this->order->id,
            'tracking_url' => $this->order->tracking_url,
        ];
    }
}

// Dispatch
$user->notify(new OrderShipped($order));

// Or via Notification facade (bulk)
Notification::send($users, new OrderShipped($order));
```

---

## Scheduled Tasks

```php
// routes/console.php (Laravel 11) or app/Console/Kernel.php
Schedule::job(new GenerateDailySalesReport())->dailyAt('08:00');
Schedule::command('orders:expire-pending')->everyFifteenMinutes();
Schedule::call(fn() => Cache::flush())->weekly()->sundays()->at('03:00');

// Prevent overlapping long-running tasks
Schedule::job(new HeavyDataSync())->hourly()->withoutOverlapping();

// Run in maintenance mode
Schedule::command('backup:run')->daily()->evenInMaintenanceMode();
```
