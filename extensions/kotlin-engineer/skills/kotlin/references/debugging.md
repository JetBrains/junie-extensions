# Debugging & Investigation Patterns

## Investigation Workflow

1. **Define the failure precisely** — what was expected, what happened, in which environment and inputs
2. **Reproduce with the smallest possible scenario** — one endpoint, one use case, one failing test
3. **Narrow scope** — is it request-specific, tenant-specific, time-dependent, concurrency-related, or environment-specific?
4. **Collect evidence before editing code** — logs, metrics, recent deploys/config changes, stack traces, correlation IDs
5. **Form one concrete hypothesis** at a time
6. **Run the smallest validation** that can falsify the hypothesis
7. **Implement fix only after the cause is demonstrated**
8. **Re-run the reproducer** and confirm the fix doesn't just hide the symptom

## Triage Checklist

- Is the issue deterministic or intermittent?
- Did it start after a deploy, config change, schema migration, or dependency upgrade?
- Is the failure isolated to one node / region / queue / external dependency?
- Can bad input, missing validation, or stale cache explain the behavior?
- Are retries, timeouts, circuit breakers, or async boundaries masking the first failure?

## Logging Guidelines

```kotlin
private val logger = LoggerFactory.getLogger(OrderService::class.java)

fun submit(command: CreateOrderCommand): OrderResult {
    logger.info(
        "Submitting order: orderId={}, customerId={}, itemsCount={}",
        command.orderId,
        command.customerId,
        command.items.size,
    )

    val inventoryAvailable = inventoryGateway.reserve(command.items)
    if (!inventoryAvailable) {
        logger.warn("Inventory reservation failed: orderId={}", command.orderId)
        return OrderResult.rejected("inventory_unavailable")
    }

    return OrderResult.accepted(command.orderId)
}
```

- Prefer structured logs with stable field names
- Include correlation IDs, request IDs, tenant/aggregate identifiers
- Log state transitions and decision points — not every line
- Avoid logging secrets, tokens, PII, or large payloads
- Add temporary focused logging around the suspected branch; remove it after the fix

## Metrics During Investigation

- Add short-lived counters/timers when logs alone can't show frequency or latency
- Compare successful and failed paths using the same dimensions
- Follow one failing request across service boundaries with distributed tracing before changing code
- Ask: did error rate change first, or latency? Is one dependency slower than others?

## Common Failure Patterns

### Wrong data, no exception
- Compare read model vs write model
- Check mapping, serialization, timezone, null/default handling
- Check stale cache or eventual consistency window

### Intermittent failure
- Check shared mutable state, ordering assumptions, retries, background jobs
- Check test isolation and cleanup between tests
- Check clock and time-based logic (freeze time in tests)

### Only in production or CI
- Check environment variables, profiles, secrets, feature flags, missing migrations
- Check resource limits, startup ordering, external dependency availability

### Timeout or slowdown
- Check downstream latency, pool exhaustion, lock contention, unexpected N+1 queries
- See `references/performance.md` once confirmed as a performance issue

### Coroutine-specific issues
- `CancellationException` swallowed — always rethrow it; never `catch (e: Exception)` without rethrowing CE
- Deadlock from `.block()` on event loop — check scheduler rules
- Coroutine leak — check that parent scope is cancelled on teardown; use structured concurrency

## Minimal Reproducer Strategy

- Start from the smallest failing automated test or CLI reproduction
- Freeze non-essential variables: seed data, clocks, random values, time zones, concurrency level
- Remove unrelated integrations until the failure disappears or is isolated
- If the reproducer is too broad, split into smaller cases until one explains the bug

## Anti-Patterns

- Patching code before you can describe the failure mode precisely
- Adding broad debug logging everywhere and leaving it permanently
- Assuming the last changed file is the root cause
- Stopping at the first symptom when retries or wrappers can hide the original failure
- "Fixing" flaky tests by relaxing assertions or adding `delay()` without proving timing is the cause

## Done When You Can State

- The exact trigger or input shape
- The failing component or boundary
- Evidence that supports the root-cause hypothesis
- The smallest fix or mitigation that addresses the cause
- Validation that the original reproducer now passes
