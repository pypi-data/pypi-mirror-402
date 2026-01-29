## Django Transactional Outbox Pattern

### What is the Outbox Pattern?
The Transactional Outbox pattern ensures reliable event publishing by storing events in the same database transaction as your business data. This guarantees that events are published if and only if the business operation succeeds, solving the dual-write problem.

### Use Cases
- Publishing domain events to message brokers (RabbitMQ, Kafka, SQS)
- Implementing event-driven architecture
- Ensuring eventual consistency across microservices
- Reliable webhook delivery
- Audit logging with guaranteed delivery

### Recommended Library: django-outbox-pattern

**Use `django-outbox-pattern` for production implementations.** This library provides a battle-tested implementation of the outbox pattern with STOMP protocol support for message brokers.

## Installation

```bash
pip install django-outbox-pattern
```

**Add to INSTALLED_APPS:**
```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_outbox_pattern",
]
```

**Run migrations:**
```bash
python manage.py migrate
```

## Configuration

**settings.py:**
```python
DJANGO_OUTBOX_PATTERN = {
    # Message broker connection
    "DEFAULT_STOMP_HOST_AND_PORTS": [("127.0.0.1", 61613)],
    "DEFAULT_STOMP_USERNAME": "guest",
    "DEFAULT_STOMP_PASSCODE": "guest",

    # Retry settings
    "DEFAULT_MAXIMUM_RETRY_ATTEMPTS": 50,
    "DEFAULT_PAUSE_FOR_RETRY": 240,  # seconds

    # Data retention
    "DAYS_TO_KEEP_DATA": 30,

    # Async processing (optional)
    "DEFAULT_CONSUMER_PROCESS_MSG_ON_BACKGROUND": True,
}
```

**Environment Variables (recommended):**
```python
# settings.py
import os

DJANGO_OUTBOX_PATTERN = {
    "DEFAULT_STOMP_HOST_AND_PORTS": [
        (os.getenv("STOMP_HOST", "127.0.0.1"),
         int(os.getenv("STOMP_PORT", 61613)))
    ],
    "DEFAULT_STOMP_USERNAME": os.getenv("STOMP_USERNAME", "guest"),
    "DEFAULT_STOMP_PASSCODE": os.getenv("STOMP_PASSCODE", "guest"),
}
```

## Basic Usage

### Decorate Your Models

**Simple Configuration:**
```python
from django.db import models
from django_outbox_pattern.decorators import Config, publish

@publish([Config(destination='/topic/orders')])
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Custom Serializer Method:**
```python
@publish([
    Config(
        destination='/topic/orders',
        serializer='serialize_for_event'
    )
])
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def serialize_for_event(self):
        """Custom serialization for outbox events"""
        return {
            "order_id": str(self.id),
            "user_id": str(self.user_id),
            "total_amount": str(self.total),
            "status": self.status,
            "timestamp": self.created_at.isoformat(),
        }
```

**Additional Options:**
- Specify fields: `Config(fields=['id', 'status'])`
- Multiple destinations: `@publish([Config(...), Config(...)])`
- Versioning: `Config(version='v2')` → `/topic/orders.v2`

## Publishing Events

**Development:**
```bash
python manage.py publish
```

**Production (Docker):**
Add to docker-compose.yml:
```yaml
outbox_publisher:
  build: .
  command: python manage.py publish
  depends_on:
    - db
    - rabbitmq
```

## Consuming Events

### Subscribe to Messages

**Define a Callback:**
```python
# apps/events/callbacks.py
from django.db import transaction
from django_outbox_pattern.payloads import Payload

def handle_order_event(payload: Payload):
    """
    Process incoming order events.

    Args:
        payload: Contains message body and metadata
    """
    try:
        # Validate message
        if not payload.body or 'order_id' not in payload.body:
            payload.nack()  # Reject invalid message
            return

        # Process with idempotency
        with transaction.atomic():
            order_id = payload.body['order_id']

            # Check if already processed (idempotency)
            if already_processed(payload.message_id):
                payload.ack()
                return

            # Process the event
            process_order(order_id, payload.body)

            # Save message ID to prevent reprocessing
            payload.save()

            # Acknowledge successful processing
            payload.ack()

    except Exception as e:
        # Reject and requeue on error
        payload.nack()
        raise
```

**Run the Subscriber:**
```bash
python manage.py subscribe 'apps.events.callbacks.handle_order_event' '/topic/orders' 'order_queue'
```

**Parameters:**
- Callback function path
- Destination topic
- Queue name (for durable subscriptions)

## Best Practices

**1. Implement Idempotency**
Always check `payload.message_id` to prevent duplicate processing:
```python
def handle_event(payload: Payload):
    with transaction.atomic():
        if already_processed(payload.message_id):
            payload.ack()
            return
        process_event(payload.body)
        payload.save()  # Records message_id
        payload.ack()
```

**2. Keep Payloads Lightweight**
Publish IDs, not full objects: `{"order_id": "123", "status": "completed"}`

**3. Respect Transaction Boundaries**
Outbox entries are created within model save transactions automatically

**4. Handle Consumer Errors**
- Validate payloads before processing
- Use `payload.nack()` for retryable errors
- Use `payload.ack()` to prevent infinite retries on permanent failures

**5. Monitor Queue Health**
Alert if `OutboxEntry.objects.filter(published=False).count()` grows unexpectedly

## Testing

```python
import pytest
from django_outbox_pattern.models import OutboxEntry

@pytest.mark.django_db
def test_order_creates_outbox_entry(user):
    order = Order.objects.create(user=user, total=100.00, status='pending')

    entry = OutboxEntry.objects.get(aggregate_id=str(order.id))
    assert entry.destination == '/topic/orders'
    assert not entry.published
```

## Advanced Configuration

**Dynamic Serialization:**
Use conditional logic in serializer methods to include different fields based on model state

**Environment-Specific Destinations:**
Use `f'/topic/{settings.ENVIRONMENT}/orders'` for environment-specific routing

## Production Deployment

**Requirements:** Python >=3.10, Django >=5.0, STOMP-compatible broker (RabbitMQ, ActiveMQ)

**RabbitMQ Setup:**
```bash
# Enable STOMP plugin
rabbitmq-plugins enable rabbitmq_stomp

# Or via Docker (docker-compose.yml)
rabbitmq:
  image: rabbitmq:3-management-alpine
  command: bash -c "rabbitmq-plugins enable rabbitmq_stomp && rabbitmq-server"
```

**Scaling:** Run multiple publisher/subscriber processes. Library handles concurrency safely. See `standards/global/tech-stack.md` for Docker scaling patterns.

## When NOT to Use django-outbox-pattern

- **Very high frequency** (>10,000 events/sec) - Consider CDC (Debezium)
- **Real-time requirements** (<10ms latency) - Use direct messaging
- **Simple apps** without distributed systems - Overhead not justified
- **Non-STOMP brokers** - Library requires STOMP protocol

## Alternatives

- **Custom implementation** - Full control but more maintenance
- **Debezium** - CDC for very high throughput (reads DB transaction log)
- **django-postgres-outbox** - PostgreSQL-specific with LISTEN/NOTIFY
- **Celery** - For simple async tasks (not true outbox pattern)

## Resources

- PyPI: https://pypi.org/project/django-outbox-pattern/
- Requirements: Python >=3.10, Django 5.0+
- License: MIT
