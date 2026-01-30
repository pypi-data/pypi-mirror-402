"""
This module contains the BearerAuth class.
"""

import asyncio
import threading
from typing import AsyncGenerator, Generator

from httpx import Auth, Request, Response
from overrides import override

from .authenticator import IAuthenticator


class AuthenticationError(Exception):
    """Raised when an authentication error occurs."""


class NoAuthenticationResultError(Exception):
    """Raised when no authentication result is received."""


class NoAccessTokenError(Exception):
    """Raised when no access token is present in the authentication result."""


class BearerAuth(Auth):
    """
    BearerAuth is an authentication class that implements the 'httpx.Auth' interface for
    handling bearer token-based authentication. It acquires access tokens using an instance
    of 'IAuthenticator'. The access token is added to the 'Authorization' header of the
    outgoing HTTP request.
    """

    def __init__(self, authenticator: IAuthenticator):
        """
        Initializes a BearerAuth instance with the provided authenticator.

        Args:
            authenticator (IAuthenticator): The authenticator.
        """
        self._authenticator = authenticator
        self._sync_lock: threading.Lock = threading.Lock()
        self._async_lock: asyncio.Lock = asyncio.Lock()

    @override
    def sync_auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        """
        Performs the synchronous authentication for the given request.

        Args:
            request (Request): The outgoing HTTP request.

        Yields:
            Generator[Request, Response, None]: The modified request with the authentication
            header.
        """
        with self._sync_lock:
            access_token = self._acquire_token()
        request.headers["Authorization"] = self._get_bearer_token_header(access_token)
        yield request

    @override
    async def async_auth_flow(
        self, request: Request
    ) -> AsyncGenerator[Request, Response]:
        """
        Performs the asynchronous authentication for the given request.

        Args:
            request (Request): The outgoing HTTP request.

        Yields:
            AsyncGenerator[Request, Response]: The modified request with the authentication header.
        """
        async with self._async_lock:
            access_token = self._acquire_token()
        request.headers["Authorization"] = self._get_bearer_token_header(access_token)
        yield request

    def _acquire_token(self) -> str:
        """
        Acquires a new access token using the authenticator.

        This method invokes the authenticate method of the authenticator object to acquire a new
        access token. The method checks the authentication result for the presence of an
        'access_token' or an 'error'. If an 'access_token' is present, it is returned. If an
        'error' is present, an exception is raised with the error message. If the authentication
        result is None, an exception is raised indicating no authentication result was received.

        Returns:
            str: The access token if authentication is successful.

        Raises:
            Exception: If no authentication result is received, if authentication fails, or if no
            access token is present in the authentication result.
        """
        auth_result = self._authenticator.authenticate()

        if not auth_result:
            raise NoAuthenticationResultError("No authentication result received.")

        if "error" in auth_result:
            raise AuthenticationError(
                f"Authentication failed with error: {auth_result['error']}"
            )

        if "access_token" not in auth_result:
            raise NoAccessTokenError("No access token in authentication result.")

        return auth_result["access_token"]

    def _get_bearer_token_header(self, access_token: str) -> str:
        """
        Generates a bearer token header from an access token.

        Args:
            access_token (str): The access token to include in the header.

        Returns:
            str: The bearer token header.
        """
        return f"Bearer {access_token}"
