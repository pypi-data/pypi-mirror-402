## Django REST Framework API Standards

### URL Design
- **Plural Nouns**: Use plural resource names (e.g., `/api/users/`, `/api/products/`)
- **Trailing Slashes**: Always use trailing slashes (Django convention)
- **Versioning**: Use URL path versioning (`/api/v1/`, `/api/v2/`)
- **Nested Resources**: Limit to 2 levels max (e.g., `/api/posts/{id}/comments/`)
- **Actions**: Use ViewSet actions for non-CRUD operations (e.g., `@action(detail=True, methods=['post'])`)

### ViewSets and Views
- **Prefer ViewSets**: Use `ModelViewSet` or `ReadOnlyModelViewSet` for standard CRUD
- **Generic Views**: Use when you need more control than ViewSets (ListAPIView, RetrieveAPIView, etc.)
- **APIView**: Only use for completely custom logic
- **Action Methods**: Use `@action` decorator for custom endpoints on ViewSets
- **get_queryset**: Override to customize queryset (filtering, user-specific data)
- **get_serializer_class**: Override to use different serializers per action

### Serializers
- **ModelSerializer**: Default choice for model-based APIs
- **Nested Serializers**: Use for read operations, separate serializers for write operations
- **Read-Only Fields**: Use `read_only_fields` in Meta for computed/auto fields
- **Write-Only Fields**: Use `write_only=True` for password-like fields
- **Method Fields**: Use `SerializerMethodField` for computed data (prefix methods with `get_`)
- **Validation**: Use `validate_<field>` for field validation, `validate` for object-level validation
- **to_representation**: Override to customize output format
- **to_internal_value**: Override to customize input parsing

### Permissions
- **View-Level**: Set `permission_classes` at ViewSet/View level
- **Built-in**: Use `IsAuthenticated`, `IsAdminUser`, `AllowAny`, `IsAuthenticatedOrReadOnly`
- **Custom**: Create custom permission classes inheriting from `BasePermission`
- **Object-Level**: Implement `has_object_permission` for instance-specific rules
- **Composition**: Combine permissions with `&` (AND) and `|` (OR) operators

### Filtering, Pagination, Ordering
- **django-filter**: Use `DjangoFilterBackend` for complex filtering
- **SearchFilter**: Use for simple text search across fields
- **OrderingFilter**: Enable client-side ordering with `?ordering=field`
- **Pagination**: Set globally in settings or per-ViewSet with `pagination_class`
- **PageNumberPagination**: Default choice for most APIs
- **CursorPagination**: Use for large datasets or real-time data

### Response Standards
- **Status Codes**: Use DRF's status module (`status.HTTP_200_OK`, etc.)
- **Consistent Format**: Return consistent JSON structure across endpoints
- **Error Format**: Use DRF's default error format or customize via exception handler
```python
{
    "detail": "Error message",
    "field_name": ["Field-specific error"]
}
```

### Throttling
- **Set Globally**: Define in `REST_FRAMEWORK` settings
- **AnonRateThrottle**: For unauthenticated users
- **UserRateThrottle**: For authenticated users
- **ScopedRateThrottle**: For specific ViewSet/action throttling

### Authentication
- **TokenAuthentication**: Simple token-based auth
- **SessionAuthentication**: For same-origin browser clients
- **JWTAuthentication**: Use `djangorestframework-simplejwt` for JWT
- **Multiple Schemes**: Support multiple auth methods in `authentication_classes`

### Best Practices
- **Atomic Transactions**: Wrap create/update operations in `transaction.atomic()`
- **Validation**: Validate in serializers, not in views
- **Avoid N+1**: See `standards/backend/queries.md` for ORM optimization
- **Business Logic**: See `standards/global/conventions.md` for service layer pattern
- **Versioning**: Plan for API evolution from the start
- **Documentation**: Use drf-spectacular or drf-yasg for OpenAPI/Swagger docs
- **Testing**: Use `APITestCase` and `APIClient` for testing endpoints

### Avoid
- Don't put business logic in serializers (use services.py - see conventions.md)
- Don't use generic field names like `data`, `result` (be specific)
- Don't return different structures from the same endpoint
- Avoid deep nesting in serializers (keep it flat when possible)
