"""
Integration tests for Patronus authentication flow.

These tests verify the complete end-to-end authentication flow including:
- Token verification
- Profile loading
- User creation
- Permission checking
- Error handling for various scenarios

All tests use mocked providers to avoid external dependencies while
testing the complete integration between components.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from django.http import HttpResponse
from rest_framework import status
from rest_framework.test import APIRequestFactory

import patronus
from patronus import (
    AuthProvider,
    ExpiredTokenError,
    HasAnyPermission,
    HasPermission,
    HasProfile,
    InvalidTokenError,
    IsSameCompany,
    MockProfileLoader,
    NoProfileError,
    NovahUser,
    PatronusAuthentication,
    ProviderError,
    RevokedTokenError,
    TokenPayload,
    UserProfile,
    get_current_company,
)
from patronus.middleware import TenantMiddleware


class MockAuthProvider(AuthProvider):
    """Mock auth provider for testing."""

    def __init__(self, credentials_config=None):
        """Initialize mock provider."""
        self._responses: dict = {}
        self._errors: dict = {}

    def set_response(self, token: str, payload: TokenPayload) -> None:
        """Set a mock response for a token."""
        self._responses[token] = payload

    def set_error(self, token: str, error: Exception) -> None:
        """Set a mock error for a token."""
        self._errors[token] = error

    def verify_token(self, token: str) -> TokenPayload:
        """Verify token with mock responses."""
        if token in self._errors:
            raise self._errors[token]
        if token in self._responses:
            return self._responses[token]
        raise InvalidTokenError("Token not found in mock")

    def revoke_token(self, token: str) -> None:
        """Mock token revocation."""
        pass

    def get_user_by_uid(self, uid: str) -> dict:
        """Mock user retrieval."""
        return {"uid": uid, "email": "test@example.com"}

    async def verify_token_async(self, token: str) -> TokenPayload:
        """Async mock verification."""
        return self.verify_token(token)

    async def revoke_token_async(self, token: str) -> None:
        """Async mock revocation."""
        pass

    async def get_user_by_uid_async(self, uid: str) -> dict:
        """Async mock user retrieval."""
        return self.get_user_by_uid(uid)


@pytest.fixture
def mock_provider():
    """Create a mock auth provider."""
    return MockAuthProvider()


@pytest.fixture
def mock_loader():
    """Create a mock profile loader."""
    return MockProfileLoader()


@pytest.fixture
def request_factory():
    """Create a DRF request factory."""
    return APIRequestFactory()


@pytest.fixture
def valid_token_payload():
    """Create a valid token payload."""
    return TokenPayload(
        uid="integration-test-uid",
        email="integration@example.com",
        email_verified=True,
        phone_number=None,
        claims={"uid": "integration-test-uid", "email": "integration@example.com"},
    )


@pytest.fixture
def valid_phone_token_payload():
    """Create a valid phone token payload."""
    return TokenPayload(
        uid="phone-test-uid",
        email=None,
        email_verified=False,
        phone_number="+5511999999999",
        claims={"uid": "phone-test-uid", "phone_number": "+5511999999999"},
    )


@pytest.fixture
def valid_user_profile():
    """Create a valid user profile."""
    return UserProfile(
        company_id=uuid4(),
        permissions=frozenset(["read:patients", "write:patients"]),
        profile_type="colaborador",
    )


@pytest.fixture
def different_company_profile():
    """Create a user profile with a different company."""
    return UserProfile(
        company_id=uuid4(),
        permissions=frozenset(["read:patients"]),
        profile_type="colaborador",
    )


class TestCompleteAuthFlow:
    """Tests for the complete authentication flow."""

    def test_complete_auth_flow_email_user(
        self,
        mock_provider,
        mock_loader,
        request_factory,
        valid_token_payload,
        valid_user_profile,
    ):
        """
        Test complete auth flow: token -> NovahUser -> permission check.

        This test verifies the entire authentication pipeline:
        1. Token is verified by the provider
        2. Profile is loaded from the database
        3. NovahUser is created with correct attributes
        4. Permission checking works correctly
        """
        # Setup
        mock_provider.set_response("valid-token", valid_token_payload)
        mock_loader.add_profile("integration-test-uid", valid_user_profile)

        # Patch at the point of use in authentication module
        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            # Create request with auth header
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer valid-token"

            # Authenticate
            auth = PatronusAuthentication()
            result = auth.authenticate(request)

            # Verify authentication succeeded
            assert result is not None
            user, token_payload = result

            # Verify user attributes
            assert isinstance(user, NovahUser)
            assert user.identity_provider_uid == "integration-test-uid"
            assert user.email == "integration@example.com"
            assert user.phone_number is None
            assert user.company_id == valid_user_profile.company_id
            assert user.permissions == valid_user_profile.permissions
            assert user.profile_type == "colaborador"
            assert user.is_authenticated is True

            # Verify token payload
            assert token_payload.uid == "integration-test-uid"
            assert token_payload.email == "integration@example.com"

            # Verify permission checking
            assert user.has_permission("read:patients") is True
            assert user.has_permission("delete:patients") is False
            assert user.has_any_permission(["read:patients", "admin:all"]) is True
            assert user.has_any_permission(["delete:patients"]) is False
            assert user.has_all_permissions(["read:patients", "write:patients"]) is True
            assert user.has_all_permissions(["read:patients", "admin:all"]) is False

    def test_phone_authentication_flow(
        self,
        mock_provider,
        mock_loader,
        request_factory,
        valid_phone_token_payload,
        valid_user_profile,
    ):
        """
        Test phone number authentication flow (passwordless).

        This verifies that users authenticating via phone number
        are properly handled through the entire flow.
        """
        # Setup
        mock_provider.set_response("phone-token", valid_phone_token_payload)
        mock_loader.add_profile("phone-test-uid", valid_user_profile)

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            # Create request with auth header
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer phone-token"

            # Authenticate
            auth = PatronusAuthentication()
            result = auth.authenticate(request)

            # Verify authentication succeeded
            assert result is not None
            user, _token_payload = result

            # Verify phone user attributes
            assert isinstance(user, NovahUser)
            assert user.identity_provider_uid == "phone-test-uid"
            assert user.email is None
            assert user.phone_number == "+5511999999999"
            assert user.company_id == valid_user_profile.company_id
            assert user.is_authenticated is True


class TestAuthenticationErrors:
    """Tests for authentication error scenarios."""

    def test_invalid_token_returns_401(
        self, mock_provider, mock_loader, request_factory
    ):
        """
        Test invalid token returns 401 Unauthorized.

        When the provider cannot verify the token, an InvalidTokenError
        should be raised which maps to HTTP 401.
        """
        # Setup - token will raise InvalidTokenError
        mock_provider.set_error(
            "invalid-token", InvalidTokenError("Token signature is invalid")
        )

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer invalid-token"

            auth = PatronusAuthentication()

            with pytest.raises(InvalidTokenError) as exc_info:
                auth.authenticate(request)

            # Verify exception maps to 401
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.default_code == "invalid_token"

    def test_expired_token_returns_401(
        self, mock_provider, mock_loader, request_factory
    ):
        """
        Test expired token returns 401 Unauthorized.

        When the token has expired, an ExpiredTokenError should be raised
        which maps to HTTP 401.
        """
        # Setup - token will raise ExpiredTokenError
        mock_provider.set_error("expired-token", ExpiredTokenError("Token has expired"))

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer expired-token"

            auth = PatronusAuthentication()

            with pytest.raises(ExpiredTokenError) as exc_info:
                auth.authenticate(request)

            # Verify exception maps to 401
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.default_code == "token_expired"

    def test_revoked_token_returns_401(
        self, mock_provider, mock_loader, request_factory
    ):
        """
        Test revoked token returns 401 Unauthorized.

        When the token has been revoked, a RevokedTokenError should be raised
        which maps to HTTP 401.
        """
        # Setup - token will raise RevokedTokenError
        mock_provider.set_error(
            "revoked-token", RevokedTokenError("Token has been revoked")
        )

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer revoked-token"

            auth = PatronusAuthentication()

            with pytest.raises(RevokedTokenError) as exc_info:
                auth.authenticate(request)

            # Verify exception maps to 401
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.default_code == "token_revoked"

    def test_no_profile_returns_403(
        self, mock_provider, mock_loader, request_factory, valid_token_payload
    ):
        """
        Test no profile returns 403 Forbidden.

        When the user exists in the identity provider but has no profile
        in the application database, a NoProfileError should be raised
        which maps to HTTP 403.
        """
        # Setup - token valid but no profile in loader
        mock_provider.set_response("valid-token", valid_token_payload)
        # Don't add profile to loader - will raise NoProfileError

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer valid-token"

            auth = PatronusAuthentication()

            with pytest.raises(NoProfileError) as exc_info:
                auth.authenticate(request)

            # Verify exception maps to 403
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert exc_info.value.default_code == "no_profile"

    def test_provider_error_returns_503(
        self, mock_provider, mock_loader, request_factory
    ):
        """
        Test provider error returns 503 Service Unavailable.

        When the identity provider is unavailable or returns an unexpected
        error, a ProviderError should be raised which maps to HTTP 503.
        """
        # Setup - token will raise ProviderError
        mock_provider.set_error(
            "any-token", ProviderError("Firebase is temporarily unavailable")
        )

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer any-token"

            auth = PatronusAuthentication()

            with pytest.raises(ProviderError) as exc_info:
                auth.authenticate(request)

            # Verify exception maps to 503
            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert exc_info.value.default_code == "provider_unavailable"


class TestTenantMismatch:
    """Tests for tenant mismatch scenarios."""

    def test_tenant_mismatch_returns_403(
        self,
        mock_provider,
        mock_loader,
        request_factory,
        valid_token_payload,
        valid_user_profile,
        different_company_profile,
    ):
        """
        Test tenant mismatch returns 403 Forbidden.

        When a user tries to access a resource belonging to a different
        company, access should be denied with HTTP 403.
        """
        # Setup authenticated user
        mock_provider.set_response("valid-token", valid_token_payload)
        mock_loader.add_profile("integration-test-uid", valid_user_profile)

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            # Create and authenticate request
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer valid-token"

            auth = PatronusAuthentication()
            result = auth.authenticate(request)
            assert result is not None
            user, _ = result
            request.user = user

            # Create a mock object with different company
            class MockResource:
                company_id = different_company_profile.company_id

            mock_resource = MockResource()

            # Check IsSameCompany permission
            permission = IsSameCompany()
            view = MagicMock()

            has_permission = permission.has_object_permission(
                request, view, mock_resource
            )

            # Verify access is denied
            assert has_permission is False

    def test_tenant_match_allows_access(
        self,
        mock_provider,
        mock_loader,
        request_factory,
        valid_token_payload,
        valid_user_profile,
    ):
        """
        Test that users can access resources from their own company.
        """
        # Setup authenticated user
        mock_provider.set_response("valid-token", valid_token_payload)
        mock_loader.add_profile("integration-test-uid", valid_user_profile)

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer valid-token"

            auth = PatronusAuthentication()
            result = auth.authenticate(request)
            assert result is not None
            user, _ = result
            request.user = user

            # Create a mock object with same company
            class MockResource:
                company_id = valid_user_profile.company_id

            mock_resource = MockResource()

            # Check IsSameCompany permission
            permission = IsSameCompany()
            view = MagicMock()

            has_permission = permission.has_object_permission(
                request, view, mock_resource
            )

            # Verify access is granted
            assert has_permission is True


class TestPermissionIntegration:
    """Tests for permission class integration."""

    def test_has_profile_with_authenticated_user(
        self,
        mock_provider,
        mock_loader,
        request_factory,
        valid_token_payload,
        valid_user_profile,
    ):
        """Test HasProfile permission with authenticated NovahUser."""
        mock_provider.set_response("valid-token", valid_token_payload)
        mock_loader.add_profile("integration-test-uid", valid_user_profile)

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer valid-token"

            auth = PatronusAuthentication()
            result = auth.authenticate(request)
            assert result is not None
            user, _ = result
            request.user = user

            permission = HasProfile()
            view = MagicMock()

            assert permission.has_permission(request, view) is True

    def test_has_permission_with_valid_permission(
        self,
        mock_provider,
        mock_loader,
        request_factory,
        valid_token_payload,
        valid_user_profile,
    ):
        """Test HasPermission with a permission the user has."""
        mock_provider.set_response("valid-token", valid_token_payload)
        mock_loader.add_profile("integration-test-uid", valid_user_profile)

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer valid-token"

            auth = PatronusAuthentication()
            result = auth.authenticate(request)
            assert result is not None
            user, _ = result
            request.user = user

            permission = HasPermission("read:patients")
            view = MagicMock()

            assert permission.has_permission(request, view) is True

    def test_has_permission_with_missing_permission(
        self,
        mock_provider,
        mock_loader,
        request_factory,
        valid_token_payload,
        valid_user_profile,
    ):
        """Test HasPermission with a permission the user doesn't have."""
        mock_provider.set_response("valid-token", valid_token_payload)
        mock_loader.add_profile("integration-test-uid", valid_user_profile)

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer valid-token"

            auth = PatronusAuthentication()
            result = auth.authenticate(request)
            assert result is not None
            user, _ = result
            request.user = user

            permission = HasPermission("admin:all")
            view = MagicMock()

            assert permission.has_permission(request, view) is False

    def test_has_any_permission_with_one_matching(
        self,
        mock_provider,
        mock_loader,
        request_factory,
        valid_token_payload,
        valid_user_profile,
    ):
        """Test HasAnyPermission with at least one matching permission."""
        mock_provider.set_response("valid-token", valid_token_payload)
        mock_loader.add_profile("integration-test-uid", valid_user_profile)

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer valid-token"

            auth = PatronusAuthentication()
            result = auth.authenticate(request)
            assert result is not None
            user, _ = result
            request.user = user

            permission = HasAnyPermission(["read:patients", "admin:all"])
            view = MagicMock()

            assert permission.has_permission(request, view) is True


