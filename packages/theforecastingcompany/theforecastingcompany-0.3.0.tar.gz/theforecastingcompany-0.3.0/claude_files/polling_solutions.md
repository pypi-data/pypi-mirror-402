# Polling Optimization Solutions for /forecast-jobs

## Problem Statement

With 50,000 forecast job requests:
- **Submit phase**: 50,000 POST requests to `/forecast-jobs`
- **Poll phase**: 50,000 GET requests × ~15 cycles = **750,000 requests**
- **Total**: ~800,000 API requests

This can trigger rate limiting or IP bans.

---

## Solution 1: Batch Status Endpoint (Recommended)

### API Change Required

Add a new endpoint to `navi/apps/retrocast/main.py`:

```python
from fastapi import Query
from typing import List

@app.get("/forecast-jobs/batch-status")
async def get_batch_job_status(
    job_ids: List[str] = Query(..., description="List of job IDs to check"),
    x_user_key: str = Header(...),
    authorization: str = Header(...),
) -> dict[str, str]:
    """Check status of multiple jobs in a single request.

    Returns:
        Dict mapping job_id -> status ("completed" | "in_progress" | "not_found" | "error")
    """
    hashed_key = hashlib.sha256(x_user_key.encode()).hexdigest()
    results = {}

    for job_id in job_ids:
        # Verify authorization
        if job_store.get(job_id) != hashed_key:
            results[job_id] = "not_found"
            continue

        try:
            function_call = modal.functions.FunctionCall.from_id(job_id)
            function_call.get(timeout=0)
            results[job_id] = "completed"
        except TimeoutError:
            results[job_id] = "in_progress"
        except Exception:
            results[job_id] = "error"

    return results
```

### SDK Change

Update `utils.py`:

```python
async def poll_batch_job_status(
    job_ids: list[str],
    client: httpx.AsyncClient,
    api_key: str,
    base_url: str,
) -> dict[str, str]:
    """Poll status of multiple jobs in a single request."""
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"job_ids": job_ids}
    url = f"{base_url}/forecast-jobs/batch-status"
    response = await client.get(url, headers=headers, params=params)
    _handle_response(response)
    return response.json()


async def send_async_requests_via_jobs(
    # ... existing params ...
    poll_interval: float = 2.0,
    use_batch_status: bool = True,  # New parameter
) -> list[IDForecastResponse]:
    # ... submission phase unchanged ...

    # Phase 2: Poll using batch status
    pending: dict[str, IDForecastRequest] = {job_id: req for job_id, req in job_submissions}
    results: list[IDForecastResponse] = []

    with tqdm(total=len(pending), desc="Polling jobs") as pbar:
        while pending:
            if use_batch_status:
                # Single request for all job statuses
                statuses = await poll_batch_job_status(
                    list(pending.keys()), client, api_key, base_url
                )

                for job_id, status in statuses.items():
                    if status == "completed":
                        # Fetch full result
                        response = await poll_job_result(job_id, client, api_key, base_url)
                        if response:
                            req = pending.pop(job_id)
                            results.append(_extract_job_response(response, req.unique_ids, req.model))
                            pbar.update(1)
            else:
                # Fallback to individual polling (existing behavior)
                # ...

            if pending:
                await asyncio.sleep(poll_interval)

    return results
```

### Impact

| Metric | Before | After |
|--------|--------|-------|
| Submit requests | 50,000 | 50,000 |
| Poll requests | 750,000 | 15 (status) + ~50,000 (fetch results) |
| **Total** | **800,000** | **~50,015** |

---

## Solution 2: Semaphore-Limited Polling (SDK-only)

No API change required. Limits concurrent poll requests.

### SDK Change

