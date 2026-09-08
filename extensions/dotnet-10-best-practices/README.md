# dotnet-10-best-practices

Junie extension that turns the agent into a disciplined .NET 10 / C# 14 engineer: applies the mechanical migration steps correctly, adopts new language and runtime features where they pay off, and catches the third-party breaking changes that LLMs get wrong by default — assuming `FluentFTP`'s async methods kept their `Async` suffix, missing that OpenAPI 3.1 is now the default, or sealing the wrong classes.

## Philosophy

Baseline .NET and C# knowledge is assumed — the extension does not re-teach the language. Instead it encodes:

- **Migration mechanics** — the exact `.csproj`, Dockerfile, CI pipeline, and NuGet changes required to move a solution to `net10.0`.
- **New language/runtime features** — C# 14 additions (Extension Members, `field` keyword, and more) and .NET 10 performance wins, with guidance on when they're worth adopting.
- **Breaking-change awareness** — real, documented breaking changes in the framework and in commonly-used third-party libraries (FluentFTP, OpenTelemetry, Silverback), so upgrades don't silently regress.

## What it covers

- TFM and `.csproj` updates, including the `$(Configuration)`/`$(TargetFramework)` pattern for `DocumentationFile`.
- C# 14: Extension Members, the `field` keyword, null-conditional assignment, lambda parameter modifiers, implicit `Span<T>` conversions, partial constructors, user-defined compound operators, improved `nameof`.
- ASP.NET Core 10: built-in Minimal API validation, native OpenAPI 3.1 generation (Scalar/Swagger UI), the `WithOpenApi()` deprecation, passkey support, Blazor `QuickGrid` improvements.
- Performance: LINQ abstraction-overhead reduction, `System.Text.Json` source generators, JIT devirtualization, NativeAOT, `TimeProvider`, and a "sealed by default" policy with the `CA1852` analyzer.
- Dockerfile/CI/Helm updates for .NET 10's Ubuntu-based (no `-jammy`) official images.
- Known third-party breaking changes: OpenTelemetry's `SetDbStatementForText` removal, FluentFTP 53's `Async`-suffix removal, and the Silverback 4.x → 5.x Kafka messaging rewrite.

## Files

- `skills/dotnet10-best-practices/SKILL.md` — hub: Setup Check, Key Patterns, Constraints (MUST DO / MUST NOT DO), Reference Guide, Output Format.
- `skills/dotnet10-best-practices/references/csharp-14-features.md` — Extension Members, `field` keyword, and the rest of the C# 14 language additions.
- `skills/dotnet10-best-practices/references/minimal-apis.md` — ASP.NET Core 10: Minimal API validation, native OpenAPI 3.1, passkeys, Blazor.
- `skills/dotnet10-best-practices/references/performance.md` — LINQ/JSON/JIT/NativeAOT performance, `TimeProvider`, sealed-by-default guidance.
- `skills/dotnet10-best-practices/references/csproj-and-build.md` — `.csproj`, NuGet, Dockerfile, CI pipeline, and Helm migration steps plus known breaking changes.
- `skills/dotnet10-best-practices/references/messaging-patterns.md` — Silverback 4.x → 5.x Kafka messaging migration guide.

## Requirements

- .NET 10 SDK.
- A C# 14-capable compiler (ships with the .NET 10 SDK).

## Installation

Drop the extension folder into your Junie extensions directory and enable it. Junie picks up `SKILL.md` automatically and loads references on demand.
