# RobotnikAI Python Client - API Documentation

A Python client for RobotnikAI API that enables seamless integration with various APIs and services.

> **For development documentation** (versioning, publishing, etc.), see [README.dev.md](README.dev.md)

## Installation

```bash
pip install robotnikai
```

## Quick Start

### Environment Variables

Create a `.env` file in your project root for configuration:

```env
# Cache Service (when available)
CACHE_SERVICE_URL=https://cache.robotnikai.com
CACHE_SERVICE_TOKEN=your_cache_token

# Redis Configuration (for local development)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=optional_password

# RobotnikAI API Configuration
API_BASE_URL=https://robotnikai.com
APP_TOKEN=your_api_token
APP_ID=your_app_id
ACTION_ID=your_action_id

# Task Management
TASK_ID=optional_custom_task_id
```

### Usage Example
```python
from robotnikai.wrapper import API

api = API()
```


## Core Methods

### 🔌 Integration API Calls

#### `api.integrations.call()`
Make synchronous API calls to integrated services.

```python
# Basic API call
integration = api.integrations.get_integration("github")
data, response = api.integrations.call(
    integration, 
    method="GET", 
    endpoint="/user"
)

# With parameters and selected account
data, response = api.integrations.call(
    integration,
    method="GET", 
    endpoint="/sale/offers",
    params={"limit": 10, "offset": 0},
    connection_id="ecommercelab@yandex.com"
)

# POST with JSON payload
data, response = api.integrations.call(
    integration,
    method="POST",
    endpoint="/messages/submit",
    json={
        "from": {"name": "John Doe", "address": "john@example.com"},
        "to": [{"name": "Jane Doe", "address": "jane@example.com"}],
        "subject": "Test Email",
        "text": "Hello from Python client!"
    },
    connection_id="user@domain.com"
)
```

**Returns:** `(data, response)` tuple where:
- `data`: Parsed JSON response data
- `response`: HTTP response object with `.ok`, `.status_code`, `.text`, `.headers`, `.url` attributes

**Parallel Methods Return:** `List[ParallelCallResponse]` objects where each response contains:
- `.api_data`: Parsed JSON response data from the external service
- `.api_response`: HTTP response object (same as above)
- `.connection_id`: ID of the connection used for this request
- `.organization_id`: Organization ID associated with the connection

### ⚡ Parallel API Calls

#### `api.integrations.parallel_call()`
Execute multiple API calls concurrently using different connections per request for maximum performance and flexibility.

```python
# Multi-connection parallel calls (recommended for scaling across accounts)
responses = api.integrations.parallel_call(
    integration,
    method="GET",
    endpoint="/sale/product-offers/{offerId}",
    data_list=[
        {
            "connection_id": 123,
            "organization_id": 456,
            "url_params": {"offerId": "offer_1"},
            "params": {"include": "details"}
        },
        {
            "connection_id": 789,
            "organization_id": 101,
            "url_params": {"offerId": "offer_2"},
            "data": {"expand": True}
        }
    ],
    table="app_123_products"
)

# Process results with new object-based API
for response in responses:
    print(f"Connection {response.connection_id}, Org {response.organization_id}")
    if response.api_response.ok:
        print(f"Offer: {response.api_data['name']}")
        print(f"Status: {response.api_response.status_code}")
    else:
        print(f"Error: {response.api_response.text}")
```

#### `api.integrations.parallel_call_for_connection()`
Execute multiple API calls in parallel using a single connection (simpler for single-account operations).

```python
# Single-connection parallel calls
responses = api.integrations.parallel_call_for_connection(
    integration,
    method="GET",
    endpoint="/sale/product-offers/{offerId}",
    data_list=[
        {"url_params": {"offerId": "123"}},
        {"url_params": {"offerId": "456"}},
        {"url_params": {"offerId": "789"}}
    ],
    connection_id="user@domain.com",
    organization_id=123,
    table="app_124_offers"
)

# Process results
for response in responses:
    if response.api_response.ok:
        print(f"Offer: {response.api_data['name']}")
    else:
        print(f"Error: {response.api_response.text}")
```

#### `api.integrations.parallel_call_stream()`
Stream parallel API calls for real-time processing and progress visibility.

```python
# Stream parallel calls with real-time processing (single connection)
for result in api.integrations.parallel_call_stream(
    integration,
    method="GET",
    endpoint="/sale/product-offers/{offerId}",
    data_list=[{"url_params": {"offerId": offer["id"]}} for offer in offers],
    connection_id=connection_id
):
    
    if result.get("final"):
        print(f"✅ Completed! Processed {result['total_processed']} requests")
        break
    else:
        # Process individual response as it arrives
        data = result["data"]
        response = result["response"]
        index = result["index"]
        
        if response.ok:
            # Process immediately without waiting for all requests
            processed_data = process_data(data)
            save_to_database(processed_data)
        else:
            print(f"❌ Error for request {index}: {response.text}")
```

