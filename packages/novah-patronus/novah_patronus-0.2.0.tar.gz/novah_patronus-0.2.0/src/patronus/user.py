"""
User models and data transfer objects for Patronus authentication.

This module contains the core data models used throughout the authentication flow:
- TokenPayload: Raw data extracted from JWT tokens
- UserProfile: User profile data loaded from the database
- NovahUser: The authenticated user object with permissions
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class TokenPayload:
    """
    Raw token data extracted from JWT.

    This dataclass holds the decoded token information from the identity provider.
    It is immutable (frozen) to ensure token data cannot be modified after extraction.

    Attributes:
        uid: The user's unique identifier from the identity provider.
        email: The user's email address, if available.
        email_verified: Whether the email has been verified by the provider.
        phone_number: The user's phone number, if available (for passwordless auth).
        claims: The complete set of claims from the JWT token.
    """

    uid: str
    email: str | None
    email_verified: bool
    phone_number: str | None
    claims: dict[str, Any]


@dataclass(frozen=True)
class UserProfile:
    """
    User profile loaded from the database.

    This dataclass holds the user's profile information including their
    company association and permissions. It is loaded by a ProfileLoader
    implementation.

    Attributes:
        company_id: The UUID of the company the user belongs to.
        permissions: A frozen set of permission strings the user has.
        profile_type: The type of user profile (e.g., "company_admin", "colaborador").
    """

    company_id: UUID
    permissions: frozenset[str]
    profile_type: str


@dataclass(frozen=True)
class NovahUser:
    """
    Authenticated user with identity and permissions.

    This is the main user object that represents an authenticated user in the
    Patronus system. It combines identity information from the token with
    profile/permission data from the database.

    The class is immutable (frozen) and provides convenience methods for
    permission checking. It is designed to be compatible with Django's
    authentication system expectations.

    Attributes:
        identity_provider_uid: The user's unique identifier from the identity provider.
        email: The user's email address, if available.
        phone_number: The user's phone number, if available.
        company_id: The UUID of the company the user belongs to.
        permissions: A frozen set of permission strings the user has.
        profile_type: The type of user profile.

    Example:
        user = NovahUser(
            identity_provider_uid="abc123",
            email="user@example.com",
            phone_number=None,
            company_id=uuid4(),
            permissions=frozenset(["read:patients", "write:patients"]),
            profile_type="colaborador",
        )

        if user.has_permission("read:patients"):
            # Allow access
            pass
    """

    identity_provider_uid: str
    email: str | None
    phone_number: str | None
    company_id: UUID
    permissions: frozenset[str]
    profile_type: str

    @property
    def is_authenticated(self) -> bool:
        """
        Check if the user is authenticated.

        Django compatibility property - always returns True for NovahUser instances,
        as the existence of a NovahUser object implies successful authentication.

        Returns:
            True, always.
        """
        return True

    def has_permission(self, permission: str) -> bool:
        """
        Check if the user has a specific permission.

        Args:
            permission: The permission string to check.

        Returns:
            True if the user has the permission, False otherwise.
        """
        return permission in self.permissions

    def has_any_permission(self, permissions: list[str]) -> bool:
        """
        Check if the user has any of the specified permissions.

        Args:
            permissions: A list of permission strings to check.

        Returns:
            True if the user has at least one of the permissions, False otherwise.
        """
        return bool(self.permissions & set(permissions))

    def has_all_permissions(self, permissions: list[str]) -> bool:
        """
        Check if the user has all of the specified permissions.

        Args:
            permissions: A list of permission strings to check.

        Returns:
            True if the user has all of the permissions, False otherwise.
        """
        return set(permissions) <= self.permissions
