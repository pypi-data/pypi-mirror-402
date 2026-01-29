"""
Identity provider implementations for Patronus.

This package contains the abstract AuthProvider interface and concrete
implementations for various identity providers.

Currently supported providers:
- GCIPProvider: Google Cloud Identity Platform (Firebase Auth)

Example usage:
    from patronus.providers import AuthProvider
    from patronus.providers.gcip import GCIPProvider

    provider = GCIPProvider(credentials_config={"type": "service_account", ...})
    token_payload = provider.verify_token(token)
"""

from patronus.providers.base import AuthProvider

__all__ = ["AuthProvider"]
