# Tech Stack

## Language & Runtime

| Component | Choice | Notes |
|-----------|--------|-------|
| Language | Python 3.13+ | Latest stable Python with performance improvements |
| Type Checking | Static typing with mypy | Full type annotations throughout codebase |

## Framework & Libraries

### Production Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| django | >=6.0 | Web framework, middleware, cache integration |
| djangorestframework | >=3.14 | DRF authentication and permission classes |
| firebase-admin | >=6.0 | GCIP JWT validation (isolated in provider) |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=8.0 | Test runner |
| pytest-django | >=4.5 | Django test integration |
| pytest-cov | >=4.0 | Coverage reporting |
| pytest-asyncio | >=0.23 | Async test support |
| ruff | >=0.1 | Linting and formatting |
| mypy | >=1.0 | Static type checking |
| django-stubs | >=4.0 | Django type stubs for mypy |
| djangorestframework-stubs | >=3.14 | DRF type stubs for mypy |

## Build System

| Component | Choice | Notes |
|-----------|--------|-------|
| Build Backend | hatchling | Modern Python build backend |
| Project Config | pyproject.toml | Single source of project metadata |
| Version Management | hatch-vcs or manual | Semantic versioning |

## Code Quality

### Linting & Formatting

```toml
# ruff configuration (pyproject.toml)
[tool.ruff]
target-version = "py313"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
```

### Type Checking

```toml
# mypy configuration (pyproject.toml)
[tool.mypy]
python_version = "3.13"
strict = true
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
```

## Testing

| Aspect | Approach |
|--------|----------|
| Framework | pytest with pytest-django |
| Coverage Target | >90% line coverage |
| Test Types | Unit, integration, contract tests |
| Mocking | unittest.mock, pytest fixtures |
| CI Enforcement | Coverage gate in CI pipeline |

### Test Structure

```
tests/
  conftest.py          # Shared fixtures
  test_authentication.py
  test_permissions.py
  test_middleware.py
  test_decorators.py
  test_context.py
  test_cache.py
  providers/
    test_gcip.py
```

## Distribution

| Aspect | Choice |
|--------|--------|
| Package Type | Pure Python wheel |
| Distribution | Private PyPI or Git-based pip install |
| License | Proprietary (Novah Care internal) |
| Installation | `pip install patronus` or `pip install git+ssh://...` |

### Package Structure

```
patronus/
  __init__.py
  authentication.py
  permissions.py
  middleware.py
  decorators.py
  context.py
  user.py
  exceptions.py
  cache.py
  settings.py
  providers/
    __init__.py
    base.py
    gcip.py
```

## Performance Requirements

| Metric | Target | Approach |
|--------|--------|----------|
| Token validation | <50ms (cached) | Cache validated tokens with TTL |
| Permission check | <10ms (cached) | Cache permission lookups per user |
| Cache backend | Django cache | Redis recommended for production |

## CI/CD Integration

| Stage | Tools |
|-------|-------|
| Linting | ruff check |
| Formatting | ruff format --check |
| Type Check | mypy |
| Tests | pytest --cov |
| Coverage | pytest-cov with 90% threshold |
| Build | hatch build |
| Publish | twine or hatch publish |
