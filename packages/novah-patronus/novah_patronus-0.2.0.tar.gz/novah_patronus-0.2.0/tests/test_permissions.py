"""
Tests for DRF permission classes.

This module tests the permission classes in patronus.permissions:
- HasProfile: Requires user to have a profile (be a NovahUser)
- HasPermission: Requires a specific permission
- HasAnyPermission: Requires any of a list of permissions
- IsSameCompany: Requires user to belong to same company as resource
"""

from dataclasses import dataclass
from unittest.mock import MagicMock
from uuid import uuid4

from patronus import NovahUser
from patronus.permissions import (
    HasAnyPermission,
    HasPermission,
    HasProfile,
    IsSameCompany,
)


class TestHasProfile:
    """Tests for HasProfile permission class."""

    def test_has_permission_returns_true_for_novah_user(
        self, sample_novah_user: NovahUser
    ) -> None:
        """HasProfile should return True when request.user is a NovahUser."""
        permission = HasProfile()
        request = MagicMock()
        request.user = sample_novah_user
        view = MagicMock()

        result = permission.has_permission(request, view)

        assert result is True

    def test_has_permission_returns_false_for_non_novah_user(self) -> None:
        """HasProfile should return False when request.user is not a NovahUser."""
        permission = HasProfile()
        request = MagicMock()
        request.user = MagicMock()  # Not a NovahUser
        view = MagicMock()

        result = permission.has_permission(request, view)

        assert result is False

    def test_has_permission_returns_false_for_anonymous_user(self) -> None:
        """HasProfile should return False for anonymous/unauthenticated users."""
        permission = HasProfile()
        request = MagicMock()
        request.user = None
        view = MagicMock()

        result = permission.has_permission(request, view)

        assert result is False

    def test_message_attribute(self) -> None:
        """HasProfile should have the correct error message."""
        permission = HasProfile()

        assert permission.message == "User profile is required."


class TestHasPermission:
    """Tests for HasPermission permission class."""

    def test_has_permission_returns_true_when_user_has_permission(
        self, sample_novah_user: NovahUser
    ) -> None:
        """HasPermission should return True when user has the required permission."""
        # sample_novah_user has permissions: frozenset(["read:patients", "write:patients"])
        permission = HasPermission("read:patients")
        request = MagicMock()
        request.user = sample_novah_user
        view = MagicMock()

        result = permission.has_permission(request, view)

        assert result is True

    def test_has_permission_returns_false_when_user_lacks_permission(
        self, sample_novah_user: NovahUser
    ) -> None:
        """HasPermission should return False when user lacks the required permission."""
        # sample_novah_user does NOT have "delete:patients" permission
        permission = HasPermission("delete:patients")
        request = MagicMock()
        request.user = sample_novah_user
        view = MagicMock()

        result = permission.has_permission(request, view)

        assert result is False

    def test_has_permission_returns_false_for_non_novah_user(self) -> None:
        """HasPermission should return False when request.user is not a NovahUser."""
        permission = HasPermission("read:patients")
        request = MagicMock()
        request.user = MagicMock()  # Not a NovahUser
        view = MagicMock()

        result = permission.has_permission(request, view)

        assert result is False

    def test_message_includes_required_permission(self) -> None:
        """HasPermission message should include the required permission name."""
        permission = HasPermission("read:patients")

        assert permission.message == "Permission 'read:patients' is required."


class TestHasAnyPermission:
    """Tests for HasAnyPermission permission class."""

    def test_has_permission_returns_true_when_user_has_any_permission(
        self, sample_novah_user: NovahUser
    ) -> None:
        """HasAnyPermission should return True when user has at least one permission."""
        # sample_novah_user has "read:patients" but not "admin:patients"
        permission = HasAnyPermission(["read:patients", "admin:patients"])
        request = MagicMock()
        request.user = sample_novah_user
        view = MagicMock()

        result = permission.has_permission(request, view)

        assert result is True

    def test_has_permission_returns_false_when_user_has_none(
        self, sample_novah_user: NovahUser
    ) -> None:
        """HasAnyPermission should return False when user has none of the permissions."""
        # sample_novah_user does NOT have any of these permissions
        permission = HasAnyPermission(["delete:patients", "admin:patients"])
        request = MagicMock()
        request.user = sample_novah_user
        view = MagicMock()

        result = permission.has_permission(request, view)

        assert result is False

    def test_has_permission_returns_false_for_non_novah_user(self) -> None:
        """HasAnyPermission should return False when request.user is not a NovahUser."""
        permission = HasAnyPermission(["read:patients", "write:patients"])
        request = MagicMock()
        request.user = MagicMock()  # Not a NovahUser
        view = MagicMock()

        result = permission.has_permission(request, view)

        assert result is False

    def test_message_includes_required_permissions(self) -> None:
        """HasAnyPermission message should include the list of required permissions."""
        permissions_list = ["read:patients", "admin:patients"]
        permission = HasAnyPermission(permissions_list)

        assert (
            permission.message == f"One of permissions {permissions_list} is required."
        )


class TestIsSameCompany:
    """Tests for IsSameCompany permission class."""

    def test_has_object_permission_returns_true_for_matching_company(
        self, sample_novah_user: NovahUser
    ) -> None:
        """IsSameCompany should return True when user and object have same company_id."""
        permission = IsSameCompany()
        request = MagicMock()
        request.user = sample_novah_user
        view = MagicMock()

        # Create an object with the same company_id as the user
        obj = MagicMock()
        obj.company_id = sample_novah_user.company_id

        result = permission.has_object_permission(request, view, obj)

        assert result is True

    def test_has_object_permission_returns_false_for_different_company(
        self, sample_novah_user: NovahUser
    ) -> None:
        """IsSameCompany should return False when user and object have different company_id."""
        permission = IsSameCompany()
        request = MagicMock()
        request.user = sample_novah_user
        view = MagicMock()

        # Create an object with a different company_id
        obj = MagicMock()
        obj.company_id = uuid4()  # Different from user's company_id

        result = permission.has_object_permission(request, view, obj)

        assert result is False

    def test_has_object_permission_returns_false_when_object_has_no_company_id(
        self, sample_novah_user: NovahUser
    ) -> None:
        """IsSameCompany should return False when object has no company_id attribute."""
        permission = IsSameCompany()
        request = MagicMock()
        request.user = sample_novah_user
        view = MagicMock()

        # Create an object without company_id attribute
        @dataclass
        class ObjectWithoutCompanyId:
            name: str

        obj = ObjectWithoutCompanyId(name="test")

        result = permission.has_object_permission(request, view, obj)

        assert result is False

    def test_has_object_permission_returns_false_for_non_novah_user(self) -> None:
        """IsSameCompany should return False when request.user is not a NovahUser."""
        permission = IsSameCompany()
        request = MagicMock()
        request.user = MagicMock()  # Not a NovahUser
        view = MagicMock()

        obj = MagicMock()
        obj.company_id = uuid4()

        result = permission.has_object_permission(request, view, obj)

        assert result is False

    def test_message_attribute(self) -> None:
        """IsSameCompany should have the correct error message."""
        permission = IsSameCompany()

        assert permission.message == "You do not have access to this resource."
