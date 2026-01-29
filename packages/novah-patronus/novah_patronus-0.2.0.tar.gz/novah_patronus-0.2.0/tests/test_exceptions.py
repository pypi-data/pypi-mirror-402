"""
Tests for Patronus exception hierarchy.

This module tests that all exceptions have the correct HTTP status codes,
default messages, codes, and proper inheritance from DRF exception classes.
"""

import pytest
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    PermissionDenied,
)

from patronus import (
    ExpiredTokenError,
    InvalidTokenError,
    NoProfileError,
    PatronusException,
    ProviderError,
    RevokedTokenError,
    TenantMismatchError,
)


class TestPatronusException:
    """Tests for PatronusException base class."""

    def test_inherits_from_exception(self):
        """Test PatronusException inherits from base Exception."""
        assert issubclass(PatronusException, Exception)

    def test_can_be_raised_with_message(self):
        """Test PatronusException can be raised with a custom message."""
        with pytest.raises(PatronusException) as exc_info:
            raise PatronusException("Custom error message")

        assert str(exc_info.value) == "Custom error message"


class TestInvalidTokenError:
    """Tests for InvalidTokenError exception."""

    def test_inherits_from_authentication_failed(self):
        """Test InvalidTokenError inherits from AuthenticationFailed."""
        assert issubclass(InvalidTokenError, AuthenticationFailed)

    def test_has_correct_status_code(self):
        """Test InvalidTokenError maps to 401 status code."""
        error = InvalidTokenError()
        assert error.status_code == 401

    def test_has_correct_default_detail(self):
        """Test InvalidTokenError has correct default message."""
        error = InvalidTokenError()
        assert error.detail == "The provided token is invalid."

    def test_has_correct_default_code(self):
        """Test InvalidTokenError has correct default code."""
        assert InvalidTokenError.default_code == "invalid_token"
        error = InvalidTokenError()
        assert error.get_codes() == "invalid_token"

    def test_can_override_detail(self):
        """Test InvalidTokenError detail can be overridden."""
        error = InvalidTokenError("Custom invalid token message")
        assert error.detail == "Custom invalid token message"


class TestExpiredTokenError:
    """Tests for ExpiredTokenError exception."""

    def test_inherits_from_authentication_failed(self):
        """Test ExpiredTokenError inherits from AuthenticationFailed."""
        assert issubclass(ExpiredTokenError, AuthenticationFailed)

    def test_has_correct_status_code(self):
        """Test ExpiredTokenError maps to 401 status code."""
        error = ExpiredTokenError()
        assert error.status_code == 401

    def test_has_correct_default_detail(self):
        """Test ExpiredTokenError has correct default message."""
        error = ExpiredTokenError()
        assert error.detail == "The provided token has expired."

    def test_has_correct_default_code(self):
        """Test ExpiredTokenError has correct default code."""
        assert ExpiredTokenError.default_code == "token_expired"
        error = ExpiredTokenError()
        assert error.get_codes() == "token_expired"


class TestRevokedTokenError:
    """Tests for RevokedTokenError exception."""

    def test_inherits_from_authentication_failed(self):
        """Test RevokedTokenError inherits from AuthenticationFailed."""
        assert issubclass(RevokedTokenError, AuthenticationFailed)

    def test_has_correct_status_code(self):
        """Test RevokedTokenError maps to 401 status code."""
        error = RevokedTokenError()
        assert error.status_code == 401

    def test_has_correct_default_detail(self):
        """Test RevokedTokenError has correct default message."""
        error = RevokedTokenError()
        assert error.detail == "The provided token has been revoked."

    def test_has_correct_default_code(self):
        """Test RevokedTokenError has correct default code."""
        assert RevokedTokenError.default_code == "token_revoked"
        error = RevokedTokenError()
        assert error.get_codes() == "token_revoked"


