# Product Roadmap

## Phase 1: Core Authentication (Must-Have)

1. [x] Provider Interface — Define abstract base class for identity providers with methods for token validation and user extraction `S`
2. [x] GCIP Provider Implementation — Implement the provider interface using firebase-admin SDK for JWT validation against GCIP `M`
3. [x] NovahUser Model — Create user abstraction class that holds identity attributes (user_id, email, empresa_id, roles) extracted from tokens `S`
4. [x] Custom Exceptions — Implement authentication and authorization exception classes (InvalidTokenError, ExpiredTokenError, PermissionDeniedError, TenantMismatchError) `XS`
5. [x] Library Settings — Create settings module with Django settings integration for configuring provider, cache backend, and other options `S`
6. [x] DRF Authentication Class — Implement PatronusAuthentication class that validates JWT tokens and returns NovahUser instances `M`
7. [x] Tenant Context Manager — Build thread-local storage for empresa_id with context manager for safe access across the request lifecycle `S`
8. [x] Tenant Middleware — Create Django middleware that extracts empresa_id from authenticated user and injects into tenant context `S`
9. [x] DRF Permission Classes — Implement HasPermission and HasAnyPermission classes that check user permissions against required permissions `M`
10. [x] Integration Testing — End-to-end tests validating complete auth flow from token to permission check with mocked GCIP responses `M`

## Phase 2: Enhanced Features (Should-Have)

11. [ ] Permission Caching — Implement configurable cache layer for permission lookups with Django cache backend support and TTL configuration `M`
12. [ ] Permission Decorators — Create @require_permission and @require_any_permission decorators for function-based views `S`
13. [ ] Token Caching — Add caching layer for validated tokens to achieve <50ms validation latency on cache hits `S`
14. [ ] Test Utilities — Provide mock authentication helpers and fixtures for consuming applications to use in their test suites `M`
15. [ ] Documentation — Comprehensive usage documentation with integration examples for common patterns `M`

## Phase 3: Future Enhancements (Could-Have)

16. [ ] Async Authentication — Implement async-compatible authentication class for use with Django async views and ASGI `L`
17. [ ] Async Permission Checking — Async versions of permission classes and decorators `M`
18. [ ] Alternative Provider Template — Example implementation skeleton for migrating to a different IdP (Auth0/Keycloak) `S`
19. [ ] Audit Logging — Optional audit trail for authentication and authorization events `M`
20. [ ] Rate Limiting Integration — Hooks for integrating with rate limiting based on user/tenant identity `S`

> Notes
> - Order items by technical dependencies and product architecture
> - Each item should represent an end-to-end functional and testable feature
> - Phase 1 delivers a complete, production-ready authentication solution
> - Phase 2 adds performance optimizations and developer experience improvements
> - Phase 3 enables future scalability and provider flexibility
