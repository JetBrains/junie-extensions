# Performance & Runtime (.NET 10)

.NET 10 is described by Microsoft as the "fastest .NET yet." Many improvements are automatic — you get them just by retargeting the framework, with no code changes. Load this reference when evaluating performance-sensitive code, JSON serialization, or class design for a .NET 10 target.

## LINQ: Reduced Abstraction Overhead

The overhead of using `IEnumerable<T>` (vs. hand-written loops) dropped drastically:

| Version | Abstraction overhead |
| ------- | -------------------- |
| .NET 9  | ~83%                 |
| .NET 10 | **~10%**             |

Data pipelines like `Where().Select().ToList()` get significantly faster with no code changes:

```csharp
// This code gets ~15% faster just by migrating to .NET 10
var activeItems = items
    .Where(i => i.IsActive)
    .Select(i => new { i.Id, i.Name })
    .ToList();
```

## `System.Text.Json`: 2-3x Faster

With **source generators** and **NativeAOT**, JSON serialization is 2-3x faster.

**Source generator configuration:**

```csharp
// Define the serialization context
[JsonSerializable(typeof(ApiResult<FileRecord>))]
[JsonSerializable(typeof(ApiResult<bool>))]
[JsonSerializable(typeof(UploadDownloadDto))]
public partial class ApiJsonContext : JsonSerializerContext { }

// Register in Program.cs
builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.TypeInfoResolverChain.Insert(0, ApiJsonContext.Default);
});
```

> Benefit: fewer allocations, faster serialization, and **required** for NativeAOT.

### .NET 8 vs .NET 10 comparison

| Metric                            | .NET 8   | .NET 10            |
| --------------------------------- | -------- | ------------------ |
| JSON Schema validation            | baseline | **~29% faster**    |
| Serialization (source gen)        | 1x       | **2-3x faster**    |
| Deserialization with `PipeReader` | N/A      | **Native support** |

## JIT Compiler

The .NET 10 JIT includes several optimizations:

- **Better inlining** — more methods inlined automatically.
- **Devirtualization** — virtual calls resolved at compile time (especially with `sealed` classes).
- **Loop inversion** — more efficient loops.
- **AVX10.2** — support for newer SIMD instructions.
- **Struct arguments** — optimized struct passing.

## NativeAOT

Improvements for AOT deployment scenarios:

- Lower memory footprint.
- Faster startup.
- Better compatibility with existing libraries.

## Post-Quantum Cryptography

.NET 10 introduces **ML-DSA** (Module-Lattice Digital Signature Algorithm) support, preparing applications for the post-quantum era:

```csharp
using System.Security.Cryptography;

// Generate an ML-DSA key
using var mlDsa = MLDsa.GenerateKey(MLDsaAlgorithm.MLDsa65);

// Sign data
byte[] signature = mlDsa.SignData(data);

// Verify a signature
bool valid = mlDsa.VerifyData(data, signature);
```

## `TimeProvider`: Testable Time

`TimeProvider` is an abstraction that replaces `DateTime.UtcNow` with an injectable, testable time source.

**Before:**

```csharp
public class ReportService
{
    public string GetOutputDirectory()
    {
        // Hard to test - depends on the system clock
        string year = DateTime.Today.Year.ToString();
        string month = DateTime.Today.Month.ToString();
        string day = DateTime.Today.Day.ToString();
        return $"{year}/{month}/{day}/";
    }
}
```

**After:**

```csharp
public class ReportService(TimeProvider timeProvider)
{
    public string GetOutputDirectory()
    {
        var today = timeProvider.GetLocalNow().Date;
        return $"{today.Year}/{today.Month}/{today.Day}/";
    }
}

// DI registration:
builder.Services.AddSingleton(TimeProvider.System);

// In tests:
var fakeTime = new FakeTimeProvider(new DateTimeOffset(2026, 3, 3, 0, 0, 0, TimeSpan.Zero));
var service = new ReportService(fakeTime);
// GetOutputDirectory() always returns "2026/3/3/"
```

## Summary of Automatic Gains

Obtained **just by migrating** to .NET 10, no code changes required:

- LINQ ~15% faster on data pipelines.
- JSON Schema ~29% faster.
- JIT with better inlining and devirtualization.
- Generally lower memory usage.

