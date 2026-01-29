# netsuite-async

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance, async-first Python client for NetSuite's REST API with built-in concurrency controls, intelligent pagination, and comprehensive error handling.

## Features

- **Async-first design** - Built from the ground up for asyncio
- **High-performance concurrent operations** - Configurable concurrency limits with semaphore-based rate limiting
- **Smart pagination** - Automatic handling of NetSuite's pagination with both sequential and concurrent strategies
- **OAuth 1.0 authentication** - Secure authentication with HMAC-SHA256 signatures
- **Comprehensive error handling** - Detailed exception hierarchy for different error types
- **Type-safe** - Full type hints and dataclass models
- **Structured parameters** - Type-safe parameter classes for NetSuite API options
- **Flexible record mapping** - Dynamic record access with fuzzy matching for typos

## Installation

```bash
pip install netsuite-async
```

## Quick Start

### 1. Set up environment variables

```bash
export NETSUITE_ACCOUNT_ID="your_account_id"
export NETSUITE_CONSUMER_KEY="your_consumer_key"
export NETSUITE_CONSUMER_SECRET="your_consumer_secret"
export NETSUITE_TOKEN_KEY="your_token_key"
export NETSUITE_TOKEN_SECRET="your_token_secret"
```

### 2. Basic usage

```python
import asyncio
from netsuite_async import AsyncNetsuiteRestClient, OAuth1AsyncAuthProvider, OAuth1Credentials
from netsuite_async import GetParams, UpdateParams

async def main():
    # Option 1: Use default OAuth1 auth provider (reads from environment)
    async with AsyncNetsuiteRestClient() as netsuite:
        # Use built-in record types (no registration needed)
        customer = await netsuite.customers.get("123")
        print(f"Customer: {customer.raw['companyname']}")
        
        # Use structured parameters for better type safety
        get_params = GetParams(fields=["companyname", "email"], expand=True)
        customer = await netsuite.customers.get("123", params=get_params)
        
        # List records with pagination
        customers = await netsuite.customers.list_summaries()
        print(f"Found {len(customers)} customers")
        
        # Other built-in types work the same way
        projects = await netsuite.projects.list_summaries()
        employees = await netsuite.employees.get("456")
        
        # Concurrent bulk operations
        customer_ids = ["123", "456", "789"]
        results = await netsuite.customers.get_many(customer_ids, max_concurrency=5)
        
        for customer_id, result in results.items():
            if result.success:
                print(f"Success {customer_id}: {result.data.raw['companyname']}")
            else:
                print(f"Error {customer_id}: {result.error}")
    
    # Option 2: Custom auth provider with explicit credentials
    credentials = OAuth1Credentials(
        consumer_key="your_key",
        consumer_secret="your_secret",
        token_key="your_token",
        token_secret="your_token_secret",
        realm="your_account_id"
    )
    auth_provider = OAuth1AsyncAuthProvider(credentials)
    
    async with AsyncNetsuiteRestClient(auth_provider) as netsuite:
        customers = await netsuite.customers.list_summaries()

asyncio.run(main())
```

## Advanced Usage

### Concurrent Pagination

For large datasets, use concurrent pagination for significantly faster retrieval:

```python
# Sequential pagination (default)
customers = await netsuite.customers.list_summaries()

# Concurrent pagination (faster for large datasets)
customers = await netsuite.customers.list_summaries_concurrent(
    max_concurrency=10
)

# Get all records as full records (sequential)
full_customers = await netsuite.customers.all_full()

# Get all records as full records (concurrent)
full_results = await netsuite.customers.all_full_concurrent(max_concurrency=10)
```

### Structured Parameters

Use type-safe parameter classes for better IDE support and validation:

```python
from netsuite_async import GetParams, UpdateParams, CreateParams

# Type-safe GET parameters
get_params = GetParams(
    fields=["companyname", "email", "phone"],  # List of specific fields
    expand=True,                               # Expand sublists and subrecords
    simple_enum_format=True                   # Use simple enum format
)
customer = await netsuite.customers.get("123", params=get_params)

# Or use comma-separated string
get_params = GetParams(fields="companyname,email,phone", expand=True)
customer = await netsuite.customers.get("123", params=get_params)

# Type-safe UPDATE parameters
update_params = UpdateParams(
    replace=["addressbook"],          # Replace addressbook sublist
    replace_selected_fields=True      # Replace only specified fields
)
update_data = {"phone": "555-0124"}
await netsuite.customers.update("123", update_data, params=update_params)

# Type-safe CREATE parameters
create_params = CreateParams(
    replace=["addressbook", "contactlist"]  # Replace multiple sublists as list
)
customer_data = {"companyname": "Acme Corp", "email": "contact@acme.com"}
customer_id = await netsuite.customers.create(customer_data, params=create_params)

# You can still use plain dictionaries for backward compatibility
plain_params = {"fields": "companyname,email", "expandSubResources": "true"}
customer = await netsuite.customers.get("123", params=plain_params)
```

