# Django Standards Reference Guide

Quick reference for navigating the Python Django profile standards.

## 📂 Directory Structure

```
standards/
├── backend/        # Django backend standards
├── frontend/       # Frontend standards (if applicable)
├── global/         # Cross-cutting standards
└── testing/        # Testing standards
```

## 🎯 Quick Reference Map

### Backend Standards (`backend/`)

| File | Purpose | Key Topics |
|------|---------|------------|
| **models.md** | Django ORM & Models | Field types, relationships, Meta options, custom managers, validation |
| **api.md** | REST API (DRF) | ViewSets, serializers, permissions, filtering, pagination, throttling |
| **queries.md** | Query Optimization | select_related, prefetch_related, N+1 prevention, indexing |
| **migrations.md** | Database Migrations | Creating migrations, data migrations, rollback strategies |
| **outbox.md** | Event Outbox Pattern | django-outbox-pattern library, STOMP protocol, event publishing |

### Global Standards (`global/`)

| File | Purpose | Key Topics |
|------|---------|------------|
| **conventions.md** | Project Structure | Directory layout, service layer pattern, naming conventions |
| **tech-stack.md** | Technology Stack | **Poetry** (required), **Docker** (required), dependencies, tools |
| **coding-style.md** | Code Style | PEP 8, naming, imports, docstrings, formatting (black/isort) |
| **error-handling.md** | Exception Handling | Django exceptions, DRF exceptions, logging, custom errors |

### Testing Standards (`testing/`)

| File | Purpose | Key Topics |
|------|---------|------------|
| **test-writing.md** | Testing Practices | pytest-django, factories, API testing, mocking, test configuration |

## 🔑 Single Sources of Truth

To avoid duplication, these files are the authoritative sources for specific topics:

- **Poetry & Docker setup** → `global/tech-stack.md`
- **Service layer pattern** → `global/conventions.md`
- **ORM optimization** → `backend/queries.md`
- **DRF API patterns** → `backend/api.md`

## 🚀 Quick Start

**New to the project?** Read in this order:
1. `global/tech-stack.md` - Understand required tools (Poetry, Docker)
2. `global/conventions.md` - Learn project structure and patterns
3. `backend/api.md` - DRF API standards
4. `backend/models.md` - Django model best practices

**Building a feature?** Reference:
1. `global/conventions.md` - Service layer pattern
2. `backend/queries.md` - Optimize your queries
3. `backend/api.md` - Build your endpoints
4. `testing/test-writing.md` - Write tests

## 📋 Required Tools

All Django projects **must** use:
- ✅ **Poetry** for dependency management
- ✅ **Docker** for containerization

See `global/tech-stack.md` for complete setup instructions.

## 🔗 Cross-References

Files frequently reference each other to avoid duplication:
- API standards reference query optimization and service layer
- Models reference query optimization
- All files reference tech-stack.md for Poetry/Docker
- All files reference conventions.md for service layer pattern
