## Django Project Conventions

### Project Structure

**Standard Django Project Layout (with Poetry & Docker):**
```
myproject/
├── manage.py
├── Dockerfile              # REQUIRED: Docker image definition
├── docker-compose.yml      # REQUIRED: Local development orchestration
├── docker-compose.prod.yml # Production override
├── .dockerignore           # Docker build exclusions
├── pyproject.toml          # REQUIRED: Poetry dependencies & config
├── poetry.lock             # REQUIRED: Locked dependency versions
├── myproject/              # Project package (settings, urls)
│   ├── __init__.py
│   ├── settings/           # Split settings
│   │   ├── __init__.py
│   │   ├── base.py         # Common settings
│   │   ├── local.py        # Development
│   │   ├── production.py   # Production
│   │   └── test.py         # Testing
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/                   # Django apps
│   ├── users/
│   ├── core/
│   └── api/
├── static/                 # Static files
├── media/                  # User uploads
├── templates/              # Global templates
├── .env.example
├── .gitignore
├── pytest.ini
└── README.md
```

**⚠️ IMPORTANT: NO requirements.txt files!**
- Use `pyproject.toml` managed by Poetry
- All dependencies defined in Poetry configuration
- `poetry.lock` ensures reproducible builds

**App Structure:**
```
users/
├── __init__.py
├── models.py
├── views.py
├── serializers.py          # For DRF
├── urls.py
├── admin.py
├── apps.py
├── forms.py
├── managers.py             # Custom managers
├── services.py             # Business logic
├── selectors.py            # Query logic
├── signals.py              # Signal handlers
├── migrations/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── factories.py
└── management/
    └── commands/
```

### Settings Management

**Split Settings Pattern:**
```python
# settings/base.py - Common settings
# settings/local.py - Development
from .base import *
DEBUG = True

# settings/production.py - Production
from .base import *
DEBUG = False
```

**Environment Variables:**
```python
# Use django-environ or python-decouple
import environ

env = environ.Env(
    DEBUG=(bool, False)
)

# Read .env file
environ.Env.read_env()

DEBUG = env('DEBUG')
SECRET_KEY = env('SECRET_KEY')
DATABASE_URL = env('DATABASE_URL')
```

**Never commit:**
- `.env` files
- `SECRET_KEY`
- Database credentials
- API keys
- Always include `.env.example` with dummy values

### App Organization

**When to Create New App:**
- Represents a distinct domain concept
- Could be reused in another project
- Has 5+ models or substantial functionality

**Keep Apps Focused:**
- Single responsibility principle
- Clear boundaries between apps
- Avoid circular dependencies

**Common App Patterns:**
- `core/` - Shared utilities, base models, common mixins
- `users/` - User authentication and profiles
- `api/` - REST API endpoints (if using DRF)
- Domain apps - `orders/`, `products/`, `billing/`, etc.

### URL Configuration

**Project urls.py:**
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.api.urls')),
    path('users/', include('apps.users.urls')),
]
```

**App urls.py:**
```python
from django.urls import path
from . import views

app_name = 'users'  # For reverse URL lookups

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
]
```

### Service Layer Pattern

**Separate Business Logic from Views:**
```python
# services.py
from django.db import transaction

@transaction.atomic
def create_order(user, items):
    """Business logic for order creation"""
    order = Order.objects.create(user=user, total=0)
    # ... business logic
    return order

# views.py
class CreateOrderView(APIView):
    def post(self, request):
        order = create_order(request.user, request.data['items'])
        return Response(OrderSerializer(order).data)
```

### Dependency Management & Development Environment

**⚠️ REQUIRED: All projects must use Poetry and Docker**

For complete setup instructions, configuration examples, and best practices, see:
- **Poetry configuration**: `standards/global/tech-stack.md` (Poetry section)
- **Docker setup**: `standards/global/tech-stack.md` (Docker section)

**Quick reference:**
```bash
# Add dependency
poetry add package-name

# Start development
docker-compose up -d

# Run Django commands
docker-compose exec web python manage.py [command]
```

### Static Files

**Development:**
```python
# settings/local.py
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

**Production:**
```python
# Use WhiteNoise or CDN
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Media Files

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# In production, use cloud storage (S3, GCS)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

### Version Control

**Git Workflow:**
- Use meaningful branch names: `feature/user-authentication`, `fix/order-total-bug`
- Commit messages: Use conventional commits format
  - `feat: add user registration endpoint`
  - `fix: correct order total calculation`
  - `refactor: extract order service logic`
  - `test: add tests for order creation`

**Commit Migrations:**
- Always commit migration files
- Review migrations before committing
- Never modify migrations after merging to main

### Django-Specific Files

**.gitignore:**
```
*.pyc
__pycache__/
db.sqlite3
.env
/media/
/staticfiles/
.DS_Store
```

**Django Admin Customization:**
```python
# admin.py
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'id']
    readonly_fields = ['created_at', 'updated_at']
```

### Documentation

**README.md Should Include:**
- Project description
- Setup instructions
- Environment variables needed
- How to run tests
- How to run migrations
- Deployment instructions

**Docstrings:**
```python
def create_order(user, items):
    """
    Create a new order for the given user.

    Args:
        user (User): The user creating the order
        items (list): List of order items

    Returns:
        Order: The created order instance

    Raises:
        ValidationError: If items are invalid
    """
```

### Configuration Best Practices

1. Use environment-specific settings files
2. Never hardcode configuration values
3. Use environment variables for secrets
4. Document all configuration options
5. Provide sensible defaults where possible
6. Use `django-environ` or `python-decouple` for env management

### Django Management Commands

**Create custom commands for common tasks:**
```
management/
└── commands/
    ├── seed_data.py
    ├── cleanup_old_data.py
    └── process_outbox.py
```

### Testing Configuration

**pytest.ini:**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = myproject.settings.test
python_files = tests.py test_*.py *_tests.py
```

**conftest.py:**
```python
import pytest
from django.conf import settings

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass
```
