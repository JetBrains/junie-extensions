# Project File, Dependencies & Build/Deploy Updates

Reference for mechanically updating `.csproj` files, NuGet dependencies, and CI/CD configuration when migrating a project to .NET 10. Load this when performing or reviewing the actual migration steps (as opposed to adopting new language/runtime features).

## Target Framework Moniker (TFM)

In **every** `.csproj` file of a multi-project solution (API, Application, Domain, Infrastructure, Repository, Services, Tests, ...), update the target framework:

**Before:**

```xml
<PropertyGroup>
  <TargetFramework>net8.0</TargetFramework>
</PropertyGroup>
```

**After:**

```xml
<PropertyGroup>
  <TargetFramework>net10.0</TargetFramework>
</PropertyGroup>
```

> **Why:** this tells the compiler to use the .NET 10 SDK and libraries.

## `DocumentationFile`

Do not hardcode the framework version in the `DocumentationFile` path. Use MSBuild variables so the path adapts automatically in future migrations.

**Before:**

```xml
<PropertyGroup Condition="'$(Configuration)|$(Platform)'=='Debug|AnyCPU'">
  <DocumentationFile>bin\Debug\net8.0\Api.xml</DocumentationFile>
  <NoWarn>1591</NoWarn>
</PropertyGroup>
<PropertyGroup Condition="'$(Configuration)|$(Platform)'=='Release|AnyCPU'">
  <DocumentationFile>bin\Release\net8.0\Api.xml</DocumentationFile>
</PropertyGroup>
```

**After:**

```xml
<PropertyGroup Condition="'$(Configuration)|$(Platform)'=='Debug|AnyCPU'">
  <DocumentationFile>bin\$(Configuration)\$(TargetFramework)\Api.xml</DocumentationFile>
  <NoWarn>1591</NoWarn>
</PropertyGroup>
<PropertyGroup Condition="'$(Configuration)|$(Platform)'=='Release|AnyCPU'">
  <DocumentationFile>bin\$(Configuration)\$(TargetFramework)\Api.xml</DocumentationFile>
</PropertyGroup>
```

> **Why:** using `$(Configuration)` and `$(TargetFramework)`, the path adjusts automatically on framework or configuration changes, avoiding manual edits in future migrations.

## Removing an unnecessary `OutputPath`

If the Release block has an empty `<OutputPath />`, it can be removed — it has no effect:

**Remove:**

```xml
<PropertyGroup Condition="'$(Configuration)|$(Platform)'=='Release|AnyCPU'">
  <DocumentationFile>bin\$(Configuration)\$(TargetFramework)\Api.xml</DocumentationFile>
  <OutputPath />
</PropertyGroup>
```

**Keep:**

```xml
<PropertyGroup Condition="'$(Configuration)|$(Platform)'=='Release|AnyCPU'">
  <DocumentationFile>bin\$(Configuration)\$(TargetFramework)\Api.xml</DocumentationFile>
</PropertyGroup>
```

## Checklist: project files

- [ ] Change `TargetFramework` to `net10.0` in **all** `.csproj` files
- [ ] Replace hardcoded `DocumentationFile` paths with `$(Configuration)\$(TargetFramework)`
- [ ] Remove an empty `<OutputPath />` if present
- [ ] Run `dotnet build` to validate

## NuGet Dependency Updates

### General rule

Do not bump package versions arbitrarily. Check the compatibility notes for each dependency, and keep an internal reference (a wiki page, an `.editorconfig`, or a central `Directory.Packages.props`) of the versions homologated for the target framework across the organization's projects.

### External packages

**Before (.NET 8):**

```xml
<PackageReference Include="Microsoft.AspNetCore.Mvc.NewtonsoftJson" Version="8.0.16" />
<PackageReference Include="OpenTelemetry.Instrumentation.SqlClient" Version="1.12.0-beta.1" />
<PackageReference Include="OpenTelemetry.Instrumentation.StackExchangeRedis" Version="1.12.0-beta.1" />
<PackageReference Include="FluentFTP" Version="40.0.0" />
```

**After (.NET 10):**

```xml
<PackageReference Include="Microsoft.AspNetCore.Mvc.NewtonsoftJson" Version="10.0.3" />
<PackageReference Include="OpenTelemetry.Instrumentation.SqlClient" Version="1.15.0" />
<PackageReference Include="OpenTelemetry.Instrumentation.StackExchangeRedis" Version="1.15.0-beta.1" />
<PackageReference Include="FluentFTP" Version="53.0.2" />
```

### Test packages

**Before:**

```xml
<PackageReference Include="coverlet.collector" Version="6.0.4" />
<PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.14.1" />
<PackageReference Include="xunit" Version="2.9.3" />
<PackageReference Include="xunit.runner.visualstudio" Version="3.1.3" />
```

**After:**

```xml
<PackageReference Include="coverlet.collector" Version="8.0.0" />
<PackageReference Include="Microsoft.NET.Test.Sdk" Version="18.3.0" />
<PackageReference Include="xunit" Version="2.9.3" />
<PackageReference Include="xunit.runner.visualstudio" Version="3.1.5" />
```

### Verifying installed versions

```bash
dotnet list package
```

### Checklist: dependencies

- [ ] Update external packages to the versions homologated for .NET 10
- [ ] Update test packages
- [ ] Run `dotnet restore` and `dotnet build` to validate

## Known Third-Party Breaking Changes