### 🔗 Connection Management

#### `api.integrations.get_connections()`
Get all connected accounts for an integration. Returns list of connections with `id` and `name`.

```python
# Get all connected accounts
connections = api.integrations.get_connections("allegro_sandbox")
for connection in connections:
    print(f"ID: {connection.id}, Name: {connection.name}")
    
    # Use connection ID in API calls
    data, response = api.integrations.call(
        integration,
        method="GET",
        endpoint="/sale/offers",
        connection_id=connection.id  # Use the connection ID in API calls
    )
```

### 💾 Caching System

#### App Cache
Shared cache accessible across the entire application. Access by key only for users within the same organization.

```python
# Set cache with TTL
api.app_cache.set(
    key="api_data",
    value={"rates": [1.2, 1.5, 1.8]},
    ttl=300  # 5 minutes
)

# Get cached data
cached_data = api.app_cache.get(key="api_data")
print(cached_data)  # {'rates': [1.2, 1.5, 1.8]}

# Delete cache entry
api.app_cache.delete(key="api_data")
```

#### User Cache
User-specific cache for personalized data. It is assigned to user's organization and can be shared between apps.

```python
# Set user-specific cache
api.user_cache.set(
    key="my_key", 
    value="my_value",
    ttl=3600  # 1 hour
)

# Get user cache
preferences = api.user_cache.get(key="my_key")

# Delete user cache
api.user_cache.delete(key="my_key")
```

### 📧 Notifications

#### `api.notify_me()`
Send notifications (via email) to yourself (useful for monitoring and alerts).

```python
# Send notification
api.notify_me(
    subject="API Process Completed",
    text="Successfully processed 1000 records",
    html="<h1>Success!</h1><p>Processed <strong>1000</strong> records</p>"
)
```

### 📊 Task Progress Tracking

#### `api.task.set_progress(progress: int, info: str, status: 'pending' | 'completed' | 'failed')`
Update task progress for long-running operations.
`progress` and `info` are displayed in the UI during task execution, while `status` indicates the task state.

```python
# Initialize progress
api.task.set_progress(0, "Starting data processing...", "pending")

# Update progress throughout your task
for i, item in enumerate(large_dataset):
    # Process item
    process_item(item)
    
    # Update progress every 100 items
    if i % 100 == 0:
        progress = int((i / len(large_dataset)) * 100)
        api.task.set_progress(
            progress, 
            f"Processed {i}/{len(large_dataset)} items", 
            "pending"
        )

# Complete the task
api.task.set_progress(100, "Processing completed!", "completed")
```

## 🔧 Configuration & Environment

### Cache & Progress Service Configuration

The client automatically detects and adapts to your environment:

#### **RobotnikAI Sandbox (Automatic)**
When running in RobotnikAI Sandbox:
- Uses the hosted cache service API
- `TASK_ID` is automatically assigned by the platform
- Progress tracking is displayed in the RobotnikAI UI
- Cache is shared across the organization

#### **Local Development (Redis)**
When running locally without `CACHE_SERVICE_URL`:
- Automatically uses direct Redis connection
- `TASK_ID` is generated as a random UUID4
- Progress is logged to console
- Requires Redis server running locally

#### Required Dependencies

For local Redis usage, install the Redis client:
```bash
pip install redis
```

### Usage Impact

**From the user perspective, there are no code changes required.** The client automatically:

- **Detects environment** and chooses appropriate backend
- **Maintains consistent API** across both configurations
- **Handles serialization/deserialization** transparently
- **Provides same response format** regardless of backend

```python
# This code works identically in both environments
api.app_cache.set("my_key", {"data": "value"}, ttl=300)
cached_data = api.app_cache.get("my_key")
api.task.set_progress(50, "Halfway done", "pending")
```

#### Environment Detection Logic

```python
# The client automatically determines configuration:
if CACHE_SERVICE_URL:
    # Use RobotnikAI cache service API
    # - HTTP requests to cache service
    # - Progress updates sent to platform
    # - Task ID from environment or auto-generated
else:
    # Use local Redis connection
    # - Direct Redis operations
    # - Progress logged to console
    # - UUID4 generated for task tracking
```

### 🏗️ Integration Management

