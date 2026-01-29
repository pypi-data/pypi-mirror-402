"""
Patronus - Production-ready authentication library for Django REST Framework.

Patronus provides a provider-agnostic authentication solution for Django REST Framework
applications in the Novah Care ecosystem. It includes support for Google Cloud Identity
Platform (GCIP), tenant context management, and DRF-compatible permission classes.

Example usage:
    # settings.py
    PATRONUS = {
        "PROVIDER_CLASS": "patronus.providers.gcip.GCIPProvider",
        "PROVIDER_CREDENTIALS": json.loads(os.environ.get("GCIP_CREDENTIALS", "{}")),
        "PROFILE_LOADER_CLASS": "your_app.auth.YourProfileLoader",
    }

    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "patronus.PatronusAuthentication",
        ],
    }

    MIDDLEWARE = [
        # ... other middleware ...
        "patronus.TenantMiddleware",
    ]
"""

from patronus.authentication import PatronusAuthentication
from patronus.context import (
    clear_current_company,
    company_context,
    get_current_company,
    set_current_company,
)
from patronus.exceptions import (
    ExpiredTokenError,
    InvalidTokenError,
    NoProfileError,
    PatronusException,
    ProviderError,
    RevokedTokenError,
    TenantMismatchError,
)
from patronus.middleware import TenantMiddleware
from patronus.permissions import (
    HasAnyPermission,
    HasPermission,
    HasProfile,
    IsSameCompany,
)
from patronus.profile_loader import MockProfileLoader, ProfileLoader
from patronus.providers.base import AuthProvider
from patronus.settings import (
    PatronusSettings,
    get_profile_loader,
    get_provider,
    get_settings,
    reset_instances,
)
from patronus.user import NovahUser, TokenPayload, UserProfile

__version__ = "0.1.0"

__all__ = [
    "AuthProvider",
    "ExpiredTokenError",
    "HasAnyPermission",
    "HasPermission",
    "HasProfile",
    "InvalidTokenError",
    "IsSameCompany",
    "MockProfileLoader",
    "NoProfileError",
    "NovahUser",
    "PatronusAuthentication",
    "PatronusException",
    "PatronusSettings",
    "ProfileLoader",
    "ProviderError",
    "RevokedTokenError",
    "TenantMiddleware",
    "TenantMismatchError",
    "TokenPayload",
    "UserProfile",
    "__version__",
    "clear_current_company",
    "company_context",
    "get_current_company",
    "get_profile_loader",
    "get_provider",
    "get_settings",
    "reset_instances",
    "set_current_company",
]
