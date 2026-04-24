# laravel-engineer

Junie extension that turns the agent into a disciplined Laravel engineer: enforces thin-controller architecture, Form Request validation, API Resources, Services/Actions pattern, eager loading, and catches common mistakes (N+1, mass assignment, service locator anti-pattern, raw password storage).

## Philosophy

Baseline Laravel knowledge is assumed — the extension does not re-teach Eloquent, routing, or middleware. Instead it encodes:

- **Policy** — MUST / MUST NOT rules for architecture and security.
- **Setup awareness** — requires `laravel/boost` to be installed and configured; `boost:install` generates project-specific AI guidelines, installs best-practice skills, and configures MCP tools (routes, schema, logs, Tinker). Without it the agent has no project context.

## What it covers

- Architecture: thin controllers, Form Requests for validation, API Resources for transformation, Services/Actions for business logic.
- Eloquent discipline: `$fillable` / `$guarded`, eager loading, typed casts, scopes.
- Security: `Hash::make()` for passwords, no `$request->all()` mass assignment, constructor injection over service locator.
- Output order: migration → model → form request → service/action → controller → resource → Pest tests.

## Requirements

- Laravel project with `composer.json`.
- `laravel/boost` installed (`composer require --dev laravel/boost`) and initialized (`php artisan boost:install`).
- PHPStan via `vendor/bin/phpstan` — run after generating code.

## Installation

Drop the extension folder into your Junie extensions directory and enable it. The agent will check for `laravel/boost` on every task and prompt you to install it if missing.
