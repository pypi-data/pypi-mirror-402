from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional, TYPE_CHECKING
from urllib.parse import parse_qs

from netsuite_async.exceptions import NetsuiteResponseError, raise_for_response
from netsuite_async.models.records import (
    FetchResult,
    FetchResultError,
    FetchResultSuccess,
    FullRecord,
    Link,
    SummaryRecord,
    parse_id,
)
from netsuite_async.client.params import ParamsLike, BaseParams


if TYPE_CHECKING:  # pragma: no cover - type checking only
    from netsuite_async.client.rest import AsyncNetsuiteRestClient

__all__ = [
    "RecordAccessor",
    "page_link",
    "parse_limit_offset",
    "response_ok",
]


class RecordAccessor:
    """Provides CRUD operations and data access methods for NetSuite records.
    
    Accessed via dynamic attributes on AsyncNetsuiteRestClient (e.g., client.customers).
    Supports both individual record operations and bulk/concurrent operations.
    """
    def __init__(self, client: "AsyncNetsuiteRestClient", record_name: str):
        self._client = client
        self._record_name = record_name

    def _resolve_params(self, params: Optional[ParamsLike]) -> Optional[dict]:
        """Convert ParamsLike to dict for HTTP requests."""
        if params is None:
            return None
        if isinstance(params, BaseParams):
            return params.to_dict()
        return dict(params)

    def _build_params(self, base_params: dict, user_params: Optional[ParamsLike]) -> dict:
        """Build final params dict by merging base params with user params."""
        final_params = base_params.copy()
        resolved_user_params = self._resolve_params(user_params)
        if resolved_user_params:
            final_params.update(resolved_user_params)
        return final_params

    # ---------------------------
    # Helpers
    # ---------------------------
    def _parse_links(self, link_list: List[Dict[str, Any]]) -> List[Link]:
        return [Link(rel=l["rel"], href=l["href"]) for l in link_list or []]

    def _to_summary(self, raw: Dict[str, Any]) -> SummaryRecord:
        return SummaryRecord(
            id=str(raw["id"]),
            type=self._record_name,
            links=self._parse_links(raw.get("links", [])),
            raw=raw,
        )

    def _to_full(self, raw: Dict[str, Any]) -> FullRecord:
        return FullRecord(
            id=str(raw["id"]),
            type=self._record_name,
            links=self._parse_links(raw.get("links", [])),
            raw=raw,
        )


    # ---------------------------
    # Full-record fetching
    # ---------------------------
    async def get(self, internal_id: str, params: Optional[ParamsLike] = None) -> FullRecord:
        """Fetch a single record by its internal ID.
        
        Args:
            internal_id: NetSuite internal ID of the record
            params: Optional query parameters (dict, BaseParams, or ParamsLike) to include in the request
            
        Returns:
            FullRecord with complete record data
            
        Raises:
            NetsuiteValidationError: If record ID is invalid
            NetsuiteAuthError: If authentication fails
            
        Example:
            >>> customer = await client.customers.get("123")
            >>> print(customer.raw["companyname"])
        """
        url = self._client.build_url(self._record_name, internal_id)
        res = await self._client.request("GET", url, params=self._resolve_params(params))
        if not response_ok(res):
            raise_for_response(res, operation="get", record_name=self._record_name)
        return self._to_full(res.json())

    async def get_many(
        self, internal_ids: List[str], params: Optional[ParamsLike] = None, *, max_concurrency: int = 10
    ) -> Dict[str, FetchResult]:
        """Fetch multiple records concurrently by their internal IDs.
        
        Args:
            internal_ids: List of NetSuite internal IDs
            params: Optional query parameters (dict, BaseParams, or ParamsLike) to include in each request
            max_concurrency: Maximum number of concurrent requests (default: 10)
            
        Returns:
            Dict mapping record IDs to FetchResult objects (success or error)
            
        Example:
            >>> ids = ["123", "456", "789"]
            >>> results = await client.customers.get_many(ids, max_concurrency=5)
            >>> for id_, result in results.items():
            ...     if result.success:
            ...         print(f"Success {id_}: {result.data.raw['companyname']}")
            ...     else:
            ...         print(f"Error {id_}: {result.error}")
        """
        sem = asyncio.Semaphore(max_concurrency)

        async def fetch_one(id_: str) -> tuple[str, FetchResult]:
            async with sem:
                try:
                    record = await self.get(id_, params)
                    return id_, FetchResultSuccess(data=record)
                except Exception as exc:
                    return id_, FetchResultError(error=str(exc))

        tasks = [asyncio.create_task(fetch_one(id_)) for id_ in internal_ids]
        results = await asyncio.gather(*tasks)
        return {id_: data for id_, data in results}

    async def all_full(self, *, q: Optional[str] = None, params: Optional[ParamsLike] = None) -> List[FullRecord]:
        """Fetch all records as full records (sequential approach).
        
        Memory-efficient but slower than concurrent version. Use for smaller datasets
        or when memory usage is a concern.
        
        Args:
            q: Optional query filter using NetSuite's query syntax
            params: Optional query parameters (dict, BaseParams, or ParamsLike) to include in requests
            
        Returns:
            List of FullRecord objects with complete record data
            
        Example:
            >>> # Get all active customers
            >>> customers = await client.customers.all_full(q='isinactive IS false')
            >>> for customer in customers:
            ...     print(customer.raw["companyname"])
        """
        summaries = await self.list_summaries(q=q)
        results = []
        for summary in summaries:
            record = await self.get(summary.id, params=params)
            results.append(record)
        return results

    async def all_full_concurrent(
        self,
        q: Optional[str] = None,
        params: Optional[ParamsLike] = None,
        max_concurrency: int = 10,
        limit: int = 1000,
        offset: int = 0,
    ) -> Dict[str, FetchResult]:
        """Fetch all records as full records using concurrent requests.
        
        Faster than sequential version but uses more memory. Recommended for
        large datasets when performance is critical.
        
        Args:
            q: Optional query filter using NetSuite's query syntax
            params: Optional query parameters (dict, BaseParams, or ParamsLike) to include in requests
            max_concurrency: Maximum number of concurrent requests (default: 10)
            limit: Records per page for pagination (default: 1000)
            offset: Starting offset for pagination (default: 0)
            
        Returns:
            Dict mapping record IDs to FetchResult objects (success or error)
            
        Example:
            >>> # Get all customers with error handling
            >>> results = await client.customers.all_full_concurrent(max_concurrency=15)
            >>> successful = [r.data for r in results.values() if r.success]
            >>> errors = [r.error for r in results.values() if not r.success]
        """
        summaries = await self.list_summaries_concurrent(
            q=q,
            max_concurrency=max_concurrency,
            limit=limit,
            offset=offset,
        )

        ids = [s.id for s in summaries]
        return await self.get_many(ids, params=params, max_concurrency=max_concurrency)

    # ---------------------------
    # Summary Pagination
    # ---------------------------
    async def iter_summary_pages(
        self, limit: int = 1000, offset: int = 0, q: Optional[str] = None, params: Optional[ParamsLike] = None
    ) -> AsyncGenerator[List[SummaryRecord], None]:
        """Iterate through pages of summary records.
        
        Memory-efficient streaming approach for processing large datasets.
        Each page is yielded as a list of SummaryRecord objects.
        
        Args:
            limit: Records per page (default: 1000, max: 1000)
            offset: Starting offset (default: 0)
            q: Optional query filter using NetSuite's query syntax
            params: Optional query parameters (dict, BaseParams, or ParamsLike) to include in requests
            
        Yields:
            List[SummaryRecord]: Each page of summary records
            
        Example:
            >>> async for page in client.customers.iter_summary_pages(limit=500):
            ...     for customer in page:
            ...         print(f"Processing {customer.raw['companyname']}")
            ...     # Process page before loading next one
        """
        url = self._client.build_url(self._record_name)

        base_params = {"limit": limit, "offset": offset}
        if q:
            base_params["q"] = q
        final_params = self._build_params(base_params, params)

        while True:
            res = await self._client.request("GET", url, params=final_params)
            if not response_ok(res):
                raise_for_response(res, operation="list", record_name=self._record_name)

            payload = res.json()
            items = payload.get("items", [])
            yield [self._to_summary(item) for item in items]

            next_link = page_link("next", payload.get("links", []))
            if not next_link:
                break

            url, _, query = next_link.partition("?")
            final_params.update(parse_limit_offset(query))

    async def list_summaries(self, q: Optional[str] = None, params: Optional[ParamsLike] = None) -> List[SummaryRecord]:
        """List all summary records using sequential pagination.
        
        Fetches all pages sequentially and returns complete list. Memory usage
        grows with dataset size but provides simple list interface.
        
        Args:
            q: Optional query filter using NetSuite's query syntax
            params: Optional query parameters (dict, BaseParams, or ParamsLike) to include in requests
            
        Returns:
            List of SummaryRecord objects with basic record data
            
        Example:
            >>> # Get all active customers
            >>> customers = await client.customers.list_summaries(
            ...     q='isinactive IS false'
            ... )
            >>> print(f"Found {len(customers)} active customers")
        """
        records = []
        async for page_items in self.iter_summary_pages(q=q, params=params):
            records.extend(page_items)
        return records

    # ---------------------------
    # Concurrent Summary Fetch
    # ---------------------------
    async def list_summaries_concurrent(
        self,
        q: Optional[str] = None,
        max_concurrency: int = 10,
        limit: int = 1000,
        offset: int = 0,
        params: Optional[ParamsLike] = None,
    ) -> List[SummaryRecord]:
        """List all summary records using concurrent pagination.
        
        Fetches multiple pages concurrently for faster retrieval of large datasets.
        Significantly faster than sequential pagination but uses more resources.
        
        Args:
            q: Optional query filter using NetSuite's query syntax
            max_concurrency: Maximum number of concurrent page requests (default: 10)
            limit: Records per page (default: 1000, max: 1000)
            offset: Starting offset (default: 0)
            params: Optional query parameters (dict, BaseParams, or ParamsLike) to include in requests
            
        Returns:
            List of SummaryRecord objects with basic record data
            
        Example:
            >>> # Fast retrieval of large dataset
            >>> customers = await client.customers.list_summaries_concurrent(
            ...     q='datecreated AFTER "2024-01-01"',
            ...     max_concurrency=15
            ... )
            >>> print(f"Retrieved {len(customers)} customers concurrently")
        """
        url = self._client.build_url(self._record_name)
        base_params = {"limit": limit, "offset": offset}
        if q:
            base_params["q"] = q
        final_params = self._build_params(base_params, params)

        # fetch first page
        res = await self._client.request("GET", url, params=final_params)
        if not response_ok(res):
            raise_for_response(res, operation="list", record_name=self._record_name)

        first_page = res.json()
        items = [self._to_summary(i) for i in first_page.get("items", [])]

        # see if pagination is needed
        last_url = page_link("last", first_page.get("links", []))
        if not last_url:
            return items

        _, _, last_query = last_url.partition("?")
        last_params = parse_limit_offset(last_query)
        last_offset = last_params["offset"]
        offsets = list(range(offset + limit, last_offset + limit, limit))

        sem = asyncio.Semaphore(max_concurrency)

        async def fetch_page(page_offset: int) -> List[SummaryRecord]:
            async with sem:
                base_page_params = {"limit": limit, "offset": page_offset}
                if q:
                    base_page_params["q"] = q
                page_params = self._build_params(base_page_params, params)

                res = await self._client.request("GET", url, params=page_params)
                if not response_ok(res):
                    raise_for_response(
                        res, operation="list", record_name=self._record_name
                    )
                payload = res.json()
                return [self._to_summary(i) for i in payload.get("items", [])]

        tasks = [asyncio.create_task(fetch_page(off)) for off in offsets]
        pages = await asyncio.gather(*tasks)

        for page in pages:
            items.extend(page)

        return items

    # ---------------------------
    # Mutations
    # ---------------------------
    async def update(self, internal_id: str, data: dict, params: Optional[ParamsLike] = None) -> str:
        """Update an existing record with new data.
        
        Args:
            internal_id: NetSuite internal ID of the record to update
            data: Dictionary containing fields to update
            params: Optional query parameters (dict, BaseParams, or ParamsLike) to include in the request
            
        Returns:
            The internal ID of the updated record
            
        Raises:
            NetsuiteValidationError: If data validation fails
            NetsuiteAuthError: If authentication fails
            
        Example:
            >>> # Update customer phone number
            >>> await client.customers.update("123", {"phone": "555-0124"})
            >>> 
            >>> # Update multiple fields
            >>> update_data = {
            ...     "email": "newemail@company.com",
            ...     "phone": "555-9999"
            ... }
            >>> await client.customers.update("123", update_data)
        """
        url = self._client.build_url(self._record_name, internal_id)
        res = await self._client.request("PATCH", url, json=data, params=self._resolve_params(params))
        if not response_ok(res):
            raise_for_response(res, operation="update", record_name=self._record_name)
        return internal_id

    async def create(self, data: dict, params: Optional[ParamsLike] = None) -> str:
        """Create a new record with the provided data.
        
        Args:
            data: Dictionary containing record fields and values
            params: Optional query parameters (dict, BaseParams, or ParamsLike) to include in the request
            
        Returns:
            The internal ID of the newly created record
            
        Raises:
            NetsuiteValidationError: If required fields are missing or invalid
            NetsuiteAuthError: If authentication fails
            NetsuiteResponseError: If Location header is missing from response
            
        Example:
            >>> # Create a new customer
            >>> customer_data = {
            ...     "companyname": "Acme Corp",
            ...     "email": "contact@acme.com",
            ...     "phone": "555-0123"
            ... }
            >>> customer_id = await client.customers.create(customer_data)
            >>> print(f"Created customer with ID: {customer_id}")
        """
        url = self._client.build_url(self._record_name)
        res = await self._client.request("POST", url, json=data, params=self._resolve_params(params))
        if not response_ok(res):
            raise_for_response(res, operation="create", record_name=self._record_name)

        location = res.headers.get("Location")
        if not location:
            raise NetsuiteResponseError(
                "Create succeeded but response did not include a Location header",
                status_code=res.status_code,
                operation="create",
                record_name=self._record_name,
            )
        return parse_id(location)