### Query Filtering

```python
# Filter records using NetSuite's query syntax
active_customers = await netsuite.customers.list_summaries(
    q='isinactive IS false'
)

# Complex queries
recent_orders = await netsuite.sales_orders.list_summaries(
    q='trandate AFTER "2024-01-01" AND status IS "Pending Fulfillment"'
)
```

### Built-in Record Types

The following record types are available out of the box with full IDE autocompletion:

```python
# Built-in record types (no registration needed)
await netsuite.customers.list_summaries()    # customer records
await netsuite.contacts.get("123")           # contact records  
await netsuite.projects.list_summaries()     # job records
await netsuite.partners.get("456")           # partner records
await netsuite.employees.list_summaries()    # employee records
```

### Custom Record Types

For other record types, register them first:

```python
# Register custom record types
RecordCatalog.register("items", "inventoryitem")
RecordCatalog.register("equipment_config", "customrecord_equipment_config")

# Then use them
items = await netsuite.items.list_summaries()
configs = await netsuite.equipment_config.get("456")
```

### Error Handling

```python
from netsuite_async import (
    NetsuiteAuthError,
    NetsuiteRateLimitError,
    NetsuiteValidationError,
    NetsuiteServerError
)

try:
    customer = await netsuite.customers.get("invalid_id")
except NetsuiteAuthError:
    print("Authentication failed - check credentials")
except NetsuiteRateLimitError:
    print("Rate limited - implement backoff strategy")
except NetsuiteValidationError as e:
    print(f"Validation error: {e}")
except NetsuiteServerError:
    print("NetSuite server error - retry later")
```

### Creating and Updating Records

```python
# Create a new customer
customer_data = {
    "companyname": "Acme Corp",
    "email": "contact@acme.com",
    "phone": "555-0123"
}
customer_id = await netsuite.customers.create(customer_data)

# Update existing customer
update_data = {"phone": "555-0124"}
await netsuite.customers.update(customer_id, update_data)
```

## API Reference

### Core Classes

#### `AsyncNetsuiteRestClient`

The main client for interacting with NetSuite's REST API. Supports context manager usage.

```python
# Default usage (uses OAuth1AsyncAuthProvider with environment variables)
client = AsyncNetsuiteRestClient()

# Custom auth provider
auth_provider = OAuth1AsyncAuthProvider(credentials)
client = AsyncNetsuiteRestClient(
    auth_provider=auth_provider,
    account_id="your_account_id",  # optional, reads from NETSUITE_ACCOUNT_ID if not provided
    base_url="https://custom.suitetalk.api.netsuite.com/services/rest/record/v1/"  # optional
)

# Context manager usage (automatically manages HTTP client lifecycle)
async with AsyncNetsuiteRestClient() as client:
    customers = await client.customers.list_summaries()
```

#### `RecordAccessor`

Provides CRUD operations for NetSuite records. Accessed via dynamic attributes on the client:

```python
# These create RecordAccessor instances
customers = client.customers
items = client.items
custom_records = client.my_custom_record
```

**Methods:**
- `get(internal_id: str, params: Optional[ParamsLike] = None) -> FullRecord` - Fetch a single record
- `get_many(ids: List[str], params: Optional[ParamsLike] = None, max_concurrency: int = 10) -> Dict[str, FetchResult]` - Fetch multiple records concurrently
- `list_summaries(q: Optional[str] = None, params: Optional[ParamsLike] = None) -> List[SummaryRecord]` - List all records (with pagination)
- `list_summaries_concurrent(max_concurrency: int = 10, params: Optional[ParamsLike] = None) -> List[SummaryRecord]` - Concurrent pagination
- `all_full(q: Optional[str] = None, params: Optional[ParamsLike] = None) -> List[FullRecord]` - Fetch all records as full records (sequential)
- `all_full_concurrent(q: Optional[str] = None, params: Optional[ParamsLike] = None, max_concurrency: int = 10) -> Dict[str, FetchResult]` - Fetch all records as full records (concurrent)
- `iter_summary_pages(limit: int = 1000, offset: int = 0, params: Optional[ParamsLike] = None) -> AsyncGenerator` - Iterate through pages
- `create(data: dict, params: Optional[ParamsLike] = None) -> str` - Create a new record
- `update(internal_id: str, data: dict, params: Optional[ParamsLike] = None) -> str` - Update an existing record

#### `RecordCatalog`

Maps friendly names to NetSuite record type IDs. Ships with common record types pre-registered:

**Built-in mappings:**
- `customers` → `customer`
- `contacts` → `contact` 
- `projects` → `job`
- `partners` → `partner`
- `employees` → `employee`

**Register additional mappings:**
```python
RecordCatalog.register("items", "inventoryitem")
RecordCatalog.register("sales_orders", "salesorder")
RecordCatalog.register("custom_record", "customrecord_my_record")

# Get all registered names
names = RecordCatalog.registered_names()
```

