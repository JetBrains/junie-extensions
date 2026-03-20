# Event-Driven Architecture — Spring Boot

## Domain Event Base

```java
// Immutable event — use records (Java 16+)
public record ProductCreatedEvent(
    UUID eventId,
    UUID correlationId,
    LocalDateTime occurredAt,
    String productId,
    String name,
    BigDecimal price
) {
    public static ProductCreatedEvent of(String productId, String name, BigDecimal price) {
        return new ProductCreatedEvent(
            UUID.randomUUID(), UUID.randomUUID(), LocalDateTime.now(),
            productId, name, price
        );
    }
}
```

## Aggregate Root Collecting Events

```java
public class Product {
    private String id;
    private String name;
    private BigDecimal price;

    @Transient
    private final List<Object> domainEvents = new ArrayList<>();

    public static Product create(String name, BigDecimal price) {
        Product p = new Product();
        p.id    = UUID.randomUUID().toString();
        p.name  = name;
        p.price = price;
        p.domainEvents.add(ProductCreatedEvent.of(p.id, name, price));
        return p;
    }

    public List<Object> getDomainEvents() { return List.copyOf(domainEvents); }
    public void clearDomainEvents()       { domainEvents.clear(); }
}
```

## Publishing Events in Application Service

```java
@Service
@RequiredArgsConstructor
@Transactional
public class ProductService {
    private final ProductRepository productRepository;
    private final ApplicationEventPublisher eventPublisher;

    public ProductResponse createProduct(CreateProductRequest request) {
        Product product = Product.create(request.name(), request.price());
        Product saved   = productRepository.save(product);

        saved.getDomainEvents().forEach(eventPublisher::publishEvent);
        saved.clearDomainEvents();

        return ProductResponse.from(saved);
    }
}
```

## Transactional Event Listeners

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class ProductEventHandler {
    private final NotificationService notificationService;
    private final InventoryService    inventoryService;

    // Fires only AFTER the transaction commits — safest default
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onProductCreated(ProductCreatedEvent event) {
        log.info("Product created: {}", event.productId());
        notificationService.sendCreatedNotification(event.name(), event.price());
        inventoryService.register(event.productId());
    }
}
```

| Phase | When it fires |
|-------|---------------|
| `BEFORE_COMMIT` | Just before commit — can still roll back |
| `AFTER_COMMIT` | After successful commit (recommended) |
| `AFTER_ROLLBACK` | On rollback |
| `AFTER_COMPLETION` | Either outcome |

> **Warning**: `@TransactionalEventListener` fires on the same thread after commit. For long-running work, use `@Async` or publish to Kafka.

## Async Event Handling

```java
@Component
@Slf4j
public class AsyncProductEventHandler {

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onProductCreated(ProductCreatedEvent event) {
        // Runs on a separate thread — transaction is already committed
        sendEmailAsync(event);
    }
}

// Enable in @SpringBootApplication class:
@SpringBootApplication
@EnableAsync
public class MyApplication { ... }
```

## Kafka Event Publishing

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class KafkaEventPublisher {
    private final KafkaTemplate<String, Object> kafkaTemplate;

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void publishProductCreated(ProductCreatedEvent event) {
        kafkaTemplate.send("product-events", event.productId(), event)
            .whenComplete((result, ex) -> {
                if (ex != null) log.error("Failed to publish {}", event.productId(), ex);
            });
    }
}
```

```yaml
spring:
  kafka:
    bootstrap-servers: localhost:9092
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
    consumer:
      group-id: product-service
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.springframework.kafka.support.serializer.JsonDeserializer
      properties:
        spring.json.trusted.packages: "*"
```

## Transactional Outbox Pattern

Use when you need guaranteed delivery — stores events atomically with business data, polls and publishes separately:

```java
@Entity
@Table(name = "outbox_events")
@Builder @Getter
@NoArgsConstructor @AllArgsConstructor
public class OutboxEvent {
    @Id @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    private String aggregateId;
    private String eventType;

    @Column(columnDefinition = "TEXT")
    private String payload;           // JSON

    private LocalDateTime createdAt;
    private LocalDateTime publishedAt; // null = pending
}

// In application service — same transaction as business data
@Transactional
public ProductResponse createProduct(CreateProductRequest request) {
    Product product = productRepository.save(Product.create(request.name(), request.price()));

    outboxRepository.save(OutboxEvent.builder()
        .aggregateId(product.getId())
        .eventType("ProductCreated")
        .payload(objectMapper.writeValueAsString(ProductCreatedEvent.from(product)))
        .createdAt(LocalDateTime.now())
        .build());

    return ProductResponse.from(product);
}

// Scheduled publisher (separate transaction)
@Component
@RequiredArgsConstructor
@Slf4j
public class OutboxPublisher {
    private final OutboxEventRepository outboxRepository;
    private final KafkaTemplate<String, String> kafkaTemplate;

    @Scheduled(fixedDelay = 5_000)
    @Transactional
    public void publishPending() {
        outboxRepository.findByPublishedAtIsNull().forEach(event -> {
            try {
                kafkaTemplate.send("product-events", event.getAggregateId(), event.getPayload());
                event.setPublishedAt(LocalDateTime.now());
            } catch (Exception ex) {
                log.error("Outbox publish failed for {}", event.getId(), ex);
            }
        });
    }
}
```

## Idempotent Consumer

```java
@Component
@RequiredArgsConstructor
public class IdempotentProductConsumer {
    private final ProcessedEventRepository processedEvents;

    @KafkaListener(topics = "product-events", groupId = "inventory-service")
    public void consume(ProductCreatedEvent event) {
        String key = event.eventId().toString();
        if (processedEvents.existsByEventId(key)) return;  // already handled

        doProcess(event);
        processedEvents.save(new ProcessedEvent(key, LocalDateTime.now()));
    }
}
```

## Best Practices

- Name events in past tense: `ProductCreated`, not `CreateProduct`
- Keep events immutable (records in Java, data classes in Kotlin)
- Include `eventId` + `correlationId` for tracing
- Use `AFTER_COMMIT` phase — prevents handlers firing on rolled-back transactions
- Design consumers to be idempotent — distributed systems may deliver duplicates
- Use outbox pattern for cross-service guaranteed delivery (avoids dual-write problem)
