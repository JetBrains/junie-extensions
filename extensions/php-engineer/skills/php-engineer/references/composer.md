# Composer

## Version Constraints

```json
{
    "require": {
        "php": ">=8.2",
        "vendor/package": "^2.0",
        "vendor/other": "~1.5",
        "vendor/exact": "1.2.3"
    }
}
```

| Constraint | Meaning |
|------------|---------|
| `^2.0` | `>=2.0.0 <3.0.0` — allows minor and patch updates (preferred) |
| `~1.5` | `>=1.5.0 <2.0.0` — allows only patch updates |
| `>=1.0 <2.0` | Explicit range |
| `1.2.3` | Exact version — avoid unless necessary |
| `*` | Any version — avoid in production |
| `dev-main` | Main branch — development only |

**Always commit `composer.lock`.** It guarantees reproducible installs across environments.

## Project Setup

```bash
# Create new project
composer init

# Install dependencies from lock file (CI/production)
composer install --no-dev --optimize-autoloader

# Install including dev dependencies (local development)
composer install

# Add runtime dependency
composer require vendor/package

# Add dev-only dependency
composer require --dev vendor/package

# Update a single package
composer update vendor/package

# Update all (use carefully)
composer update

# Check for outdated packages
composer outdated

# Validate composer.json
composer validate
```

## Autoloading

```json
{
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        },
        "files": [
            "src/helpers.php"
        ]
    },
    "autoload-dev": {
        "psr-4": {
            "App\\Tests\\": "tests/"
        }
    }
}
```

```bash
# Regenerate autoloader (after adding new classes)
composer dump-autoload

# Optimized for production (builds class map)
composer dump-autoload --optimize --no-dev
```

## Scripts

```json
{
    "scripts": {
        "test":    "vendor/bin/pest",
        "analyse": "vendor/bin/phpstan analyse",
        "format":  "vendor/bin/pint",
        "check":   [
            "@format",
            "@analyse",
            "@test"
        ],
        "post-autoload-dump": [
            "php -r \"echo 'Autoloader rebuilt.\\n';\""
        ]
    },
    "scripts-descriptions": {
        "check": "Run format, static analysis, and tests"
    }
}
```

```bash
composer check        # runs format → analyse → test
composer test         # runs test suite
```

## Platform Requirements

```json
{
    "config": {
        "platform": {
            "php": "8.2.0"
        }
    },
    "require": {
        "php": ">=8.2",
        "ext-json": "*",
        "ext-pdo": "*",
        "ext-mbstring": "*"
    }
}
```

## Security and Audit

```bash
# Check for known vulnerabilities
composer audit

# Check with more detail
composer audit --format=json
```

## composer.json Structure

```json
{
    "name": "vendor/project",
    "description": "Project description",
    "type": "project",
    "license": "MIT",
    "minimum-stability": "stable",
    "prefer-stable": true,
    "require": {
        "php": ">=8.2",
        "ext-json": "*"
    },
    "require-dev": {
        "pestphp/pest": "^3.0",
        "phpstan/phpstan": "^2.0",
        "laravel/pint": "^1.0"
    },
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "Tests\\": "tests/"
        }
    },
    "scripts": {
        "test":    "vendor/bin/pest",
        "analyse": "vendor/bin/phpstan analyse"
    },
    "config": {
        "sort-packages": true,
        "allow-plugins": {
            "pestphp/pest-plugin": true
        }
    }
}
```

## Private Repositories

```json
{
    "repositories": [
        {
            "type": "vcs",
            "url": "https://github.com/company/private-repo"
        },
        {
            "type": "path",
            "url": "../local-package"
        }
    ]
}
```

## Key Rules

- Always commit `composer.lock` for applications
- Never commit `vendor/` directory
- Use `^` constraints for libraries, exact for internal packages
- Run `composer audit` in CI
- Keep `require` and `require-dev` separate — dev tools must not be in production
