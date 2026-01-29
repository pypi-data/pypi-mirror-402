"""
Permission decorators for function-based views.

This module is a placeholder for Phase 2 implementation.

Phase 2 will include:
- @require_permission(permission) - Decorator requiring specific permission
- @require_any_permission(permissions) - Decorator requiring any of permissions
- @require_all_permissions(permissions) - Decorator requiring all permissions
- @require_profile - Decorator requiring authenticated NovahUser

These decorators will provide convenient permission checking for
function-based views (FBVs) as an alternative to class-based permission
classes.

Example (Phase 2):
    @api_view(["GET"])
    @require_permission("read:patients")
    def list_patients(request):
        return Response(...)

    @api_view(["POST"])
    @require_any_permission(["write:patients", "admin:patients"])
    def create_patient(request):
        return Response(...)
"""

# Phase 2 implementation will go here
