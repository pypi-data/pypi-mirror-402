"""
Tests for Django middleware for tenant context injection.

This module tests the TenantMiddleware which automatically injects
the authenticated user's company_id into the tenant context for use
throughout the request lifecycle.
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from django.http import HttpRequest, HttpResponse

from patronus import (
    NovahUser,
    clear_current_company,
    get_current_company,
    set_current_company,
)
from patronus.middleware import TenantMiddleware


class TestTenantMiddlewareWithNovahUser:
    """Tests for TenantMiddleware with authenticated NovahUser."""

    def test_sets_company_context_for_novah_user_requests(self):
        """Test middleware sets company context when request has NovahUser."""
        company_id = uuid4()

        # Create a NovahUser
        user = NovahUser(
            identity_provider_uid="test-uid-123",
            email="test@example.com",
            phone_number=None,
            company_id=company_id,
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        # Track context during request processing
        context_during_request = None

        def get_response(request):
            nonlocal context_during_request
            context_during_request = get_current_company()
            return HttpResponse("OK")

        # Create request with NovahUser
        request = HttpRequest()
        request.user = user

        # Clear context before test
        clear_current_company()

        # Process request through middleware
        middleware = TenantMiddleware(get_response)
        middleware(request)

        # Context should have been set during request processing
        assert context_during_request == company_id

    def test_context_available_in_nested_views(self):
        """Test company context is available in nested view calls."""
        company_id = uuid4()

        user = NovahUser(
            identity_provider_uid="test-uid",
            email="test@example.com",
            phone_number=None,
            company_id=company_id,
            permissions=frozenset(),
            profile_type="colaborador",
        )

        contexts_captured = []

        def get_response(request):
            # Simulate nested function calls that check context
            contexts_captured.append(get_current_company())

            def inner_function():
                contexts_captured.append(get_current_company())

            inner_function()
            return HttpResponse("OK")

        request = HttpRequest()
        request.user = user

        clear_current_company()
        middleware = TenantMiddleware(get_response)
        middleware(request)

        # All nested calls should see the same company context
        assert all(ctx == company_id for ctx in contexts_captured)


class TestTenantMiddlewareUnauthenticated:
    """Tests for TenantMiddleware with unauthenticated requests."""

    def test_does_nothing_for_unauthenticated_requests(self):
        """Test middleware does nothing when request has no user."""
        context_during_request = None

        def get_response(request):
            nonlocal context_during_request
            context_during_request = get_current_company()
            return HttpResponse("OK")

        # Create request without user attribute
        request = HttpRequest()
        # request.user is not set

        clear_current_company()

        middleware = TenantMiddleware(get_response)
        middleware(request)

        # Context should remain None (not set)
        assert context_during_request is None

    def test_does_nothing_for_anonymous_user(self):
        """Test middleware does nothing for non-NovahUser user objects."""
        context_during_request = None

        def get_response(request):
            nonlocal context_during_request
            context_during_request = get_current_company()
            return HttpResponse("OK")

        # Create request with anonymous user (not NovahUser)
        request = HttpRequest()
        request.user = MagicMock()  # Some other user type
        request.user.__class__ = object  # Ensure it's not NovahUser

        clear_current_company()

        middleware = TenantMiddleware(get_response)
        middleware(request)

        # Context should remain None for non-NovahUser
        assert context_during_request is None

    def test_does_nothing_when_user_is_none(self):
        """Test middleware does nothing when user is explicitly None."""
        context_during_request = None

        def get_response(request):
            nonlocal context_during_request
            context_during_request = get_current_company()
            return HttpResponse("OK")

        request = HttpRequest()
        request.user = None

        clear_current_company()

        middleware = TenantMiddleware(get_response)
        middleware(request)

        assert context_during_request is None


class TestTenantMiddlewareContextCleanup:
    """Tests for TenantMiddleware context cleanup."""

    def test_clears_context_after_request_completes(self):
        """Test middleware clears context after request processing."""
        company_id = uuid4()

        user = NovahUser(
            identity_provider_uid="test-uid",
            email="test@example.com",
            phone_number=None,
            company_id=company_id,
            permissions=frozenset(),
            profile_type="colaborador",
        )

        context_during = None

        def get_response(request):
            nonlocal context_during
            context_during = get_current_company()
            return HttpResponse("OK")

        request = HttpRequest()
        request.user = user

        clear_current_company()

        middleware = TenantMiddleware(get_response)
        middleware(request)

        # Context should be set during request
        assert context_during == company_id

        # Context should be cleared after request
        assert get_current_company() is None

    def test_clears_context_even_if_exception_raised(self):
        """Test middleware clears context even when view raises exception."""
        company_id = uuid4()

        user = NovahUser(
            identity_provider_uid="test-uid",
            email="test@example.com",
            phone_number=None,
            company_id=company_id,
            permissions=frozenset(),
            profile_type="colaborador",
        )

        def get_response(request):
            # Verify context is set before exception
            assert get_current_company() == company_id
            raise ValueError("View error")

        request = HttpRequest()
        request.user = user

        clear_current_company()

        middleware = TenantMiddleware(get_response)

        # The exception should propagate
        with pytest.raises(ValueError, match="View error"):
            middleware(request)

        # Context should still be cleared even after exception
        assert get_current_company() is None

    def test_clears_context_for_unauthenticated_requests(self):
        """Test middleware clears context for unauthenticated requests too."""

        def get_response(request):
            return HttpResponse("OK")

        request = HttpRequest()
        # No user set

        # Pre-set some context to verify cleanup
        set_current_company(uuid4())

        middleware = TenantMiddleware(get_response)
        middleware(request)

        # Context should be cleared
        assert get_current_company() is None


class TestTenantMiddlewareInitialization:
    """Tests for TenantMiddleware initialization."""

    def test_constructor_stores_get_response(self):
        """Test middleware constructor stores get_response callable."""

        def my_get_response(request):
            return HttpResponse("OK")

        middleware = TenantMiddleware(my_get_response)

        assert middleware.get_response is my_get_response

    def test_middleware_is_callable(self):
        """Test middleware instance is callable."""

        def get_response(request):
            return HttpResponse("OK")

        middleware = TenantMiddleware(get_response)

        assert callable(middleware)


class TestTenantMiddlewareResponseHandling:
    """Tests for TenantMiddleware response handling."""

    def test_returns_response_from_get_response(self):
        """Test middleware returns the response from get_response."""
        expected_response = HttpResponse("Test Response", status=200)

        def get_response(request):
            return expected_response

        request = HttpRequest()

        middleware = TenantMiddleware(get_response)
        result = middleware(request)

        assert result is expected_response

    def test_returns_response_for_authenticated_requests(self):
        """Test middleware returns response for authenticated requests."""
        company_id = uuid4()

        user = NovahUser(
            identity_provider_uid="test-uid",
            email="test@example.com",
            phone_number=None,
            company_id=company_id,
            permissions=frozenset(),
            profile_type="colaborador",
        )

        expected_response = HttpResponse("Authenticated Response", status=200)

        def get_response(request):
            return expected_response

        request = HttpRequest()
        request.user = user

        clear_current_company()

        middleware = TenantMiddleware(get_response)
        result = middleware(request)

        assert result is expected_response
        assert result.status_code == 200


class TestTenantMiddlewareEdgeCases:
    """Tests for TenantMiddleware edge cases."""

    def test_handles_multiple_sequential_requests(self):
        """Test middleware handles multiple sequential requests correctly."""
        company_a = uuid4()
        company_b = uuid4()

        user_a = NovahUser(
            identity_provider_uid="user-a",
            email="a@example.com",
            phone_number=None,
            company_id=company_a,
            permissions=frozenset(),
            profile_type="colaborador",
        )

        user_b = NovahUser(
            identity_provider_uid="user-b",
            email="b@example.com",
            phone_number=None,
            company_id=company_b,
            permissions=frozenset(),
            profile_type="colaborador",
        )

        contexts = []

        def get_response(request):
            contexts.append(get_current_company())
            return HttpResponse("OK")

        middleware = TenantMiddleware(get_response)

        # First request
        request_a = HttpRequest()
        request_a.user = user_a
        clear_current_company()
        middleware(request_a)

        # Second request (should get fresh context)
        request_b = HttpRequest()
        request_b.user = user_b
        middleware(request_b)

        # Each request should have seen its own company context
        assert contexts[0] == company_a
        assert contexts[1] == company_b

        # Context should be cleared after last request
        assert get_current_company() is None

    def test_handles_phone_authenticated_user(self):
        """Test middleware works with phone-authenticated NovahUser."""
        company_id = uuid4()

        user = NovahUser(
            identity_provider_uid="phone-user",
            email=None,
            phone_number="+5511999999999",
            company_id=company_id,
            permissions=frozenset(["read:patients"]),
            profile_type="colaborador",
        )

        context_during = None

        def get_response(request):
            nonlocal context_during
            context_during = get_current_company()
            return HttpResponse("OK")

        request = HttpRequest()
        request.user = user

        clear_current_company()

        middleware = TenantMiddleware(get_response)
        middleware(request)

        assert context_during == company_id
        assert get_current_company() is None
