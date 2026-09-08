---
name: "dotnet10-best-practices"
description: ".NET 10 / C# 14 migration & best practices — TFM upgrades, ASP.NET Core 10 (Minimal API validation, native OpenAPI 3.1), C# 14 language features (Extension Members, field keyword), sealed-by-default performance guidance, and real third-party breaking changes (FluentFTP, Silverback/Kafka). Use when migrating a project to .NET 10, writing C# 14 code, or reviewing a .csproj/Dockerfile/pipeline update."
---

# .NET 10 / C# 14 — migration & best practices

Baseline .NET/C# knowledge is assumed. This skill encodes the concrete migration steps, new C# 14 language features, and the breaking changes that trip up both LLMs and humans when moving a project from .NET 8 to .NET 10.

## Setup Check (run first)

Before touching a project's migration:

1. **Current TFM** — check every `.csproj` in the solution; multi-project solutions (API, Application, Domain, Infrastructure, Tests, ...) must all move to `net10.0` together.
2. **Third-party dependencies** — check each major dependency's own changelog for the version jump you're making (see `references/csproj-and-build.md` for known traps in OpenTelemetry and FluentFTP, and `references/messaging-patterns.md` for Silverback).
3. **CI/CD and containers** — Dockerfile base images and CI pipeline SDK version pins need matching updates; .NET 10's official images dropped the `-jammy` suffix.
4. **OpenAPI tooling** — .NET 10 defaults to OpenAPI 3.1; check whether client generators or API gateways downstream still expect 3.0.

## Key Patterns

**TFM bump** (repeat in every `.csproj`):

```xml
<PropertyGroup>
  <TargetFramework>net10.0</TargetFramework>
</PropertyGroup>
```

**`field` keyword** — validation/transformation without an explicit backing field:

```csharp
public string Host
{
    get;
    set => field = value ?? throw new ArgumentNullException(nameof(value));
}
```

**Sealed by default:**

```csharp
public sealed class OrderService(IOrderRepository repository) : IOrderService { }
```

**Minimal API built-in validation:**

```csharp
public class UploadRequest
{
    [Required] public string SystemCode { get; set; }
}

app.MapPost("/api/upload", (UploadRequest request) => Results.Ok()); // validated automatically
```

## Constraints

**MUST DO:**

- Move **every** `.csproj` in a solution to `net10.0` together — a mixed-TFM solution breaks project references.
- Use `$(Configuration)`/`$(TargetFramework)` MSBuild variables in `DocumentationFile` and similar paths instead of hardcoding the framework version.
- Check each third-party dependency's own breaking-change notes before bumping its major version alongside the framework — a framework migration is not a safe time to also blind-bump unrelated packages.
- Default new classes to `sealed` unless the class is explicitly designed for inheritance; mock via an interface, not the concrete class.
- Verify whether downstream tooling (client generators, gateways) can consume OpenAPI 3.1 before relying on .NET 10's new default.

**MUST NOT DO:**

- MUST NOT assume a third-party library's method names are unchanged across a major version bump — e.g. FluentFTP 53 dropped the `Async` suffix from `AsyncFtpClient` methods while keeping them asynchronous.
- MUST NOT keep `-jammy`-suffixed Docker base image tags when moving to .NET 10 — the official images dropped that suffix and the old tag may not exist.
- MUST NOT hardcode NuGet package versions without checking what's actually compatible with the target framework — version claims go stale fast.
- MUST NOT seal a class that is part of a planned inheritance hierarchy, or an `abstract class` meant to be a base type.
- MUST NOT upgrade Silverback to 5.x on a project still using RabbitMQ through it — RabbitMQ support was dropped in that release.

## Reference Guide

| Load when                                                                                                                                                   | File                               |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Writing or reviewing C# 14 code (Extension Members, `field` keyword, lambda modifiers, partial constructors, implicit `Span<T>`, custom compound operators) | `references/csharp-14-features.md` |
| Building or reviewing Minimal API endpoints, OpenAPI/Scalar setup, or Blazor `QuickGrid` usage on ASP.NET Core 10                                           | `references/minimal-apis.md`       |
| Evaluating performance-sensitive code, `System.Text.Json` source generators, or `sealed`/`TimeProvider` design                                              | `references/performance.md`        |
| Performing the mechanical migration: `.csproj` TFM bump, NuGet version updates, Dockerfile/CI/Helm changes, known breaking changes                          | `references/csproj-and-build.md`   |
| Upgrading Silverback (Kafka messaging) alongside a .NET 10 migration                                                                                        | `references/messaging-patterns.md` |

## Output Format

When performing or reviewing a migration step:

1. Short plan (1–3 bullets) — which files/packages/config are touched and why.
2. The diff (before/after), matching the style in the relevant reference file.
3. Call out any breaking change the step depends on, and where to verify it (changelog, `dotnet list package`, `EXPLAIN`-equivalent for the dependency in question).
4. If the step is part of a checklist in a reference file, point to it instead of re-deriving the checklist inline.