class TestMiddlewareIntegration:
    """Tests for middleware integration with authentication."""

    def test_middleware_sets_company_context(
        self,
        mock_provider,
        mock_loader,
        request_factory,
        valid_token_payload,
        valid_user_profile,
    ):
        """Test that TenantMiddleware sets company context for authenticated users."""
        mock_provider.set_response("valid-token", valid_token_payload)
        mock_loader.add_profile("integration-test-uid", valid_user_profile)

        with (
            patch("patronus.authentication.get_provider", return_value=mock_provider),
            patch(
                "patronus.authentication.get_profile_loader", return_value=mock_loader
            ),
        ):
            request = request_factory.get("/test/")
            request.META["HTTP_AUTHORIZATION"] = "Bearer valid-token"

            # Authenticate first
            auth = PatronusAuthentication()
            result = auth.authenticate(request)
            assert result is not None
            user, _ = result
            request.user = user

            # Track if context was set during request
            context_during_request = None

            def mock_view(request):
                nonlocal context_during_request
                context_during_request = get_current_company()
                return HttpResponse("OK")

            # Run through middleware
            middleware = TenantMiddleware(mock_view)
            middleware(request)

            # Verify context was set during request
            assert context_during_request == valid_user_profile.company_id

            # Verify context is cleared after request
            assert get_current_company() is None


