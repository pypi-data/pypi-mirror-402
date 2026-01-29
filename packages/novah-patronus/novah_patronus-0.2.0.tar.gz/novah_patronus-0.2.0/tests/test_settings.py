"""
Tests for library settings and configuration management.

This module tests the PatronusSettings dataclass and the settings loading
functions that provide configuration from Django settings.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.test import override_settings

from patronus import (
    MockProfileLoader,
    PatronusSettings,
    ProfileLoader,
    UserProfile,
    get_profile_loader,
    get_provider,
    get_settings,
    reset_instances,
)
from patronus.providers import AuthProvider


class TestPatronusSettingsDataclass:
    """Tests for PatronusSettings dataclass."""

    def test_default_values(self):
        """Test PatronusSettings has correct default values."""
        settings = PatronusSettings()

        assert settings.provider_class == "patronus.providers.gcip.GCIPProvider"
        assert settings.provider_credentials is None
        assert (
            settings.profile_loader_class == "patronus.profile_loader.MockProfileLoader"
        )
        assert settings.cache_backend is None
        assert settings.cache_timeout == 300

    def test_custom_values(self):
        """Test PatronusSettings can be created with custom values."""
        creds = {"type": "service_account", "project_id": "test"}

        settings = PatronusSettings(
            provider_class="custom.provider.MyProvider",
            provider_credentials=creds,
            profile_loader_class="custom.loader.MyLoader",
            cache_backend="default",
            cache_timeout=600,
        )

        assert settings.provider_class == "custom.provider.MyProvider"
        assert settings.provider_credentials == creds
        assert settings.profile_loader_class == "custom.loader.MyLoader"
        assert settings.cache_backend == "default"
        assert settings.cache_timeout == 600

    def test_provider_credentials_can_be_string_path(self):
        """Test provider_credentials can be a file path string."""
        settings = PatronusSettings(provider_credentials="/path/to/credentials.json")

        assert settings.provider_credentials == "/path/to/credentials.json"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_returns_defaults_when_no_django_config(self):
        """Test get_settings returns defaults when PATRONUS is empty dict."""
        # Reset to ensure fresh state
        reset_instances()

        with override_settings(PATRONUS={}):
            settings = get_settings()

            assert settings.provider_class == "patronus.providers.gcip.GCIPProvider"
            assert settings.provider_credentials is None
            assert (
                settings.profile_loader_class
                == "patronus.profile_loader.MockProfileLoader"
            )
            assert settings.cache_backend is None
            assert settings.cache_timeout == 300

    def test_loads_from_django_patronus_namespace(self):
        """Test get_settings loads configuration from Django PATRONUS namespace."""
        reset_instances()

        custom_config = {
            "PROVIDER_CLASS": "custom.provider.TestProvider",
            "PROVIDER_CREDENTIALS": {"key": "value"},
            "PROFILE_LOADER_CLASS": "custom.loader.TestLoader",
            "CACHE_BACKEND": "redis",
            "CACHE_TIMEOUT": 600,
        }

        with override_settings(PATRONUS=custom_config):
            settings = get_settings()

            assert settings.provider_class == "custom.provider.TestProvider"
            assert settings.provider_credentials == {"key": "value"}
            assert settings.profile_loader_class == "custom.loader.TestLoader"
            assert settings.cache_backend == "redis"
            assert settings.cache_timeout == 600

    def test_partial_config_uses_defaults_for_missing_keys(self):
        """Test get_settings uses defaults for missing configuration keys."""
        reset_instances()

        partial_config = {
            "PROVIDER_CLASS": "custom.provider.PartialProvider",
            # Missing other keys
        }

        with override_settings(PATRONUS=partial_config):
            settings = get_settings()

            assert settings.provider_class == "custom.provider.PartialProvider"
            # These should use defaults
            assert settings.provider_credentials is None
            assert (
                settings.profile_loader_class
                == "patronus.profile_loader.MockProfileLoader"
            )
            assert settings.cache_backend is None
            assert settings.cache_timeout == 300

    def test_settings_are_cached_singleton_pattern(self):
        """Test get_settings returns cached instance (singleton pattern)."""
        reset_instances()

        with override_settings(PATRONUS={"CACHE_TIMEOUT": 999}):
            settings1 = get_settings()
            settings2 = get_settings()

            # Should return the same cached instance
            assert settings1 is settings2
            assert settings1.cache_timeout == 999

    def test_cached_settings_not_affected_by_config_change(self):
        """Test cached settings are not affected by Django config changes."""
        reset_instances()

        with override_settings(PATRONUS={"CACHE_TIMEOUT": 111}):
            settings1 = get_settings()
            assert settings1.cache_timeout == 111

        # Even with new settings, cached value remains
        with override_settings(PATRONUS={"CACHE_TIMEOUT": 222}):
            settings2 = get_settings()
            # Still returns the cached instance with old value
            assert settings2.cache_timeout == 111
            assert settings1 is settings2


class TestGetProvider:
    """Tests for get_provider function."""

    def test_returns_configured_provider_instance(self):
        """Test get_provider returns the configured provider instance."""
        reset_instances()

        # Use MockProfileLoader class path with a mock provider
        with (
            override_settings(
                PATRONUS={
                    "PROFILE_LOADER_CLASS": "patronus.profile_loader.MockProfileLoader",
                }
            ),
            patch("patronus.settings.import_string") as mock_import,
        ):
            # We need to mock the provider creation since GCIPProvider needs Firebase
            mock_provider_class = MagicMock()
            mock_provider_instance = MagicMock(spec=AuthProvider)
            mock_provider_class.return_value = mock_provider_instance

            # First call returns provider class, subsequent returns other classes
            mock_import.return_value = mock_provider_class

            provider = get_provider()

            assert provider is mock_provider_instance
            mock_provider_class.assert_called_once_with(
                None
            )  # credentials is None by default

    def test_provider_is_cached(self):
        """Test get_provider returns cached instance on subsequent calls."""
        reset_instances()

        with (
            override_settings(PATRONUS={}),
            patch("patronus.settings.import_string") as mock_import,
        ):
            mock_provider_class = MagicMock()
            mock_provider_instance = MagicMock(spec=AuthProvider)
            mock_provider_class.return_value = mock_provider_instance
            mock_import.return_value = mock_provider_class

            provider1 = get_provider()
            provider2 = get_provider()

            # Should be the same cached instance
            assert provider1 is provider2
            # Provider class should only be called once
            mock_provider_class.assert_called_once()

    def test_provider_receives_credentials_from_settings(self):
        """Test get_provider passes credentials from settings to provider."""
        reset_instances()

        creds = {"type": "service_account", "project_id": "test"}

        with (
            override_settings(PATRONUS={"PROVIDER_CREDENTIALS": creds}),
            patch("patronus.settings.import_string") as mock_import,
        ):
            mock_provider_class = MagicMock()
            mock_provider_instance = MagicMock(spec=AuthProvider)
            mock_provider_class.return_value = mock_provider_instance
            mock_import.return_value = mock_provider_class

            get_provider()

            mock_provider_class.assert_called_once_with(creds)


class TestGetProfileLoader:
    """Tests for get_profile_loader function."""

    def test_returns_configured_loader_instance(self):
        """Test get_profile_loader returns the configured loader instance."""
        reset_instances()

        with override_settings(
            PATRONUS={
                "PROFILE_LOADER_CLASS": "patronus.profile_loader.MockProfileLoader",
            }
        ):
            loader = get_profile_loader()

            assert isinstance(loader, MockProfileLoader)
            assert isinstance(loader, ProfileLoader)

    def test_profile_loader_is_cached(self):
        """Test get_profile_loader returns cached instance on subsequent calls."""
        reset_instances()

        with override_settings(
            PATRONUS={
                "PROFILE_LOADER_CLASS": "patronus.profile_loader.MockProfileLoader",
            }
        ):
            loader1 = get_profile_loader()
            loader2 = get_profile_loader()

            # Should be the same cached instance
            assert loader1 is loader2

    def test_default_loader_is_mock_profile_loader(self):
        """Test default profile loader is MockProfileLoader."""
        reset_instances()

        with override_settings(PATRONUS={}):
            loader = get_profile_loader()

            assert isinstance(loader, MockProfileLoader)


class TestResetInstances:
    """Tests for reset_instances function."""

    def test_clears_cached_settings(self):
        """Test reset_instances clears cached settings."""
        with override_settings(PATRONUS={"CACHE_TIMEOUT": 111}):
            settings1 = get_settings()
            assert settings1.cache_timeout == 111

        reset_instances()

        with override_settings(PATRONUS={"CACHE_TIMEOUT": 222}):
            settings2 = get_settings()
            # After reset, should get new settings
            assert settings2.cache_timeout == 222
            assert settings1 is not settings2

    def test_clears_cached_provider(self):
        """Test reset_instances clears cached provider."""
        with (
            override_settings(PATRONUS={}),
            patch("patronus.settings.import_string") as mock_import,
        ):
            mock_provider_class = MagicMock()
            mock_import.return_value = mock_provider_class

            get_provider()

            reset_instances()

            get_provider()

            # Provider class should be instantiated twice (once before reset, once after)
            assert mock_provider_class.call_count == 2

    def test_clears_cached_profile_loader(self):
        """Test reset_instances clears cached profile loader."""
        with override_settings(
            PATRONUS={
                "PROFILE_LOADER_CLASS": "patronus.profile_loader.MockProfileLoader",
            }
        ):
            loader1 = get_profile_loader()

            reset_instances()

            loader2 = get_profile_loader()

            # Should be different instances after reset
            assert loader1 is not loader2

    def test_clears_all_cached_instances(self):
        """Test reset_instances clears all cached instances at once."""
        with (
            override_settings(
                PATRONUS={
                    "CACHE_TIMEOUT": 999,
                    "PROFILE_LOADER_CLASS": "patronus.profile_loader.MockProfileLoader",
                }
            ),
            patch("patronus.settings.import_string") as mock_import,
        ):
            mock_provider_class = MagicMock()

            # Use side_effect to return new MockProfileLoader instance each time
            def import_side_effect(path):
                if "provider" in path.lower() or "gcip" in path.lower():
                    return mock_provider_class
                # Return a class that creates new instances
                return MockProfileLoader

            mock_import.side_effect = import_side_effect

            settings1 = get_settings()
            loader1 = get_profile_loader()

            reset_instances()

            settings2 = get_settings()
            loader2 = get_profile_loader()

            # All should be different instances after reset
            assert settings1 is not settings2
            assert loader1 is not loader2

    def test_enables_test_isolation(self):
        """Test reset_instances enables proper test isolation."""
        # Simulate first test configuring settings
        with override_settings(PATRONUS={"CACHE_TIMEOUT": 100}):
            first_test_settings = get_settings()
            assert first_test_settings.cache_timeout == 100

        # Simulate cleanup between tests
        reset_instances()

        # Simulate second test with different config
        with override_settings(PATRONUS={"CACHE_TIMEOUT": 200}):
            second_test_settings = get_settings()
            # Second test should get its own configuration
            assert second_test_settings.cache_timeout == 200
            # Should not be affected by first test's cached settings
            assert second_test_settings is not first_test_settings


class TestSettingsIntegration:
    """Integration tests for settings working together."""

    def test_mock_profile_loader_can_be_used_after_settings_load(self):
        """Test MockProfileLoader works correctly when loaded via settings."""
        reset_instances()

        with override_settings(
            PATRONUS={
                "PROFILE_LOADER_CLASS": "patronus.profile_loader.MockProfileLoader",
            }
        ):
            loader = get_profile_loader()

            # Add a profile and verify it works
            profile = UserProfile(
                company_id=uuid4(),
                permissions=frozenset(["read:data"]),
                profile_type="test",
            )
            loader.add_profile("test-uid", profile)

            result = loader.load_profile("test-uid")
            assert result == profile

    def test_settings_provider_and_loader_work_together(self):
        """Test settings, provider, and loader can be configured together."""
        reset_instances()

        config = {
            "PROVIDER_CLASS": "patronus.providers.gcip.GCIPProvider",
            "PROVIDER_CREDENTIALS": None,
            "PROFILE_LOADER_CLASS": "patronus.profile_loader.MockProfileLoader",
            "CACHE_BACKEND": "default",
            "CACHE_TIMEOUT": 600,
        }

        with override_settings(PATRONUS=config):
            settings = get_settings()

            assert settings.provider_class == config["PROVIDER_CLASS"]
            assert settings.profile_loader_class == config["PROFILE_LOADER_CLASS"]
            assert settings.cache_backend == config["CACHE_BACKEND"]
            assert settings.cache_timeout == config["CACHE_TIMEOUT"]

            # Profile loader should be accessible
            loader = get_profile_loader()
            assert isinstance(loader, MockProfileLoader)
