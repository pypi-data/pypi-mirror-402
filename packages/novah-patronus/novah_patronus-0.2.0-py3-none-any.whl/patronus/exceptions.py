"""
Custom exception hierarchy for Patronus authentication.

All exceptions inherit from DRF exceptions for automatic HTTP response handling.
This ensures that when exceptions are raised during authentication or authorization,
they are automatically converted to appropriate HTTP responses by DRF.

Exception Mapping:
    - InvalidTokenError, ExpiredTokenError, RevokedTokenError -> 401 Unauthorized
    - NoProfileError, TenantMismatchError -> 403 Forbidden
    - ProviderError -> 503 Service Unavailable
"""

from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    PermissionDenied,
)


class PatronusException(Exception):
    """
    Base exception for Patronus library errors that don't map to HTTP.

    This is the base class for any Patronus-specific exceptions that don't
    need to be converted to HTTP responses. Most exceptions should inherit
    from DRF exceptions instead for automatic HTTP handling.
    """

    pass


class InvalidTokenError(AuthenticationFailed):
    """
    Token is malformed or invalid.

    Raised when the provided JWT token cannot be parsed or has an invalid
    signature. Maps to 401 Unauthorized.
    """

    default_detail = "The provided token is invalid."
    default_code = "invalid_token"


class ExpiredTokenError(AuthenticationFailed):
    """
    Token has expired.

    Raised when the provided JWT token's expiration time has passed.
    Maps to 401 Unauthorized.
    """

    default_detail = "The provided token has expired."
    default_code = "token_expired"


class RevokedTokenError(AuthenticationFailed):
    """
    Token has been revoked.

    Raised when the provided JWT token has been explicitly revoked
    (e.g., user logged out from all devices). Maps to 401 Unauthorized.
    """

    default_detail = "The provided token has been revoked."
    default_code = "token_revoked"


class NoProfileError(PermissionDenied):
    """
    User has no profile in the system.

    Raised when the authenticated user exists in the identity provider
    but has no corresponding profile/permissions in the application database.
    Maps to 403 Forbidden.
    """

    default_detail = "User profile not found."
    default_code = "no_profile"


class TenantMismatchError(PermissionDenied):
    """
    Tenant context mismatch.

    Raised when a user attempts to access resources belonging to a different
    tenant (company) than the one they are associated with.
    Maps to 403 Forbidden.
    """

    default_detail = "You do not have access to this tenant's resources."
    default_code = "tenant_mismatch"


class ProviderError(APIException):
    """
    Identity provider unavailable.

    Raised when the identity provider (e.g., GCIP/Firebase) is temporarily
    unavailable or returns an unexpected error. Maps to 503 Service Unavailable.
    """

    status_code = 503
    default_detail = "Identity provider is temporarily unavailable."
    default_code = "provider_unavailable"