Gains that **require code changes** to realize:

- Source generators for `System.Text.Json`.
- `TimeProvider` for testable code.
- Sealed classes for devirtualization (see below).

## Sealed Classes

`sealed` classes cannot be inherited, which clearly signals design intent and enables JIT performance optimizations.

### Why use `sealed`?

**1. Design intent** — most classes are not designed to be inherited. Marking them `sealed` communicates that explicitly.

**2. Performance: JIT devirtualization** — when a class is `sealed`, the JIT knows there are no subclasses and can optimize virtual method calls, eliminating the v-table lookup.

**Comparative benchmark:**

| Scenario               | Non-sealed | Sealed       |
| ---------------------- | ---------- | ------------ |
| Virtual method call    | ~0.45 ns   | **~0.01 ns** |
| Type check (`is`/`as`) | ~0.20 ns   | **~0.04 ns** |

> The absolute difference is small (nanoseconds), but in hot paths with millions of calls the impact is significant.

**3. Encapsulation** — sealed classes prevent accidental or unwanted inheritance, avoiding behavior being overridden incorrectly.

### Where to apply it

**Seal by default** — any class not designed for inheritance should be `sealed`:

**Before:**

```csharp
public class FileUploadService : IFileUploadService
{
    private readonly IFileUploadRepository _repository;
    private readonly IMessagePublisher _messaging;

    public FileUploadService(IFileUploadRepository repository, IMessagePublisher messaging)
    {
        _repository = repository;
        _messaging = messaging;
    }

    public async Task<bool> DeleteFile(Guid fileId, string systemCode, CancellationToken ct)
    {
        // ...
    }
}
```

**After:**

```csharp
public sealed class FileUploadService(IFileUploadRepository repository, IMessagePublisher messaging) : IFileUploadService
{
    public async Task<bool> DeleteFile(Guid fileId, string systemCode, CancellationToken ct)
    {
        // ...
    }
}
```

> This example also uses the C# 12 **primary constructor** alongside standard `sealed`.

### Types of classes that should be sealed

- **Services** (`FileUploadService`, `EmailService`, etc.)
- **Repositories** (`FileUploadRepository`, etc.)
- **DTOs** and **ViewModels** (`UploadDownloadDto`, etc.)
- **Helpers and extension classes**
- **Handlers and middlewares**
- **Validators**

### Where NOT to apply it

- **Abstract base classes** designed to be inherited (`abstract class`).
- **Classes that are part of a planned inheritance hierarchy**.
- **Classes mocked in tests without an interface** — if the class implements an **interface** (`IFileUploadService`), it can be `sealed` without issue since mocks target the interface.

```csharp
// This works fine with sealed:
public sealed class FileUploadService : IFileUploadService { }

// In tests:
var mock = new Mock<IFileUploadService>();  // mocking the interface, not the class
```

### Analyzer CA1852

.NET ships the **CA1852** analyzer, which automatically detects classes that could be sealed. Enable it in `.editorconfig`:

```ini
[*.cs]
dotnet_diagnostic.CA1852.severity = suggestion
```

Or, to make it a warning:

```ini
[*.cs]
dotnet_diagnostic.CA1852.severity = warning
```

### Sealed override methods

Besides classes, `override` methods can also be marked `sealed` to stop subclasses from overriding them further:

```csharp
public class BaseService
{
    public virtual void Process() { }
}

public class MyService : BaseService
{
    public sealed override void Process()
    {
        // No one can override this method further
    }
}
```

### Recommended pattern

Adopt **"sealed by default"** across projects:

1. Every new class is `sealed` by default.
2. Remove `sealed` only when inheritance is **explicitly required**.
3. Enable the CA1852 analyzer as `suggestion` or `warning`.
4. Classes that implement interfaces can (and should) be `sealed`.

### Summary

| Aspect                                         | Recommendation                      |
| ---------------------------------------------- | ----------------------------------- |
| Services, repositories, DTOs, helpers          | **Always sealed**                   |
| Abstract classes                               | Never sealed                        |
| Classes with an interface                      | Sealed (mock via the interface)     |
| Classes without an interface that need mocking | Don't seal, or extract an interface |
| General rule                                   | **Sealed by default**               |
