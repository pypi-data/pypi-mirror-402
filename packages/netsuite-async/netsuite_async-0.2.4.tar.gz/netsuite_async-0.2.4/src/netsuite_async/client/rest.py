from __future__ import annotations

import os
from typing import Optional, Type

import httpx

from netsuite_async.catalog import RecordCatalog, record_id
from netsuite_async.client.accessors import RecordAccessor
from netsuite_async.exceptions import NetsuiteAuthError
from netsuite_async.client.oauth import AsyncAuthProvider, OAuth1AsyncAuthProvider

__all__ = ["AsyncNetsuiteRestClient"]


class AsyncNetsuiteRestClient:
    """Async client for NetSuite REST API operations.

    Supports context manager usage for automatic HTTP client cleanup.

    Args:
        auth_provider: Authentication provider for creating HTTP clients (defaults to OAuth1AsyncAuthProvider)
        account_id: NetSuite account ID (optional, reads from NETSUITE_ACCOUNT_ID env var if not provided)
        record_catalog_cls: Record catalog class for mapping record names to IDs
        base_url: Custom base URL (optional, auto-generated from account_id if not provided)

    Example:
        async with AsyncNetsuiteRestClient() as client:
            customers = await client.customers.list_summaries()
    """

    def __init__(
        self,
        auth_provider: Optional[AsyncAuthProvider] = None,
        account_id: Optional[str] = None,
        record_catalog_cls: Type[RecordCatalog] = RecordCatalog,
        *,
        base_url: Optional[str] = None,
    ):
        self.auth_provider = auth_provider or OAuth1AsyncAuthProvider()
        self.http: Optional[httpx.AsyncClient] = None
        self._catalog_cls = record_catalog_cls
        self._base_url = base_url
        self._account_id = None if base_url else self._resolve_account_id(account_id)

    @staticmethod
    def _resolve_account_id(account_id: Optional[str]) -> str:
        if account_id:
            return account_id
        env_value = os.getenv("NETSUITE_ACCOUNT_ID")
        if env_value:
            return env_value
        raise NetsuiteAuthError(
            "NetSuite account_id is required. Pass it explicitly or set NETSUITE_ACCOUNT_ID."
        )

    @property
    def base_url(self) -> str:
        if self._base_url:
            return self._base_url
        return f"https://{self._account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/"

    def build_url(self, record_name: str, internal_id: Optional[str] = None) -> str:
        """Build NetSuite REST API URL for the given record type and optional ID.
        
        Args:
            record_name: Name of the record type (e.g., 'customers', 'items')
            internal_id: Optional NetSuite internal ID for specific record
            
        Returns:
            Complete URL for the NetSuite REST API endpoint
            
        Example:
            >>> client.build_url('customers')
            'https://123456.suitetalk.api.netsuite.com/services/rest/record/v1/customer'
            >>> client.build_url('customers', '123')
            'https://123456.suitetalk.api.netsuite.com/services/rest/record/v1/customer/123'
        """
        url = f"{self.base_url}{record_id(record_name, self._catalog_cls)}"
        if internal_id:
            url += f"/{internal_id}"
        return url

    def __getattr__(self, name: str) -> RecordAccessor:
        """Create a RecordAccessor for the specified record type.
        
        Args:
            name: Record type name (e.g., 'customers', 'items', 'projects')
            
        Returns:
            RecordAccessor instance for the specified record type
            
        Example:
            >>> customers = client.customers  # Creates RecordAccessor for 'customers'
            >>> items = client.items          # Creates RecordAccessor for 'items'
        """
        return RecordAccessor(self, name)

    async def _ensure_http(self) -> httpx.AsyncClient:
        if self.http is None:
            self.http = await self.auth_provider.create_client()
        return self.http

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make an authenticated HTTP request to NetSuite.
        
        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            url: Target URL
            **kwargs: Additional arguments passed to httpx.request
            
        Returns:
            HTTP response object
            
        Example:
            >>> response = await client.request('GET', client.build_url('customers', '123'))
            >>> customer_data = response.json()
        """
        if not self.http:
            self.http = await self._ensure_http()
        return await self.http.request(method, url, **kwargs)

    async def close(self):
        """Close the HTTP client and clean up resources.
        
        Should be called when done with the client, or use context manager
        for automatic cleanup.
        
        Example:
            >>> client = AsyncNetsuiteRestClient()
            >>> # ... use client ...
            >>> await client.close()
        """
        if self.http:
            await self.http.aclose()
            self.http = None

    async def __aenter__(self) -> "AsyncNetsuiteRestClient":
        await self._ensure_http()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
