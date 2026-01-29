"""
Django middleware for tenant context injection.

This module provides the TenantMiddleware which automatically injects
the authenticated user's company_id into the tenant context for use
throughout the request lifecycle.
"""

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from patronus.context import clear_current_company, set_current_company
from patronus.user import NovahUser


class TenantMiddleware:
    """
    Middleware to inject tenant context from authenticated user.

    This middleware checks if the request has an authenticated NovahUser
    and if so, sets the company context for the duration of the request.
    The context is always cleaned up after the request completes, even
    if an exception is raised.

    Usage in Django settings:
        MIDDLEWARE = [
            # ... other middleware ...
            "patronus.TenantMiddleware",
        ]

    Note:
        This middleware should be placed after Django's authentication
        middleware and after any DRF authentication happens. In practice,
        DRF authentication happens in the view layer, so this middleware
        will set the context based on the user attached to the request
        by DRF authentication.

    Example flow:
        1. Request comes in
        2. DRF authentication runs, sets request.user to NovahUser
        3. TenantMiddleware sets company context
        4. View code can use get_current_company()
        5. Response is generated
        6. TenantMiddleware clears company context
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """
        Initialize the middleware.

        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process the request.

        If the request has an authenticated NovahUser, sets the company
        context. Always cleans up the context after the request.

        Args:
            request: The Django HttpRequest object.

        Returns:
            The HttpResponse from the next middleware or view.
        """
        # Check if user is authenticated with NovahUser
        user = getattr(request, "user", None)

        if user is not None and isinstance(user, NovahUser):
            set_current_company(user.company_id)

        try:
            response: HttpResponse = self.get_response(request)
        finally:
            # Always clean up context, even on exceptions
            clear_current_company()

        return response
