# PSR Standards

## PSR-1: Basic Coding Standard

- Files MUST use only `<?php` or `<?=` tags
- Files MUST use UTF-8 encoding without BOM
- Files SHOULD either declare symbols (classes, functions, constants) OR cause side effects — not both
- Namespaces and classes MUST follow PSR-4
- Class names MUST be `StudlyCaps`
- Class constants MUST be `UPPER_CASE_WITH_UNDERSCORES`
- Method names MUST be `camelCase`

## PSR-4: Autoloading

Map namespace prefixes to directory paths in `composer.json`:

```json
{
    "autoload": {
        "psr-4": {
            "App\\": "src/",
            "App\\Tests\\": "tests/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "App\\Tests\\": "tests/"
        }
    }
}
```

File path must match namespace exactly:

```
src/
├── Domain/
│   ├── User/
│   │   ├── User.php           → App\Domain\User\User
│   │   └── UserRepository.php → App\Domain\User\UserRepository
│   └── Order/
│       └── Order.php          → App\Domain\Order\Order
└── Application/
    └── UserService.php        → App\Application\UserService
```

After adding or changing autoload config: `composer dump-autoload`

## PSR-12: Extended Coding Style

### Namespace and Use Declarations

```php
<?php

declare(strict_types=1);

namespace App\Domain\User;

use App\Domain\Order\Order;
use App\Shared\ValueObject\Email;
use DateTimeImmutable;
use InvalidArgumentException;

// blank line before class
class User
{
}
```

### Class Structure

```php
class User extends BaseEntity implements UserInterface, JsonSerializable
{
    // Constants first
    public const STATUS_ACTIVE = 'active';

    // Properties (public → protected → private)
    public int $id;
    protected string $status;
    private DateTimeImmutable $createdAt;

    // Constructor
    public function __construct(
        private readonly string $name,
        private readonly Email  $email,
    ) {
        $this->createdAt = new DateTimeImmutable();
    }

    // Abstract methods (in abstract class)
    // Interface methods
    // Public methods
    // Protected methods
    // Private methods
}
```

### Control Structures

```php
// if/elseif/else — opening brace on same line
if ($condition) {
    // ...
} elseif ($other) {
    // ...
} else {
    // ...
}

// No space before ( in control structures, space after keyword
foreach ($items as $key => $value) {
    // ...
}

// Match (preferred over switch)
$result = match($value) {
    'a', 'b' => 'first',
    'c'      => 'second',
    default  => 'other',
};
```

### Function and Method Declarations

```php
// Short signatures on one line
public function getId(): int
{
    return $this->id;
}

// Long signatures split across lines
public function createOrder(
    int       $userId,
    array     $items,
    ?Address  $shippingAddress = null,
): Order {
    // ...
}
```

## PSR-7: HTTP Message Interface

Standard interfaces for HTTP requests and responses (used by frameworks and middleware):

```php
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\StreamInterface;
use Psr\Http\Message\UriInterface;

// Immutable — all mutations return new instance
$request  = $request->withHeader('Accept', 'application/json');
$response = $response->withStatus(201)->withHeader('Location', '/users/1');

// Read request data
$method  = $request->getMethod();            // 'POST'
$path    = $request->getUri()->getPath();    // '/users'
$body    = (string) $request->getBody();     // raw body
$params  = $request->getParsedBody();        // decoded body (array|object|null)
$headers = $request->getHeaders();           // all headers
$query   = $request->getQueryParams();       // $_GET equivalent
```

## PSR-15: HTTP Handlers and Middleware

```php
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

// Middleware
class AuthMiddleware implements MiddlewareInterface
{
    public function process(
        ServerRequestInterface  $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $token = $request->getHeaderLine('Authorization');

        if (! $this->isValid($token)) {
            return new JsonResponse(['error' => 'Unauthorized'], 401);
        }

        return $handler->handle(
            $request->withAttribute('user', $this->resolve($token))
        );
    }
}

// Request Handler (final handler, no next)
class UserListHandler implements RequestHandlerInterface
{
    public function handle(ServerRequestInterface $request): ResponseInterface
    {
        $users = $this->repository->findAll();
        return new JsonResponse($users);
    }
}
```

## PSR-3: Logger Interface

```php
use Psr\Log\LoggerInterface;
use Psr\Log\LogLevel;

class UserService
{
    public function __construct(
        private readonly LoggerInterface $logger,
    ) {}

    public function create(array $data): User
    {
        $this->logger->info('Creating user', ['email' => $data['email']]);

        try {
            $user = $this->doCreate($data);
            $this->logger->debug('User created', ['id' => $user->id]);
            return $user;
        } catch (\Exception $e) {
            $this->logger->error('User creation failed', [
                'email'     => $data['email'],
                'exception' => $e,
            ]);
            throw $e;
        }
    }
}

// Log levels (use the most specific)
$logger->emergency($msg); // System unusable
$logger->alert($msg);     // Immediate action required
$logger->critical($msg);  // Critical condition
$logger->error($msg);     // Runtime error
$logger->warning($msg);   // Non-error warning
$logger->notice($msg);    // Normal but significant
$logger->info($msg);      // Informational
$logger->debug($msg);     // Debug detail
```
