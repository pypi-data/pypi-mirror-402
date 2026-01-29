## Django Error Handling Best Practices

### Built-in Django Exceptions

**Common Django Exceptions:**
```python
from django.core.exceptions import (
    ValidationError,        # Model/form validation errors
    ObjectDoesNotExist,    # Generic object not found
    PermissionDenied,      # 403 Forbidden
    SuspiciousOperation,   # Security-related errors
    ImproperlyConfigured,  # Configuration errors
)
from django.http import Http404  # 404 Not Found
```

**Usage:**
```python
from django.shortcuts import get_object_or_404

def get_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order.html', {'order': order})
```

### Model Validation

```python
from django.core.exceptions import ValidationError

class Order(models.Model):
    def clean(self):
        if self.total < 0:
            raise ValidationError({'total': 'Total cannot be negative'})

    def cancel(self):
        if self.status == 'completed':
            raise ValidationError('Cannot cancel completed order')
        self.status = 'cancelled'
        self.save()
```

### DRF Exception Handling

**Built-in DRF Exceptions:**
```python
from rest_framework.exceptions import (
    ValidationError,      # 400 Bad Request
    AuthenticationFailed, # 401 Unauthorized
    PermissionDenied,     # 403 Forbidden
    NotFound,             # 404 Not Found
    MethodNotAllowed,     # 405 Method Not Allowed
    NotAcceptable,        # 406 Not Acceptable
    Throttled,            # 429 Too Many Requests
)
```

**Usage:**
```python
from rest_framework.exceptions import NotFound, ValidationError

class OrderViewSet(ModelViewSet):
    def retrieve(self, request, pk=None):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
        except Order.DoesNotExist:
            raise NotFound('Order not found')
        return Response(OrderSerializer(order).data)
```

**Custom Exception Handler:**
```python
# exceptions.py
from rest_framework.views import exception_handler
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        logger.error(f'Unhandled exception: {exc}', exc_info=True)
    return response

# settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'myapp.exceptions.custom_exception_handler'
}
```

### Logging

**Basic Setup (settings.py):**
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO'},
        'myapp': {'handlers': ['console'], 'level': 'DEBUG'},
    },
}
```

**Usage:**
```python
import logging

logger = logging.getLogger(__name__)

def process_payment(order):
    try:
        payment = PaymentGateway.charge(order.total)
        logger.info(f'Payment processed for order {order.id}')
        return payment
    except PaymentException as e:
        logger.error(f'Payment failed: {e}', exc_info=True)
        raise
```

### Custom Exceptions

```python
# exceptions.py
class OrderException(Exception):
    """Base exception for order-related errors"""
    pass

class InsufficientStockException(OrderException):
    pass

# Map to DRF
from rest_framework.exceptions import APIException

class InsufficientStock(APIException):
    status_code = 400
    default_detail = 'Insufficient stock'

# Usage in ViewSet
class OrderViewSet(ModelViewSet):
    def create(self, request):
        try:
            order = create_order(request.user, request.data['items'])
            return Response(OrderSerializer(order).data, status=201)
        except InsufficientStockException as e:
            raise InsufficientStock(str(e))
```

### Middleware for Error Handling

```python
# middleware.py
import logging

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        logger.error(f'Unhandled exception: {exception}', exc_info=True)
        return None  # Let Django's default handler take over
```

### Handling External Service Failures

**Retry with Exponential Backoff:**
Use Celery's built-in retry mechanism or implement simple retry logic with exponential backoff (2^attempt seconds)

**Graceful Degradation:**
```python
def get_product_recommendations(product_id):
    try:
        return RecommendationService.get_recommendations(product_id)
    except ServiceException as e:
        logger.warning(f'Recommendation service failed: {e}')
        # Fallback to related products
        return Product.objects.filter(category=product.category)[:5]
```

### Testing Error Handling

```python
from rest_framework.test import APITestCase
from rest_framework import status

class OrderAPITestCase(APITestCase):
    def test_get_nonexistent_order(self):
        response = self.client.get('/api/orders/99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
```

### Production Error Tracking

**Integration with Sentry:**
```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True,
    environment=env('ENVIRONMENT', default='development'),
)
```

### Best Practices Summary

1. ✅ Use Django/DRF built-in exceptions when appropriate
2. ✅ Raise specific exceptions, not generic `Exception`
3. ✅ Validate early (in serializers, model `clean()` methods)
4. ✅ Log all errors with context
5. ✅ Provide user-friendly error messages (never expose internal details)
6. ✅ Use custom exception handlers for consistent API responses
7. ✅ Implement graceful degradation for non-critical failures
8. ✅ Test error scenarios
9. ✅ Use error tracking tools (Sentry) in production
10. ❌ Don't catch exceptions you can't handle
11. ❌ Don't silence errors (always log)
12. ❌ Don't expose sensitive data in error messages
