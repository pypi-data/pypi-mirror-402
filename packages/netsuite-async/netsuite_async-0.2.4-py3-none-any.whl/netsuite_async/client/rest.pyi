# async_netsuite/client.pyi

from typing import Any, Optional, Type
import httpx
from netsuite_async.client.accessors import RecordAccessor
from netsuite_async.client.oauth import AsyncAuthProvider
from netsuite_async.catalog import RecordCatalog


class AsyncNetsuiteRestClient:
    # ------------------------------------
    # Static shadow of dynamically-added API
    # ------------------------------------
    projects: RecordAccessor
    contacts: RecordAccessor
    customers: RecordAccessor
    partners: RecordAccessor
    employees: RecordAccessor

    # ------------------------------------
    # Constructor & real methods
    # ------------------------------------
    def __init__(
        self,
        auth_provider: Optional[AsyncAuthProvider] = None,
        account_id: Optional[str] = None,
        record_catalog_cls: Type[RecordCatalog] = RecordCatalog,
        *,
        base_url: Optional[str] = None,
    ) -> None: ...
    
    @property
    def base_url(self) -> str: ...
    
    def build_url(self, record_name: str, internal_id: Optional[str] = None) -> str: ...
    
    def __getattr__(self, name: str) -> RecordAccessor: ...
    
    async def request(self, method: str, url: str, **kwargs) -> httpx.Response: ...
    
    async def close(self) -> None: ...
    
    async def __aenter__(self) -> "AsyncNetsuiteRestClient": ...
    
    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None: ...
