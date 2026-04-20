# Authentication & Authorization

## Laravel Sanctum (API Tokens)

### Setup

```bash
composer require laravel/sanctum
php artisan vendor:publish --provider="Laravel\Sanctum\SanctumServiceProvider"
php artisan migrate
```

Add `HasApiTokens` to User model:

```php
use Laravel\Sanctum\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens, HasFactory, Notifiable;
}
```

### Token Issuance

```php
class AuthController extends Controller
{
    public function login(LoginRequest $request): JsonResponse
    {
        if (! Auth::attempt($request->only('email', 'password'))) {
            throw new AuthenticationException('Invalid credentials.');
        }

        $user  = Auth::user();
        $token = $user->createToken(
            name:       $request->device_name ?? 'api',
            abilities:  ['orders:read', 'orders:write'],
            expiresAt:  now()->addDays(30),
        );

        return response()->json([
            'token' => $token->plainTextToken,
            'user'  => new UserResource($user),
        ]);
    }

    public function logout(Request $request): Response
    {
        $request->user()->currentAccessToken()->delete();
        return response()->noContent();
    }

    public function logoutAll(Request $request): Response
    {
        $request->user()->tokens()->delete();
        return response()->noContent();
    }
}
```

### Token Abilities

```php
// Check in middleware or controller
$request->user()->tokenCan('orders:write');

// Middleware on routes
Route::middleware(['auth:sanctum', 'abilities:orders:write'])
    ->post('/orders', [OrderController::class, 'store']);
```

---

## Policies

Define authorization logic for a model — keep it out of controllers:

```php
// app/Policies/OrderPolicy.php
class OrderPolicy
{
    public function viewAny(User $user): bool
    {
        return true;
    }

    public function view(User $user, Order $order): bool
    {
        return $user->id === $order->user_id || $user->isAdmin();
    }

    public function create(User $user): bool
    {
        return $user->hasVerifiedEmail();
    }

    public function update(User $user, Order $order): bool
    {
        return $user->id === $order->user_id
            && $order->status === OrderStatus::Pending;
    }

    public function delete(User $user, Order $order): bool
    {
        return $user->id === $order->user_id || $user->isAdmin();
    }

    public function cancel(User $user, Order $order): bool
    {
        return $user->id === $order->user_id
            && in_array($order->status, [OrderStatus::Pending, OrderStatus::Paid]);
    }
}
```

Register (Laravel auto-discovers policies by convention `Model` → `ModelPolicy`).

### Using Policies in Controllers

```php
// Single authorization check
$this->authorize('update', $order);

// In Form Request
public function authorize(): bool
{
    return $this->user()->can('update', $this->route('order'));
}

// Manual check
if ($request->user()->cannot('cancel', $order)) {
    abort(403);
}
```

---

## Gates

For actions not tied to a specific model:

```php
// app/Providers/AppServiceProvider.php
Gate::define('access-admin', function (User $user): bool {
    return $user->role === 'admin';
});

Gate::define('manage-settings', function (User $user): bool {
    return $user->hasPermission('settings.manage');
});

// Middleware
Route::middleware('can:access-admin')->group(function () {
    Route::get('/admin', AdminController::class);
});

// In controller
Gate::authorize('access-admin');

// In Blade
@can('access-admin')
    <a href="/admin">Admin Panel</a>
@endcan
```

---

## Role-based Access

Simple role system without a package:

```php
// Migration
$table->string('role')->default('user');  // 'user', 'editor', 'admin'

// Model helpers
class User extends Authenticatable
{
    public function isAdmin(): bool
    {
        return $this->role === 'admin';
    }

    public function hasRole(string $role): bool
    {
        return $this->role === $role;
    }
}

// Gate with role check
Gate::before(function (User $user, string $ability): ?bool {
    if ($user->isAdmin()) {
        return true;  // admin bypasses all gates
    }
    return null;  // proceed to gate/policy check
});
```

---

## Middleware

```php
// Apply to all API routes
Route::middleware('auth:sanctum')->group(function () { ... });

// Require specific ability
Route::middleware(['auth:sanctum', 'abilities:reports:read'])->get('/reports', ...);

// Rate limiting (config/routes.php)
Route::middleware(['auth:sanctum', 'throttle:60,1'])->group(function () { ... });

// Custom middleware
class EnsureUserIsVerified
{
    public function handle(Request $request, Closure $next): Response
    {
        if (! $request->user()->hasVerifiedEmail()) {
            return response()->json(['message' => 'Email not verified.'], 403);
        }

        return $next($request);
    }
}
```

---

## Password Reset

```php
// Trigger reset email
Password::sendResetLink(['email' => $request->email]);

// Reset password
$status = Password::reset(
    $request->only('email', 'password', 'password_confirmation', 'token'),
    function (User $user, string $password) {
        $user->forceFill(['password' => Hash::make($password)])->save();
        $user->tokens()->delete();  // revoke all tokens
        event(new PasswordReset($user));
    }
);

if ($status !== Password::PASSWORD_RESET) {
    throw new \Exception(__($status));
}
```
