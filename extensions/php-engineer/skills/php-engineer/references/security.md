# PHP security pitfalls

The subset of security issues that are PHP-specific (not "generic web security"). Framework skills (`laravel-engineer`, Symfony, etc.) add their own protections — check those first if a framework is in use.

## SQL — PDO, never string concat

- **Always prepared statements** with bound parameters. Concatenation + `mysqli_real_escape_string` is not safe against all dialect quirks.
- **Disable emulation** on PDO for MySQL:
  ```php
  $pdo = new PDO($dsn, $user, $pass, [
      PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
      PDO::ATTR_EMULATE_PREPARES   => false,
      PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
  ]);
  ```
  With emulation on, parameters are substituted client-side → a non-UTF-8 charset + clever input can still inject. With emulation off, prepared statements are real on the server.
- `PDO::ERRMODE_EXCEPTION` is mandatory. Default is `ERRMODE_SILENT` — silent failures, null results, impossible to debug.
- Bind types: `$stmt->bindValue(':id', $id, PDO::PARAM_INT)`. Default is `PARAM_STR`, which works but can defeat indexes.
- **LIKE with user input** — escape `%` and `_` yourself: `$search = addcslashes($input, '%_\\')`. Prepared statements don't handle LIKE wildcards.
- `IN (?, ?, ?)` — can't bind an array. Build the placeholder list manually: `str_repeat('?,', count($ids) - 1) . '?'` and pass array to `execute`.

## Passwords

- `password_hash($p, PASSWORD_BCRYPT)` — bcrypt, tuned by `cost` option (default 10, bump to 12+).
- `PASSWORD_ARGON2ID` — preferred for new systems (memory-hard). Tune `memory_cost` / `time_cost` / `threads`.
- `password_verify($p, $hash)` — constant-time, safe against timing attacks.
- `password_needs_rehash($hash, PASSWORD_ARGON2ID)` — call after every successful verify; rehash if config changed.
- **Never**: `md5`, `sha1`, `sha256`, `hash('sha256', ...)` with a salt, custom HMAC schemes. All too fast for password hashing.
- **Never** store passwords anywhere — not in logs, not in DB audit trails, not in session dumps.

## CSRF

- PHP ≤ 8.x has no built-in CSRF protection — frameworks add it. If you're raw PHP:
  - Generate a token: `$_SESSION['csrf'] = bin2hex(random_bytes(32))`.
  - Embed in forms / send in header for JSON.
  - Validate with `hash_equals($_SESSION['csrf'], $submitted)` (constant-time).
- `SameSite=Lax` cookies (default in modern PHP) mitigate most CSRF but NOT:
  - Same-site but cross-subdomain attacks.
  - Forms auto-submitted by the site itself.
- Never use `==` / `===` for token comparison on user input — always `hash_equals`.

## Sessions

- `session_start()` **must** precede any output. One BOM / one whitespace → "headers already sent".
- **Regenerate the session ID** on privilege elevation (login, role change): `session_regenerate_id(delete_old_session: true)`.
- Cookie flags in `session_set_cookie_params([...])` or `php.ini`:
  - `secure => true` (HTTPS only)
  - `httponly => true` (no JS access)
  - `samesite => 'Strict'` or `'Lax'`
- Default session save handler is files in `/tmp` — shared between virtual hosts if not scoped. For production: DB / Redis handler, or `session.save_path` per-app.

## `json_decode`

- Default: on malformed JSON returns `null` AND sets `json_last_error` — no exception.
- **Always** pass `JSON_THROW_ON_ERROR`:
  ```php
  $data = json_decode($raw, true, flags: JSON_THROW_ON_ERROR);
  ```
  or use `json_validate($raw)` first (PHP 8.3+).
- Default associative mode (`true` second arg) — objects become arrays. Subtle: `{}` becomes `[]` (empty array), not stdClass. If you need to preserve empty-object distinction, decode as object.
- `json_encode` with large floats / NaN / INF returns `false`. Pass `JSON_THROW_ON_ERROR` (yes, it works on encode too).

## Unserialization

- **Never `unserialize` untrusted input.** Objects are instantiated — `__wakeup` / `__destruct` / magic methods run — this is a known RCE vector.
- If you must deserialize PHP objects: `unserialize($data, ['allowed_classes' => [User::class, ...]])` restricts to a whitelist.
- Prefer JSON for any untrusted boundary (cache, queue, API).

