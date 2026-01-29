"""
Django REST Framework permission classes for Patronus.

This module provides DRF-compatible permission classes for authorization
checks based on NovahUser permissions and company membership.

All permission classes follow DRF conventions and integrate seamlessly
with DRF's permission checking system.
"""

from typing import TYPE_CHECKING, Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from patronus.user import NovahUser

if TYPE_CHECKING:
    from uuid import UUID


class HasProfile(BasePermission):
    """
    Permission class requiring user to have a profile.

    This is the most basic permission check - it simply requires that
    the request has an authenticated NovahUser. Use this as a base
    permission for endpoints that require authentication but no
    specific permissions.

    Example:
        class MyView(APIView):
            permission_classes = [HasProfile]
    """

    message = "User profile is required."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if the request has an authenticated NovahUser.

        Args:
            request: The DRF Request object.
            view: The view being accessed.

        Returns:
            True if request.user is a NovahUser, False otherwise.
        """
        user = request.user
        return isinstance(user, NovahUser)


class HasPermission(BasePermission):
    """
    Permission class requiring a specific permission.

    Use this to check for a single required permission. The permission
    is checked against the user's permission set.

    Example:
        class PatientDetailView(APIView):
            permission_classes = [HasPermission("read:patients")]
    """

    def __init__(self, permission: str) -> None:
        """
        Initialize with the required permission.

        Args:
            permission: The permission string to require.
        """
        self.permission = permission
        self.message = f"Permission '{permission}' is required."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if the user has the required permission.

        Args:
            request: The DRF Request object.
            view: The view being accessed.

        Returns:
            True if user has the permission, False otherwise.
        """
        user = request.user
        if not isinstance(user, NovahUser):
            return False
        return user.has_permission(self.permission)


class HasAnyPermission(BasePermission):
    """
    Permission class requiring any of the specified permissions.

    Use this when multiple permissions can grant access to a resource.
    The user only needs one of the listed permissions.

    Example:
        class PatientListView(APIView):
            permission_classes = [HasAnyPermission(["read:patients", "admin:patients"])]
    """

    def __init__(self, permissions: list[str]) -> None:
        """
        Initialize with the list of acceptable permissions.

        Args:
            permissions: List of permission strings, any of which grants access.
        """
        self.permissions = permissions
        self.message = f"One of permissions {permissions} is required."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if the user has any of the required permissions.

        Args:
            request: The DRF Request object.
            view: The view being accessed.

        Returns:
            True if user has at least one permission, False otherwise.
        """
        user = request.user
        if not isinstance(user, NovahUser):
            return False
        return user.has_any_permission(self.permissions)


class IsSameCompany(BasePermission):
    """
    Permission class requiring user to belong to the same company as the resource.

    This is an object-level permission that checks if the user's company_id
    matches the object's company_id. Use this for tenant isolation.

    The object must have a company_id attribute for this check to work.
    If the object doesn't have a company_id attribute, access is denied.

    Example:
        class PatientDetailView(RetrieveAPIView):
            permission_classes = [HasProfile, IsSameCompany]

            def get_object(self):
                obj = super().get_object()
                self.check_object_permissions(self.request, obj)
                return obj
    """

    message = "You do not have access to this resource."

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        """
        Check if the user belongs to the same company as the object.

        Args:
            request: The DRF Request object.
            view: The view being accessed.
            obj: The object being accessed.

        Returns:
            True if user's company_id matches object's company_id,
            False otherwise (including if object has no company_id).
        """
        user = request.user
        if not isinstance(user, NovahUser):
            return False

        # Object must have company_id attribute
        obj_company: UUID | None = getattr(obj, "company_id", None)
        if obj_company is None:
            return False

        return bool(user.company_id == obj_company)
