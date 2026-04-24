---
name: laravel-engineer
description: Use when working on Laravel projects. Covers architecture patterns, thin controllers, Services/Actions, Form Requests, and API Resources. Ensures Laravel Boost is set up for project-aware AI assistance.
---

# Laravel Engineer

> **Self-contained.** This skill intentionally ships **without a `references/` directory**.
> Deep, project-aware Laravel guidance (version-specific idioms, package rules, routes/schema/log introspection) is delivered by **Laravel Boost** at runtime — it installs the matching best-practices skills and MCP tools into the project. This SKILL.md only encodes the policy + pitfalls that Boost does not cover (architecture layering, anti-patterns, output contract).

## Core Workflow

1. **Check toolchain** — run Setup Check below before doing anything else
2. **Design first** — for non-trivial tasks, confirm approach before coding
3. **Implement** — follow architecture rules below: thin controllers, Form Requests, Services/Actions
4. **Verify** — run `./vendor/bin/phpstan analyse` after generating code

## Setup Check

**Strongly recommended.** Laravel Boost is how this skill delegates project-specific knowledge. If the project cannot or will not use Boost, proceed with the rules below alone and state that assumption in your plan.

### Step 1 — Is `laravel/boost` installed?

Read `composer.json`. Look for `laravel/boost` in `require` or `require-dev`.

- Found → continue to Step 2
- Not found → **suggest installing** (do not install silently):
  ```
  composer require --dev laravel/boost
  ```

### Step 2 — Has `boost:install` been run?

Read `boost.json` in the project root. Check that `"guidelines": true` is present.

- `boost.json` exists and `"guidelines": true` → proceed with the task
- `boost.json` missing or `"guidelines"` is not `true` → **suggest running:**
  ```
  php artisan boost:install
  ```

`boost:install` generates project-specific AI guidelines, installs Laravel best practices skills, and configures MCP tools (routes, schema, logs, Tinker). Without it the AI has no project context — fall back to the Constraints section of this file as the only source of truth.


## Constraints

### MUST DO

| Rule | Correct Pattern |
|------|----------------|
| Validate in Form Requests | `class StorePostRequest extends FormRequest` |
| Transform in Resources | `class PostResource extends JsonResource` |
| Business logic in Services or Actions | `OrderService::create()`, `CreateOrderAction::handle()` |
| Use `$fillable` or `$guarded` | Never leave both empty |
| Eager-load relationships | `Order::with('items', 'user')->get()` |
| Use casts for types | `'status' => OrderStatus::class` in `$casts` |
| Type-hint injected services | `private readonly OrderService $service` |

### MUST NOT DO

- Put business logic in controllers
- Use `DB::table()` when an Eloquent model exists
- Call `->get()` inside a loop (N+1)
- Use `$request->all()` for mass assignment
- Leave relationships un-eager-loaded in collection endpoints
- Return raw arrays from controllers instead of Resources
- Use `Auth::user()` directly in service layer — pass user as parameter
- Use `app()` or `resolve()` as service locator — use constructor injection instead
- Store passwords in plain text — use `Hash::make()`, never raw `md5()` or `sha1()`

## Output Format

When implementing a feature, deliver in this order:
1. Migration (if schema changes needed)
2. Model with casts, relationships, scopes
3. Form Request + Service / Action
4. Controller + API Resource
5. Tests (Pest if the project uses it, PHPUnit otherwise)
6. One-line explanation of key architecture decisions
