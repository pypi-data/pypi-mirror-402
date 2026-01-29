"""
Tests for ProfileLoader interface and MockProfileLoader implementation.

This module tests the abstract ProfileLoader interface and its mock
implementation to ensure they work correctly for testing purposes.
"""

from uuid import uuid4

import pytest

from patronus import MockProfileLoader, NoProfileError, ProfileLoader, UserProfile


class TestProfileLoaderInterface:
    """Tests for ProfileLoader abstract interface."""

    def test_profile_loader_is_abstract(self):
        """Test that ProfileLoader cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ProfileLoader()

    def test_profile_loader_has_required_abstract_methods(self):
        """Test that ProfileLoader defines required abstract methods."""
        # Check that the abstract methods exist
        assert hasattr(ProfileLoader, "load_profile")
        assert hasattr(ProfileLoader, "load_profile_async")

        # Verify they are abstract
        assert getattr(ProfileLoader.load_profile, "__isabstractmethod__", False)
        assert getattr(ProfileLoader.load_profile_async, "__isabstractmethod__", False)


class TestMockProfileLoader:
    """Tests for MockProfileLoader implementation."""

    def test_load_profile_returns_correct_profile(self):
        """Test MockProfileLoader.load_profile returns the correct profile for known uid."""
        company_id = uuid4()
        profile = UserProfile(
            company_id=company_id,
            permissions=frozenset(["read:patients", "write:patients"]),
            profile_type="colaborador",
        )

        loader = MockProfileLoader()
        loader.add_profile("user-123", profile)

        result = loader.load_profile("user-123")

        assert result == profile
        assert result.company_id == company_id
        assert result.permissions == frozenset(["read:patients", "write:patients"])
        assert result.profile_type == "colaborador"

    def test_load_profile_raises_no_profile_error_for_unknown_uid(self):
        """Test MockProfileLoader.load_profile raises NoProfileError for unknown uid."""
        loader = MockProfileLoader()

        with pytest.raises(NoProfileError) as exc_info:
            loader.load_profile("unknown-uid")

        assert "No profile found for uid: unknown-uid" in str(exc_info.value.detail)

    def test_add_profile_adds_profiles_correctly(self):
        """Test MockProfileLoader.add_profile adds profiles correctly."""
        profile1 = UserProfile(
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )
        profile2 = UserProfile(
            company_id=uuid4(),
            permissions=frozenset(["admin:company"]),
            profile_type="company_admin",
        )

        loader = MockProfileLoader()

        # Initially no profiles
        with pytest.raises(NoProfileError):
            loader.load_profile("user-1")

        # Add first profile
        loader.add_profile("user-1", profile1)
        assert loader.load_profile("user-1") == profile1

        # Add second profile
        loader.add_profile("user-2", profile2)
        assert loader.load_profile("user-2") == profile2

        # Both profiles accessible
        assert loader.load_profile("user-1") == profile1

    def test_add_profile_overwrites_existing_profile(self):
        """Test MockProfileLoader.add_profile overwrites existing profile for same uid."""
        profile_v1 = UserProfile(
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )
        profile_v2 = UserProfile(
            company_id=uuid4(),
            permissions=frozenset(["admin:company"]),
            profile_type="company_admin",
        )

        loader = MockProfileLoader()
        loader.add_profile("user-1", profile_v1)

        # Verify first profile
        assert loader.load_profile("user-1") == profile_v1

        # Overwrite with second profile
        loader.add_profile("user-1", profile_v2)

        # Should return updated profile
        assert loader.load_profile("user-1") == profile_v2

    @pytest.mark.asyncio
    async def test_load_profile_async_works_correctly(self):
        """Test MockProfileLoader.load_profile_async works correctly."""
        company_id = uuid4()
        profile = UserProfile(
            company_id=company_id,
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        loader = MockProfileLoader()
        loader.add_profile("user-123", profile)

        result = await loader.load_profile_async("user-123")

        assert result == profile
        assert result.company_id == company_id

    @pytest.mark.asyncio
    async def test_load_profile_async_raises_no_profile_error_for_unknown_uid(self):
        """Test MockProfileLoader.load_profile_async raises NoProfileError for unknown uid."""
        loader = MockProfileLoader()

        with pytest.raises(NoProfileError) as exc_info:
            await loader.load_profile_async("unknown-uid")

        assert "No profile found for uid: unknown-uid" in str(exc_info.value.detail)

    def test_load_profile_accepts_email_parameter(self):
        """Test load_profile accepts email parameter without error."""
        profile = UserProfile(
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        loader = MockProfileLoader()
        loader.add_profile("user-123", profile)

        # Should work with email parameter (even though mock doesn't use it)
        result = loader.load_profile("user-123", email="test@example.com")

        assert result == profile

    def test_load_profile_accepts_phone_number_parameter(self):
        """Test load_profile accepts phone_number parameter without error."""
        profile = UserProfile(
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        loader = MockProfileLoader()
        loader.add_profile("user-123", profile)

        # Should work with phone_number parameter (even though mock doesn't use it)
        result = loader.load_profile("user-123", phone_number="+5511999999999")

        assert result == profile

    def test_load_profile_accepts_all_parameters(self):
        """Test load_profile accepts uid, email, and phone_number parameters together."""
        profile = UserProfile(
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        loader = MockProfileLoader()
        loader.add_profile("user-123", profile)

        # Should work with all parameters
        result = loader.load_profile(
            uid="user-123",
            email="test@example.com",
            phone_number="+5511999999999",
        )

        assert result == profile

    def test_constructor_with_predefined_profiles(self):
        """Test MockProfileLoader can be initialized with predefined profiles."""
        profile1 = UserProfile(
            company_id=uuid4(),
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )
        profile2 = UserProfile(
            company_id=uuid4(),
            permissions=frozenset(["admin:company"]),
            profile_type="company_admin",
        )

        profiles = {
            "user-1": profile1,
            "user-2": profile2,
        }

        loader = MockProfileLoader(profiles=profiles)

        assert loader.load_profile("user-1") == profile1
        assert loader.load_profile("user-2") == profile2

    def test_constructor_with_none_profiles(self):
        """Test MockProfileLoader constructor handles None profiles argument."""
        loader = MockProfileLoader(profiles=None)

        with pytest.raises(NoProfileError):
            loader.load_profile("any-uid")

    def test_constructor_with_empty_profiles(self):
        """Test MockProfileLoader constructor handles empty profiles dict."""
        loader = MockProfileLoader(profiles={})

        with pytest.raises(NoProfileError):
            loader.load_profile("any-uid")

    def test_mock_profile_loader_is_profile_loader_subclass(self):
        """Test MockProfileLoader is a subclass of ProfileLoader."""
        assert issubclass(MockProfileLoader, ProfileLoader)

    def test_mock_profile_loader_instance_is_profile_loader(self):
        """Test MockProfileLoader instance is an instance of ProfileLoader."""
        loader = MockProfileLoader()
        assert isinstance(loader, ProfileLoader)
