"""
Tests for DRF authentication class.

This module tests the PatronusAuthentication class which integrates
with DRF's authentication system to validate tokens and create NovahUser
instances.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from patronus import (
    InvalidTokenError,
    MockProfileLoader,
    NoProfileError,
    NovahUser,
    TokenPayload,
    UserProfile,
    reset_instances,
)
from patronus.authentication import PatronusAuthentication


class TestPatronusAuthenticationReturnsNone:
    """Tests for cases where authentication should return None."""

    def test_returns_none_for_missing_authorization_header(self):
        """Test authenticate returns None when Authorization header is missing."""
        reset_instances()

        factory = APIRequestFactory()
        request = factory.get("/test/")
        drf_request = Request(request)

        auth = PatronusAuthentication()
        result = auth.authenticate(drf_request)

        assert result is None

    def test_returns_none_for_empty_authorization_header(self):
        """Test authenticate returns None when Authorization header is empty."""
        reset_instances()

        factory = APIRequestFactory()
        request = factory.get("/test/", HTTP_AUTHORIZATION="")
        drf_request = Request(request)

        auth = PatronusAuthentication()
        result = auth.authenticate(drf_request)

        assert result is None

    def test_returns_none_for_non_bearer_auth_scheme(self):
        """Test authenticate returns None for non-Bearer authentication schemes."""
        reset_instances()

        factory = APIRequestFactory()
        # Test with Basic auth
        request = factory.get("/test/", HTTP_AUTHORIZATION="Basic dXNlcjpwYXNz")
        drf_request = Request(request)

        auth = PatronusAuthentication()
        result = auth.authenticate(drf_request)

        assert result is None

    def test_returns_none_for_malformed_bearer_header(self):
        """Test authenticate returns None for malformed Bearer header."""
        reset_instances()

        factory = APIRequestFactory()
        # Test with just 'Bearer' without token
        request = factory.get("/test/", HTTP_AUTHORIZATION="Bearer")
        drf_request = Request(request)

        auth = PatronusAuthentication()
        result = auth.authenticate(drf_request)

        assert result is None

    def test_returns_none_for_too_many_parts_in_header(self):
        """Test authenticate returns None when header has too many parts."""
        reset_instances()

        factory = APIRequestFactory()
        # Test with extra parts in the header
        request = factory.get("/test/", HTTP_AUTHORIZATION="Bearer token extra_part")
        drf_request = Request(request)

        auth = PatronusAuthentication()
        result = auth.authenticate(drf_request)

        assert result is None


class TestPatronusAuthenticationSuccess:
    """Tests for successful authentication scenarios."""

    def test_returns_novah_user_and_token_payload_for_valid_token(self):
        """Test authenticate returns (NovahUser, TokenPayload) for valid token."""
        reset_instances()
        company_id = uuid4()

        # Create test data
        token_payload = TokenPayload(
            uid="test-uid-123",
            email="test@example.com",
            email_verified=True,
            phone_number=None,
            claims={"uid": "test-uid-123", "email": "test@example.com"},
        )

        user_profile = UserProfile(
            company_id=company_id,
            permissions=frozenset(["read:patients", "write:patients"]),
            profile_type="colaborador",
        )

        # Create mocks
        mock_provider = MagicMock()
        mock_provider.verify_token.return_value = token_payload

        mock_loader = MockProfileLoader()
        mock_loader.add_profile("test-uid-123", user_profile)

        # Create request
        factory = APIRequestFactory()
        request = factory.get("/test/", HTTP_AUTHORIZATION="Bearer valid-token")
        drf_request = Request(request)

        # Patch the settings functions
        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            auth = PatronusAuthentication()
            result = auth.authenticate(drf_request)

        assert result is not None
        user, auth_token = result

        # Verify user is a NovahUser with correct attributes
        assert isinstance(user, NovahUser)
        assert user.identity_provider_uid == "test-uid-123"
        assert user.email == "test@example.com"
        assert user.phone_number is None
        assert user.company_id == company_id
        assert user.permissions == frozenset(["read:patients", "write:patients"])
        assert user.profile_type == "colaborador"

        # Verify token payload is returned
        assert auth_token is token_payload

        # Verify provider was called with the token
        mock_provider.verify_token.assert_called_once_with("valid-token")

    def test_authenticates_phone_number_user(self):
        """Test authenticate works for phone number authenticated users."""
        reset_instances()
        company_id = uuid4()

        # Create test data for phone auth
        token_payload = TokenPayload(
            uid="test-uid-456",
            email=None,
            email_verified=False,
            phone_number="+5511999999999",
            claims={"uid": "test-uid-456", "phone_number": "+5511999999999"},
        )

        user_profile = UserProfile(
            company_id=company_id,
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        # Create mocks
        mock_provider = MagicMock()
        mock_provider.verify_token.return_value = token_payload

        mock_loader = MockProfileLoader()
        mock_loader.add_profile("test-uid-456", user_profile)

        # Create request
        factory = APIRequestFactory()
        request = factory.get("/test/", HTTP_AUTHORIZATION="Bearer phone-auth-token")
        drf_request = Request(request)

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            auth = PatronusAuthentication()
            result = auth.authenticate(drf_request)

        assert result is not None
        user, _ = result

        assert user.email is None
        assert user.phone_number == "+5511999999999"
        assert user.identity_provider_uid == "test-uid-456"


class TestPatronusAuthenticationErrors:
    """Tests for authentication error scenarios."""

    def test_raises_invalid_token_error_for_invalid_token(self):
        """Test authenticate raises InvalidTokenError for invalid tokens."""
        reset_instances()

        # Create mock provider that raises InvalidTokenError
        mock_provider = MagicMock()
        mock_provider.verify_token.side_effect = InvalidTokenError("Invalid token")

        # Create request
        factory = APIRequestFactory()
        request = factory.get("/test/", HTTP_AUTHORIZATION="Bearer invalid-token")
        drf_request = Request(request)

        with patch("patronus.authentication.get_provider", return_value=mock_provider):
            auth = PatronusAuthentication()

            with pytest.raises(InvalidTokenError):
                auth.authenticate(drf_request)

        # Verify provider was called
        mock_provider.verify_token.assert_called_once_with("invalid-token")

    def test_raises_no_profile_error_when_profile_not_found(self):
        """Test authenticate raises NoProfileError when user profile not found."""
        reset_instances()

        # Create valid token payload
        token_payload = TokenPayload(
            uid="unknown-uid",
            email="unknown@example.com",
            email_verified=True,
            phone_number=None,
            claims={"uid": "unknown-uid"},
        )

        # Create mock provider that returns valid token
        mock_provider = MagicMock()
        mock_provider.verify_token.return_value = token_payload

        # Create empty profile loader (no profiles)
        mock_loader = MockProfileLoader()

        # Create request
        factory = APIRequestFactory()
        request = factory.get("/test/", HTTP_AUTHORIZATION="Bearer valid-token")
        drf_request = Request(request)

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            auth = PatronusAuthentication()

            with pytest.raises(NoProfileError):
                auth.authenticate(drf_request)


class TestPatronusAuthenticationHeader:
    """Tests for authenticate_header method."""

    def test_authenticate_header_returns_bearer(self):
        """Test authenticate_header returns 'Bearer' keyword."""
        auth = PatronusAuthentication()

        factory = APIRequestFactory()
        request = factory.get("/test/")
        drf_request = Request(request)

        result = auth.authenticate_header(drf_request)

        assert result == "Bearer"

    def test_keyword_class_attribute_is_bearer(self):
        """Test the keyword class attribute is 'Bearer'."""
        assert PatronusAuthentication.keyword == "Bearer"


class TestPatronusAuthenticationIntegration:
    """Integration tests for PatronusAuthentication with settings."""

    def test_uses_provider_from_settings(self):
        """Test authentication uses provider configured in settings."""
        reset_instances()
        company_id = uuid4()

        token_payload = TokenPayload(
            uid="settings-test-uid",
            email="settings@example.com",
            email_verified=True,
            phone_number=None,
            claims={"uid": "settings-test-uid"},
        )

        user_profile = UserProfile(
            company_id=company_id,
            permissions=frozenset(["read:data"]),
            profile_type="test",
        )

        mock_provider = MagicMock()
        mock_provider.verify_token.return_value = token_payload

        mock_loader = MockProfileLoader()
        mock_loader.add_profile("settings-test-uid", user_profile)

        factory = APIRequestFactory()
        request = factory.get("/test/", HTTP_AUTHORIZATION="Bearer settings-token")
        drf_request = Request(request)

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            auth = PatronusAuthentication()
            result = auth.authenticate(drf_request)

        assert result is not None
        user, _ = result
        assert user.email == "settings@example.com"
        assert user.company_id == company_id
