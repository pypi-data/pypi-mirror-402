"""
Google Cloud Identity Platform (GCIP) provider implementation.

This module provides the GCIPProvider class which implements the AuthProvider
interface using Firebase Admin SDK for token verification and user management.
"""

import asyncio
import contextlib
import json
from typing import Any

import firebase_admin
from firebase_admin import auth, credentials

from patronus.exceptions import (
    ExpiredTokenError,
    InvalidTokenError,
    ProviderError,
    RevokedTokenError,
)
from patronus.providers.base import AuthProvider
from patronus.user import TokenPayload


class GCIPProvider(AuthProvider):
    """
    Google Cloud Identity Platform provider implementation.

    This provider uses Firebase Admin SDK to verify tokens and manage users.
    It supports multiple credential configuration options for flexibility
    in different deployment environments.

    Credential Options:
        - dict: Service account credentials dict (from env vars/secrets managers)
        - str: JSON string content (auto-parsed if starts with '{')
        - str: Path to service account JSON file
        - None: Use application default credentials (ADC)

    Example usage:
        # From environment variable (JSON string - auto-parsed)
        import os
        provider = GCIPProvider(
            credentials_config=os.environ.get("GCIP_CREDENTIALS")
        )

        # From dict (pre-parsed)
        provider = GCIPProvider(credentials_config={"type": "service_account", ...})

        # From file path
        provider = GCIPProvider(credentials_config="/path/to/service-account.json")

        # Using application default credentials
        provider = GCIPProvider(credentials_config=None)

        # Verify a token
        payload = provider.verify_token(token)
        print(f"User ID: {payload.uid}")
    """

    def __init__(self, credentials_config: dict[str, Any] | str | None = None) -> None:
        """
        Initialize GCIP provider.

        Args:
            credentials_config: One of:
                - dict: Service account credentials dict (from env vars/secrets)
                - str: Path to service account JSON file
                - None: Use application default credentials
        """
        self._app = self._initialize_app(credentials_config)

    def _parse_credentials_string(
        self, credentials_string: str
    ) -> dict[str, Any] | str:
        """
        Parse credentials string as JSON or return as file path.

        If the string starts with '{', attempts to parse it as JSON.
        If parsing fails or it doesn't start with '{', returns as-is (file path).

        Args:
            credentials_string: Either a JSON string or file path.

        Returns:
            Parsed dict if valid JSON, otherwise the original string (file path).
        """
        stripped = credentials_string.strip()
        if stripped.startswith("{"):
            try:
                parsed: dict[str, Any] = json.loads(stripped)
                return parsed
            except json.JSONDecodeError:
                pass  # Not valid JSON, treat as file path
        return credentials_string

    def _initialize_app(
        self, credentials_config: dict[str, Any] | str | None
    ) -> firebase_admin.App:
        """
        Initialize Firebase Admin SDK with appropriate credentials.

        Args:
            credentials_config: Credentials configuration (dict, JSON string, path, or None).

        Returns:
            Initialized Firebase App instance.
        """
        if credentials_config is None:
            # Use application default credentials
            cred = credentials.ApplicationDefault()
        elif isinstance(credentials_config, dict):
            # Credentials from dict (env vars, secrets manager)
            cred = credentials.Certificate(credentials_config)
        else:
            # String: could be JSON content or file path
            parsed = self._parse_credentials_string(credentials_config)
            cred = credentials.Certificate(parsed)

        # Use unique app name to allow multiple instances
        # This is useful for testing and multi-tenant scenarios
        app_name = f"patronus_{id(self)}"
        return firebase_admin.initialize_app(cred, name=app_name)

    def verify_token(self, token: str) -> TokenPayload:
        """
        Verify Firebase ID token.

        Args:
            token: The Firebase ID token string.

        Returns:
            TokenPayload with extracted claims.

        Raises:
            InvalidTokenError: Token is malformed or has invalid signature.
            ExpiredTokenError: Token has expired.
            RevokedTokenError: Token has been revoked.
            ProviderError: Firebase is unavailable or returned an error.
        """
        try:
            decoded = auth.verify_id_token(token, app=self._app, check_revoked=True)
            return TokenPayload(
                uid=decoded["uid"],
                email=decoded.get("email"),
                email_verified=decoded.get("email_verified", False),
                phone_number=decoded.get("phone_number"),
                claims=decoded,
            )
        except auth.ExpiredIdTokenError as e:
            # Must be caught before InvalidIdTokenError (it's a subclass)
            raise ExpiredTokenError(str(e)) from e
        except auth.RevokedIdTokenError as e:
            # Must be caught before InvalidIdTokenError (it's a subclass)
            raise RevokedTokenError(str(e)) from e
        except auth.InvalidIdTokenError as e:
            # Catch general invalid token errors last
            raise InvalidTokenError(str(e)) from e
        except Exception as e:
            raise ProviderError(str(e)) from e

    def revoke_token(self, token: str) -> None:
        """
        Revoke all refresh tokens for the user.

        This invalidates all sessions for the user, forcing them to
        re-authenticate on all devices.

        Args:
            token: The Firebase ID token string.

        Raises:
            ProviderError: Firebase is unavailable or returned an error.
        """
        try:
            # First decode the token to get the user ID (without checking revocation)
            decoded = auth.verify_id_token(token, app=self._app, check_revoked=False)
            # Then revoke all refresh tokens for that user
            auth.revoke_refresh_tokens(decoded["uid"], app=self._app)
        except Exception as e:
            raise ProviderError(str(e)) from e

    def get_user_by_uid(self, uid: str) -> dict[str, Any]:
        """
        Get user record from Firebase.

        Args:
            uid: The user's Firebase UID.

        Returns:
            Dict with user information including:
            - uid: The user's UID
            - email: The user's email (if set)
            - phone_number: The user's phone number (if set)
            - display_name: The user's display name (if set)
            - email_verified: Whether email is verified

        Raises:
            ProviderError: Firebase is unavailable or returned an error.
        """
        try:
            user = auth.get_user(uid, app=self._app)
            return {
                "uid": user.uid,
                "email": user.email,
                "phone_number": user.phone_number,
                "display_name": user.display_name,
                "email_verified": user.email_verified,
            }
        except Exception as e:
            raise ProviderError(str(e)) from e

    async def verify_token_async(self, token: str) -> TokenPayload:
        """
        Async token verification using executor.

        The Firebase Admin SDK is synchronous, so this method runs the
        sync version in a thread pool executor for async compatibility.

        Args:
            token: The Firebase ID token string.

        Returns:
            TokenPayload with extracted claims.

        Raises:
            InvalidTokenError: Token is malformed or has invalid signature.
            ExpiredTokenError: Token has expired.
            RevokedTokenError: Token has been revoked.
            ProviderError: Firebase is unavailable or returned an error.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.verify_token, token)

    async def revoke_token_async(self, token: str) -> None:
        """
        Async token revocation using executor.

        Args:
            token: The Firebase ID token string to revoke.

        Raises:
            ProviderError: Firebase is unavailable or returned an error.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.revoke_token, token)

    async def get_user_by_uid_async(self, uid: str) -> dict[str, Any]:
        """
        Async user retrieval using executor.

        Args:
            uid: The user's Firebase UID.

        Returns:
            Dict with user information.

        Raises:
            ProviderError: Firebase is unavailable or returned an error.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_user_by_uid, uid)

    def __del__(self) -> None:
        """Clean up Firebase app on deletion."""
        with contextlib.suppress(Exception):
            firebase_admin.delete_app(self._app)
