"""
Abstract base class for identity providers.

This module defines the AuthProvider interface that all identity provider
implementations must follow. The interface provides both synchronous and
asynchronous methods for token operations.
"""

from abc import ABC, abstractmethod
from typing import Any

from patronus.user import TokenPayload


class AuthProvider(ABC):
    """
    Abstract base class for identity providers.

    This class defines the contract that all identity provider implementations
    must follow. It provides methods for token verification, revocation, and
    user information retrieval.

    Implementations should handle provider-specific error mapping to Patronus
    exceptions (InvalidTokenError, ExpiredTokenError, etc.).

    Example implementation:
        class MyProvider(AuthProvider):
            def verify_token(self, token: str) -> TokenPayload:
                # Verify with your identity provider
                decoded = my_provider.verify(token)
                return TokenPayload(
                    uid=decoded["sub"],
                    email=decoded.get("email"),
                    email_verified=decoded.get("email_verified", False),
                    phone_number=decoded.get("phone_number"),
                    claims=decoded,
                )
    """

    @abstractmethod
    def verify_token(self, token: str) -> TokenPayload:
        """
        Verify a JWT token and extract payload.

        Args:
            token: The JWT token string.

        Returns:
            TokenPayload with extracted claims.

        Raises:
            InvalidTokenError: Token is malformed or invalid.
            ExpiredTokenError: Token has expired.
            RevokedTokenError: Token has been revoked.
            ProviderError: Identity provider unavailable.
        """
        ...

    @abstractmethod
    def revoke_token(self, token: str) -> None:
        """
        Revoke a token (invalidate for future use).

        This typically revokes all refresh tokens for the user,
        forcing them to re-authenticate.

        Args:
            token: The JWT token string to revoke.

        Raises:
            ProviderError: Identity provider unavailable.
        """
        ...

    @abstractmethod
    def get_user_by_uid(self, uid: str) -> dict[str, Any]:
        """
        Retrieve user information from the identity provider.

        Args:
            uid: The user's identity provider UID.

        Returns:
            Dict with user information (email, display_name, etc.).

        Raises:
            ProviderError: Identity provider unavailable.
        """
        ...

    @abstractmethod
    async def verify_token_async(self, token: str) -> TokenPayload:
        """
        Async version of verify_token.

        Args:
            token: The JWT token string.

        Returns:
            TokenPayload with extracted claims.

        Raises:
            InvalidTokenError: Token is malformed or invalid.
            ExpiredTokenError: Token has expired.
            RevokedTokenError: Token has been revoked.
            ProviderError: Identity provider unavailable.
        """
        ...

    @abstractmethod
    async def revoke_token_async(self, token: str) -> None:
        """
        Async version of revoke_token.

        Args:
            token: The JWT token string to revoke.

        Raises:
            ProviderError: Identity provider unavailable.
        """
        ...

    @abstractmethod
    async def get_user_by_uid_async(self, uid: str) -> dict[str, Any]:
        """
        Async version of get_user_by_uid.

        Args:
            uid: The user's identity provider UID.

        Returns:
            Dict with user information.

        Raises:
            ProviderError: Identity provider unavailable.
        """
        ...
