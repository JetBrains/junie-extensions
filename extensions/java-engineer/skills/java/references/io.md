# Java I/O — pitfalls

Only the things LLM-generated Java gets wrong. Generic stream/file API usage is assumed.

## Resource lifecycle

- `Files.lines` / `Files.list` / `Files.walk` / `Files.find` return a `Stream` backed by an **open file handle**. Must be consumed inside `try (var s = Files.lines(path)) { ... }`, otherwise the descriptor leaks.
- Wrapped streams: close the **outermost** wrapper only. `new BufferedReader(new InputStreamReader(fis))` → closing the `BufferedReader` closes `fis`. Double-close via manual `fis.close()` is a bug.

## Charsets

- **Never use no-charset constructors**: `new FileReader(f)`, `new FileWriter(f)`, `new InputStreamReader(is)`, `new String(bytes)`, `String.getBytes()`. They use the platform default — dev (UTF-8 on macOS/Linux) differs from prod (can be `Cp1252` on Windows containers). Always pass `StandardCharsets.UTF_8`.
- `PrintWriter` / `PrintStream` swallow `IOException` (report via `checkError()`). Use `BufferedWriter` for real I/O.

## Partial reads (classic LLM bug)

- `InputStream.read(byte[] buf)` **does not fill the buffer** — returns bytes actually read (can be `0 < n < buf.length`), or `-1` on EOF. Naïve `in.read(buf); new String(buf)` corrupts data.
- Correct: `in.readAllBytes()` / `in.readNBytes(n)` / `in.transferTo(out)` (JDK 9+/11+).
- Same contract for `Reader.read(char[])`.

## `Files` specifics

- `Files.walk` follows symlinks only with `FileVisitOption.FOLLOW_LINKS`, but has **no cycle detection** in either mode — guard explicitly.
- `Files.createTempFile` does **not** auto-delete. Use `StandardOpenOption.DELETE_ON_CLOSE` or a shutdown hook.

## NIO

- `MappedByteBuffer` on Windows **locks the file until GC** unmaps it. For long-lived processes, close the underlying `FileChannel` explicitly; in JDK 21 use `Arena`-backed memory segments.
- `ByteBuffer.allocateDirect` leaks show up as **off-heap / native memory growth**, invisible in heap dumps.

## Sockets & HTTP

- Blocking `Socket` with no `setSoTimeout(ms)` hangs forever on a silently-dropped TCP connection. Same for `HttpClient` without `.timeout(...)` on both builder and request.
- `HttpURLConnection` is legacy — use `java.net.http.HttpClient` (JDK 11+).

## Serialization

- **Never deserialize untrusted input** with `ObjectInputStream` — arbitrary class instantiation. If legacy code must stay, install an `ObjectInputFilter` whitelist.
