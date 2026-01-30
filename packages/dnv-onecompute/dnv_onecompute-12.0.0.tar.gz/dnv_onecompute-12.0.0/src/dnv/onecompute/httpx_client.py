"""
This module provides the AsyncRetryClient and RetryClient classes, which are HTTP clients that retry
requests using a custom transport implementing exponential backoff.
"""

from typing import Any, Optional

import httpx

from .http_retry_transport import RetryTransport


class AsyncRetryClient:
    """
    An asynchronous HTTP client that retries requests using a custom transport that
    implements exponential backoff.
    """

    def __init__(self, **kwargs: Any):
        """
        Initializes a new instance of the `AsyncRetryClient` class.

        Args:
            **kwargs: Additional arguments to pass to the `httpx.AsyncClient` constructor.

        """
        transport = RetryTransport(
            httpx.AsyncHTTPTransport(), max_attempts=5, backoff_factor=0.5
        )
        self._client = httpx.AsyncClient(**kwargs, transport=transport)

    async def __aenter__(self):
        """
        A coroutine that is invoked when an instance of the `AsyncRetryClient` class
        is used in a `async with` statement.

        Returns:
            httpx.AsyncClient: The underlying HTTP client.

        """
        return self._client

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ):
        """
        A coroutine that is invoked when an instance of the `AsyncRetryClient` class
        exits a `async with` statement.

        Args:
            exc_type (Optional[type]): The type of the exception that caused the
                context to be exited, if any.
            exc_val (Optional[BaseException]): The exception that caused the context
                to be exited, if any.
            exc_tb (Optional[Any]): The traceback of the exception that caused the
                context to be exited, if any.

        """
        await self._client.aclose()


class RetryClient:
    """
    A synchronous HTTP client that retries requests using a custom transport that
    implements exponential backoff.
    """

    def __init__(self, **kwargs: Any):
        """
        Initializes a new instance of the `RetryClient` class.

        Args:
            **kwargs: Additional arguments to pass to the `httpx.Client` constructor.

        """
        transport = RetryTransport(
            httpx.HTTPTransport(), max_attempts=5, backoff_factor=0.5
        )
        self._client = httpx.Client(**kwargs, transport=transport)

    def __enter__(self):
        """
        A method that is invoked when an instance of the `RetryClient` class is used
        in a `with` statement.

        Returns:
            httpx.Client: The underlying HTTP client.

        """
        return self._client

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ):
        """
        A method that is invoked when an instance of the `RetryClient` class exits
        a `with` statement.

        Args:
            exc_type (Optional[type]): The type of the exception that caused the
                context to be exited, if any.
            exc_val (Optional[BaseException]): The exception that caused the context
                to be exited, if any.
            exc_tb (Optional[Any]): The traceback of the exception that caused the
                context to be exited, if any.

        """
        self._client.close()