def page_link(
    link_name: str,
    links: List[dict],
) -> Optional[str]:
    """Extract a specific pagination link from NetSuite's HATEOAS links.
    
    Args:
        link_name: The relation name to find (e.g., 'next', 'last', 'prev')
        links: List of link dictionaries from NetSuite response
        
    Returns:
        The href URL if found, None otherwise
        
    Example:
        >>> links = [{'rel': 'next', 'href': 'https://...?offset=1000'}]
        >>> next_url = page_link('next', links)
    """
    for link in links:
        if link["rel"] == link_name:
            return link["href"]
    return None


def parse_limit_offset(query: str) -> dict:
    """Parse limit and offset parameters from a URL query string.
    
    Args:
        query: URL query string (e.g., 'limit=1000&offset=2000')
        
    Returns:
        Dict with 'limit' and 'offset' integer values
        
    Example:
        >>> parse_limit_offset('limit=500&offset=1500')
        {'limit': 500, 'offset': 1500}
    """
    parsed = parse_qs(query or "", keep_blank_values=True)
    limit = int(parsed.get("limit", ["1000"])[0])
    offset = int(parsed.get("offset", ["0"])[0])
    return {"limit": limit, "offset": offset}


def response_ok(response) -> bool:
    """Check if an HTTP response indicates success.
    
    Args:
        response: HTTP response object with status_code attribute
        
    Returns:
        True if status code is in the 2xx range, False otherwise
        
    Example:
        >>> response_ok(response)  # True for 200, 201, etc.
    """
    return 200 <= response.status_code <= 300

