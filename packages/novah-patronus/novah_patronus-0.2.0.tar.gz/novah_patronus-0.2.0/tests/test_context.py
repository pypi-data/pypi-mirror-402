"""
Tests for tenant context management.

This module tests the context functions and context manager to ensure
they work correctly with contextvars for async-safe tenant isolation.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from patronus import (
    clear_current_company,
    company_context,
    get_current_company,
    set_current_company,
)


class TestGetCurrentCompany:
    """Tests for get_current_company function."""

    def test_returns_none_when_not_set(self):
        """Test get_current_company returns None when no context is set."""
        # Ensure we start with clean context
        clear_current_company()

        result = get_current_company()

        assert result is None

    def test_returns_company_id_after_set(self):
        """Test get_current_company returns the company ID after it is set."""
        company_id = uuid4()
        set_current_company(company_id)

        try:
            result = get_current_company()
            assert result == company_id
        finally:
            clear_current_company()


class TestSetCurrentCompany:
    """Tests for set_current_company function."""

    def test_sets_company_correctly(self):
        """Test set_current_company sets the company ID correctly."""
        company_id = uuid4()

        set_current_company(company_id)

        try:
            assert get_current_company() == company_id
        finally:
            clear_current_company()

    def test_overwrites_previous_value(self):
        """Test set_current_company overwrites the previous value."""
        company_a = uuid4()
        company_b = uuid4()

        set_current_company(company_a)
        assert get_current_company() == company_a

        set_current_company(company_b)
        try:
            assert get_current_company() == company_b
        finally:
            clear_current_company()


class TestClearCurrentCompany:
    """Tests for clear_current_company function."""

    def test_clears_the_context(self):
        """Test clear_current_company clears the context."""
        company_id = uuid4()
        set_current_company(company_id)

        clear_current_company()

        assert get_current_company() is None

    def test_clears_when_already_none(self):
        """Test clear_current_company works when context is already None."""
        clear_current_company()

        # Should not raise
        clear_current_company()

        assert get_current_company() is None


class TestCompanyContext:
    """Tests for company_context context manager."""

    def test_sets_context_inside_block(self):
        """Test company_context sets the context inside the block."""
        company_id = uuid4()

        with company_context(company_id):
            assert get_current_company() == company_id

    def test_restores_none_on_exit(self):
        """Test company_context restores None when exiting."""
        company_id = uuid4()
        clear_current_company()

        with company_context(company_id):
            assert get_current_company() == company_id

        assert get_current_company() is None

    def test_restores_previous_value_on_exit(self):
        """Test company_context restores previous value on exit."""
        company_a = uuid4()
        company_b = uuid4()

        set_current_company(company_a)
        try:
            with company_context(company_b):
                assert get_current_company() == company_b

            assert get_current_company() == company_a
        finally:
            clear_current_company()

    def test_restores_on_exception(self):
        """Test company_context restores context even when exception is raised."""
        company_a = uuid4()
        company_b = uuid4()

        set_current_company(company_a)
        try:
            with pytest.raises(ValueError), company_context(company_b):
                assert get_current_company() == company_b
                raise ValueError("Test exception")

            # Previous context should be restored
            assert get_current_company() == company_a
        finally:
            clear_current_company()

    def test_nested_contexts(self):
        """Test company_context works correctly with nested contexts."""
        company_a = uuid4()
        company_b = uuid4()
        company_c = uuid4()

        clear_current_company()

        with company_context(company_a):
            assert get_current_company() == company_a

            with company_context(company_b):
                assert get_current_company() == company_b

                with company_context(company_c):
                    assert get_current_company() == company_c

                assert get_current_company() == company_b

            assert get_current_company() == company_a

        assert get_current_company() is None


class TestContextIsolation:
    """Tests for context isolation between concurrent operations."""

    def test_context_isolation_between_threads(self):
        """Test context is isolated between threads using contextvars."""
        company_a = uuid4()
        company_b = uuid4()
        results = {}

        def thread_work(thread_id: str, company_id):
            """Work performed in a thread."""
            set_current_company(company_id)
            # Small delay to increase chance of interleaving
            time.sleep(0.01)
            results[thread_id] = get_current_company()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(thread_work, "thread_a", company_a)
            future_b = executor.submit(thread_work, "thread_b", company_b)
            future_a.result()
            future_b.result()

        # Each thread should see its own context
        assert results["thread_a"] == company_a
        assert results["thread_b"] == company_b

    @pytest.mark.asyncio
    async def test_context_isolation_between_async_tasks(self):
        """Test context is isolated between async tasks using contextvars."""
        company_a = uuid4()
        company_b = uuid4()
        results = {}

        async def async_work(task_id: str, company_id):
            """Work performed in an async task."""
            set_current_company(company_id)
            # Yield to allow task interleaving
            await asyncio.sleep(0.01)
            results[task_id] = get_current_company()

        # Run tasks concurrently
        await asyncio.gather(
            async_work("task_a", company_a),
            async_work("task_b", company_b),
        )

        # Each task should see its own context
        assert results["task_a"] == company_a
        assert results["task_b"] == company_b

    def test_context_manager_isolation_in_nested_threads(self):
        """Test context manager maintains isolation in nested thread scenarios."""
        main_company = uuid4()
        thread_company = uuid4()
        results = {"main_before": None, "main_after": None, "thread": None}

        def thread_work():
            """Work in a separate thread with its own context."""
            with company_context(thread_company):
                results["thread"] = get_current_company()

        with company_context(main_company):
            results["main_before"] = get_current_company()

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(thread_work)
                future.result()

            results["main_after"] = get_current_company()

        # Main thread context should be maintained
        assert results["main_before"] == main_company
        assert results["main_after"] == main_company
        # Thread should have its own context
        assert results["thread"] == thread_company
