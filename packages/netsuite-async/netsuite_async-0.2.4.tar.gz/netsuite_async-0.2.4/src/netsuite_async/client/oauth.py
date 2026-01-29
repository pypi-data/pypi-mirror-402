from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
from typing import Mapping, MutableMapping, Optional

import httpx
from authlib.integrations.httpx_client import AsyncOAuth1Client
from netsuite_async.exceptions import NetsuiteAuthError, NetsuiteClientException
from netsuite_async.signature import SIGNATURE_HMAC_SHA256

__all__ = [
    "OAuth1Credentials",
    "AsyncAuthProvider",
    "OAuth1AsyncAuthProvider",
    "async_oauth1_client",
]


class AsyncAuthProvider(ABC):
    """Interface for components that can create authenticated Async HTTP clients."""

    @abstractmethod
    async def create_client(self) -> httpx.AsyncClient:
        """Return an authenticated HTTP client."""


@dataclass(frozen=True)
class OAuth1Credentials:
    """OAuth 1.0 credentials for NetSuite authentication.

    Args:
        consumer_key: OAuth consumer key
        consumer_secret: OAuth consumer secret
        token_key: OAuth token key
        token_secret: OAuth token secret
        realm: OAuth realm (defaults to NETSUITE_ACCOUNT_ID from environment)
    """

    consumer_key: str
    consumer_secret: str
    token_key: str
    token_secret: str
    realm: Optional[str] = None

    @classmethod
    def from_env(cls) -> "OAuth1Credentials":
        """Build credentials from environment variables, raising if any are missing.
        
        Required environment variables:
        - NETSUITE_CONSUMER_KEY
        - NETSUITE_CONSUMER_SECRET  
        - NETSUITE_TOKEN_KEY
        - NETSUITE_TOKEN_SECRET
        - NETSUITE_ACCOUNT_ID (optional, used as realm)
        
        Returns:
            OAuth1Credentials instance with values from environment
            
        Raises:
            NetsuiteAuthError: If any required environment variable is missing
            
        Example:
            >>> credentials = OAuth1Credentials.from_env()
            >>> auth_provider = OAuth1AsyncAuthProvider(credentials)
        """

        def require(name: str) -> str:
            value = os.getenv(name)
            if not value:
                raise NetsuiteAuthError(
                    f"Missing required NetSuite credential environment variable: {name}"
                )
            return value

        return cls(
            consumer_key=require("NETSUITE_CONSUMER_KEY"),
            consumer_secret=require("NETSUITE_CONSUMER_SECRET"),
            token_key=require("NETSUITE_TOKEN_KEY"),
            token_secret=require("NETSUITE_TOKEN_SECRET"),
            realm=os.getenv("NETSUITE_ACCOUNT_ID"),
        )


class OAuth1AsyncAuthProvider(AsyncAuthProvider):
    """Builds OAuth1-enabled Async HTTP clients with configurable transport."""

    def __init__(
        self,
        credentials: Optional[OAuth1Credentials] = None,
        *,
        timeout: float = 30.0,
        headers: Optional[Mapping[str, str]] = None,
        retries: int = 0,
        signature_method: str = SIGNATURE_HMAC_SHA256,
        **kwargs,
    ):
        """
        Initialize the auth provider.

        Args:
            credentials: Optional credentials object; defaults to loading from the
                environment when omitted.
            timeout: Request timeout passed to the Authlib client unless overridden
                via `kwargs`.
            headers: Extra headers merged into the NetSuite defaults.
            retries: Value forwarded to `AsyncOAuth1Client` (often consumed by the
                underlying transport implementation).
            **kwargs: Additional keyword arguments that are forwarded directly to
                `AsyncOAuth1Client`. Passing values here overrides the named params
                above, giving callers low-level control (e.g., custom transports,
                proxies, timeout objects) without us needing to expose every option.
        """
        self._credentials = credentials or OAuth1Credentials.from_env()
        self._timeout = timeout
        self._headers = headers
        self._retries = retries
        self._signature_method = signature_method
        self._kwargs = kwargs

    async def create_client(self) -> AsyncOAuth1Client:
        """Create an authenticated AsyncOAuth1Client for NetSuite API requests.
        
        Returns:
            Configured AsyncOAuth1Client with OAuth1 authentication and NetSuite headers
            
        Raises:
            NetsuiteClientException: If OAuth1 client configuration fails
            
        Example:
            >>> auth_provider = OAuth1AsyncAuthProvider()
            >>> client = await auth_provider.create_client()
            >>> response = await client.get('https://example.suitetalk.api.netsuite.com/...')
        """
        try:
            client = AsyncOAuth1Client(
                realm=self._credentials.realm,
                client_id=self._credentials.consumer_key,
                client_secret=self._credentials.consumer_secret,
                token=self._credentials.token_key,
                token_secret=self._credentials.token_secret,
                signature_method=self._signature_method,
                timeout=self._timeout,
                retries=self._retries,
                # CRITICAL: Authlib's AsyncOAuth1Client silently strips request bodies from POST/PATCH requests
                # by default, which breaks NetSuite REST API calls that require JSON payloads.
                # This parameter forces the client to include the body in OAuth signature calculation
                # and preserve it in the actual HTTP request.
                force_include_body=True,
                **self._kwargs,
            )
        except Exception as exc:  # pragma: no cover - authlib raises different errors
            raise NetsuiteClientException(
                f"Failed to configure OAuth1 client: {exc}"
            ) from exc
        client.headers.update(_apply_headers(self._headers))
        return client


async def async_oauth1_client(
    credentials: Optional[OAuth1Credentials] = None,
    *,
    timeout: float = 30.0,
    headers: Optional[Mapping[str, str]] = None,
    retries: int = 2,
    **kwargs,
) -> AsyncOAuth1Client:
    """Convenience function to create an authenticated OAuth1 HTTP client.
    
    Args:
        credentials: OAuth1 credentials (defaults to loading from environment)
        timeout: Request timeout in seconds (default: 30.0)
        headers: Additional headers to include in requests
        retries: Number of retry attempts (default: 2)
        **kwargs: Additional arguments passed to AsyncOAuth1Client
        
    Returns:
        Configured AsyncOAuth1Client ready for NetSuite API requests
        
    Example:
        >>> # Using environment variables
        >>> client = await async_oauth1_client()
        >>> 
        >>> # Using explicit credentials
        >>> credentials = OAuth1Credentials(
        ...     consumer_key="key",
        ...     consumer_secret="secret",
        ...     token_key="token", 
        ...     token_secret="token_secret"
        ... )
        >>> client = await async_oauth1_client(credentials=credentials)
    """
    provider = OAuth1AsyncAuthProvider(
        credentials,
        timeout=timeout,
        headers=headers,
        retries=retries,
        **kwargs,
    )
    return await provider.create_client()


def _apply_headers(
    extra_headers: Optional[Mapping[str, str]],
) -> MutableMapping[str, str]:
    headers: MutableMapping[str, str] = {
        "Content-Type": "application/json",
        "cache-control": "no-cache",
    }
    if extra_headers:
        headers.update(extra_headers)
    return headers
