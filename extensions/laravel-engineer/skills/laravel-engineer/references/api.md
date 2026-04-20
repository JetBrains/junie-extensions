# API Layer

## Routing

```php
// routes/api.php
Route::prefix('v1')->middleware('auth:sanctum')->group(function () {
    Route::apiResource('orders', OrderController::class);

    // Custom actions alongside resource routes
    Route::post('orders/{order}/cancel', [OrderController::class, 'cancel'])
        ->name('orders.cancel');

    Route::get('users/me', [UserController::class, 'me'])
        ->name('users.me');
});

// Public routes
Route::prefix('v1')->group(function () {
    Route::post('auth/login', [AuthController::class, 'login']);
    Route::post('auth/register', [AuthController::class, 'register']);
});
```

`apiResource` generates: `index`, `store`, `show`, `update`, `destroy` (no `create`/`edit`).

## Controllers

Thin controllers — direct traffic only:

```php
class OrderController extends Controller
{
    public function __construct(
        private readonly OrderService $orderService,
    ) {}

    public function index(Request $request): AnonymousResourceCollection
    {
        $orders = Order::with('items')
            ->forUser($request->user()->id)
            ->paginate(20);

        return OrderResource::collection($orders);
    }

    public function store(StoreOrderRequest $request): OrderResource
    {
        $order = $this->orderService->create(
            $request->validated(),
            $request->user(),
        );

        return (new OrderResource($order))
            ->response()
            ->setStatusCode(201);
    }

    public function show(Order $order): OrderResource
    {
        $this->authorize('view', $order);
        return new OrderResource($order->load('items.product'));
    }

    public function update(UpdateOrderRequest $request, Order $order): OrderResource
    {
        $this->authorize('update', $order);
        $this->orderService->update($order, $request->validated());
        return new OrderResource($order->fresh('items'));
    }

    public function destroy(Order $order): Response
    {
        $this->authorize('delete', $order);
        $this->orderService->delete($order);
        return response()->noContent();
    }
}
```

## Form Requests

All validation goes in Form Requests — never in controllers:

```php
class StoreOrderRequest extends FormRequest
{
    public function authorize(): bool
    {
        // Use policies for complex authorization
        return $this->user()->can('create', Order::class);
    }

    public function rules(): array
    {
        return [
            'items'              => ['required', 'array', 'min:1'],
            'items.*.product_id' => ['required', 'integer', 'exists:products,id'],
            'items.*.quantity'   => ['required', 'integer', 'min:1', 'max:100'],
            'shipping_address'   => ['required', 'string', 'max:500'],
            'notes'              => ['nullable', 'string', 'max:1000'],
        ];
    }

    public function messages(): array
    {
        return [
            'items.required' => 'At least one item is required.',
            'items.*.product_id.exists' => 'Product :input does not exist.',
        ];
    }

    // Transform/prepare input before validation
    protected function prepareForValidation(): void
    {
        $this->merge([
            'shipping_address' => trim($this->shipping_address ?? ''),
        ]);
    }
}
```

## API Resources

Transform models consistently — never return raw models from API endpoints:

```php
class OrderResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id'         => $this->id,
            'status'     => $this->status->value,
            'status_label' => $this->status->label(),
            'total'      => number_format($this->total, 2),
            'items'      => OrderItemResource::collection($this->whenLoaded('items')),
            'user'       => new UserResource($this->whenLoaded('user')),
            'created_at' => $this->created_at->toISOString(),

            // Conditional fields
            'admin_notes' => $this->when(
                $request->user()?->isAdmin(),
                $this->admin_notes,
            ),
        ];
    }
}

// Collection resource with metadata
class OrderCollection extends ResourceCollection
{
    public function toArray(Request $request): array
    {
        return [
            'data' => $this->collection,
            'meta' => [
                'total_value' => $this->collection->sum('total'),
            ],
        ];
    }
}
```

## Error Handling

Register in `app/Exceptions/Handler.php` (or `bootstrap/app.php` in Laravel 11):

```php
// Laravel 11 — bootstrap/app.php
->withExceptions(function (Exceptions $exceptions) {
    $exceptions->render(function (ModelNotFoundException $e, Request $request) {
        if ($request->expectsJson()) {
            return response()->json([
                'message' => 'Resource not found.',
            ], 404);
        }
    });

    $exceptions->render(function (AuthorizationException $e, Request $request) {
        if ($request->expectsJson()) {
            return response()->json([
                'message' => 'This action is unauthorized.',
            ], 403);
        }
    });
})

// Custom exception
class InsufficientStockException extends \RuntimeException
{
    public function __construct(
        public readonly int $productId,
        public readonly int $requested,
        public readonly int $available,
    ) {
        parent::__construct("Insufficient stock for product {$productId}");
    }

    public function render(): JsonResponse
    {
        return response()->json([
            'message'   => $this->getMessage(),
            'requested' => $this->requested,
            'available' => $this->available,
        ], 422);
    }
}
```

## Pagination

```php
// Controller returns paginated resource
public function index(): AnonymousResourceCollection
{
    return OrderResource::collection(
        Order::with('user')->paginate(20)
    );
}

// Response includes pagination links automatically:
// {
//   "data": [...],
//   "links": { "first": "...", "last": "...", "prev": null, "next": "..." },
//   "meta": { "current_page": 1, "total": 150, "per_page": 20, ... }
// }

// Cursor pagination for large datasets
Order::cursorPaginate(20);
```

## Response Helpers

```php
// 200 OK with data
return new OrderResource($order);

// 201 Created
return (new OrderResource($order))->response()->setStatusCode(201);

// 204 No Content
return response()->noContent();

// 202 Accepted (async job dispatched)
return response()->json(['message' => 'Processing started.'], 202);
```
