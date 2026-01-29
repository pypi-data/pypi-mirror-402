"""
Shared test fixtures for Patronus test suite.

This module provides pytest fixtures used across all test modules.
The fixtures provide sample data objects and mock implementations
for testing without external dependencies.
"""

from uuid import uuid4

import django
import pytest
from django.conf import settings

# Configure Django settings before any Django imports
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "rest_framework",
        ],
        ROOT_URLCONF="tests.urls",
        SECRET_KEY="test-secret-key-not-for-production",
        USE_TZ=True,
        PATRONUS={},
    )
    django.setup()

from patronus import (
    MockProfileLoader,
    NovahUser,
    TokenPayload,
    UserProfile,
    reset_instances,
)


@pytest.fixture
def sample_token_payload() -> TokenPayload:
    """
    Create a sample TokenPayload for email-authenticated user.

    Returns:
        TokenPayload with email authentication data.
    """
    return TokenPayload(
        uid="test-uid-123",
        email="test@example.com",
        email_verified=True,
        phone_number=None,
        claims={"uid": "test-uid-123", "email": "test@example.com"},
    )


@pytest.fixture
def sample_phone_token_payload() -> TokenPayload:
    """
    Create a sample TokenPayload for phone-authenticated user.

    Returns:
        TokenPayload with phone authentication data.
    """
    return TokenPayload(
        uid="test-uid-456",
        email=None,
        email_verified=False,
        phone_number="+5511999999999",
        claims={"uid": "test-uid-456", "phone_number": "+5511999999999"},
    )


@pytest.fixture
def sample_company_id():
    """
    Create a sample company UUID.

    Returns:
        UUID for a sample company.
    """
    return uuid4()


@pytest.fixture
def sample_user_profile(sample_company_id) -> UserProfile:
    """
    Create a sample UserProfile.

    Returns:
        UserProfile with sample permissions.
    """
    return UserProfile(
        company_id=sample_company_id,
        permissions=frozenset(["read:patients", "write:patients"]),
        profile_type="colaborador",
    )


@pytest.fixture
def sample_novah_user(sample_user_profile) -> NovahUser:
    """
    Create a sample NovahUser for email-authenticated user.

    Returns:
        NovahUser with email authentication and sample permissions.
    """
    return NovahUser(
        identity_provider_uid="test-uid-123",
        email="test@example.com",
        phone_number=None,
        company_id=sample_user_profile.company_id,
        permissions=sample_user_profile.permissions,
        profile_type=sample_user_profile.profile_type,
    )


@pytest.fixture
def sample_phone_user(sample_user_profile) -> NovahUser:
    """
    Create a sample NovahUser for phone-authenticated user.

    Returns:
        NovahUser with phone authentication and sample permissions.
    """
    return NovahUser(
        identity_provider_uid="test-uid-456",
        email=None,
        phone_number="+5511999999999",
        company_id=sample_user_profile.company_id,
        permissions=sample_user_profile.permissions,
        profile_type=sample_user_profile.profile_type,
    )


@pytest.fixture
def admin_user_profile(sample_company_id) -> UserProfile:
    """
    Create an admin UserProfile with elevated permissions.

    Returns:
        UserProfile with admin-level permissions.
    """
    return UserProfile(
        company_id=sample_company_id,
        permissions=frozenset(
            [
                "read:patients",
                "write:patients",
                "delete:patients",
                "admin:company",
            ]
        ),
        profile_type="company_admin",
    )


@pytest.fixture
def mock_profile_loader(sample_user_profile) -> MockProfileLoader:
    """
    Create a MockProfileLoader with a sample profile.

    Returns:
        MockProfileLoader with pre-configured test profile.
    """
    loader = MockProfileLoader()
    loader.add_profile("test-uid-123", sample_user_profile)
    return loader


@pytest.fixture(autouse=True)
def reset_patronus_settings():
    """
    Reset Patronus settings between tests.

    This autouse fixture ensures test isolation by clearing
    all cached settings and instances after each test.
    """
    yield
    reset_instances()
