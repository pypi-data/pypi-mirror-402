# Performance Report: 100k Series with Chronos-2 (batch_size=256)

**Date:** 2026-01-16
**Test Command:** `TFC_API_KEY="..." uv run python -m pyinstrument src/tests/test_scalability.py --num_series 100_000 --model chronos-2 --batch_size 256`

## Summary

| Metric | Value |
|--------|-------|
| Total Time | 180.3s |
| Forecast Time | 165.4s |
| Throughput | 604.53 series/sec |
| Series Count | 100,000 |
| Batches Sent | 391 |
| Output Shape | (1,200,000, 8) |

## Time Breakdown

### Overall Distribution

```
Total: 180.3s
├─ TFCClient.forecast: 165.4s (91.7%)
│   ├─ extract_forecast_df_from_model_idresponse: 97.0s (58.6% of forecast)
│   ├─ asyncio run (requests + building): 67.7s (40.9% of forecast)
│   │   ├─ _build_forecast_requests: 37.0s
│   │   └─ send_request_with_retries: 14.5s (actual HTTP)
│   └─ Other: 0.7s
└─ generate_dataset: 14.0s (7.8%)
```

### Post-Response Processing (MAIN BOTTLENECK): 97s

The `extract_forecast_df_from_model_idresponse` function consumes **59% of total forecast time**:

| Operation | Time | Details |
|-----------|------|---------|
| `DataFrame.assign` | 42.1s | Repeated column insertion with full DataFrame copies |
| `DataFrame.__setitem__` | 38.5s | Inefficient single-column additions |
| `DataFrame.__init__` | 8.3s | Creating DataFrames per response (391 times) |
| `concat` | 7.0s | Final concatenation of all DataFrames |

**Root Cause:** Each batch response triggers:
1. DataFrame creation
2. Multiple `.assign()` calls (each copies entire DataFrame)
3. Multiple `__setitem__` calls (each triggers `BlockManager.insert`)

Internal pandas operations called 391 times:
- `BlockManager.insert` → `Index.insert` → expensive array operations
- `DataFrame.copy` → `BlockManager.copy` → `_consolidate_inplace`

### Request Building: 37s

`_build_forecast_requests` breakdown:

| Operation | Time | Details |
|-----------|------|---------|
| `_get_ts_df` | 17.5s | DataFrame manipulation, `reset_index`, `.loc` indexing |
| `_build_input_serie` | 17.4s | Datetime formatting (`.strftime()` takes 9s alone) |

### Network I/O: 14.5s

Actual HTTP requests are efficient:
- `AsyncClient.post`: 5.9s
- `IDForecastRequest.payload`: 5.2s (serialization)
- Response handling: 2.7s

### Data Generation: 14s

Test data generation for 100k series - acceptable overhead.

## Detailed Pyinstrument Output

```
180.287 <module>  test_scalability.py:1
└─ 179.879 main  test_scalability.py:68
   ├─ 165.418 TFCClient.forecast  theforecastingcompany/tfc_client.py:204
   │  └─ 165.418 cross_validate_models  theforecastingcompany/utils.py:876
   │     ├─ 96.967 extract_forecast_df_from_model_idresponse  theforecastingcompany/utils.py:216
   │     │  ├─ 42.147 DataFrame.assign  pandas/core/frame.py:5181
   │     │  │  ├─ 29.415 DataFrame.__setitem__  pandas/core/frame.py:4276
   │     │  │  │  ├─ 26.036 DataFrame._set_item  pandas/core/frame.py:4519
   │     │  │  │  │  ├─ 21.051 DataFrame._set_item_mgr  pandas/core/frame.py:4486
   │     │  │  │  │  │  └─ 18.239 BlockManager.insert  pandas/core/internals/managers.py:1347
   │     │  │  │  │  │     └─ 11.854 Index.insert  pandas/core/indexes/base.py:6981
   │     │  │  │  │  └─ 4.465 DataFrame._sanitize_column  pandas/core/frame.py:5249
   │     │  │  │  └─ 2.549 Index.is_unique  pandas/core/indexes/base.py:2320
   │     │  │  └─ 12.360 DataFrame.copy  pandas/core/generic.py:6681
   │     │  ├─ 38.459 DataFrame.__setitem__  pandas/core/frame.py:4276
   │     │  │  └─ 36.969 DataFrame._set_item  pandas/core/frame.py:4519
   │     │  ├─ 8.334 DataFrame.__init__  pandas/core/frame.py:694
   │     │  └─ 7.045 concat  pandas/core/reshape/concat.py:157
   │     └─ 67.731 run  asyncio/runners.py:160
   │           └─ 51.900 Handle._run  asyncio/events.py:87
   │              ├─ 37.087 _run  theforecastingcompany/utils.py:904
   │              │  └─ 37.085 send_async_requests_multiple_models  theforecastingcompany/utils.py:783
   │              │     └─ 36.953 _build_forecast_requests  theforecastingcompany/utils.py:434
   │              │        ├─ 17.479 _get_ts_df  theforecastingcompany/utils.py:648
   │              │        └─ 17.353 _build_input_serie  theforecastingcompany/utils.py:675
   │              │           └─ 8.977 DatetimeProperties.strftime (datetime formatting)
   │              └─ 14.457 send_request_with_retries  theforecastingcompany/utils.py:294
   └─ 13.977 generate_dataset  test_scalability.py:39
```

## Optimization Recommendations

### Priority 1: `extract_forecast_df_from_model_idresponse` (potential 60-80s savings)

**Current Pattern (slow):**
```python
for response in responses:
    df = pd.DataFrame(response_data)
    df = df.assign(col1=val1)  # copies entire df
    df["col2"] = val2          # copies again
    dfs.append(df)
result = pd.concat(dfs)
```

**Recommended Pattern:**
```python
# Collect all data first
all_timestamps, all_values, all_ids, ... = [], [], [], ...
for response in responses:
    all_timestamps.extend(response["timestamps"])
    all_values.extend(response["values"])
    ...

# Single DataFrame creation at the end
result = pd.DataFrame({
    "timestamp": all_timestamps,
    "value": all_values,
    "unique_id": all_ids,
    ...
})
```

### Priority 2: `_build_input_serie` datetime formatting (potential 5-8s savings)

Replace `.strftime()` with vectorized operations or pre-cached formatting.

### Priority 3: `_get_ts_df` DataFrame operations (potential 5-10s savings)

Reduce `reset_index` and `.loc` calls by restructuring data access patterns.

## Expected Impact

| Optimization | Current | Estimated After | Savings |
|--------------|---------|-----------------|---------|
| DataFrame extraction | 97s | 15-25s | 70-80s |
| Datetime formatting | 9s | 2-3s | 6-7s |
| DataFrame indexing | 17s | 10-12s | 5-7s |
| **Total** | **165s** | **~80-90s** | **~75-85s** |

This could improve throughput from **604 series/sec** to **~1,100-1,250 series/sec**.