#### `api.integrations.get_integration()`
Get integration configuration for API calls.

```python
# Get integration
integration = api.integrations.get_integration("allegro_sandbox")
# Now use this integration object in .call() methods
```

#### `api.integrations.get_integrations()`
List all available integrations.

```python
integrations = api.integrations.get_integrations()
for integration in integrations.results:
    print(f"ID: {integration.integration_id}, Name: {integration.name}")
```

## Common Patterns

### 1. **Parallel Data Processing**
```python
# Efficient parallel processing pattern
integration = api.integrations.get_integration("api_service")

# Step 1: Get list of items
list_data, response = api.integrations.call(
    integration, method="GET", endpoint="/items", 
    params={"limit": 50}, connection_id="user@domain.com"
)

# Step 2: Process details in parallel (single connection)
detail_requests = [
    {"url_params": {"id": item["id"]}} 
    for item in list_data["items"]
]

responses = api.integrations.parallel_call_for_connection(
    integration,
    method="GET", 
    endpoint="/items/{id}/details",
    data_list=detail_requests,
    connection_id="user@domain.com",
    organization_id=123
)

# Step 3: Process results with new object API
processed_data = []
for response in responses:
    if response.api_response.ok:
        processed_data.append(transform_data(response.api_data))
    else:
        print(f"Error for connection {response.connection_id}: {response.api_response.text}")
```

### 2. **Multi-Connection Parallel Processing**
```python
# Advanced: Parallel processing across multiple connections simultaneously
integration = api.integrations.get_integration("api_service")

# Get all connections for the service
table_connections = api.integrations.all_connections(integration, "data_table")

# Build parallel requests for multiple connections
data_list = []
for org_id, connections in table_connections.items():
    for connection in connections:
        data_list.append({
            "connection_id": connection["id"],
            "organization_id": org_id,
            "params": {"limit": 50},
            "url_params": {"account_id": connection["id"]}
        })

# Execute all requests in parallel across all connections
responses = api.integrations.parallel_call(
    integration,
    method="GET",
    endpoint="/accounts/{account_id}/data",
    data_list=data_list,
    table="app_123_consolidated_data"
)

# Process results with full traceability
for response in responses:
    print(f"Org {response.organization_id}, Connection {response.connection_id}")
    if response.api_response.ok:
        save_data(response.api_data, response.connection_id, response.organization_id)
    else:
        log_error(response.connection_id, response.api_response.text)
```

### 3. **Multi-Account Operations**
```python
# Process data across multiple connected accounts
connections = api.integrations.get_connections("service_name")

for connection in connections:
    print(f"Processing account: {connection.name}")
    
    data, response = api.integrations.call(
        integration,
        method="GET",
        endpoint="/data",
        connection_id=connection.id
    )
    
    if response.ok:
        # Process account-specific data
        process_account_data(data, connection.id)
```

### 3. **Progress Tracking with Caching**
```python
def long_running_task():
    api.task.set_progress(0, "Initializing...", "in_progress")
    
    # Cache intermediate results
    api.app_cache.set("task_checkpoint", {"processed": 0}, ttl=3600)
    
    for i in range(1000):
        # Do work
        process_item(i)
        
        # Update progress and cache
        if i % 100 == 0:
            progress = int((i / 1000) * 100)
            api.task.set_progress(progress, f"Processed {i}/1000", "in_progress")
            api.app_cache.set("task_checkpoint", {"processed": i}, ttl=3600)
    
    api.task.set_progress(100, "Completed!", "completed")
    api.app_cache.delete("task_checkpoint")
```

## Performance Tips

- **Use parallel calls** for multiple API requests to the same service
- **Cache frequently accessed data** to reduce API calls
- **Stream parallel calls** for real-time processing of large datasets
- **Set appropriate TTL** for cached data based on update frequency
- **Monitor progress** for long-running tasks to improve user experience

## Error Handling

### Single API Calls
```python
data, response = api.integrations.call(integration, method="GET", endpoint="/data")

if not response.ok:
    print(f"API Error: {response.status_code} - {response.text}")
    return

if not data:
    print("No data received")
    return

# Process successful response
process_data(data)
```

### Parallel API Calls
```python
responses = api.integrations.parallel_call(
    integration, method="GET", endpoint="/data",
    data_list=requests_data
)

for response in responses:
    if not response.api_response.ok:
        print(f"Error for connection {response.connection_id}: {response.api_response.text}")
        continue
    
    if not response.api_data:
        print(f"No data received for connection {response.connection_id}")
        continue
    
    # Process successful response
    process_data(response.api_data, response.connection_id)
```
