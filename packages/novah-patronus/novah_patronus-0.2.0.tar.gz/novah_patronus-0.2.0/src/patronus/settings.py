"""
Library settings and configuration management.

This module handles loading configuration from Django settings and provides
factory functions for creating provider and profile loader instances.

Configuration is loaded from the PATRONUS namespace in Django settings:

    PATRONUS = {
        "PROVIDER_CLASS": "patronus.providers.gcip.GCIPProvider",
        "PROVIDER_CREDENTIALS": {...},  # or path string, or None
        "PROFILE_LOADER_CLASS": "your_app.auth.YourProfileLoader",
        "CACHE_BACKEND": "default",  # Phase 2
        "CACHE_TIMEOUT": 300,  # Phase 2
    }
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.utils.module_loading import import_string

if TYPE_CHECKING:
    from patronus.profile_loader import ProfileLoader
    from patronus.providers.base import AuthProvider


@dataclass
class PatronusSettings:
    """
    Configuration container for Patronus settings.

    This dataclass holds all configuration options for the Patronus library.
    Default values are provided for all settings.

    Attributes:
        provider_class: Import path for the AuthProvider implementation.
        provider_credentials: Credentials for the provider (dict, path, or None).
        profile_loader_class: Import path for the ProfileLoader implementation.
        cache_backend: Django cache backend name (Phase 2).
        cache_timeout: Cache TTL in seconds (Phase 2).
    """

    provider_class: str = "patronus.providers.gcip.GCIPProvider"
    provider_credentials: dict[str, Any] | str | None = None
    profile_loader_class: str = "patronus.profile_loader.MockProfileLoader"
    cache_backend: str | None = None
    cache_timeout: int = 300


# Module-level cache for singleton instances
_settings: PatronusSettings | None = None
_provider: "AuthProvider | None" = None
_profile_loader: "ProfileLoader | None" = None


def get_settings() -> PatronusSettings:
    """
    Get Patronus settings from Django settings.

    Settings are loaded from the PATRONUS dict in Django settings.
    Missing keys use default values. The settings are cached after
    first load.

    Returns:
        PatronusSettings instance with configuration.

    Example:
        settings = get_settings()
        print(settings.provider_class)
    """
    global _settings

    if _settings is None:
        django_settings = getattr(settings, "PATRONUS", {})
        _settings = PatronusSettings(
            provider_class=django_settings.get(
                "PROVIDER_CLASS", PatronusSettings.provider_class
            ),
            provider_credentials=django_settings.get("PROVIDER_CREDENTIALS"),
            profile_loader_class=django_settings.get(
                "PROFILE_LOADER_CLASS", PatronusSettings.profile_loader_class
            ),
            cache_backend=django_settings.get("CACHE_BACKEND"),
            cache_timeout=django_settings.get(
                "CACHE_TIMEOUT", PatronusSettings.cache_timeout
            ),
        )

    return _settings


def get_provider() -> "AuthProvider":
    """
    Get or create the configured auth provider instance.

    The provider is lazily instantiated and cached for subsequent calls.
    The provider class is determined by the PROVIDER_CLASS setting.

    Returns:
        AuthProvider instance configured according to settings.

    Example:
        provider = get_provider()
        payload = provider.verify_token(token)
    """
    global _provider

    if _provider is None:
        patronus_settings = get_settings()
        provider_class = import_string(patronus_settings.provider_class)
        _provider = provider_class(patronus_settings.provider_credentials)

    return _provider


def get_profile_loader() -> "ProfileLoader":
    """
    Get or create the configured profile loader instance.

    The profile loader is lazily instantiated and cached for subsequent calls.
    The loader class is determined by the PROFILE_LOADER_CLASS setting.

    Returns:
        ProfileLoader instance configured according to settings.

    Example:
        loader = get_profile_loader()
        profile = loader.load_profile(uid="user-123")
    """
    global _profile_loader

    if _profile_loader is None:
        patronus_settings = get_settings()
        loader_class = import_string(patronus_settings.profile_loader_class)
        _profile_loader = loader_class()

    return _profile_loader


def reset_instances() -> None:
    """
    Reset cached instances.

    This clears all cached settings, provider, and profile loader instances.
    Essential for test isolation to ensure each test gets fresh instances.

    Example:
        # In test fixtures
        @pytest.fixture(autouse=True)
        def reset_patronus():
            yield
            reset_instances()
    """
    global _settings, _provider, _profile_loader
    _settings = None
    _provider = None
    _profile_loader = None
