"""
Tenant context management using contextvars.

This module provides thread-safe and async-safe tenant context management
using Python's contextvars. The context is automatically isolated between
concurrent requests and async tasks.

Example usage:
    # Set context for the current request
    set_current_company(user.company_id)

    # Get context anywhere in the request lifecycle
    company_id = get_current_company()

    # Use context manager for scoped access
    with company_context(company_id):
        do_tenant_scoped_work()
"""

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import UUID

# Context variable for storing the current company ID
# Default is None, indicating no tenant context is set
_current_company: ContextVar[UUID | None] = ContextVar("current_company", default=None)


def get_current_company() -> UUID | None:
    """
    Get the current company ID from context.

    Returns:
        The UUID of the current company, or None if no context is set.

    Example:
        company_id = get_current_company()
        if company_id is not None:
            # Filter queries by company
            queryset = Model.objects.filter(company_id=company_id)
    """
    return _current_company.get()


def set_current_company(company_id: UUID) -> None:
    """
    Set the current company ID in context.

    This should typically be called by middleware after authentication.
    The context is automatically isolated between concurrent requests.

    Args:
        company_id: The UUID of the company to set as current.

    Example:
        set_current_company(user.company_id)
    """
    _current_company.set(company_id)


def clear_current_company() -> None:
    """
    Clear the current company from context.

    This should be called at the end of request processing to ensure
    proper cleanup. The TenantMiddleware handles this automatically.
    """
    _current_company.set(None)


@contextmanager
def company_context(company_id: UUID) -> Generator[None]:
    """
    Context manager for scoped company context.

    This provides a safe way to temporarily set the company context
    for a block of code. The previous context is automatically restored
    when exiting the block, even if an exception is raised.

    Args:
        company_id: The UUID of the company to set as current.

    Yields:
        None

    Example:
        with company_context(company_id):
            # All code here sees company_id as current company
            do_tenant_scoped_work()
        # Previous context is restored here

    Note:
        This works correctly with nested contexts:

        with company_context(company_a):
            # company_a is current
            with company_context(company_b):
                # company_b is current
            # company_a is current again
    """
    token = _current_company.set(company_id)
    try:
        yield
    finally:
        _current_company.reset(token)
