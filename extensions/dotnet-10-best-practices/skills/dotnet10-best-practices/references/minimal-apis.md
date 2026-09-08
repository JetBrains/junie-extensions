# ASP.NET Core 10 & Minimal APIs

ASP.NET Core 10 brings significant improvements to Minimal APIs, OpenAPI generation, and security. Load this reference when building or reviewing Minimal API endpoints, OpenAPI configuration, or Blazor components targeting .NET 10.

## Built-in Validation in Minimal APIs

ASP.NET Core 10 now includes **native validation** for Minimal APIs, removing the need for manual validation or libraries like FluentValidation for simple cases.

**Before (manual validation):**

```csharp
app.MapPost("/api/upload", (UploadRequest request) =>
{
    if (string.IsNullOrEmpty(request.SystemCode))
        return Results.BadRequest("System code is required");

    if (request.Data == null || request.Data.Length == 0)
        return Results.BadRequest("Data is required");

    // logic...
    return Results.Ok();
});
```

**After (built-in validation with DataAnnotations):**

```csharp
public class UploadRequest
{
    [Required(ErrorMessage = "System code is required")]
    public string SystemCode { get; set; }

    [Required(ErrorMessage = "Data is required")]
    [MinLength(1)]
    public byte[] Data { get; set; }
}

// Validation is applied automatically
app.MapPost("/api/upload", (UploadRequest request) =>
{
    // request has already been validated automatically
    return Results.Ok();
});
```

## Native OpenAPI 3.1

.NET 10 generates OpenAPI 3.1 documentation **natively**, without Swashbuckle. It can be paired with UIs like **Scalar** or **Redoc**.

**Configuration with Scalar (Swagger UI alternative):**

```csharp
// Program.cs
builder.Services.AddOpenApi();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();              // generates /openapi/v1.json
    app.MapScalarApiReference();   // interactive UI at /scalar
}
```

**Configuration with Swagger UI (keeping compatibility):**

```csharp
builder.Services.AddOpenApi();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.UseSwaggerUI(options =>
    {
        options.SwaggerEndpoint("/openapi/v1.json", "API v1");
    });
}
```

### OpenAPI 3.1 is now the default

.NET 10 generates OpenAPI 3.1 documents by default. This can break tooling or client generators that still expect OpenAPI 3.0.

**To keep OpenAPI 3.0 (if needed):**

```csharp
builder.Services.AddOpenApi(options =>
{
    options.OpenApiVersion = Microsoft.OpenApi.OpenApiSpecVersion.OpenApi3_0;
});
```

### `WithOpenApi()` is deprecated

The `WithOpenApi()` extension method is deprecated (warning `ASPDEPR002`).

**Before:**

```csharp
app.MapGet("/api/items", () => Results.Ok())
   .WithOpenApi();
```

**After:**

```csharp
app.MapGet("/api/items", () => Results.Ok())
   .WithOpenApi(operation =>
   {
       // use AddOpenApiOperationTransformer() for custom transforms
       return operation;
   });
```

Or, preferably, rely on the native OpenAPI pipeline:

```csharp
builder.Services.AddOpenApi();
```

## Passkey Support for Identity

ASP.NET Core 10 adds **passkey** support for authentication via ASP.NET Core Identity, aligned with the WebAuthn/FIDO2 standards.

## Blazor

- **Script served as a static web asset**: the Blazor script is served as a static asset with automatic compression and fingerprinting.
- **`QuickGrid` `RowClass`**: apply CSS classes to grid rows conditionally.

```csharp
<QuickGrid Items="@files" RowClass="@GetRowClass">
    <PropertyColumn Property="@(f => f.FileName)" Title="File" />
    <PropertyColumn Property="@(f => f.CreatedAt)" Title="Date" />
</QuickGrid>

@code {
    private string GetRowClass(FileRecord file) =>
        file.IsActive ? "row-highlight" : "";
}
```

## WebSocketStream and TLS 1.3

- **`WebSocketStream`**: a simplified API for working with WebSockets through a `Stream`.
- **TLS 1.3**: native support on macOS (previously available only on Linux/Windows).

## Summary

| Feature                | Impact                                |
| ---------------------- | ------------------------------------- |
| Built-in validation    | Less manual code in Minimal APIs      |
| Native OpenAPI 3.1     | Replaces Swashbuckle for new projects |
| Passkeys               | Modern, passwordless authentication   |
| Blazor improvements    | Better performance and DX             |
| Cross-platform TLS 1.3 | Improved security                     |
