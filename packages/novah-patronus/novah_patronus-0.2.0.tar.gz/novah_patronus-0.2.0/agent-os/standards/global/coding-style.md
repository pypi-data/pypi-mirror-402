## Django Coding Style Guide

### Python and Django Style

**Follow PEP 8 + Django Conventions:**
- Django follows PEP 8 with some specific additions
- Use 4 spaces for indentation (never tabs)
- Maximum line length: 119 characters (Django's convention)
- Use blank lines to separate logical sections

**Code Formatting Tools:**
```bash
# black - opinionated code formatter
black .

# isort - sort imports
isort .

# flake8 - linting
flake8 .

# Combine in pre-commit hook
```

### Naming Conventions

**Python/Django Naming:**
```python
# Models: PascalCase, singular
class User(models.Model):
    pass

class OrderItem(models.Model):
    pass

# Variables, functions: snake_case
def calculate_total_price(order_items):
    total_price = 0
    for item in order_items:
        total_price += item.price
    return total_price

# Constants: UPPER_SNAKE_CASE
MAX_UPLOAD_SIZE = 5 * 1024 * 1024
DEFAULT_CURRENCY = 'USD'

# Private methods/variables: leading underscore
def _internal_helper():
    pass

_cache = {}

# Classes: PascalCase
class UserSerializer(serializers.ModelSerializer):
    pass

class OrderViewSet(viewsets.ModelViewSet):
    pass
```

**File Naming:**
```
# Python files: snake_case
user_services.py
order_utils.py
payment_processors.py

# Django apps: snake_case, plural
users/
orders/
products/
```

**URL Naming:**
```python
# URL patterns: kebab-case
path('order-history/', views.OrderHistoryView.as_view(), name='order_history')
path('user-profile/', views.UserProfileView.as_view(), name='user_profile')

# URL names: snake_case
reverse('order_history')
reverse('user_profile')
```

### Import Organization

**Import Order (use isort):**
```python
# 1. Standard library imports
import json
import os
from datetime import datetime

# 2. Related third party imports
import requests
from celery import shared_task

# 3. Django imports
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

# 4. Third-party app imports
from rest_framework import serializers
from rest_framework.views import APIView

# 5. Local application imports
from apps.orders.models import Order
from apps.users.services import UserService
from .models import Product
from .serializers import ProductSerializer
```

**Absolute vs Relative Imports:**
```python
# Prefer absolute imports for cross-app imports
from apps.users.models import User

# Use relative imports within the same app
from .models import Product
from .serializers import ProductSerializer
from ..utils import helper_function  # One level up
```

### Function and Method Style

**Small, Focused Functions:**
```python
# Good: Single responsibility
def calculate_order_total(order):
    return sum(item.price * item.quantity for item in order.items.all())

def apply_discount(total, discount_code):
    discount = Discount.objects.get(code=discount_code)
    return total * (1 - discount.percentage / 100)

# Bad: Too many responsibilities
def process_order(order, discount_code=None):
    total = 0
    for item in order.items.all():
        total += item.price * item.quantity
    if discount_code:
        discount = Discount.objects.get(code=discount_code)
        total = total * (1 - discount.percentage / 100)
    order.total = total
    order.save()
    send_email(order.user.email, 'Order confirmed')
    log_order(order)
    return order
```

**Function Signatures:**
```python
# Good: Type hints (Python 3.6+)
def create_order(user: User, items: list[OrderItem]) -> Order:
    pass

# Good: Default arguments at the end
def send_email(to: str, subject: str, body: str, cc: list = None):
    pass

# Good: Keyword-only arguments for clarity
def create_user(*, username: str, email: str, password: str):
    pass
```

### Class-Based Views Style

**ViewSet Organization:**
```python
class OrderViewSet(viewsets.ModelViewSet):
    # 1. Class attributes
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'created_at']

    # 2. Standard methods (alphabetically)
    def create(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        pass

    def list(self, request, *args, **kwargs):
        pass

    # 3. Custom actions
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        pass

    @action(detail=False, methods=['get'])
    def recent(self, request):
        pass

    # 4. Helper methods (private)
    def _send_confirmation_email(self, order):
        pass
```

### Django Model Style

**Model Organization:**
```python
class Order(models.Model):
    # 1. Field definitions
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    # 2. Meta class
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    # 3. Magic methods
    def __str__(self):
        return f'Order #{self.id} by {self.user.email}'

    # 4. Public methods (alphabetically)
    def calculate_total(self):
        return sum(item.price * item.quantity for item in self.items.all())

    def cancel(self):
        self.status = 'cancelled'
        self.save()

    # 5. get_absolute_url
    def get_absolute_url(self):
        return reverse('order_detail', kwargs={'pk': self.pk})
```

### QuerySet and Manager Style

```python
# Custom QuerySet
class OrderQuerySet(models.QuerySet):
    def completed(self):
        return self.filter(status='completed')

    def for_user(self, user):
        return self.filter(user=user)

# Custom Manager
class OrderManager(models.Manager):
    def get_queryset(self):
        return OrderQuerySet(self.model, using=self._db)

    def completed(self):
        return self.get_queryset().completed()

# Model
class Order(models.Model):
    # ...
    objects = OrderManager()
```

### Comments and Docstrings

**Docstring Style (Google format):**
```python
def create_order(user, items):
    """
    Create a new order for the given user.

    Args:
        user (User): The user creating the order
        items (list): List of order items with product and quantity

    Returns:
        Order: The newly created order instance

    Raises:
        ValidationError: If items are invalid or out of stock
        PaymentException: If payment processing fails
    """
    pass
```

**Class Docstrings:**
```python
class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model.

    Handles serialization and validation of order data including
    nested order items and user information.
    """
    pass
```

**Comments:**
```python
# Good: Explain WHY, not WHAT
# Use atomic transaction to ensure order and items are created together
with transaction.atomic():
    order = Order.objects.create(user=user)
    OrderItem.objects.bulk_create(items)

# Bad: Explaining obvious code
# Loop through items
for item in items:
    # Add item price to total
    total += item.price
```

### Code Organization Principles

**DRY (Don't Repeat Yourself):**
```python
# Bad: Repeated logic
def get_active_users():
    return User.objects.filter(is_active=True, email_verified=True)

def count_active_users():
    return User.objects.filter(is_active=True, email_verified=True).count()

# Good: Extract to manager/queryset
class UserQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True, email_verified=True)

class User(models.Model):
    objects = UserQuerySet.as_manager()

# Usage
active_users = User.objects.active()
active_count = User.objects.active().count()
```

**Service Layer:**
Keep views thin, business logic in services.py.

**For complete service layer pattern, see:** `standards/global/conventions.md`

### Linting and Formatting

**Configuration Files:**

**pyproject.toml (Black + isort):**
```toml
[tool.black]
line-length = 119
target-version = ['py310']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | migrations
)/
'''

[tool.isort]
profile = "black"
line_length = 119
skip = ["migrations", ".venv"]
```

**.flake8:**
```ini
[flake8]
max-line-length = 119
exclude = .git,__pycache__,*/migrations/*,.venv
ignore = E203,W503
```

### Best Practices

1. ✅ Follow PEP 8 and Django coding style
2. ✅ Use type hints for function signatures
3. ✅ Keep functions small and focused (< 20 lines ideally)
4. ✅ Use meaningful variable names
5. ✅ Organize imports with isort
6. ✅ Format code with black
7. ✅ Remove dead code immediately
8. ✅ Use docstrings for public functions/classes
9. ✅ Prefer composition over inheritance
10. ✅ Keep views thin, use service layer for business logic
11. ❌ Don't abbreviate names unnecessarily
12. ❌ Don't leave commented-out code
13. ❌ Don't mix tabs and spaces
14. ❌ Don't create god classes or functions