class TestNoProfileError:
    """Tests for NoProfileError exception."""

    def test_inherits_from_permission_denied(self):
        """Test NoProfileError inherits from PermissionDenied."""
        assert issubclass(NoProfileError, PermissionDenied)

    def test_has_correct_status_code(self):
        """Test NoProfileError maps to 403 status code."""
        error = NoProfileError()
        assert error.status_code == 403

    def test_has_correct_default_detail(self):
        """Test NoProfileError has correct default message."""
        error = NoProfileError()
        assert error.detail == "User profile not found."

    def test_has_correct_default_code(self):
        """Test NoProfileError has correct default code."""
        assert NoProfileError.default_code == "no_profile"
        error = NoProfileError()
        assert error.get_codes() == "no_profile"

    def test_can_override_detail(self):
        """Test NoProfileError detail can be overridden."""
        error = NoProfileError("No profile found for uid: user-123")
        assert error.detail == "No profile found for uid: user-123"


class TestTenantMismatchError:
    """Tests for TenantMismatchError exception."""

    def test_inherits_from_permission_denied(self):
        """Test TenantMismatchError inherits from PermissionDenied."""
        assert issubclass(TenantMismatchError, PermissionDenied)

    def test_has_correct_status_code(self):
        """Test TenantMismatchError maps to 403 status code."""
        error = TenantMismatchError()
        assert error.status_code == 403

    def test_has_correct_default_detail(self):
        """Test TenantMismatchError has correct default message."""
        error = TenantMismatchError()
        assert error.detail == "You do not have access to this tenant's resources."

    def test_has_correct_default_code(self):
        """Test TenantMismatchError has correct default code."""
        assert TenantMismatchError.default_code == "tenant_mismatch"
        error = TenantMismatchError()
        assert error.get_codes() == "tenant_mismatch"


class TestProviderError:
    """Tests for ProviderError exception."""

    def test_inherits_from_api_exception(self):
        """Test ProviderError inherits from APIException."""
        assert issubclass(ProviderError, APIException)

    def test_has_correct_status_code(self):
        """Test ProviderError maps to 503 status code."""
        error = ProviderError()
        assert error.status_code == 503

    def test_has_correct_default_detail(self):
        """Test ProviderError has correct default message."""
        error = ProviderError()
        assert error.detail == "Identity provider is temporarily unavailable."

    def test_has_correct_default_code(self):
        """Test ProviderError has correct default code."""
        assert ProviderError.default_code == "provider_unavailable"
        error = ProviderError()
        assert error.get_codes() == "provider_unavailable"

    def test_can_override_detail(self):
        """Test ProviderError detail can be overridden."""
        error = ProviderError("Firebase connection failed")
        assert error.detail == "Firebase connection failed"


class TestExceptionInheritanceHierarchy:
    """Tests for the overall exception inheritance hierarchy."""

    def test_authentication_exceptions_inherit_correctly(self):
        """Test all 401 exceptions inherit from AuthenticationFailed."""
        auth_exceptions = [InvalidTokenError, ExpiredTokenError, RevokedTokenError]
        for exc_class in auth_exceptions:
            assert issubclass(exc_class, AuthenticationFailed)
            error = exc_class()
            assert error.status_code == 401

    def test_permission_exceptions_inherit_correctly(self):
        """Test all 403 exceptions inherit from PermissionDenied."""
        perm_exceptions = [NoProfileError, TenantMismatchError]
        for exc_class in perm_exceptions:
            assert issubclass(exc_class, PermissionDenied)
            error = exc_class()
            assert error.status_code == 403

    def test_service_exceptions_inherit_correctly(self):
        """Test all 503 exceptions inherit from APIException."""
        service_exceptions = [ProviderError]
        for exc_class in service_exceptions:
            assert issubclass(exc_class, APIException)
            error = exc_class()
            assert error.status_code == 503

    def test_all_drf_exceptions_are_api_exceptions(self):
        """Test all DRF-based exceptions are APIExceptions."""
        drf_exceptions = [
            InvalidTokenError,
            ExpiredTokenError,
            RevokedTokenError,
            NoProfileError,
            TenantMismatchError,
            ProviderError,
        ]
        for exc_class in drf_exceptions:
            assert issubclass(exc_class, APIException)
