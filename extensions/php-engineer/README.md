# php-engineer

Junie extension that turns the agent into a disciplined PHP 8.x engineer: enforces project-level policy and catches the subtle language traps that LLMs get wrong by default — type coercion, `foreach`-by-reference leaks, `readonly` mutation through references, `DateTime` aliasing, PDO emulation mode, unsafe `unserialize`, file-upload MIME spoofing.

## Philosophy

Baseline PHP 8.x knowledge (enums, readonly, match, nullsafe, union/intersection/DNF types, named arguments, first-class callables, fibers, PSR-1/4/12, Composer) is assumed — the extension does not re-teach the language. Instead it encodes:

- **Policy** — MUST / MUST NOT rules the agent should follow in every file it touches.
- **Pitfalls** — behaviors that pass linters and trivial tests, then fail in production or security review.
- **Setup awareness** — detect PHP version, strict_types, PHPStan level, formatter, framework before writing non-trivial code.

## What it covers

- Strict-types discipline: enforcement, coercion traps, PHPStan level 8+ workflow.
- Type system: backed enums, readonly/readonly class, match, DNF types, named arguments, generics via PHPDoc.
- Language pitfalls: `foreach` reference leak, `readonly` mutation through `&`, `==` vs `===`, `DateTime` aliasing, `count` on empty.
- Security: prepared statements, password hashing, CSRF, `unserialize` dangers, file-upload MIME spoofing, credentials in logs.
- Framework detection: if Laravel/Symfony is present, defers to the corresponding framework skill.

## Files

- `skills/php-engineer/SKILL.md` — hub: Setup Check, MUST DO / MUST NOT, Reference Guide, Output Format.
- `skills/php-engineer/references/pitfalls.md` — subtle language / API gotchas.
- `skills/php-engineer/references/types.md` — type signatures: PHPStan generics, DNF, `mixed`/`never`/`void`, narrowing.
- `skills/php-engineer/references/security.md` — SQL injection, password hashing, CSRF, file upload, serialization.

## Requirements

- PHP 8.2+ (`"php": ">=8.2"` in `composer.json`).
- `declare(strict_types=1);` in every file — non-negotiable.
- `vendor/bin/phpstan` at level 8+ recommended (`composer require --dev phpstan/phpstan`).
- Formatter: `pint` / `php-cs-fixer` / `phpcs` — the agent respects whatever is already configured.

## Installation

Drop the extension folder into your Junie extensions directory and enable it. Junie picks up `SKILL.md` automatically and loads references on demand.
