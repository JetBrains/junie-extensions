# laravel-engineer

Junie extension that turns the agent into a disciplined Laravel engineer: enforces thin-controller architecture, Form Request validation, API Resources, Services/Actions pattern, eager loading, and catches common mistakes (N+1, mass assignment, service locator anti-pattern, raw password storage).

## Philosophy

Baseline Laravel knowledge is assumed — the extension does not re-teach Eloquent, routing, or middleware. Instead it encodes:

- **Policy** — MUST / MUST NOT rules for architecture and security.
- **Architecture decisions** — Services vs Actions vs Jobs decision table to prevent the most common LLM mistake: generating the wrong abstraction layer.
- **Static analysis** — Larastan (Laravel-aware PHPStan) as a mandatory verification step after code generation.

## What it covers

- Architecture: thin controllers, Form Requests for validation, API Resources for transformation, Services/Actions for business logic, with a clear decision table for when to use each.
- Eloquent discipline: `$fillable` / `$guarded`, eager loading, typed casts, scopes.
- Security: `Hash::make()` for passwords, no `$request->all()` mass assignment, constructor injection over service locator.
- Static analysis: Larastan at level 5+, baseline workflow for legacy projects.
- API versioning: URI path versioning, deprecation headers.
- Output order: migration → model → form request → service/action → controller → resource → Pest tests.

## Requirements

- Laravel project with `composer.json`.
- Larastan via `composer require --dev nunomaduro/larastan` — run after generating code.

## Installation

Drop the extension folder into your Junie extensions directory and enable it.
