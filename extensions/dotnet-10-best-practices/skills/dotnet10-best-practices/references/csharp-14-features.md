# C# 14 Language Features

Detailed reference for the new C# 14 language features shipped with .NET 10. Load this when writing or reviewing code that could benefit from Extension Members, the `field` keyword, or the other additions below.

## Extension Members

C# 14 replaces the traditional `this`-parameter extension method with an `extension` block that names the target type once and lets you declare methods, properties, operators, and static members with a unified syntax.

**Before (C# 12 / traditional extension methods):**

```csharp
public static class StringExtensions
{
    public static bool IsNullOrEmpty(this string value)
    {
        return string.IsNullOrEmpty(value);
    }

    public static string Truncate(this string value, int maxLength)
    {
        if (string.IsNullOrEmpty(value) || value.Length <= maxLength)
            return value;
        return value.Substring(0, maxLength);
    }
}
```

**After (C# 14 / extension members):**

```csharp
public static class StringExtensions
{
    extension(string value)
    {
        public bool IsNullOrEmpty => string.IsNullOrEmpty(value);

        public string Truncate(int maxLength)
        {
            if (string.IsNullOrEmpty(value) || value.Length <= maxLength)
                return value;
            return value.Substring(0, maxLength);
        }
    }
}
```

Call sites are unchanged: `"text".IsNullOrEmpty` or `"text".Truncate(5)`.

### Extension properties

Before C# 14 it was not possible to declare an extension _property_. Now it is:

```csharp
public static class EnumerableExtensions
{
    extension<TSource>(IEnumerable<TSource> source)
    {
        public bool IsEmpty => !source.Any();

        public int SafeCount => source?.Count() ?? 0;
    }
}

// Usage:
int[] data = [1, 2, 3];
if (data.IsEmpty)
{
    // ...
}
```

### Static extension members and operators

Static members and operators can be added to the extended type inside the same block:

```csharp
public static class EnumerableExtensions
{
    extension<TSource>(IEnumerable<TSource> source)
    {
        // Static member
        public static IEnumerable<TSource> Identity => Enumerable.Empty<TSource>();

        // Extension operator
        public static IEnumerable<TSource> operator +(
            IEnumerable<TSource> left,
            IEnumerable<TSource> right) => left.Concat(right);
    }
}

// Usage:
var combined = data + [4, 5];
var empty = IEnumerable<int>.Identity;
```

### Practical example: extending a domain entity

```csharp
public static class FileRecordExtensions
{
    extension(FileRecord file)
    {
        public bool HasFile => file != null && !string.IsNullOrEmpty(file.FileId.ToString());

        public string FullPath => $"{file.Directory}{file.FileId}{file.Extension}";

        public string PublicUrl(string baseUrl)
        {
            var dir = file.Directory.Replace("/data/", "");
            return $"{baseUrl}{dir}{file.FileId}{file.Extension}";
        }
    }
}
```

### Compatibility

- Extension members compile to the **same IL** as traditional extension methods.
- They are **source and binary compatible** — migrate one method at a time.
- Code that already calls your extension methods **does not need to change**.

### When to use

- You have **multiple** extension methods for the same type.
- You want to add **properties** as extensions (impossible before C# 14).
- You want to group a type's extensions logically.

### When NOT to use

- A single, isolated extension method — the traditional form is simpler.
- The project still needs to support a pre-C# 14 compiler.

## `field` keyword

C# 14 introduces the contextual keyword `field`, which gives direct access to the compiler-generated backing field of an auto-property without declaring a private field by hand.

**The problem (before C# 14):** any property that needs validation or setter logic requires an explicit backing field.

```csharp
public class ServiceConfig
{
    private string _host;

    public string Host
    {
        get => _host;
        set => _host = value ?? throw new ArgumentNullException(nameof(value));
    }

    private int _port;

    public int Port
    {
        get => _port;
        set => _port = value > 0
            ? value
            : throw new ArgumentOutOfRangeException(nameof(value));
    }

    private int _retries;

    public int Retries
    {
        get => _retries;
        set => _retries = Math.Clamp(value, 1, 10);
    }
}
```

**The solution (C# 14):** the compiler generates the backing field for you, accessible via `field`.

```csharp
public class ServiceConfig
{
    public string Host
    {
        get;
        set => field = value ?? throw new ArgumentNullException(nameof(value));
    }

    public int Port
    {
        get;
        set => field = value > 0
            ? value
            : throw new ArgumentOutOfRangeException(nameof(value));
    }

    public int Retries
    {
        get;
        set => field = Math.Clamp(value, 1, 10);
    }
}
```

Result: less boilerplate, identical behavior — the explicit `_host`/`_port`/`_retries` fields disappear.

### Practical example: DTO with validation

```csharp
public class UploadRequest
{
    public string SystemCode
    {
        get;
        set => field = !string.IsNullOrWhiteSpace(value)
            ? value.Trim().ToUpper()
            : throw new ArgumentException("System code is required");
    }

    public string Extension
    {
        get;
        set => field = value?.StartsWith('.') == true
            ? value
            : $".{value}";
    }

    public byte[] Data
    {
        get;
        set => field = value?.Length > 0
            ? value
            : throw new ArgumentException("File data is required");
    }
}
```

### Example: lazy initialization

```csharp
public class ServiceSettings
{
    public string ConnectionString
    {
        get => field ??= LoadFromEnvironment();
        set;
    }

    private static string LoadFromEnvironment()
        => Environment.GetEnvironmentVariable("CONNECTION_STRING") ?? "";
}
```

### Important characteristics

- `field` can only be used inside a property's **getter and setter**.
- It is a **contextual keyword** — it does not break code that already declares a variable named `field`.
- The generated backing field is **not accessible** outside the accessor (better encapsulation than a private `_field`).
- No change to generated IL — it is purely a compile-time convenience.

### When to use

- Properties that need **setter validation**.
- Properties with **value transformation** (trim, clamp, normalization).
- **Lazy initialization** with `??=`.
- Any case where you would otherwise declare a private `_field` solely for the getter/setter.

### When NOT to use

- Plain auto-properties with no logic (`public string Name { get; set; }` already works without `field`).
- When the field must be accessed **outside the property** — keep the explicit field in that case.

## Other C# 14 additions

### Null-conditional assignment

Safely assign to a property of a possibly-null object.

**Before:**

```csharp
if (file != null)
{
    file.ReturnUrl = url;
}
```

**After:**

```csharp
file?.ReturnUrl = url;
```

### Lambda parameter modifiers

Lambdas now support `params`, `ref`, `in`, and `out` on their parameters.

**Before:**

```csharp
// params was not allowed on a lambda
Func<int[], int> sum = (int[] numbers) => numbers.Sum();
```

**After:**

```csharp
var sum = (params int[] numbers) => numbers.Sum();

// Usage:
int result = sum(1, 2, 3, 4, 5);
```

### Implicit `Span<T>` conversions

`Span<T>` and `ReadOnlySpan<T>` now convert implicitly in more scenarios, reducing the need to call `.AsSpan()` explicitly.

**Before:**

```csharp
void ProcessData(ReadOnlySpan<byte> data) { }

byte[] buffer = new byte[1024];
ProcessData(buffer.AsSpan());  // .AsSpan() required
```

**After:**

```csharp
void ProcessData(ReadOnlySpan<byte> data) { }

byte[] buffer = new byte[1024];
ProcessData(buffer);  // implicit conversion
```

> In overload-resolution scenarios the chosen overload can change. If there's ambiguity, use an explicit cast.

### Partial constructors

Constructors can now be `partial`, splitting initialization logic across files.

```csharp
// File: OrderService.cs
public partial class OrderService
{
    public partial OrderService(IOrderRepository repository, IMessagePublisher messaging);
}

// File: OrderService.Init.cs
public partial class OrderService
{
    public partial OrderService(IOrderRepository repository, IMessagePublisher messaging)
    {
        _repository = repository;
        _messaging = messaging;
    }
}
```

### User-defined compound operators

You can now define `+=`, `-=`, and other compound operators directly, without relying on the base binary operator.

```csharp
public class Counter
{
    public int Value { get; private set; }

    public static Counter operator +=(Counter c, int increment)
    {
        c.Value += increment;
        return c;
    }
}

// Usage:
var counter = new Counter();
counter += 5;
```

### Improved `nameof`

`nameof` now works in more contexts, including attribute arguments and members of open generic types.

**Before:**

```csharp
// Not allowed in some attribute contexts
[Display(Name = "UserName")]
public string UserName { get; set; }
```

**After:**

```csharp
[Display(Name = nameof(UserName))]
public string UserName { get; set; }
```

### Summary

| Feature                         | Main benefit                   |
| ------------------------------- | ------------------------------ |
| Null-conditional assignment     | Fewer `if (x != null)` guards  |
| Lambda parameter modifiers      | More flexible lambdas          |
| Implicit Span conversion        | Fewer manual `.AsSpan()` calls |
| Partial constructors            | Better code organization       |
| User-defined compound operators | More ergonomic custom types    |
| Improved `nameof`               | Fewer hardcoded strings        |