## File uploads

- `$_FILES['upload']['type']` is **client-provided** — don't trust. Use `finfo_file(finfo_open(FILEINFO_MIME_TYPE), $path)` instead.
- `$_FILES['upload']['name']` is also client-provided — sanitize before use (never as part of the saved path). Generate your own filename: `bin2hex(random_bytes(16)) . '.' . $extension`.
- Check `$_FILES['upload']['error']` — 0 = UPLOAD_ERR_OK. Anything else → reject.
- `is_uploaded_file($_FILES['upload']['tmp_name'])` before `move_uploaded_file` — or LFI (local file inclusion) if the var is manipulated.
- Never save uploads inside the public webroot as-is. Save outside + stream through a controller.
- Size limits: `upload_max_filesize` (per file), `post_max_size` (all data), `max_file_uploads`. Exceeding → `$_FILES` is empty / silently truncated.

## `include` / `require` & path traversal

- **Never** `include` a path built from user input. Even with `basename` or `realpath`, an allowlist is safer.
- `realpath('/safe/' . $userInput)` — if `$userInput = '../../etc/passwd'`, realpath correctly resolves but the final path may still escape `/safe/`. Verify with `str_starts_with($resolved, '/safe/')`.
- `file_get_contents('/safe/' . $input)` has the same class of bugs.
- Null-byte truncation was fixed in PHP 5.3+; don't rely on the old behavior anyway.

## `eval`, `assert`, preg_replace `/e`

- `eval($input)` — RCE. There is no safe usage of `eval` on user-influenced data.
- `assert($string)` executes the string as PHP (legacy). Make sure `zend.assertions=1, assert.exception=1` and never pass string assertions.
- `preg_replace('/.../e', ...)` — removed in PHP 7. Don't try to emulate via `create_function` (removed too).

## Cryptography

- **Never invent**. Use `sodium_*` (libsodium, bundled since 7.2): `sodium_crypto_secretbox` for symmetric, `sodium_crypto_box` for asymmetric, `sodium_crypto_aead_*` for AEAD.
- `openssl_encrypt` — still valid but error-prone (mode + IV management). If libsodium is enough, use it.
- Random:
  - `random_bytes($n)` / `random_int($min, $max)` — cryptographically secure. On failure throws.
  - `rand` / `mt_rand` — NOT secure. Use only for non-security randomness (shuffled UI).
  - `uniqid()` — NOT a secure ID. Use `bin2hex(random_bytes(16))` instead.
- `hash_equals($known, $user)` for comparing tokens / HMACs — constant-time. Plain `===` leaks timing.

## Error reporting in production

- `display_errors=Off`, `log_errors=On`, `error_log=/path/to/err.log`. An exception message displayed to the user (`mysql:...`, `/var/www/...`) is an information leak.
- Exception stack traces: don't render to users. Middleware / error handler should log and return a generic message.
- `opcache.revalidate_freq` / `opcache.validate_timestamps` — correct tuning for prod, but remember a bad deploy (syntax error in a file included by opcache) can persist until restart. Plan for it.

## Cookies

- Always `setcookie($name, $val, ['httponly' => true, 'secure' => true, 'samesite' => 'Lax'])`.
- `session.cookie_*` parameters set via `session_set_cookie_params` BEFORE `session_start`.
- Session ID in URL (`session.use_only_cookies = 0`) — turn this OFF. Session fixation vector.

## Headers

- `header('X-Frame-Options: DENY')` — or CSP `frame-ancestors 'none'`.
- `header('Content-Security-Policy: default-src \'self\'')` — start restrictive, loosen with justification.
- `header('Strict-Transport-Security: max-age=31536000; includeSubDomains')` — HTTPS only.
- Never construct headers with unvalidated input (CRLF injection).

## XSS

- HTML context: `htmlspecialchars($s, ENT_QUOTES | ENT_HTML5, 'UTF-8')`. The flags matter: without `ENT_QUOTES`, single quotes pass through.
- Attribute context (JS handlers, `href`): `htmlspecialchars` is not enough for `href="javascript:"` — validate scheme whitelist.
- JSON context: use `json_encode($v, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT)` when embedding in HTML.
- URL context: `rawurlencode` for path segments, `http_build_query` for query strings.
