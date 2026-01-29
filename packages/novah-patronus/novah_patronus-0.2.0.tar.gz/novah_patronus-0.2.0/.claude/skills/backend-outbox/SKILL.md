---
name: backend-outbox
description: Implement the Transactional Outbox pattern using django-outbox-pattern for reliable event publishing to message brokers. Use this skill when publishing domain events, implementing event-driven architecture, integrating with RabbitMQ or other STOMP brokers, decorating models with @publish for event emission, writing event consumers/subscribers, ensuring eventual consistency across services, or working on files related to event publishing, messaging, or outbox configuration.
---

## When to use this skill:

- When implementing the Transactional Outbox pattern for reliable messaging
- When decorating models with @publish to emit events on save
- When configuring django-outbox-pattern settings
- When writing event consumer callbacks with Payload handling
- When setting up RabbitMQ or STOMP broker connections
- When implementing idempotent event processing
- When creating custom serializer methods for outbox events
- When running the publish management command
- When writing subscriber handlers for incoming messages
- When ensuring data consistency across microservices
- When implementing webhook delivery with guaranteed delivery
- When working on event-driven architecture components
- When testing outbox entries with OutboxEntry model

# Backend Outbox

This Skill provides Claude Code with specific guidance on how to adhere to coding standards as they relate to how it should handle backend outbox.

## Instructions

For details, refer to the information provided in this file:
[backend outbox](../../../agent-os/standards/backend/outbox.md)