### OpenTelemetry: `SetDbStatementForText` removed

`SetDbStatementForText` was removed/deprecated in OpenTelemetry 1.12+. Remove the call.

**Before:**

```csharp
options.SetDbStatementForText = true;
```

**After:** delete the line. The default behavior already covers this scenario.

### FluentFTP 53: methods drop the `Async` suffix

`AsyncFtpClient` in FluentFTP 53 removed the `Async` suffix from its methods. **They are still asynchronous** (they return `Task`), only the names changed.

**Before (FluentFTP 40):**

```csharp
var client = new AsyncFtpClient(host, user, pass);
await client.ConnectAsync(cancellationToken);
await client.DeleteFileAsync(path, cancellationToken);
await client.UploadFileAsync(localPath, remotePath, FtpRemoteExists.Overwrite);
await client.FileExistsAsync(path, cancellationToken);
await client.CreateDirectoryAsync(path, cancellationToken);
await client.DownloadBytesAsync(path, cancellationToken);
await client.DisconnectAsync(cancellationToken);
```

**After (FluentFTP 53):**

```csharp
var client = new AsyncFtpClient(host, user, pass);
await client.Connect(cancellationToken);
await client.DeleteFile(path, cancellationToken);
await client.UploadFile(localPath, remotePath, FtpRemoteExists.Overwrite);
await client.FileExists(path, cancellationToken);
await client.CreateDirectory(path, cancellationToken);
await client.DownloadBytes(path, cancellationToken);
await client.Disconnect(cancellationToken);
```

> All methods return `Task` and must be `await`ed. `AsyncFtpClient` exposes **only** async operations; the synchronous `FtpClient` exists as a separate class.

### Internal shared libraries: watch for breaking changes on major jumps

If your organization maintains internal shared packages (a common auth/logging/messaging kernel, etc.), a .NET 10 migration is a natural point where those packages also jump major versions. Treat any such jump like a third-party breaking change: read the changelog, check for namespace moves or signature changes, and don't assume the public API is unchanged just because the package is "internal."

### Test package major-version jumps

Test tooling packages had major version jumps in this cycle. Verify compatibility:

- `coverlet.collector`: 6.x → **8.0.0**
- `Microsoft.NET.Test.Sdk`: 17.x → **18.3.0**
- `xunit.runner.visualstudio`: 3.1.3 → **3.1.5**

## Other .NET 10 Breaking Changes

- **Docker images** now use Ubuntu by default (no `-jammy` suffix).
- **C# 14**: `Span<T>` overload resolution may require an explicit cast in ambiguous scenarios.
- **`BufferedStream.WriteByte`** no longer performs an implicit flush.
- **`FilePatternMatch.Stem`** is now non-nullable.
- **Default trace-context propagator** changed to W3C.

## Docker & CI/CD Updates

### Dockerfile

.NET base images must be bumped to `10.0`. In .NET 10, the official images **no longer use the `-jammy` suffix**.

**Before (.NET 8):**

```dockerfile
ARG DOTNET_VER=8.0

FROM mcr.microsoft.com/dotnet/aspnet:${DOTNET_VER}-jammy AS base

RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash appuser

WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:${DOTNET_VER}-jammy AS build
WORKDIR /src
COPY . .
RUN dotnet restore
RUN dotnet publish -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
USER appuser
ENTRYPOINT ["dotnet", "my-api.dll"]
```

**After (.NET 10):**

```dockerfile
ARG DOTNET_VER=10.0

FROM mcr.microsoft.com/dotnet/aspnet:${DOTNET_VER} AS base

RUN groupadd -g 10000 appgroup && \
    useradd -u 10000 -g appgroup -s /bin/bash appuser

WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:${DOTNET_VER} AS build
WORKDIR /src
COPY . .
RUN dotnet restore
RUN dotnet publish -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
USER appuser
ENTRYPOINT ["dotnet", "my-api.dll"]
```

#### Key changes

| Item         | Before             | After                                                |
| ------------ | ------------------ | ---------------------------------------------------- |
| `DOTNET_VER` | `8.0`              | `10.0`                                               |
| Base image   | `aspnet:8.0-jammy` | `aspnet:10.0` (no `-jammy`)                          |
| SDK image    | `sdk:8.0-jammy`    | `sdk:10.0` (no `-jammy`)                             |
| UID/GID      | `1000`             | `10000` (or any convention your org standardizes on) |

> .NET 10 uses Ubuntu by default in the official images. The `-jammy` suffix is no longer needed and can cause errors if that tag doesn't exist.

### CI pipeline

Update the .NET SDK version used by your pipeline's build tasks — for example, in Azure Pipelines:

```yaml
variables:
  dotnetVersion: "10.0"
```

The same principle applies to any other CI system (GitHub Actions, GitLab CI, Jenkins): whatever variable pins the SDK/runtime version needs to move to `10.0`.

### Helm chart `values.yaml`

If `values.yaml` pins the Docker image tag, update it to point at the .NET 10 image built by the pipeline.

### Checklist: build & deploy

- [ ] Update `DOTNET_VER` to `10.0` in the Dockerfile
- [ ] Remove the `-jammy` suffix from images
- [ ] Update the UID/GID convention if applicable
- [ ] Update the SDK version variable in the CI pipeline
- [ ] Update the image tag in Helm/`values.yaml` if applicable
- [ ] Test the container build locally
