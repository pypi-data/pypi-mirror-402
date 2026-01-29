# Patronus

Production-ready, provider-agnostic authentication library for Django REST Framework applications in the Novah Care ecosystem.

## Features

- **Provider Agnostic**: Abstract authentication provider interface with GCIP (Firebase Auth) implementation
- **DRF Compatible**: Native Django REST Framework authentication and permission classes
- **Multi-tenant Support**: Automatic tenant context injection via middleware
- **Type Safe**: Full type annotations with mypy strict mode support
- **Async Ready**: Async variants for all provider operations

## Requirements

- Python 3.13+
- Django 6.0+
- Django REST Framework 3.14+

## Installation

### From PyPI (Recommended)

```bash
# Install with pip
pip install novah-patronus

# Or with Poetry
poetry add novah-patronus
```

### From GitHub

```bash
# Add specific version with Poetry
poetry add git+ssh://git@github.com/Novah-Care/patronus.git@v0.1.0

# Or with pip
pip install git+ssh://git@github.com/Novah-Care/patronus.git@v0.1.0
```

Or add to your `pyproject.toml` manually:

```toml
[tool.poetry.dependencies]
novah-patronus = { git = "https://github.com/Novah-Care/patronus.git", tag = "v0.1.0" }
```

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/Novah-Care/patronus.git
cd patronus

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### 1. Configure Django Settings

```python
# settings.py
import os

PATRONUS = {
    # Provider configuration
    "PROVIDER_CLASS": "patronus.providers.gcip.GCIPProvider",

    # Credentials from environment variable (production)
    # JSON strings are auto-parsed, no need for json.loads()
    "PROVIDER_CREDENTIALS": os.environ.get("GCIP_CREDENTIALS"),

    # Or from file path (development)
    # "PROVIDER_CREDENTIALS": "/path/to/service-account.json",

    # Or use application default credentials
    # "PROVIDER_CREDENTIALS": None,

    # Profile loader (implement your own or use mock for testing)
    "PROFILE_LOADER_CLASS": "patronus.profile_loader.MockProfileLoader",
}

# Add Patronus authentication to DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "patronus.PatronusAuthentication",
    ],
}

# Add tenant middleware
MIDDLEWARE = [
    # ... other middleware ...
    "patronus.TenantMiddleware",
]
```

### 2. Implement a Profile Loader

```python
# your_app/auth.py
from patronus import ProfileLoader, UserProfile, NoProfileError

class YourProfileLoader(ProfileLoader):
    def load_profile(
        self,
        uid: str,
        email: str | None = None,
        phone_number: str | None = None,
    ) -> UserProfile:
        try:
            user = User.objects.get(identity_provider_uid=uid)
            permissions = user.get_all_permissions()
            return UserProfile(
                company_id=user.company_id,
                permissions=frozenset(permissions),
                profile_type=user.profile_type,
            )
        except User.DoesNotExist:
            raise NoProfileError(f"No profile found for uid: {uid}")

    async def load_profile_async(
        self,
        uid: str,
        email: str | None = None,
        phone_number: str | None = None,
    ) -> UserProfile:
        # Async implementation
        return self.load_profile(uid, email, phone_number)
```

### 3. Use Permission Classes

```python
# your_app/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from patronus import HasPermission, HasProfile, IsSameCompany

class PatientListView(APIView):
    permission_classes = [HasPermission("read:patients")]

    def get(self, request):
        # request.user is a NovahUser instance
        return Response({"patients": []})

class PatientDetailView(APIView):
    permission_classes = [HasProfile, IsSameCompany]

    def get(self, request, pk):
        patient = get_object_or_404(Patient, pk=pk)
        self.check_object_permissions(request, patient)
        return Response({"patient": patient.data})
```

### 4. Use Tenant Context

```python
from patronus import get_current_company, company_context

def some_service_function():
    company_id = get_current_company()
    if company_id:
        # Filter by tenant
        return Model.objects.filter(company_id=company_id)

# Or use context manager for scoped access
with company_context(some_company_id):
    do_tenant_scoped_work()
```

## API Reference

### Authentication

- `PatronusAuthentication`: DRF authentication class

### User Models

- `NovahUser`: Authenticated user with permissions
- `TokenPayload`: Raw token data from JWT
- `UserProfile`: User profile from database

### Context Management

- `get_current_company()`: Get current tenant UUID
- `set_current_company(uuid)`: Set current tenant
- `clear_current_company()`: Clear tenant context
- `company_context(uuid)`: Context manager for scoped access

### Permission Classes

- `HasProfile`: Require authenticated NovahUser
- `HasPermission(permission)`: Require specific permission
- `HasAnyPermission(permissions)`: Require any of listed permissions
- `IsSameCompany`: Require same company as resource

### Exceptions

- `InvalidTokenError`: Token malformed (401)
- `ExpiredTokenError`: Token expired (401)
- `RevokedTokenError`: Token revoked (401)
- `NoProfileError`: No user profile (403)
- `TenantMismatchError`: Wrong tenant (403)
- `ProviderError`: Provider unavailable (503)

### Settings Functions

- `get_settings()`: Get Patronus configuration
- `get_provider()`: Get configured AuthProvider
- `get_profile_loader()`: Get configured ProfileLoader
- `reset_instances()`: Reset cached instances (for testing)

## Development

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/Novah-Care/patronus.git
cd patronus

# Create virtual environment
python3.13 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install package with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=patronus --cov-report=html

# Run specific test file
pytest tests/test_user.py

# Run tests matching a pattern
pytest -k "test_novah_user"
```

### Code Quality

```bash
# Run type checking
mypy src/patronus

# Run linting
ruff check src/patronus tests

# Run linting with auto-fix
ruff check --fix src/patronus tests

# Format code
ruff format src/patronus tests

# Check formatting without changes
ruff format --check src/patronus tests
```

### All-in-One Check (before committing)

```bash
# Run all checks
ruff check src/patronus tests && \
ruff format --check src/patronus tests && \
mypy src/patronus && \
pytest --cov=patronus
```

### Project Structure

```
patronus/
├── src/patronus/
│   ├── __init__.py           # Public API exports
│   ├── authentication.py     # DRF authentication class
│   ├── permissions.py        # DRF permission classes
│   ├── middleware.py         # Tenant middleware
│   ├── context.py            # Tenant context (contextvars)
│   ├── user.py               # NovahUser, TokenPayload, UserProfile
│   ├── exceptions.py         # Exception hierarchy
│   ├── settings.py           # Configuration management
│   ├── profile_loader.py     # ProfileLoader interface
│   ├── decorators.py         # (Phase 2)
│   ├── cache.py              # (Phase 2)
│   └── providers/
│       ├── __init__.py
│       ├── base.py           # AuthProvider ABC
│       └── gcip.py           # GCIP/Firebase implementation
└── tests/
    ├── conftest.py           # Shared fixtures
    └── providers/
```

## Publishing to PyPI

The package is published to [PyPI](https://pypi.org/project/novah-patronus/) using GitHub Actions with Trusted Publishing (no API tokens needed).

To publish a new version:
1. Update the version in `pyproject.toml`
2. Create a GitHub release with a new tag (e.g., `v0.2.0`)
3. The workflow automatically builds and publishes to PyPI

For detailed setup and troubleshooting, see [docs/PUBLISHING.md](docs/PUBLISHING.md).

## License

MIT License - see LICENSE file for details.
