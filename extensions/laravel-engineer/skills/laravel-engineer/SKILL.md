---
name: laravel-engineer
description: Use when working on Laravel projects. Covers architecture decisions (Services vs Actions), thin controllers, Form Requests, API Resources, and API versioning. Enforces Larastan verification after code generation.
---

# Laravel Engineer

## Core Workflow

1. **Design first** — for non-trivial tasks, confirm approach before coding: which layer (Service/Action/Job?), data model changes, auth requirements
2. **Implement** — follow architecture rules below: thin controllers, Form Requests, Services/Actions
3. **Verify** — run `./vendor/bin/phpstan analyse` (Larastan) after generating code

## Services vs Actions — Pick One

The most common mistake: generating a Service where an Action fits, or vice versa.

| Pattern | When to use | Example |
|---------|-------------|---------|
| **Action** | Single operation, called in one place, no shared state | `CreateOrderAction`, `SendWelcomeEmailAction` |
| **Service** | Reusable across multiple callers, wraps a capability | `PaymentGatewayService`, `GeocodingService` |
| **Job** | Async / background work, retry semantics needed | `ProcessImportJob`, `SendBulkEmailJob` |

- An Action called from only one controller is fine — don't extract to a Service
- A Service called from only one place should be an Action
- Never introduce a Command Bus where a simple Action call works

## Static Analysis

Use **Larastan** (not raw PHPStan) for Laravel-aware type checking:

```bash
composer require --dev nunomaduro/larastan
```

Target **level 5+** for new projects. On legacy code, baseline existing violations first, then climb:

```bash
./vendor/bin/phpstan analyse --level=5
./vendor/bin/phpstan analyse --generate-baseline  # baseline legacy violations
```

Never ship code that fails at the project's configured level.

## API Versioning

For APIs expected to evolve:
- URI path versioning is standard: `/api/v1/resource`
- Version only when breaking changes exist — don't pre-version everything
- Add `Deprecation` response header before removing old endpoints

## Constraints

### MUST DO

| Rule | Correct Pattern |
|------|----------------|
| Validate in Form Requests | `class StorePostRequest extends FormRequest` |
| Transform in Resources | `class PostResource extends JsonResource` |
| Business logic in Services or Actions | `OrderService::calculate()`, `CreateOrderAction::handle()` |
| Use `$fillable` or `$guarded` | Never leave both empty |
| Eager-load relationships | `Order::with('items', 'user')->get()` |
| Use casts for types | `'status' => OrderStatus::class` in `$casts` |
| Type-hint injected services | `private readonly OrderService $service` |

### MUST NOT DO

- Put business logic in controllers
- Use `DB::table()` when an Eloquent model exists
- Call `->get()` inside a loop (N+1)
- Use `$request->all()` for mass assignment — use `$request->validated()`
- Leave relationships un-eager-loaded in collection endpoints
- Return raw arrays from controllers instead of Resources
- Use `Auth::user()` directly in service layer — pass user as parameter
- Use `app()` or `resolve()` as service locator — use constructor injection
- Store passwords in plain text — use `Hash::make()`, never `md5()` or `sha1()`
- Over-engineer: don't add Services/Actions/Command Bus for simple CRUD that a single controller method handles fine

## Output Format

When implementing a feature, deliver in this order:
1. Migration (if schema changes needed)
2. Model with casts, relationships, scopes
3. Form Request + Service / Action
4. Controller + API Resource
5. Tests (Pest if the project uses it, PHPUnit otherwise)
6. One-line explanation of key architecture decisions
