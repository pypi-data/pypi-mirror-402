"""
Profile loader interface and mock implementation.

This module defines the abstract interface for loading user profiles from
the database, as well as a mock implementation for testing purposes.

The ProfileLoader is responsible for:
- Looking up user profiles by identity provider UID
- Loading user permissions from the database
- Supporting both email and phone number authentication flows

Consuming applications (like azkaban) should implement their own ProfileLoader
that queries their user/profile models.
"""

from abc import ABC, abstractmethod

from patronus.exceptions import NoProfileError
from patronus.user import UserProfile


class ProfileLoader(ABC):
    """
    Abstract interface for loading user profiles from database.

    Implementations of this class are responsible for looking up user
    profiles and permissions from the application database. The lookup
    can be done by uid, email, or phone_number depending on the
    authentication method used.

    Example implementation:
        class MyProfileLoader(ProfileLoader):
            def load_profile(
                self,
                uid: str,
                email: str | None = None,
                phone_number: str | None = None,
            ) -> UserProfile:
                user = User.objects.get(identity_provider_uid=uid)
                permissions = user.get_all_permissions()
                return UserProfile(
                    company_id=user.company_id,
                    permissions=frozenset(permissions),
                    profile_type=user.profile_type,
                )
    """

    @abstractmethod
    def load_profile(
        self,
        uid: str,
        email: str | None = None,
        phone_number: str | None = None,
    ) -> UserProfile:
        """
        Load user profile and permissions from database.

        Args:
            uid: The user's identity provider UID.
            email: The user's email (if authenticated via email).
            phone_number: The user's phone number (if authenticated via phone).

        Returns:
            UserProfile with company_id and permissions.

        Raises:
            NoProfileError: User has no profile in the system.
        """
        ...

    @abstractmethod
    async def load_profile_async(
        self,
        uid: str,
        email: str | None = None,
        phone_number: str | None = None,
    ) -> UserProfile:
        """
        Async version of load_profile.

        Args:
            uid: The user's identity provider UID.
            email: The user's email (if authenticated via email).
            phone_number: The user's phone number (if authenticated via phone).

        Returns:
            UserProfile with company_id and permissions.

        Raises:
            NoProfileError: User has no profile in the system.
        """
        ...


class MockProfileLoader(ProfileLoader):
    """
    Mock profile loader for testing without database.

    This implementation stores profiles in memory and is intended for
    testing purposes. It allows tests to set up specific profile scenarios
    without requiring a database connection.

    Example usage:
        loader = MockProfileLoader()
        loader.add_profile("user-123", UserProfile(
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        ))

        profile = loader.load_profile("user-123")
    """

    def __init__(self, profiles: dict[str, UserProfile] | None = None) -> None:
        """
        Initialize with optional predefined profiles.

        Args:
            profiles: Optional dict mapping uid to UserProfile.
        """
        self._profiles: dict[str, UserProfile] = profiles or {}

    def add_profile(self, uid: str, profile: UserProfile) -> None:
        """
        Add a profile for testing.

        Args:
            uid: The user's identity provider UID.
            profile: The UserProfile to associate with this uid.
        """
        self._profiles[uid] = profile

    def load_profile(
        self,
        uid: str,
        email: str | None = None,
        phone_number: str | None = None,
    ) -> UserProfile:
        """
        Load profile from in-memory store.

        Args:
            uid: The user's identity provider UID.
            email: The user's email (unused in mock, but required by interface).
            phone_number: The user's phone number (unused in mock).

        Returns:
            The UserProfile associated with the uid.

        Raises:
            NoProfileError: No profile found for the given uid.
        """
        if uid not in self._profiles:
            raise NoProfileError(f"No profile found for uid: {uid}")
        return self._profiles[uid]

    async def load_profile_async(
        self,
        uid: str,
        email: str | None = None,
        phone_number: str | None = None,
    ) -> UserProfile:
        """
        Async load from in-memory store.

        This implementation simply calls the sync method since the mock
        doesn't perform any I/O operations.

        Args:
            uid: The user's identity provider UID.
            email: The user's email (unused in mock).
            phone_number: The user's phone number (unused in mock).

        Returns:
            The UserProfile associated with the uid.

        Raises:
            NoProfileError: No profile found for the given uid.
        """
        return self.load_profile(uid, email, phone_number)
