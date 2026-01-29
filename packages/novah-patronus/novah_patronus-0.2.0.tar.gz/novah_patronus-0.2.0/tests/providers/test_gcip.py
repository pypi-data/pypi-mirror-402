"""
Tests for GCIPProvider and AuthProvider interface.

These tests verify the GCIP provider implementation using mocked Firebase SDK
to avoid requiring real Firebase credentials during testing.
"""

from unittest.mock import MagicMock, patch

import pytest
from firebase_admin import auth as firebase_auth

from patronus import (
    ExpiredTokenError,
    InvalidTokenError,
    ProviderError,
    RevokedTokenError,
    TokenPayload,
)
from patronus.providers import AuthProvider
from patronus.providers.gcip import GCIPProvider


class TestAuthProviderInterface:
    """Tests for the AuthProvider abstract base class."""

    def test_auth_provider_is_abstract(self):
        """Test that AuthProvider cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            AuthProvider()

    def test_auth_provider_defines_required_methods(self):
        """Test that AuthProvider defines all required abstract methods."""
        # Verify all required abstract methods exist
        assert hasattr(AuthProvider, "verify_token")
        assert hasattr(AuthProvider, "revoke_token")
        assert hasattr(AuthProvider, "get_user_by_uid")
        assert hasattr(AuthProvider, "verify_token_async")
        assert hasattr(AuthProvider, "revoke_token_async")
        assert hasattr(AuthProvider, "get_user_by_uid_async")


class TestGCIPProviderJsonStringParsing:
    """Tests for GCIPProvider JSON string auto-parsing functionality."""

    @patch("patronus.providers.gcip.firebase_admin")
    @patch("patronus.providers.gcip.credentials")
    def test_init_with_json_string_credentials(
        self, mock_credentials, mock_firebase_admin
    ):
        """Test GCIPProvider initialization with JSON string credentials."""
        mock_cred = MagicMock()
        mock_credentials.Certificate.return_value = mock_cred
        mock_app = MagicMock()
        mock_firebase_admin.initialize_app.return_value = mock_app

        # JSON string (as would come from environment variable)
        json_string = '{"type": "service_account", "project_id": "test-project"}'

        provider = GCIPProvider(credentials_config=json_string)

        # Should be called with parsed dict, not string
        call_args = mock_credentials.Certificate.call_args[0][0]
        assert isinstance(call_args, dict)
        assert call_args["type"] == "service_account"
        assert call_args["project_id"] == "test-project"
        assert provider._app == mock_app

    @patch("patronus.providers.gcip.firebase_admin")
    @patch("patronus.providers.gcip.credentials")
    def test_init_with_json_string_with_whitespace(
        self, mock_credentials, mock_firebase_admin
    ):
        """Test GCIPProvider handles JSON strings with leading/trailing whitespace."""
        mock_cred = MagicMock()
        mock_credentials.Certificate.return_value = mock_cred
        mock_app = MagicMock()
        mock_firebase_admin.initialize_app.return_value = mock_app

        # JSON string with whitespace
        json_string = '  \n  {"type": "service_account", "project_id": "test"}  \n  '

        provider = GCIPProvider(credentials_config=json_string)

        # Should be called with parsed dict
        call_args = mock_credentials.Certificate.call_args[0][0]
        assert isinstance(call_args, dict)
        assert call_args["type"] == "service_account"
        assert provider._app == mock_app

    @patch("patronus.providers.gcip.firebase_admin")
    @patch("patronus.providers.gcip.credentials")
    def test_init_with_invalid_json_falls_back_to_file_path(
        self, mock_credentials, mock_firebase_admin
    ):
        """Test GCIPProvider treats invalid JSON starting with '{' as file path."""
        mock_cred = MagicMock()
        mock_credentials.Certificate.return_value = mock_cred
        mock_app = MagicMock()
        mock_firebase_admin.initialize_app.return_value = mock_app

        # Invalid JSON that starts with '{'
        invalid_json = "{this is not valid json}"

        provider = GCIPProvider(credentials_config=invalid_json)

        # Should be called with original string (treated as file path)
        mock_credentials.Certificate.assert_called_once_with(invalid_json)
        assert provider._app == mock_app

    @patch("patronus.providers.gcip.firebase_admin")
    @patch("patronus.providers.gcip.credentials")
    def test_init_with_file_path_not_affected(
        self, mock_credentials, mock_firebase_admin
    ):
        """Test that regular file paths are not affected by JSON parsing."""
        mock_cred = MagicMock()
        mock_credentials.Certificate.return_value = mock_cred
        mock_app = MagicMock()
        mock_firebase_admin.initialize_app.return_value = mock_app

        file_path = "/path/to/service-account.json"

        provider = GCIPProvider(credentials_config=file_path)

        # Should be called with original file path string
        mock_credentials.Certificate.assert_called_once_with(file_path)
        assert provider._app == mock_app


class TestGCIPProviderInitialization:
    """Tests for GCIPProvider initialization with different credential types."""

    @patch("patronus.providers.gcip.firebase_admin")
    @patch("patronus.providers.gcip.credentials")
    def test_init_with_dict_credentials(self, mock_credentials, mock_firebase_admin):
        """Test GCIPProvider initialization with dict credentials."""
        mock_cred = MagicMock()
        mock_credentials.Certificate.return_value = mock_cred
        mock_app = MagicMock()
        mock_firebase_admin.initialize_app.return_value = mock_app

        creds_dict = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
        }

        provider = GCIPProvider(credentials_config=creds_dict)

        mock_credentials.Certificate.assert_called_once_with(creds_dict)
        mock_firebase_admin.initialize_app.assert_called_once()
        assert provider._app == mock_app

    @patch("patronus.providers.gcip.firebase_admin")
    @patch("patronus.providers.gcip.credentials")
    def test_init_with_path_credentials(self, mock_credentials, mock_firebase_admin):
        """Test GCIPProvider initialization with file path credentials."""
        mock_cred = MagicMock()
        mock_credentials.Certificate.return_value = mock_cred
        mock_app = MagicMock()
        mock_firebase_admin.initialize_app.return_value = mock_app

        creds_path = "/path/to/service-account.json"

        provider = GCIPProvider(credentials_config=creds_path)

        mock_credentials.Certificate.assert_called_once_with(creds_path)
        mock_firebase_admin.initialize_app.assert_called_once()
        assert provider._app == mock_app

    @patch("patronus.providers.gcip.firebase_admin")
    @patch("patronus.providers.gcip.credentials")
    def test_init_with_none_uses_application_default(
        self, mock_credentials, mock_firebase_admin
    ):
        """Test GCIPProvider initialization with None uses application default credentials."""
        mock_cred = MagicMock()
        mock_credentials.ApplicationDefault.return_value = mock_cred
        mock_app = MagicMock()
        mock_firebase_admin.initialize_app.return_value = mock_app

        provider = GCIPProvider(credentials_config=None)

        mock_credentials.ApplicationDefault.assert_called_once()
        mock_credentials.Certificate.assert_not_called()
        mock_firebase_admin.initialize_app.assert_called_once()
        assert provider._app == mock_app

    @patch("patronus.providers.gcip.firebase_admin")
    @patch("patronus.providers.gcip.credentials")
    def test_init_uses_unique_app_name(self, mock_credentials, mock_firebase_admin):
        """Test that each GCIPProvider instance uses a unique app name."""
        mock_cred = MagicMock()
        mock_credentials.Certificate.return_value = mock_cred

        # Keep both instances alive to ensure different IDs
        _provider1 = GCIPProvider(credentials_config={"type": "service_account"})
        _provider2 = GCIPProvider(credentials_config={"type": "service_account"})

        # Ensure both are kept alive (prevents garbage collection)
        assert _provider1 is not _provider2

        # Check that initialize_app was called with different app names
        calls = mock_firebase_admin.initialize_app.call_args_list
        assert len(calls) == 2

        # App names should include the instance id and be different
        app_name1 = calls[0][1]["name"]
        app_name2 = calls[1][1]["name"]
        assert app_name1.startswith("patronus_")
        assert app_name2.startswith("patronus_")
        assert app_name1 != app_name2


@pytest.fixture
def mock_firebase_auth():
    """
    Create a mock for firebase_admin.auth that preserves exception classes.

    This fixture patches the auth module while keeping the real exception classes,
    allowing them to be raised and caught properly in exception handlers.
    """
    with patch("patronus.providers.gcip.auth") as mock_auth:
        # Preserve the real exception classes so they can be caught
        mock_auth.InvalidIdTokenError = firebase_auth.InvalidIdTokenError
        mock_auth.ExpiredIdTokenError = firebase_auth.ExpiredIdTokenError
        mock_auth.RevokedIdTokenError = firebase_auth.RevokedIdTokenError
        yield mock_auth


@pytest.fixture
def mock_gcip_provider():
    """Create a GCIPProvider with mocked Firebase initialization."""
    with (
        patch("patronus.providers.gcip.firebase_admin") as mock_firebase,
        patch("patronus.providers.gcip.credentials") as mock_creds,
    ):
        mock_creds.Certificate.return_value = MagicMock()
        mock_firebase.initialize_app.return_value = MagicMock()
        provider = GCIPProvider(credentials_config={"type": "service_account"})
        yield provider


class TestGCIPProviderVerifyToken:
    """Tests for GCIPProvider.verify_token method."""

    def test_verify_token_returns_correct_token_payload(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test that verify_token returns correct TokenPayload for valid token."""
        mock_firebase_auth.verify_id_token.return_value = {
            "uid": "user-123",
            "email": "user@example.com",
            "email_verified": True,
            "phone_number": "+5511999999999",
            "custom_claim": "value",
        }

        result = mock_gcip_provider.verify_token("valid-token")

        assert isinstance(result, TokenPayload)
        assert result.uid == "user-123"
        assert result.email == "user@example.com"
        assert result.email_verified is True
        assert result.phone_number == "+5511999999999"
        assert result.claims["custom_claim"] == "value"

    def test_verify_token_handles_missing_optional_fields(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test verify_token handles tokens with missing optional fields."""
        mock_firebase_auth.verify_id_token.return_value = {
            "uid": "user-456",
            # No email, email_verified, or phone_number
        }

        result = mock_gcip_provider.verify_token("valid-token")

        assert result.uid == "user-456"
        assert result.email is None
        assert result.email_verified is False  # Default value
        assert result.phone_number is None

    def test_verify_token_raises_invalid_token_error(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test verify_token raises InvalidTokenError for invalid tokens."""
        mock_firebase_auth.verify_id_token.side_effect = (
            firebase_auth.InvalidIdTokenError("Token is malformed")
        )

        with pytest.raises(InvalidTokenError) as exc_info:
            mock_gcip_provider.verify_token("invalid-token")

        assert "Token is malformed" in str(exc_info.value.detail)

    def test_verify_token_raises_expired_token_error(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test verify_token raises ExpiredTokenError for expired tokens."""
        mock_firebase_auth.verify_id_token.side_effect = (
            firebase_auth.ExpiredIdTokenError("Token has expired", cause=None)
        )

        with pytest.raises(ExpiredTokenError) as exc_info:
            mock_gcip_provider.verify_token("expired-token")

        assert "expired" in str(exc_info.value.detail).lower()

    def test_verify_token_raises_revoked_token_error(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test verify_token raises RevokedTokenError for revoked tokens."""
        mock_firebase_auth.verify_id_token.side_effect = (
            firebase_auth.RevokedIdTokenError("Token has been revoked")
        )

        with pytest.raises(RevokedTokenError) as exc_info:
            mock_gcip_provider.verify_token("revoked-token")

        assert "revoked" in str(exc_info.value.detail).lower()

    def test_verify_token_raises_provider_error_for_unexpected_errors(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test verify_token raises ProviderError for unexpected exceptions."""
        mock_firebase_auth.verify_id_token.side_effect = Exception("Network error")

        with pytest.raises(ProviderError) as exc_info:
            mock_gcip_provider.verify_token("some-token")

        assert "Network error" in str(exc_info.value.detail)


class TestGCIPProviderRevokeToken:
    """Tests for GCIPProvider.revoke_token method."""

    def test_revoke_token_calls_firebase_correctly(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test revoke_token decodes token and revokes refresh tokens."""
        mock_firebase_auth.verify_id_token.return_value = {"uid": "user-123"}

        mock_gcip_provider.revoke_token("valid-token")

        # Verify token was decoded without checking revocation
        mock_firebase_auth.verify_id_token.assert_called_once()
        call_kwargs = mock_firebase_auth.verify_id_token.call_args[1]
        assert call_kwargs.get("check_revoked") is False

        # Verify refresh tokens were revoked for the user
        mock_firebase_auth.revoke_refresh_tokens.assert_called_once_with(
            "user-123", app=mock_gcip_provider._app
        )

    def test_revoke_token_raises_provider_error_on_failure(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test revoke_token raises ProviderError when Firebase fails."""
        mock_firebase_auth.verify_id_token.side_effect = Exception(
            "Firebase unavailable"
        )

        with pytest.raises(ProviderError) as exc_info:
            mock_gcip_provider.revoke_token("some-token")

        assert "Firebase unavailable" in str(exc_info.value.detail)


class TestGCIPProviderGetUserByUid:
    """Tests for GCIPProvider.get_user_by_uid method."""

    def test_get_user_by_uid_returns_user_dict(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test get_user_by_uid returns correctly formatted user dict."""
        mock_user = MagicMock()
        mock_user.uid = "user-123"
        mock_user.email = "user@example.com"
        mock_user.phone_number = "+5511999999999"
        mock_user.display_name = "Test User"
        mock_user.email_verified = True
        mock_firebase_auth.get_user.return_value = mock_user

        result = mock_gcip_provider.get_user_by_uid("user-123")

        assert result == {
            "uid": "user-123",
            "email": "user@example.com",
            "phone_number": "+5511999999999",
            "display_name": "Test User",
            "email_verified": True,
        }
        mock_firebase_auth.get_user.assert_called_once_with(
            "user-123", app=mock_gcip_provider._app
        )

    def test_get_user_by_uid_raises_provider_error_on_failure(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test get_user_by_uid raises ProviderError when Firebase fails."""
        mock_firebase_auth.get_user.side_effect = Exception("User not found")

        with pytest.raises(ProviderError) as exc_info:
            mock_gcip_provider.get_user_by_uid("unknown-user")

        assert "User not found" in str(exc_info.value.detail)


class TestGCIPProviderAsyncMethods:
    """Tests for GCIPProvider async methods."""

    @pytest.mark.asyncio
    async def test_verify_token_async_returns_token_payload(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test verify_token_async returns TokenPayload via executor."""
        mock_firebase_auth.verify_id_token.return_value = {
            "uid": "user-123",
            "email": "user@example.com",
            "email_verified": True,
        }

        result = await mock_gcip_provider.verify_token_async("valid-token")

        assert isinstance(result, TokenPayload)
        assert result.uid == "user-123"
        assert result.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_verify_token_async_propagates_errors(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test verify_token_async propagates InvalidTokenError."""
        mock_firebase_auth.verify_id_token.side_effect = (
            firebase_auth.InvalidIdTokenError("Invalid token")
        )

        with pytest.raises(InvalidTokenError):
            await mock_gcip_provider.verify_token_async("invalid-token")

    @pytest.mark.asyncio
    async def test_revoke_token_async_calls_sync_method(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test revoke_token_async calls sync revoke_token via executor."""
        mock_firebase_auth.verify_id_token.return_value = {"uid": "user-123"}

        await mock_gcip_provider.revoke_token_async("valid-token")

        mock_firebase_auth.revoke_refresh_tokens.assert_called_once_with(
            "user-123", app=mock_gcip_provider._app
        )

    @pytest.mark.asyncio
    async def test_get_user_by_uid_async_returns_user_dict(
        self, mock_firebase_auth, mock_gcip_provider
    ):
        """Test get_user_by_uid_async returns user dict via executor."""
        mock_user = MagicMock()
        mock_user.uid = "user-123"
        mock_user.email = "user@example.com"
        mock_user.phone_number = None
        mock_user.display_name = "Test User"
        mock_user.email_verified = True
        mock_firebase_auth.get_user.return_value = mock_user

        result = await mock_gcip_provider.get_user_by_uid_async("user-123")

        assert result["uid"] == "user-123"
        assert result["email"] == "user@example.com"
        assert result["display_name"] == "Test User"


class TestGCIPProviderIsAuthProvider:
    """Tests verifying GCIPProvider properly implements AuthProvider."""

    @patch("patronus.providers.gcip.firebase_admin")
    @patch("patronus.providers.gcip.credentials")
    def test_gcip_provider_is_auth_provider_subclass(
        self, mock_credentials, mock_firebase_admin
    ):
        """Test that GCIPProvider is a subclass of AuthProvider."""
        assert issubclass(GCIPProvider, AuthProvider)

    @patch("patronus.providers.gcip.firebase_admin")
    @patch("patronus.providers.gcip.credentials")
    def test_gcip_provider_instance_is_auth_provider(
        self, mock_credentials, mock_firebase_admin
    ):
        """Test that GCIPProvider instance is an AuthProvider instance."""
        mock_credentials.Certificate.return_value = MagicMock()
        mock_firebase_admin.initialize_app.return_value = MagicMock()

        provider = GCIPProvider(credentials_config={"type": "service_account"})

        assert isinstance(provider, AuthProvider)
