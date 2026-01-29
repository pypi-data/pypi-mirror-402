## Django Testing Best Practices

### Test Philosophy
- **Write Minimal Tests During Development**: Focus on implementing features first, add strategic tests at completion points
- **Test Core Flows Only**: Test critical paths and primary workflows, defer edge cases unless business-critical
- **Test Behavior, Not Implementation**: Focus on what the code does, not how it does it

### Django Test Framework

**TestCase Classes:**
```python
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APITestCase, APIClient

# Standard Django tests (with database rollback)
class OrderModelTest(TestCase):
    pass

# For testing transactions, real database commits
class OrderTransactionTest(TransactionTestCase):
    pass

# For DRF API tests
class OrderAPITest(APITestCase):
    pass
```

**pytest-django (Recommended):**
```python
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
```

### Model Testing

**Test Model Methods:**
```python
from django.test import TestCase

class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.order = Order.objects.create(user=self.user, total=100.00)

    def test_cancel_order(self):
        self.order.cancel()
        self.assertEqual(self.order.status, 'cancelled')
```

### API Testing (DRF)

```python
from rest_framework.test import APITestCase
from rest_framework import status

class OrderAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.force_authenticate(user=self.user)

    def test_create_order(self):
        data = {'items': [{'product_id': 1, 'quantity': 2}]}
        response = self.client.post('/api/orders/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
```

### Using Factories (factory_boy)

```python
# tests/factories.py
import factory
from factory.django import DjangoModelFactory

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')

class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    total = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    status = 'pending'

# Usage
order = OrderFactory(total=150.00)
orders = OrderFactory.create_batch(5, status='completed')
```

### Fixtures

**Prefer factories over fixtures for flexibility.** If needed:
```python
class OrderTest(TestCase):
    fixtures = ['users.json', 'orders.json']
```

### pytest-django Approach

```python
import pytest
from tests.factories import UserFactory, OrderFactory

@pytest.fixture
def authenticated_client():
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=UserFactory())
    return client

@pytest.mark.django_db
def test_create_order(authenticated_client):
    data = {'items': [{'product_id': 1, 'quantity': 2}]}
    response = authenticated_client.post('/api/orders/', data, format='json')

    assert response.status_code == 201
    assert Order.objects.count() == 1
```

### Mocking External Services

```python
from unittest.mock import patch

@patch('apps.payments.services.PaymentGateway.charge')
def test_process_payment(mock_charge):
    mock_charge.return_value = {'status': 'success', 'transaction_id': '123'}

    result = process_payment(order)

    assert result['status'] == 'success'
    mock_charge.assert_called_once_with(order.total)
```

### Query Optimization Testing

```python
from django.test import TestCase

class QueryOptimizationTest(TestCase):
    def test_select_related_reduces_queries(self):
        OrderFactory.create_batch(5)

        with self.assertNumQueries(1):
            orders = list(Order.objects.select_related('user').all())
            for order in orders:
                _ = order.user.username
```

### Testing Middleware and Signals

**Middleware:** Use `RequestFactory()` to test middleware in isolation

**Signals:** Mock signal handlers with `@patch` to verify they're called

### Performance Testing

Use `assertNumQueries()` for query count testing. For response time testing, use Django Silk or dedicated profiling tools.

### Test Configuration

**settings/test.py:**
```python
# Use in-memory SQLite for speed
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}

# Faster password hashing
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
```

**pytest.ini:**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = myproject.settings.test
addopts = --reuse-db --nomigrations
```

### Running Tests

**Django Test Runner:**
```bash
python manage.py test                    # All tests
python manage.py test apps.orders        # Specific app
coverage run --source='.' manage.py test # With coverage
```

**pytest (recommended):**
```bash
pytest                              # All tests
pytest --cov=apps --cov-report=html # With coverage
pytest -n auto                      # Parallel execution
```

### Test Organization

**File Structure:**
```
orders/
├── tests/
│   ├── __init__.py
│   ├── factories.py
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_serializers.py
│   └── test_services.py
```

### Best Practices

1. ✅ Use factories instead of fixtures for flexibility
2. ✅ Keep tests independent (don't rely on test execution order)
3. ✅ Use `setUp()` for common test data
4. ✅ Test one thing per test method
5. ✅ Use descriptive test names (test_create_order_with_invalid_items)
6. ✅ Mock external services (APIs, payment gateways)
7. ✅ Use pytest-django for cleaner test syntax
8. ✅ Test critical flows only during development
9. ✅ Use `assertNumQueries` to catch N+1 problems
10. ❌ Don't test Django's built-in functionality
11. ❌ Don't test third-party library code
12. ❌ Don't write tests that depend on external services