class TestPublicAPIExports:
    """Tests to verify public API has all required exports."""

    def test_all_classes_importable(self):
        """Verify all public classes can be imported from patronus."""
        # Verify all imports are not None (using top-level imports)
        assert patronus.PatronusAuthentication is not None
        assert patronus.get_current_company is not None
        assert patronus.set_current_company is not None
        assert patronus.clear_current_company is not None
        assert patronus.company_context is not None
        assert patronus.PatronusException is not None
        assert patronus.InvalidTokenError is not None
        assert patronus.ExpiredTokenError is not None
        assert patronus.RevokedTokenError is not None
        assert patronus.NoProfileError is not None
        assert patronus.TenantMismatchError is not None
        assert patronus.ProviderError is not None
        assert patronus.TenantMiddleware is not None
        assert patronus.HasPermission is not None
        assert patronus.HasAnyPermission is not None
        assert patronus.HasProfile is not None
        assert patronus.IsSameCompany is not None
        assert patronus.ProfileLoader is not None
        assert patronus.MockProfileLoader is not None
        assert patronus.AuthProvider is not None
        assert patronus.PatronusSettings is not None
        assert patronus.get_settings is not None
        assert patronus.get_provider is not None
        assert patronus.get_profile_loader is not None
        assert patronus.reset_instances is not None
        assert patronus.NovahUser is not None
        assert patronus.TokenPayload is not None
        assert patronus.UserProfile is not None

    def test_no_gcip_in_public_api(self):
        """Verify that GCIP is not exposed in public API."""
        # Check __all__ doesn't contain GCIP-related names
        assert "GCIPProvider" not in patronus.__all__
        assert "gcip" not in patronus.__all__

        # Verify GCIPProvider is not directly accessible
        assert not hasattr(patronus, "GCIPProvider")

    def test_version_available(self):
        """Verify version is available in public API."""
        assert hasattr(patronus, "__version__")
        assert patronus.__version__ == "0.1.0"
