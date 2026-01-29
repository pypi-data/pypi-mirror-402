"""
Django REST Framework authentication class for Patronus.

This module provides the PatronusAuthentication class which integrates
with DRF's authentication system to validate tokens and create NovahUser
instances.
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request

from patronus.settings import get_profile_loader, get_provider
from patronus.user import NovahUser, TokenPayload


class PatronusAuthentication(BaseAuthentication):
    """
    DRF authentication class for Patronus.

    This authentication class:
    1. Extracts Bearer tokens from the Authorization header
    2. Verifies tokens using the configured AuthProvider
    3. Loads user profiles using the configured ProfileLoader
    4. Creates NovahUser instances for authenticated requests

    The authenticated user is set on request.user and the token payload
    is set on request.auth.

    Usage in DRF settings:
        REST_FRAMEWORK = {
            "DEFAULT_AUTHENTICATION_CLASSES": [
                "patronus.PatronusAuthentication",
            ],
        }

    Or per-view:
        class MyView(APIView):
            authentication_classes = [PatronusAuthentication]
    """

    keyword = "Bearer"

    def authenticate(self, request: Request) -> tuple[NovahUser, TokenPayload] | None:
        """
        Authenticate the request and return user/token tuple.

        This method extracts the Bearer token from the Authorization header,
        verifies it with the identity provider, loads the user profile,
        and creates a NovahUser instance.

        Args:
            request: The DRF Request object.

        Returns:
            Tuple of (NovahUser, TokenPayload) if authentication succeeds,
            or None if no Authorization header is present.

        Raises:
            InvalidTokenError: Token is malformed or has invalid signature.
            ExpiredTokenError: Token has expired.
            RevokedTokenError: Token has been revoked.
            NoProfileError: User has no profile in the system.
            ProviderError: Identity provider unavailable.
        """
        token = self._get_authorization_token(request)
        if not token:
            return None

        # Get provider and profile loader from settings
        provider = get_provider()
        profile_loader = get_profile_loader()

        # Verify token with identity provider
        token_payload = provider.verify_token(token)

        # Load profile from database
        profile = profile_loader.load_profile(
            uid=token_payload.uid,
            email=token_payload.email,
            phone_number=token_payload.phone_number,
        )

        # Create NovahUser combining token and profile data
        user = NovahUser(
            identity_provider_uid=token_payload.uid,
            email=token_payload.email,
            phone_number=token_payload.phone_number,
            company_id=profile.company_id,
            permissions=profile.permissions,
            profile_type=profile.profile_type,
        )

        return (user, token_payload)

    def authenticate_header(self, request: Request) -> str:
        """
        Return the WWW-Authenticate header value.

        This is used by DRF to construct the WWW-Authenticate response
        header when authentication fails.

        Args:
            request: The DRF Request object.

        Returns:
            The authentication scheme keyword ("Bearer").
        """
        return self.keyword

    def _get_authorization_token(self, request: Request) -> str | None:
        """
        Extract the Bearer token from the Authorization header in the request.

        This method retrieves the Authorization header from the request's metadata,
        validates its format, and extracts the token if it follows the expected
        "Bearer <token>" format.

        Args:
            request: The DRF Request object containing the HTTP headers.

        Returns:
            str: The extracted token if the Authorization header is present and valid.
            None: If the Authorization header is missing or improperly formatted.
        """
        # Retrieve the Authorization header from the request metadata
        auth_header: str = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return None

        # Split the header into parts and validate the format
        parts: list[str] = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        # Return the token part of the header
        return parts[1]
