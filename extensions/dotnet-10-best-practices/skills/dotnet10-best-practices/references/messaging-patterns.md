# Messaging: Silverback 4.x → 5.x Migration (Kafka)

[Silverback](https://silverback-messaging.net/) is a popular .NET message-bus library for Kafka/RabbitMQ. Its 5.x release is described by the maintainers as "the most significant update in the project's history," with major API and architecture changes. Load this reference when upgrading a project's Silverback dependency alongside a .NET 10 migration, or when evaluating whether to adopt Silverback for a new Kafka-based service.

## When to Upgrade

Whether to move to Silverback 5.x depends heavily on how much the codebase relies on the library's advanced features (outbox pattern, EF Core integration, endpoint configuration, publishers, etc.).

✅ **Upgrade if:**

- The project already targets `net10`.
- The service consumes a high amount of memory relative to its messaging load.
- You're starting a new project.

⚠️ **Don't upgrade if:**

- The project still targets `net6` or `net8` — Silverback 5.x requires `net10`.
- Memory usage isn't a concern.
- The project uses **RabbitMQ** through Silverback — RabbitMQ support was dropped in v5.
- The refactoring cost is too high given the breaking changes below.

## Advantages of 5.x

- **Better performance and fewer allocations** — the library was refactored to reduce allocations and improve message-processing performance.
- **Simpler `IPublisher`** — most visible when using the Message Bus pattern. `CancellationToken` support was added in this release.
- **`IPublisher` is now `Transient`** — it used to be `Scoped`, so it can now be injected into `Singleton` services. This resolves issues like publishers being cached in singleton pipelines.
- **Better Kafka support** — Kafka transactions, client-side offset storage, partition assignment, and schema registry support. Relevant if you use Kafka Streams.
- **Better serialization support** — the default serializer is now `System.Text.Json`. See the [Silverback deserialization docs](https://silverback-messaging.net/guides/broker/consuming/deserialization.html) for pipeline configuration details.

## Disadvantages / Breaking Changes

- **No compatibility with older .NET versions** — 5.x only supports projects already on `net10`.
- **Large number of breaking changes** — the configuration surface was completely rewritten: APIs were renamed, namespaces changed, and endpoint models rewritten.
- **RabbitMQ support removed** — if a project uses the `Silverback.Integration.RabbitMQ` namespace, do not upgrade until an alternative is in place.

### Configuration rewrite example

**Before (4.x):**

```csharp
services
    .AddSilverback()
    .WithConnectionToMessageBroker(options => options.AddKafka())
    .AddKafkaEndpoints(endpoints =>
    {
        endpoints.Configure(config => { config.BootstrapServers = configuration.Connection.BootstrapServers; });

        foreach (var inbound in configuration.Consumer.Inbounds)
        {
            var messageType = MessageTypeRegistry.GetMessageType(inbound.MessageType);
            if (messageType == null)
                throw new InvalidOperationException($"Message type '{inbound.MessageType}' not found.");

            if (!Enum.TryParse<AutoOffsetReset>(inbound.AutoOffsetReset, true, out var autoOffsetReset))
                throw new ArgumentException($"Invalid AutoOffsetReset value: {inbound.AutoOffsetReset}");

            var serializerType = typeof(NewtonsoftJsonMessageSerializer<>).MakeGenericType(messageType);
            var serializer = Activator.CreateInstance(serializerType) as IMessageSerializer
                                ?? throw new InvalidOperationException(
                                    $"Failed to create serializer for type {messageType}");

            endpoints.AddInbound(messageType, endpoint =>
            {
                endpoint.SkipNullMessages();
                endpoint.ConsumeFrom(inbound.Topics)
                    .Configure(config =>
                    {
                        config.GroupId = configuration.Connection.GroupId;
                        config.AutoOffsetReset = autoOffsetReset;
                    })
                    .OnError(policy =>
                    {
                        policy.Retry(
                            configuration.Retry.Attempts,
                            TimeSpan.FromSeconds(configuration.Retry.IntervalInSeconds)
                        );
                        policy.MoveToKafkaTopic(moveEndpoint => { moveEndpoint.ProduceTo(inbound.TopicError); });
                        policy.Skip();
                    })
                    .DeserializeUsing(serializer);
            });
        }
    })
    .AddScopedSubscriber<OrderCreatedConsumer>();
```

**After (5.x):**

```csharp
services
    .AddSilverback()
    .WithConnectionToMessageBroker(options => options.AddKafka())
    .AddKafkaClients(clients =>
    {
        clients.WithBootstrapServers(configuration.Connection.BootstrapServers);

        foreach (var inbound in configuration.Consumer.Inbounds)
        {
            var messageType = AppDomain.CurrentDomain
                .GetAssemblies()
                .SelectMany(a => a.GetTypes())
                .FirstOrDefault(t => string.Equals(t.Name, inbound.MessageType, StringComparison.OrdinalIgnoreCase));

            if (messageType is null)
                throw new ArgumentException($"Message type not found: {inbound.MessageType}");

            if (!Enum.TryParse<AutoOffsetReset>(inbound.AutoOffsetReset, true, out var autoOffsetReset))
                throw new ArgumentException($"Invalid AutoOffsetReset value: {inbound.AutoOffsetReset}");

            clients.AddConsumer(consumer =>
            {
                consumer.WithGroupId(configuration.Connection.GroupId);
                consumer.WithAutoOffsetReset(autoOffsetReset);

                consumer.Consume(endpoint =>
                {
                    endpoint.DisableMessageValidation();
                    endpoint.ConsumeFrom(inbound.Topic);
                    endpoint.UseDefaultErrorPolicy(inbound.TopicError, configuration.Retry.Attempts, configuration.Retry.IntervalInSeconds);
                    endpoint.DeserializeJsonDefault(messageType);
                });
            });

            // Required for the producer that forwards messages to the error topic
            clients.AddProducer(producer =>
            {
                producer.Produce(endpoint => endpoint.ProduceTo(inbound.TopicError));
            });
        }
    })
    .AddScopedSubscriber<OrderCreatedSubscriber>();
```

## Illustrative Benchmark

Measured by publishing 1,000 messages to a Kafka topic in a `foreach` loop, same infrastructure for both versions:

**4.x:**

| Method                        |    Mean |   Error |  StdDev | Ratio |      Gen0 | Allocated | Alloc Ratio |
| ----------------------------- | ------: | ------: | ------: | ----: | --------: | --------: | ----------: |
| `PublishAsync` inside foreach | 15.62 s | 0.046 s | 0.038 s |  1.00 | 3000.0000 |  20.16 MB |        1.00 |

**5.x:**

| Method                        |         Mean |     Error |    StdDev | Ratio |      Gen0 |     Gen1 | Allocated | Alloc Ratio |
| ----------------------------- | -----------: | --------: | --------: | ----: | --------: | -------: | --------: | ----------: |
| `PublishAsync` inside foreach | 15,623.57 ms | 30.528 ms | 28.556 ms | 1.000 | 1000.0000 |        - |   6.29 MB |        1.00 |
| `WrapAndPublishBatchAsync`    |     17.84 ms |  0.362 ms |  1.056 ms | 0.001 |  562.5000 | 281.2500 |   3.41 MB |        0.54 |

> `WrapAndPublishBatchAsync` was introduced in 5.0.0, so there is no 4.x baseline for it. Batch publishing shows a substantial allocation and throughput advantage over per-message `PublishAsync` — prefer it for bulk-publish scenarios.

## Summary

| Aspect                | Recommendation                                               |
| --------------------- | ------------------------------------------------------------ |
| Target framework      | 5.x requires `net10`                                         |
| RabbitMQ users        | Stay on 4.x, or migrate off Silverback for RabbitMQ          |
| `IPublisher` lifetime | Now `Transient` — safe to inject into `Singleton` services   |
| Bulk publishing       | Prefer `WrapAndPublishBatchAsync` over a `PublishAsync` loop |
| Serialization         | Default moved to `System.Text.Json`                          |