### Data Models

#### `SummaryRecord`
Lightweight record representation from list operations:
- `id: str` - NetSuite internal ID
- `type: str` - Record type name
- `links: List[Link]` - HATEOAS links
- `raw: Dict[str, Any]` - Raw NetSuite data

#### `FullRecord`
Complete record data from get operations:
- `id: str` - NetSuite internal ID  
- `type: str` - Record type name
- `links: List[Link]` - HATEOAS links
- `raw: Dict[str, Any]` - Raw NetSuite data

#### `FetchResult`
Union type for bulk operation results:
- `FetchResultSuccess(data: FullRecord, success: True)`
- `FetchResultError(error: str, success: False)`

### Parameter Classes

#### `GetParams`
Parameters for GET requests to retrieve NetSuite records:
- `fields: Union[List[str], str]` - The names of the fields and sublists on the record. Only the selected fields and sublists will be returned in the response. Can be a string (comma-separated) or list of field names.
- `expand: bool` - Set to True to automatically expand all sublists, sublist lines, and subrecords on this record.
- `simple_enum_format: bool` - Set to True to return enumeration values in a format that only shows the internal ID value.

#### `UpdateParams`
Parameters for PATCH requests to update NetSuite records:
- `replace: Union[List[str], str]` - The names of sublists on this record. All sublist lines will be replaced with lines specified in the request. The names are delimited by comma.
- `replace_selected_fields: bool` - If set to True, all fields that should be deleted in the update request, including body fields, must be included in the 'replace' query parameter.

#### `CreateParams`
Parameters for POST requests to create NetSuite records:
- `replace: Union[List[str], str]` - The names of sublists on this record. All sublist lines will be replaced with lines specified in the request. The names are delimited by comma.

#### `ParamsLike`
Type alias for parameter inputs: `Union[BaseParams, Mapping[str, Any]]`

Accepts either structured parameter classes (GetParams, UpdateParams, CreateParams) or plain dictionaries for backward compatibility.

### Authentication

#### `OAuth1AsyncAuthProvider`

Auth provider for OAuth1-authenticated HTTP clients:

```python
from netsuite_async import OAuth1AsyncAuthProvider, OAuth1Credentials

# Using environment variables (default)
auth_provider = OAuth1AsyncAuthProvider()

# Using explicit credentials
credentials = OAuth1Credentials(
    consumer_key="key",
    consumer_secret="secret", 
    token_key="token",
    token_secret="token_secret",
    realm="123456"  # optional, uses NETSUITE_ACCOUNT_ID from env if not provided
)
auth_provider = OAuth1AsyncAuthProvider(credentials=credentials)

# With custom options
auth_provider = OAuth1AsyncAuthProvider(
    timeout=60.0,
    retries=3,
    headers={"Custom-Header": "value"}
)
```

#### `async_oauth1_client()`

Convenience function that creates an authenticated HTTP client directly:

```python
from netsuite_async import async_oauth1_client

# Creates and returns an AsyncOAuth1Client
client = await async_oauth1_client()
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NETSUITE_ACCOUNT_ID` | Your NetSuite account ID | Yes |
| `NETSUITE_CONSUMER_KEY` | OAuth consumer key | Yes |
| `NETSUITE_CONSUMER_SECRET` | OAuth consumer secret | Yes |
| `NETSUITE_TOKEN_KEY` | OAuth token key | Yes |
| `NETSUITE_TOKEN_SECRET` | OAuth token secret | Yes |
| `NETSUITE_REALM` | OAuth realm (defaults to account ID) | No |

## Performance Tips

1. **Use concurrent operations** for bulk data retrieval:
   ```python
   # Fast - concurrent requests
   results = await client.customers.get_many(ids, max_concurrency=10)
   
   # Slow - sequential requests  
   results = [await client.customers.get(id) for id in ids]
   ```

2. **Choose the right pagination strategy**:
   ```python
   # Fast for large datasets
   records = await client.customers.list_summaries_concurrent()
   
   # Memory efficient for streaming
   async for page in client.customers.iter_summary_pages():
       process_page(page)
   ```

3. **Use all_full methods for complete record data**:
   ```python
   # Sequential - memory efficient
   full_records = await client.customers.all_full()
   
   # Concurrent - faster for large datasets
   results = await client.customers.all_full_concurrent(max_concurrency=10)
   ```

4. **Tune concurrency limits** based on your NetSuite plan's rate limits:
   ```python
   # Conservative for shared environments
   results = await client.customers.get_many(ids, max_concurrency=5)
   
   # Aggressive for dedicated environments
   results = await client.customers.get_many(ids, max_concurrency=20)
   ```

## Requirements

- Python 3.12+
- httpx >= 0.28.1
- authlib >= 1.6.5

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

- [NetSuite REST API Documentation](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_1540391670.html)
- [Report Issues](https://github.com/your-username/netsuite-async/issues)
- [Discussions](https://github.com/your-username/netsuite-async/discussions)