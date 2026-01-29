---
name: backend-queries
description: Optimize Django ORM queries to prevent N+1 problems and improve database performance using select_related, prefetch_related, and efficient query patterns. Use this skill when writing QuerySet operations, optimizing slow database queries, using select_related or prefetch_related, implementing bulk operations, adding database indexes, using F expressions or Q objects, working with aggregations and annotations, or debugging query performance issues.
---

## When to use this skill:

- When writing Django ORM queries that involve related models
- When optimizing queries to prevent N+1 database problems
- When using select_related for ForeignKey/OneToOne joins
- When using prefetch_related for ManyToMany or reverse relations
- When implementing Prefetch objects for filtered prefetching
- When using only(), defer(), values(), or values_list() to limit fields
- When writing aggregate() or annotate() queries
- When using F expressions for database-level operations
- When building complex queries with Q objects
- When implementing bulk_create or bulk_update operations
- When using exists() or count() for efficient checks
- When adding db_index to model fields
- When using select_for_update for row locking
- When debugging slow queries with Django Debug Toolbar
- When using iterator() for large datasets

# Backend Queries

This Skill provides Claude Code with specific guidance on how to adhere to coding standards as they relate to how it should handle backend queries.

## Instructions

For details, refer to the information provided in this file:
[backend queries](../../../agent-os/standards/backend/queries.md)
