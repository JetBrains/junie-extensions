---
name: php-engineer
description: Modern PHP 8.x policy and pitfalls. Use when writing, reviewing, or refactoring PHP code — enforces strict types, enum/readonly/match/DNF policy, PHPStan discipline, and catches the subtle traps (type coercion, mixed abuse, readonly mutation through references, enum serialization, fiber lifecycle, PDO emulation) that LLMs get wrong by default.
---

# PHP — policy & pitfalls

Baseline PHP 8.x knowledge (enums, readonly, match, nullsafe, union/intersection/DNF types, named arguments, first-class callables, fibers, PSR-1/4/12, Composer) is assumed. This skill does not teach the language — it encodes project policy and the traps that keep appearing in code review.

## Setup Check (run first)

Before writing non-trivial code:

1. **PHP version** — `composer.json` must declare `"php": ">=8.2"` (or higher). Check `php --version` if running locally.
2. **`declare(strict_types=1);`** at the top of every file. Non-negotiable — without it PHP coerces `"42"` → `42`, `3.7` → `3`, `"abc"` → `0` silently.
3. **Static analysis** — `vendor/bin/phpstan` (target level 8+) and/or `vendor/bin/psalm`. If missing, suggest `composer require --dev phpstan/phpstan`. Run before presenting code.
4. **Formatter** — `vendor/bin/pint` / `php-cs-fixer` / `phpcs`. Respect the existing config; don't introduce new violations.
5. **Lock file** — `composer.lock` must be committed for applications. Never commit `vendor/`.
6. **Framework** — check for `laravel/framework`, `symfony/framework-bundle`, etc. If present, **stop and load the corresponding framework skill** (`laravel-engineer`, etc.); this skill is pure PHP only.

## MUST DO

- **Strict types in every file** — `declare(strict_types=1);` on line 1 after `<?php`.
- **Type everything** — parameters, return types, property types. Untyped code is an error.
- **Backed `enum`** for closed value sets — never `class Status { const ACTIVE = 'active'; }`.
- **`readonly` for immutable data** — DTOs, value objects, events. Prefer `readonly class` (PHP 8.2+) over per-property `readonly`.
- **`match` over `switch`** — strict comparison (`===`), exhaustive, returns value, throws `UnhandledMatchError` on miss.
- **Named arguments for 3+ parameters** — `new UserDto(id: 1, name: 'n', email: 'e')` prevents silent argument swaps.
- **Constructor property promotion** — no separate property declarations + manual assignments.
- **`DateTimeImmutable`** — never `DateTime`; the mutable one causes aliasing bugs.
- **Prepared statements** for every SQL query reaching user input. Bind with named or `?` placeholders — never string-concat.
- **`password_hash($p, PASSWORD_BCRYPT)`** / `PASSWORD_ARGON2ID` + `password_verify`. Never `md5`/`sha1`/`sha256` for passwords.
- **Parameterized logging via PSR-3** — `$logger->info('user.updated', ['id' => $id])`, not string concat.

## MUST NOT DO

- **No `mixed` without a PHPDoc comment** explaining why — it disables type checking on the value.
- **No untyped `array` in public API** — annotate with PHPDoc: `/** @param list<User> $users */` or `/** @return array<string, int> */`.
- **No raw `SimpleXMLElement` / `json_decode` without validation** — use `json_validate()` (PHP 8.3+) first, or `JSON_THROW_ON_ERROR`.
- **No `(array)` cast on objects** to "export state" — it exposes private/protected with mangled keys (`"\0*\0prop"`).
- **No mutating a `readonly` property through a reference** — `$ref = &$obj->prop; $ref = 'x';` bypasses readonly (PHP 8.1–8.2 bug-feature).
- **No `foreach ($arr as &$v)` without `unset($v)` after** — the reference leaks to the outer scope and a later assignment silently mutates the array.
- **No `count($big) === 0` to check emptiness** — `count` walks the array. Use `$big === []` or `empty($big)`.
- **No `!=` / `==`** — always `!==` / `===`. `0 == "abc"` was `true` until PHP 8, and string/array comparisons still surprise.
- **No catching `\Throwable`** to silence errors — catch the specific exception type or let it propagate.
- **No `global` / service locator** — constructor-inject everything.
- **No credentials / PII in logs or error messages.**

## Reference Guide

| Load when | File |
|---|---|
| Debugging subtle language / API behavior (enums, readonly, match, fibers, arrays, dates, comparison) | `references/pitfalls.md` |
| Designing type signatures (PHPStan generics, DNF, `mixed`/`never`/`void`, narrowing) | `references/types.md` |
| Writing security-sensitive code (SQL, passwords, CSRF, file upload, serialization) | `references/security.md` |

## Output Format

When producing code:

1. A short plan (1–3 bullets) of what's changing.
2. The code with `declare(strict_types=1);` and types everywhere.
3. PHPStan passes at the project's configured level — mention if new `@phpstan-ignore` / `@param` annotations were added and why.

When reviewing code: call out MUST-DO / MUST-NOT violations explicitly and suggest the minimal fix.
