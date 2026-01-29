# Newscatcher CatchAll Python Library

[![fern shield](https://img.shields.io/badge/%F0%9F%8C%BF-Built%20with%20Fern-brightgreen)](https://buildwithfern.com?utm_source=github&utm_medium=github&utm_campaign=readme&utm_source=https%3A%2F%2Fgithub.com%2FNewscatcher%2Fnewscatcher-catchall-python)
[![pypi](https://img.shields.io/pypi/v/newscatcher-catchall-sdk)](https://pypi.python.org/pypi/newscatcher-catchall-sdk)

The Newscatcher CatchAll Python library provides access to the [CatchAll API](https://www.newscatcherapi.com/docs/v3/catch-all/overview/introduction), which transforms natural language queries into structured data extracted from web sources.

## Installation

```sh
pip install newscatcher-catchall-sdk
```

## Reference

A full reference for this library is available [here](./reference.md).

## Usage

### Jobs

Submit a query and retrieve structured results:

```python
from newscatcher_catchall import CatchAllApi
import time

client = CatchAllApi(api_key="YOUR_API_KEY")

# Create a job with optional limit for testing
job = client.jobs.create_job(
    query="Tech company earnings this quarter",
    context="Focus on revenue and profit margins",
    limit=10,  # Start with 10 records for quick testing
)
print(f"Job created: {job.job_id}")

# Poll for completion with progress updates
while True:
    status = client.jobs.get_job_status(job.job_id)

    # Check if completed or enriching (early access)
    current_status = status.status
    if current_status in ["completed", "enriching"]:
        print(f"Job {current_status}!")
        break

    # Show current processing step
    current_step = next((s for s in status.steps if not s.completed), None)
    if current_step:
        print(f"Processing: {current_step.status} (step {current_step.order}/7)")

    time.sleep(60)

# Retrieve initial results (available during enriching stage)
results = client.jobs.get_job_results(job.job_id)
print(f"Found {results.valid_records} valid records")
print(f"Progress: {results.progress_validated}/{results.candidate_records} validated")

# Continue job to process more records
if results.valid_records >= 10:
    continued = client.jobs.continue_job(
        job_id=job.job_id,
        new_limit=50,  # Increase to 50 records
    )
    print(f"Job continued: {continued.job_id}")
    
    # Wait for completion
    while True:
        status = client.jobs.get_job_status(job.job_id)
        if status.status == "completed":
            break
        time.sleep(60)
    
    # Get final results
    results = client.jobs.get_job_results(job.job_id)
    print(f"Final: {results.valid_records} records")
```

Jobs process asynchronously and typically complete in 10-15 minutes. To learn more, see the [Quickstart](https://www.newscatcherapi.com/docs/v3/catch-all/overview/quickstart).

### Monitors

Automate recurring queries with scheduled execution:

```python
from newscatcher_catchall import CatchAllApi

client = CatchAllApi(api_key="YOUR_API_KEY")

# Create a monitor from a completed job
monitor = client.monitors.create_monitor(
    reference_job_id=job.job_id,
    schedule="every day at 12 PM UTC",
    webhook={
        "url": "https://your-endpoint.com/webhook",
        "method": "POST",
        "headers": {"Authorization": "Bearer YOUR_TOKEN"},
    },
)
print(f"Monitor created: {monitor.monitor_id}")

# Update webhook configuration without recreating monitor
updated = client.monitors.update_monitor(
    monitor_id=monitor.monitor_id,
    webhook={
        "url": "https://new-endpoint.com/webhook",
        "method": "POST",
        "headers": {"Authorization": "Bearer NEW_TOKEN"},
    },
)

# Pause monitor execution
client.monitors.disable_monitor(monitor.monitor_id)
print("Monitor paused")

# Resume monitor execution
client.monitors.enable_monitor(monitor.monitor_id)
print("Monitor resumed")

# List monitor execution history
jobs = client.monitors.list_monitor_jobs(
    monitor_id=monitor.monitor_id,
    sort="desc",  # Most recent first
)
print(f"Monitor has executed {jobs.total_jobs} jobs")
for job in jobs.jobs:
    print(f"  Job {job.job_id}: {job.start_date} to {job.end_date}")

# Get aggregated results
results = client.monitors.pull_monitor_results(monitor.monitor_id)
print(f"Collected {results.records} records across all executions")
```

Monitors run jobs on your schedule and send webhook notifications when complete. See the [Monitors documentation](https://www.newscatcherapi.com/docs/v3/catch-all/overview/monitors) for setup and configuration.

## Async client

Use the async client for non-blocking API calls:

```python
async def main() -> None:
    job = await client.jobs.create_job(
        query="Tech company earnings this quarter",
        context="Focus on revenue and profit margins",
    )
    print(f"Job created: {job.job_id}")

    # Wait for completion
    while True:
        status = await client.jobs.get_job_status(job.job_id)

        completed = any(s.status == "completed" and s.completed for s in status.steps)
        if completed:
            print("Job completed!")
            break

        current_step = next((s for s in status.steps if not s.completed), None)
        if current_step:
            print(f"Processing: {current_step.status} (step {current_step.order}/7)")

        await asyncio.sleep(60)
```

## Exception handling

Handle API errors with the `ApiError` exception:

```python
from newscatcher_catchall.core.api_error import ApiError

try:
    client.jobs.create_job(query="...")
except ApiError as e:
    print(f"Status: {e.status_code}")
    print(f"Error: {e.body}")
```

## Advanced

### Pagination

Retrieve large result sets with pagination:

```python
# Retrieve large result sets with pagination
page = 1
while True:
    results = client.jobs.get_job_results(
        job_id="...",
        page=page,
        page_size=100,
    )
    
    print(f"Page {results.page}/{results.total_pages}: {len(results.all_records)} records")
    
    for record in results.all_records:
        # Process each record
        print(f"  - {record.record_title}")
    
    if results.page >= results.total_pages:
        break
    page += 1

print(f"Processed {results.valid_records} total records")
```

### Access raw response data

Access response headers and raw data:

```python
response = client.jobs.with_raw_response.create_job(query="...")
print(response.headers)
print(response.data)
```

### Retries

The SDK retries failed requests automatically with exponential backoff. Configure retry behavior:

```python
client.jobs.create_job(
    query="...",
    request_options={"max_retries": 3},
)
```

### Timeouts

Set custom timeouts at the client or request level:

```python
# Client-level timeout
client = CatchAllApi(api_key="YOUR_API_KEY", timeout=30.0)

# Request-level timeout
client.jobs.create_job(
    query="...",
    request_options={"timeout_in_seconds": 10},
)
```

### Custom HTTP client

Customize the underlying HTTP client for proxies or custom transports:

```python
import httpx
from newscatcher_catchall import CatchAllApi

client = CatchAllApi(
    api_key="YOUR_API_KEY",
    httpx_client=httpx.Client(
        proxy="http://my.proxy.example.com",
        transport=httpx.HTTPTransport(local_address="0.0.0.0"),
    ),
)
```

## Beta status

CatchAll API is in beta. Breaking changes may occur in minor version updates. See the [Changelog](https://www.newscatcherapi.com/docs/v3/catch-all/overview/changelog) for updates.

## Contributing

This library is generated programmatically from our API specification. Direct contributions to the generated code cannot be merged, but README improvements are welcome. To suggest SDK changes, please [open an issue](https://github.com/Newscatcher/newscatcher-catchall-python/issues).

## Support

- Documentation: [https://www.newscatcherapi.com/docs/v3/catch-all](https://www.newscatcherapi.com/docs/v3/catch-all)
- Support: <support@newscatcherapi.com>
