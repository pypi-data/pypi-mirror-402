# Product Mission

## Pitch

**Patronus** is a Python authentication library that helps Django developers in the Novah Care ecosystem implement secure, tenant-aware authentication and authorization by providing a provider-agnostic abstraction layer over identity management.

## Users

### Primary Customers

- **Novah Care Backend Developers:** Engineers building Django applications within the Novah Care ecosystem who need standardized authentication
- **Application Teams:** Teams maintaining services like "azkaban" that require consistent auth patterns across the platform

### User Personas

**Backend Developer** (Mid-level to Senior)
- **Role:** Django/DRF developer building internal services
- **Context:** Works on multiple microservices within the Novah Care ecosystem that all need to validate users and enforce permissions
- **Pain Points:** Repetitive auth boilerplate, inconsistent permission handling across services, tight coupling to specific identity providers
- **Goals:** Quickly integrate authentication without reinventing the wheel, maintain consistent security patterns, avoid vendor lock-in

**Platform Architect** (Senior/Staff)
- **Role:** Technical lead responsible for cross-cutting concerns
- **Context:** Needs to ensure all services follow security best practices and can evolve independently of infrastructure choices
- **Pain Points:** Vendor lock-in to identity providers, difficulty enforcing tenant isolation, inconsistent auth implementations
- **Goals:** Establish reusable patterns, enable future provider migrations, ensure multi-tenant security

## The Problem

### Authentication Fragmentation
Django applications in the Novah Care ecosystem currently implement authentication logic independently, leading to inconsistent security patterns, duplicated code, and tight coupling to Google Cloud Identity Platform (GCIP).

**Our Solution:** A centralized library that provides DRF-compatible authentication classes, permission checking, and tenant context injection with a clean abstraction over the identity provider.

### Vendor Lock-in Risk
Direct integration with GCIP throughout application code makes future migration to alternative identity providers costly and error-prone.

**Our Solution:** Provider abstraction layer that isolates all GCIP-specific code behind interfaces, allowing future provider swaps with zero changes to consuming applications.

### Multi-tenant Security Complexity
Ensuring proper tenant isolation (empresa_id) across requests requires careful implementation that is easy to get wrong.

**Our Solution:** Automatic tenant context injection via middleware and thread-local storage, making tenant-aware queries simple and secure.

## Differentiators

### Provider-Agnostic Architecture
Unlike direct GCIP integration, Patronus enforces zero identity provider imports in the public API. This results in the ability to migrate to a different IdP (Auth0, Keycloak, etc.) by implementing a single provider interface without touching application code.

### Django-Native Integration
Unlike generic auth libraries, Patronus provides first-class DRF authentication classes, permission classes, and middleware that feel native to Django developers. This results in faster integration and reduced learning curve.

### Performance-First Design
Unlike naive implementations, Patronus includes built-in caching for token validation (<50ms) and permission checks (<10ms). This results in minimal auth overhead even at scale.

## Key Features

### Core Features
- **JWT Token Validation:** Secure validation of GCIP tokens with automatic key rotation handling
- **DRF Authentication Class:** Drop-in authentication backend for Django REST Framework
- **Permission Classes:** Flexible permission checking integrated with DRF's permission system
- **Tenant Context Injection:** Automatic empresa_id extraction and thread-local storage for multi-tenant queries

### Developer Experience Features
- **NovahUser Abstraction:** Clean user object with identity attributes extracted from tokens
- **Permission Decorators:** Simple decorators for function-based views
- **Custom Exceptions:** Clear, actionable error types for auth failures

### Advanced Features
- **Permission Caching:** Configurable caching layer to minimize permission lookup latency
- **Async Support:** Optional async/await compatibility for high-concurrency scenarios
- **Provider Interface:** Abstract base class enabling custom identity provider implementations

## Design Principles

### 1. Abstraction Over Implementation
All identity provider-specific code must be isolated behind well-defined interfaces. The public API must never expose provider details.

### 2. Django Conventions First
Follow Django and DRF patterns wherever possible. Authentication classes, permission classes, and middleware should feel familiar to Django developers.

### 3. Secure by Default
Tenant isolation and permission checks should be automatic, not opt-in. Make the secure path the easy path.

### 4. Performance Aware
Cache aggressively where safe. Token validation and permission checks happen on every request - they must be fast.

### 5. Testability
The library must be easy to test and easy to mock. Provide test utilities for consuming applications.
