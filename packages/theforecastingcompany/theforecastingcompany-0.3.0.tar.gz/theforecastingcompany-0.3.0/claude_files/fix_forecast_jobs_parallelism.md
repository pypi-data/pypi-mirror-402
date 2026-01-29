# Fix: Parallel Submission for /forecast-jobs Endpoint

## Problem

The `/forecast-jobs` submissions are **sequential**, not parallel, causing extremely slow job submission for large numbers of series.

### Current Code (Sequential)

In `src/theforecastingcompany/utils.py`, the `send_async_requests_via_jobs` function submits jobs one at a time:

```python
for request, model_config in _build_forecast_requests(...):
    # ...
    async with semaphore:
        job_id = await submit_forecast_job(request, client, api_key, model_url)  # <-- awaited inside loop
    job_submissions.append((job_id, request))
```

This means with 50,000 jobs and ~0.5s per submission, it takes **~42 minutes just to submit** all jobs.

### Compare to /forecast (Parallel)

The `/forecast` endpoint correctly uses parallel submission:

```python
tasks = []
for request, model_config in _build_forecast_requests(...):
    tasks.append(
        asyncio.create_task(
            send_request_with_retries(request, client=client, ...)
        )
    )

responses = await tqdm_asyncio.gather(*tasks)  # All tasks run in parallel
```

## Solution

Rewrite the job submission phase to use parallel execution:

```python
async def send_async_requests_via_jobs(
    train_df: pd.DataFrame,
    fcds: list[pd.Timestamp] | dict[str, pd.Timestamp | list[pd.Timestamp]],
    models: list["ModelConfig"],
    horizon: int = 13,
    freq: str = "W",
    max_concurrent: int = 10,
    api_key: str | None = None,
    url: str | None = None,
    id_col: str = "unique_id",
    date_col: str = "ds",
    target_col: str = "target",
    new_ids: Iterable[str] | None = None,
    cloud: Literal["aws", "gcp", "oci"] | None = None,
    quantiles: list[float] | None = None,
    partition_by: list[str] | None = None,
    poll_interval: float = 2.0,
) -> list[IDForecastResponse]:
    """Submit forecast jobs and poll for completion with tqdm progress."""
    base_url = "https://api.retrocast.com"
    semaphore = asyncio.Semaphore(max_concurrent)

    async def submit_with_semaphore(request: IDForecastRequest, model_url: str) -> tuple[str, IDForecastRequest]:
        async with semaphore:
            job_id = await submit_forecast_job(request, client, api_key, model_url)
        return (job_id, request)

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=120, read=600, pool=600, write=120), follow_redirects=True
    ) as client:
        # Phase 1: Build all tasks and submit in parallel
        submit_tasks = []

        for request, model_config in _build_forecast_requests(
            train_df, fcds, models, horizon, freq, api_key,
            id_col, date_col, target_col, new_ids, quantiles, partition_by,
        ):
            model_api = (
                model_config.model if model_config.model != TFCModels.Chronos_2_multivariate else TFCModels.Chronos_2
            )
            model_url = url if url else f"{base_url}/forecast-jobs?model={model_api.value}"
            if cloud:
                model_url = f"{model_url}&cloud={cloud}"

            submit_tasks.append(submit_with_semaphore(request, model_url))

        # Submit all jobs in parallel with progress bar
        job_submissions = await tqdm_asyncio.gather(
            *submit_tasks, desc=f"Submitting {len(submit_tasks)} jobs"
        )

        # Phase 2: Poll until all jobs complete (also needs parallelization - see below)
        # ... rest of polling logic ...
```

## Additional Issue: Polling is Also Sequential

The polling phase has the same problem:

```python
while pending:
    for job_id, req in pending.items():
        async with semaphore:
            result = await poll_job_result(job_id, client, api_key, base_url)  # Sequential!
```

This should also be parallelized:

```python
async def poll_with_semaphore(job_id: str, req: IDForecastRequest) -> tuple[str, IDForecastRequest, ForecastResponse | None]:
    async with semaphore:
        result = await poll_job_result(job_id, client, api_key, base_url)
    return (job_id, req, result)

while pending:
    poll_tasks = [poll_with_semaphore(job_id, req) for job_id, req in pending.items()]
    poll_results = await asyncio.gather(*poll_tasks)

    for job_id, req, result in poll_results:
        if result is not None:
            responses = _extract_job_response(result, req.ids_to_forecast, req.model)
            results.extend(responses)
            del pending[job_id]
            pbar.update(1)

    if pending:
        await asyncio.sleep(poll_interval)
```

## Performance Impact

| Phase | Current (Sequential) | Fixed (Parallel) |
|-------|---------------------|------------------|
| Submit 50k jobs | ~42 minutes | ~42 seconds (with max_concurrent=100) |
| Poll 50k jobs | ~42 minutes per cycle | ~42 seconds per cycle |

## Notes

- The semaphore still controls concurrency to avoid overwhelming the API
- Rate limiting (10,000 req/min) should still be considered for very large batches
- Consider adding a progress bar for the submission phase too
