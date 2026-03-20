# Architecture Review

## When to Use

- Reviewing package organization or module structure
- Planning a refactoring that crosses multiple features or layers
- Checking whether responsibilities are leaking between layers
- Evaluating whether a project is over-layered or under-structured

## Core Principles

- Prefer feature cohesion over large horizontal buckets
- Keep dependency direction easy to explain in one sentence
- Separate API, application, domain, and infrastructure concerns when complexity justifies it
- Prefer the simplest structure that still keeps change localized
- Avoid introducing architectural patterns the team does not need yet

## Package Organization Options

### Package by Feature (preferred for most projects)

```
com.example.app/
  orders/
    OrderController.kt
    OrderService.kt
    OrderRepository.kt
    OrderMapper.kt
  customers/
    CustomerController.kt
    CustomerService.kt
    CustomerRepository.kt
```

Benefits: related code together, feature extraction is easy, reviewers see one feature in one place.

### Package by Layer (acceptable for small projects)

```
com.example.app/
  controller/
  service/
  repository/
  model/
```

Risk signs: very large `service` packages, one change touches many distant packages, feature boundaries blur.

### Explicit Domain / Application / Infrastructure Split

```
com.example.app/
  domain/          # entities, value objects, domain services, repository interfaces
  application/     # use cases, application services, DTOs
  infrastructure/  # JPA, external clients, messaging adapters
  web/             # controllers, request/response DTOs
```

Use when: multiple adapters exist, business rules must be isolated from framework code, or module extraction is planned.

## Architecture Smells

- Controllers contain business rules, transactions, or SQL
- Services know HTTP status codes, queue protocols, or JSON structure directly
- Domain code depends on `@Entity`, `@Repository`, or framework annotations
- One `common`, `shared`, or `util` package keeps growing without clear ownership
- Circular dependencies between features or modules
- A change in one feature requires edits across many unrelated packages

## Dependency Direction Heuristics

- Web/API layer depends on application services — not on repository implementations
- Persistence and external clients support the domain flow — they don't define it
- Shared modules provide stable abstractions — they are not a dumping ground
- If a dependency direction is hard to justify in one sentence, reconsider it

## Review Checklist

- Can you explain each top-level package's responsibility in one sentence?
- Are related classes grouped by feature or by a boundary with a clear reason?
- Do dependencies mostly point inward toward more stable code?
- Is any package acting as a catch-all for unrelated helpers?
- Would adding a new feature touch only one bounded area, or many cross-cutting folders?
- Is the current structure simpler than the next more abstract alternative?

## Refactoring Guidance

- Prefer incremental moves over architecture rewrites
- Move one feature or boundary at a time; keep behavior unchanged during structural refactors
- Add module or package boundaries only when they prevent recurring confusion or coupling
- If the project is small, prefer clearer naming and feature grouping over many layers

## Anti-Patterns

- Forcing hexagonal or clean architecture on a small CRUD service
- Creating deep package trees with one class per folder
- Introducing a `common` module for code that is not stable and shared
- Mixing architecture refactoring with behavior changes in the same commit
