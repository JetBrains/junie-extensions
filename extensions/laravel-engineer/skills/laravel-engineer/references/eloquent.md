# Eloquent ORM

## Model Definition

```php
class Product extends Model
{
    use HasFactory, SoftDeletes;

    // Always declare fillable — never leave $guarded = []
    protected $fillable = ['name', 'price', 'category_id', 'is_active'];

    protected $casts = [
        'price'      => 'decimal:2',
        'is_active'  => 'boolean',
        'metadata'   => 'array',
        'published_at' => 'datetime',
        'status'     => ProductStatus::class,  // enum cast (PHP 8.1+)
    ];

    // Hide sensitive fields from serialization
    protected $hidden = ['internal_notes'];
}
```

## Relationships

```php
class User extends Model
{
    // Has Many
    public function orders(): HasMany
    {
        return $this->hasMany(Order::class);
    }

    // Has One
    public function profile(): HasOne
    {
        return $this->hasOne(Profile::class);
    }

    // Belongs To Many (pivot)
    public function roles(): BelongsToMany
    {
        return $this->belongsToMany(Role::class)
            ->withTimestamps()
            ->withPivot('assigned_at');
    }

    // Has Many Through
    public function deployments(): HasManyThrough
    {
        return $this->hasManyThrough(Deployment::class, Project::class);
    }

    // Polymorphic
    public function comments(): MorphMany
    {
        return $this->morphMany(Comment::class, 'commentable');
    }
}

class Order extends Model
{
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function items(): HasMany
    {
        return $this->hasMany(OrderItem::class);
    }
}
```

## Eager Loading — N+1 Prevention

```php
// ❌ N+1: executes 1 + N queries
$orders = Order::all();
foreach ($orders as $order) {
    echo $order->user->name;  // query per iteration
}

// ✅ Eager load: 2 queries total
$orders = Order::with('user')->get();

// ✅ Multiple relationships
$orders = Order::with(['user', 'items', 'items.product'])->get();

// ✅ Constrained eager loading
$orders = Order::with([
    'user:id,name,email',  // select specific columns
    'items' => fn($q) => $q->where('quantity', '>', 0),
])->get();

// ✅ Lazy eager loading (when relation is conditionally needed)
$orders->loadMissing('user');
```

## Query Scopes

```php
class Order extends Model
{
    // Local scope
    public function scopePending(Builder $query): void
    {
        $query->where('status', OrderStatus::Pending);
    }

    public function scopeForUser(Builder $query, int $userId): void
    {
        $query->where('user_id', $userId);
    }

    public function scopeRecent(Builder $query, int $days = 30): void
    {
        $query->where('created_at', '>=', now()->subDays($days));
    }
}

// Usage
Order::pending()->forUser($userId)->recent()->get();

// Global scope (applied to all queries)
class ActiveScope implements Scope
{
    public function apply(Builder $builder, Model $model): void
    {
        $builder->where('is_active', true);
    }
}

// Apply in model
protected static function booted(): void
{
    static::addGlobalScope(new ActiveScope());
}
```

## Querying

```php
// Basic
User::find(1);
User::findOrFail(1);            // throws ModelNotFoundException
User::where('email', $email)->first();
User::where('email', $email)->firstOrFail();

// Conditions
User::where('active', true)
    ->where('age', '>=', 18)
    ->whereIn('role', ['admin', 'editor'])
    ->whereNotNull('email_verified_at')
    ->orderBy('created_at', 'desc')
    ->paginate(20);

// Aggregates
User::count();
Order::sum('total');
Order::avg('total');
Order::max('total');

// Exists check
User::where('email', $email)->exists();

// Chunking large datasets — avoid loading everything into memory
User::chunk(500, function (Collection $users) {
    foreach ($users as $user) {
        // process
    }
});

// Lazy collection for memory efficiency
User::lazy()->each(function (User $user) {
    // process
});
```

## Mutations

```php
// Create
$user = User::create(['name' => 'John', 'email' => 'john@example.com']);

// First or create
$user = User::firstOrCreate(
    ['email' => 'john@example.com'],        // search by
    ['name' => 'John', 'role' => 'user'],   // create with
);

// Update or create
User::updateOrCreate(
    ['email' => 'john@example.com'],
    ['name' => 'John Updated'],
);

// Update
$user->update(['name' => 'Jane']);

// Mass update (no model events fired)
User::where('active', false)->update(['deleted_at' => now()]);

// Delete
$user->delete();

// Force delete (soft deletes)
$user->forceDelete();

// Restore (soft deletes)
$user->restore();
```

## Migrations

```php
// ✅ Good migration pattern
Schema::create('orders', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->constrained()->cascadeOnDelete();
    $table->string('status', 50)->default('pending');
    $table->decimal('total', 10, 2);
    $table->json('metadata')->nullable();
    $table->timestamp('shipped_at')->nullable();
    $table->softDeletes();
    $table->timestamps();

    $table->index(['user_id', 'status']);
    $table->index('created_at');
});

// Modifying columns
Schema::table('users', function (Blueprint $table) {
    $table->string('name', 200)->change();     // change existing column
    $table->after('email', function (Blueprint $table) {
        $table->boolean('is_verified')->default(false);
    });
});
```

## Factories

```php
class OrderFactory extends Factory
{
    public function definition(): array
    {
        return [
            'user_id' => User::factory(),
            'status'  => OrderStatus::Pending,
            'total'   => $this->faker->randomFloat(2, 10, 1000),
        ];
    }

    // States
    public function paid(): static
    {
        return $this->state(['status' => OrderStatus::Paid]);
    }

    public function withItems(int $count = 3): static
    {
        return $this->has(OrderItem::factory()->count($count), 'items');
    }
}

// Usage in tests
Order::factory()->paid()->withItems(5)->create();
Order::factory()->count(10)->create();
```

## Performance Tips

```php
// ✅ Select only needed columns
User::select('id', 'name', 'email')->get();

// ✅ Use pluck for single column
$emails = User::pluck('email');
$map    = User::pluck('name', 'id');  // id => name

// ✅ Use value() for single column, single row
$name = User::where('id', 1)->value('name');

// ✅ Pagination over get() for large datasets
$users = User::paginate(50);          // with metadata
$users = User::simplePaginate(50);    // next/prev only (faster)
$users = User::cursorPaginate(50);    // cursor-based (most efficient for large sets)

// ✅ withCount instead of loading relation
$users = User::withCount('orders')->get();
// $user->orders_count

// ✅ Use exists() not count() > 0
if (User::where('email', $email)->exists()) { ... }
```
