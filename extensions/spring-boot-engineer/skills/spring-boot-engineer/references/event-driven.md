# Event-driven — policy & pitfalls

Generic Spring `@EventListener` / Kafka knowledge is assumed. This file covers the transactional gotchas and outbox pattern.

## In-process events: `@EventListener` vs `@TransactionalEventListener`

- `@EventListener` fires **inside** the publisher's transaction. If the transaction later rolls back, the listener has already run — side effects leak.
- `@TransactionalEventListener(phase = AFTER_COMMIT)` fires only after a successful commit. **This is the default you want** for anything that sends email, publishes to Kafka, or calls external services.
- `phase = AFTER_ROLLBACK` for compensations / cleanup.
- If the publisher is not in a transaction, `@TransactionalEventListener` silently **does not fire**. Set `fallbackExecution = true` if you want it to fire in that case; otherwise treat missing listeners as a bug.

## Listeners + transactions

- A `@TransactionalEventListener` that itself needs a DB write runs **after** the original commit, so it opens a new transaction with `@Transactional(propagation = REQUIRES_NEW)`. If you forget `REQUIRES_NEW`, the write might join no transaction at all (depending on config) and fail silently.
- Listener exceptions in `AFTER_COMMIT` do **not** roll back the publisher's already-committed transaction. You lose the event unless you persist it first (see outbox below).

## Async listeners

- `@Async` + `@EventListener` to run off the request thread. Requires `@EnableAsync` and a properly sized `TaskExecutor` bean (`ThreadPoolTaskExecutor` — never the default, which is unbounded).
- Exceptions in `@Async` listeners disappear unless you set `AsyncUncaughtExceptionHandler`.

## Kafka basics — what to get right

- **Idempotent consumer is not optional.** Kafka delivery is "at least once"; the same message can arrive twice. Use an idempotency key (message ID + consumer group) stored in DB, skip if already processed.
- Use manual acknowledgment: set `spring.kafka.listener.ack-mode=MANUAL_IMMEDIATE` and call `acknowledgment.acknowledge()` after business logic succeeds. Spring Kafka disables Kafka's native `enable.auto.commit` by default when using listener containers, but the default `AckMode.BATCH` commits after the entire batch completes — a handler crash mid-batch still causes redelivery, and with `BATCH` you lose per-message control.
- Consumer `max.poll.interval.ms` must comfortably exceed your longest handler. Otherwise the consumer is kicked from the group, partition rebalances, message redelivered to another instance.
- Producer: `acks=all`, `enable.idempotence=true`, `retries=Integer.MAX_VALUE`, `max.in.flight.requests.per.connection=5`. Those are the safe defaults for "exactly once" at the producer side.
- Error handling: configure `DefaultErrorHandler` with a `DeadLetterPublishingRecoverer` after N retries. Never throw from a listener without a DLT — you'll get infinite redelivery.

## Outbox pattern (dual-write problem)

Writing to DB **and** publishing to Kafka in the same service is a dual-write: one can succeed while the other fails.

Outbox:

1. In the same DB transaction: write the business row **and** insert into an `outbox` table (`id`, `aggregate`, `payload`, `created_at`, `published boolean`).
2. A separate poller (`@Scheduled` + `SKIP LOCKED` query) reads unpublished rows and emits to Kafka.
3. On successful publish, mark `published = true`. On failure, retry next poll.

Debezium CDC is an alternative: tail the DB log instead of polling. Choose based on ops complexity, not cleverness.

## Ordering

- Within a Kafka partition, order is guaranteed. Across partitions, it is not. Pick a partition key that groups everything that must stay ordered (e.g. `user_id`, `order_id`).
- `@EventListener` ordering: `@Order(…)`. Do not rely on listener declaration order.

## Common mistakes

- `@EventListener` (not `@TransactionalEventListener`) on a handler that sends email → email on every rollback.
- Listener throws → caller's transaction rolls back unexpectedly (for in-transaction listeners). Catch in the listener if you want to decouple.
- No DLT configured → Kafka consumer loops forever on a poison message.
- Outbox table never cleaned up → grows to millions of rows; add a retention job.
- Using `spring.kafka.listener.ack-mode=BATCH` but calling `ack.acknowledge()` on each message (no-op in batch mode).
