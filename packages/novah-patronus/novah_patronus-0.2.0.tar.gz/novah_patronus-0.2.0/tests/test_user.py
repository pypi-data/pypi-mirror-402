"""
Tests for user data models.

This module tests the TokenPayload, UserProfile, and NovahUser dataclasses
to ensure they work correctly and are immutable (frozen).
"""

from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from patronus import NovahUser, TokenPayload, UserProfile


class TestTokenPayload:
    """Tests for TokenPayload dataclass."""

    def test_creation_with_all_fields(self):
        """Test TokenPayload can be created with all required fields."""
        payload = TokenPayload(
            uid="user-123",
            email="test@example.com",
            email_verified=True,
            phone_number="+5511999999999",
            claims={"uid": "user-123", "custom_claim": "value"},
        )

        assert payload.uid == "user-123"
        assert payload.email == "test@example.com"
        assert payload.email_verified is True
        assert payload.phone_number == "+5511999999999"
        assert payload.claims == {"uid": "user-123", "custom_claim": "value"}

    def test_creation_with_none_values(self):
        """Test TokenPayload can be created with None for optional fields."""
        payload = TokenPayload(
            uid="user-456",
            email=None,
            email_verified=False,
            phone_number=None,
            claims={"uid": "user-456"},
        )

        assert payload.uid == "user-456"
        assert payload.email is None
        assert payload.email_verified is False
        assert payload.phone_number is None

    def test_is_immutable(self):
        """Test TokenPayload is frozen and cannot be modified."""
        payload = TokenPayload(
            uid="user-123",
            email="test@example.com",
            email_verified=True,
            phone_number=None,
            claims={},
        )

        with pytest.raises(FrozenInstanceError):
            payload.uid = "new-uid"

        with pytest.raises(FrozenInstanceError):
            payload.email = "new@example.com"


class TestUserProfile:
    """Tests for UserProfile dataclass."""

    def test_creation_with_all_fields(self):
        """Test UserProfile can be created with all required fields."""
        company_id = uuid4()
        permissions = frozenset(["read:patients", "write:patients"])

        profile = UserProfile(
            company_id=company_id,
            permissions=permissions,
            profile_type="colaborador",
        )

        assert profile.company_id == company_id
        assert profile.permissions == permissions
        assert profile.profile_type == "colaborador"

    def test_permissions_is_frozenset(self):
        """Test UserProfile permissions is a frozenset."""
        profile = UserProfile(
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="company_admin",
        )

        assert isinstance(profile.permissions, frozenset)

    def test_is_immutable(self):
        """Test UserProfile is frozen and cannot be modified."""
        profile = UserProfile(
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        with pytest.raises(FrozenInstanceError):
            profile.company_id = uuid4()

        with pytest.raises(FrozenInstanceError):
            profile.profile_type = "admin"


class TestNovahUser:
    """Tests for NovahUser dataclass."""

    def test_creation_with_all_fields(self):
        """Test NovahUser can be created with all required fields."""
        company_id = uuid4()
        permissions = frozenset(["read:patients", "write:patients"])

        user = NovahUser(
            identity_provider_uid="user-123",
            email="test@example.com",
            phone_number="+5511999999999",
            company_id=company_id,
            permissions=permissions,
            profile_type="colaborador",
        )

        assert user.identity_provider_uid == "user-123"
        assert user.email == "test@example.com"
        assert user.phone_number == "+5511999999999"
        assert user.company_id == company_id
        assert user.permissions == permissions
        assert user.profile_type == "colaborador"

    def test_is_authenticated_always_returns_true(self):
        """Test is_authenticated property always returns True."""
        user = NovahUser(
            identity_provider_uid="user-123",
            email="test@example.com",
            phone_number=None,
            company_id=uuid4(),
            permissions=frozenset(),
            profile_type="colaborador",
        )

        assert user.is_authenticated is True

    def test_is_authenticated_returns_true_for_phone_user(self):
        """Test is_authenticated returns True for phone-authenticated user."""
        user = NovahUser(
            identity_provider_uid="user-456",
            email=None,
            phone_number="+5511999999999",
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        assert user.is_authenticated is True

    def test_has_permission_returns_true_when_user_has_permission(self):
        """Test has_permission returns True when user has the permission."""
        user = NovahUser(
            identity_provider_uid="user-123",
            email="test@example.com",
            phone_number=None,
            company_id=uuid4(),
            permissions=frozenset(["read:patients", "write:patients"]),
            profile_type="colaborador",
        )

        assert user.has_permission("read:patients") is True
        assert user.has_permission("write:patients") is True

    def test_has_permission_returns_false_when_user_lacks_permission(self):
        """Test has_permission returns False when user lacks the permission."""
        user = NovahUser(
            identity_provider_uid="user-123",
            email="test@example.com",
            phone_number=None,
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        assert user.has_permission("delete:patients") is False
        assert user.has_permission("admin:company") is False

    def test_has_any_permission_returns_true_when_user_has_one(self):
        """Test has_any_permission returns True when user has at least one permission."""
        user = NovahUser(
            identity_provider_uid="user-123",
            email="test@example.com",
            phone_number=None,
            company_id=uuid4(),
            permissions=frozenset(["read:patients", "write:patients"]),
            profile_type="colaborador",
        )

        assert user.has_any_permission(["read:patients", "delete:patients"]) is True
        assert user.has_any_permission(["admin:company", "write:patients"]) is True

    def test_has_any_permission_returns_false_when_user_has_none(self):
        """Test has_any_permission returns False when user has none of the permissions."""
        user = NovahUser(
            identity_provider_uid="user-123",
            email="test@example.com",
            phone_number=None,
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        assert user.has_any_permission(["delete:patients", "admin:company"]) is False

    def test_has_any_permission_with_empty_list(self):
        """Test has_any_permission returns False with empty list."""
        user = NovahUser(
            identity_provider_uid="user-123",
            email="test@example.com",
            phone_number=None,
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        assert user.has_any_permission([]) is False

    def test_has_all_permissions_returns_true_when_user_has_all(self):
        """Test has_all_permissions returns True when user has all permissions."""
        user = NovahUser(
            identity_provider_uid="user-123",
            email="test@example.com",
            phone_number=None,
            company_id=uuid4(),
            permissions=frozenset(
                ["read:patients", "write:patients", "delete:patients"]
            ),
            profile_type="company_admin",
        )

        assert user.has_all_permissions(["read:patients", "write:patients"]) is True
        assert user.has_all_permissions(["read:patients"]) is True

    def test_has_all_permissions_returns_false_when_user_lacks_some(self):
        """Test has_all_permissions returns False when user lacks some permissions."""
        user = NovahUser(
            identity_provider_uid="user-123",
            email="test@example.com",
            phone_number=None,
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        assert user.has_all_permissions(["read:patients", "write:patients"]) is False

    def test_has_all_permissions_with_empty_list(self):
        """Test has_all_permissions returns True with empty list."""
        user = NovahUser(
            identity_provider_uid="user-123",
            email="test@example.com",
            phone_number=None,
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        # Empty set is a subset of any set
        assert user.has_all_permissions([]) is True

    def test_is_immutable(self):
        """Test NovahUser is frozen and cannot be modified."""
        user = NovahUser(
            identity_provider_uid="user-123",
            email="test@example.com",
            phone_number=None,
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        with pytest.raises(FrozenInstanceError):
            user.identity_provider_uid = "new-uid"

        with pytest.raises(FrozenInstanceError):
            user.email = "new@example.com"

        with pytest.raises(FrozenInstanceError):
            user.permissions = frozenset()