```python
async def send_async_requests_via_jobs(
    # ... existing params ...
    poll_interval: float = 2.0,
    max_concurrent_polls: int = 20,  # New parameter
) -> list[IDForecastResponse]:
    # ... submission phase unchanged ...

    # Phase 2: Poll with semaphore
    poll_semaphore = asyncio.Semaphore(max_concurrent_polls)
    pending: dict[str, IDForecastRequest] = {job_id: req for job_id, req in job_submissions}
    results: list[IDForecastResponse] = []

    async def poll_single_job(job_id: str) -> tuple[str, ForecastResponse | None]:
        async with poll_semaphore:
            result = await poll_job_result(job_id, client, api_key, base_url)
            return job_id, result

    with tqdm(total=len(pending), desc="Polling jobs") as pbar:
        while pending:
            # Poll all pending jobs with semaphore limiting concurrency
            tasks = [poll_single_job(job_id) for job_id in pending.keys()]
            poll_results = await asyncio.gather(*tasks)

            for job_id, response in poll_results:
                if response:
                    req = pending.pop(job_id)
                    results.append(_extract_job_response(response, req.unique_ids, req.model))
                    pbar.update(1)

            if pending:
                await asyncio.sleep(poll_interval)

    return results
```

### Impact

- Still makes 50,000 requests per cycle, but spread over time
- Reduces burst load on API
- Doesn't reduce total request count

---

## Solution 3: Adaptive Polling Interval (SDK-only)

Increase poll interval based on completion rate.

### SDK Change

```python
async def send_async_requests_via_jobs(
    # ... existing params ...
    initial_poll_interval: float = 1.0,
    max_poll_interval: float = 10.0,
) -> list[IDForecastResponse]:
    # ... submission phase unchanged ...

    poll_interval = initial_poll_interval
    last_completed_count = 0

    with tqdm(total=len(pending), desc="Polling jobs") as pbar:
        while pending:
            # ... poll jobs ...

            completed_this_cycle = len(results) - last_completed_count
            last_completed_count = len(results)

            # Adaptive interval: increase if no progress
            if completed_this_cycle == 0:
                poll_interval = min(poll_interval * 1.5, max_poll_interval)
            else:
                poll_interval = initial_poll_interval

            if pending:
                await asyncio.sleep(poll_interval)

    return results
```

### Impact

- Reduces polling frequency when jobs are slow
- Still makes many requests, but fewer when stalled

---

## Solution 4: Sample-Based Polling (SDK-only)

Poll a random sample to estimate completion rate.

### SDK Change

```python
import random

async def send_async_requests_via_jobs(
    # ... existing params ...
    sample_size: int = 100,
) -> list[IDForecastResponse]:
    # ... submission phase unchanged ...

    with tqdm(total=len(pending), desc="Polling jobs") as pbar:
        while pending:
            # Poll a sample first
            sample_ids = random.sample(list(pending.keys()), min(sample_size, len(pending)))

            tasks = [poll_job_result(job_id, client, api_key, base_url) for job_id in sample_ids]
            sample_results = await asyncio.gather(*tasks)

            completed_in_sample = sum(1 for r in sample_results if r is not None)
            completion_rate = completed_in_sample / len(sample_ids)

            if completion_rate > 0.5:
                # Many jobs completing - poll all remaining
                # ... full poll ...
            else:
                # Few jobs completing - just process sample results
                for job_id, response in zip(sample_ids, sample_results):
                    if response:
                        req = pending.pop(job_id)
                        results.append(_extract_job_response(response, req.unique_ids, req.model))
                        pbar.update(1)

            if pending:
                await asyncio.sleep(poll_interval)

    return results
```

### Impact

- Dramatically reduces requests when jobs are slow
- May delay completion detection for some jobs

---

## Comparison Table

| Solution | API Change | Request Reduction | Complexity | Reliability |
|----------|------------|-------------------|------------|-------------|
| 1. Batch Status | Yes | 99%+ | Medium | High |
| 2. Semaphore | No | 0% (rate limited) | Low | High |
| 3. Adaptive Interval | No | 30-50% | Low | High |
| 4. Sample-Based | No | 50-80% | Medium | Medium |

---

## Recommendation

**Short-term**: Implement Solution 2 (Semaphore) + Solution 3 (Adaptive) in SDK
- No API change needed
- Immediate relief from rate limiting

**Medium-term**: Implement Solution 1 (Batch Status Endpoint)
- Best long-term solution
- Requires API deployment

**Implementation order**:
1. Add semaphore to polling (immediate fix)
2. Add adaptive polling interval (quick win)
3. Deploy batch status endpoint (proper solution)
4. Update SDK to use batch status with fallback
