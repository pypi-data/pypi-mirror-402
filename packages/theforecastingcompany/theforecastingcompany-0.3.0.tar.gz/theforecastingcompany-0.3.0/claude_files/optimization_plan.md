# Plan: Optimize DataFrame Processing Bottlenecks

## Overview

The profiling revealed that **59% of forecast time (97s)** is spent in post-response DataFrame processing, while actual HTTP requests only take ~14.5s. This plan addresses three bottleneck areas:

1. **`extract_forecast_df_from_model_idresponse`** - 97s (Priority 1)
2. **`_build_input_serie`** - 17.4s with duplicate datetime formatting (Priority 2)
3. **`_get_ts_df`** - 17.5s in DataFrame operations (Priority 3)

## Part 1: Create Test for `extract_forecast_df_from_model_idresponse`

**File:** `src/tests/test_extract_forecast_df.py` (new)

### Test Strategy

Since this function is independent and has a clear input/output contract, we'll create a unit test that:
- Builds mock `IDForecastResponse` objects with known data
- Calls the function with various scenarios
- Asserts the output DataFrame shape, columns, and values

### Test Cases

1. **Single model, single series, single FCD**
2. **Single model, multiple series**
3. **Multiple models** (verify horizontal concat)
4. **Multiple FCDs per series** (list vs dict)
5. **Multiple quantiles** (verify quantile columns created)
6. **Edge case: single-point forecast**
7. **Error case: mismatched FCD counts**
8. **Error case: None series (model failed)**

### Mock Data Structure

```python
from theforecastingcompany.utils import IDForecastResponse, extract_forecast_df_from_model_idresponse
from theforecastingcompany.api import OutputSerie

def create_mock_response(model: str, unique_id: str, predictions: dict, index: list) -> IDForecastResponse:
    output_serie = OutputSerie(prediction=predictions, index=index)
    return IDForecastResponse(
        model=model,
        unique_id=unique_id,
        series=[[output_serie]],
        status="completed"
    )
```

### Assertion Strategy

The test will verify:
- DataFrame shape matches expected (num_rows = sum of all forecast points)
- Columns include: `{model_name}`, `{model_name}_q{quantile}`, `unique_id`, `ds`, `fcd`
- Values match input data exactly
- Sort order is correct (`unique_id`, `fcd`, `ds`)
- Types are correct (`datetime64` for ds/fcd, `str` for unique_id)

This test will work **before and after** the refactor since it tests the public interface.

---

## Part 2: Optimize `extract_forecast_df_from_model_idresponse`

**File:** `src/theforecastingcompany/utils.py` (lines 223-298)

### Current Problem

```python
for fcd, pred in zip(unique_id_fcds, serie):
    df = pd.DataFrame()           # New empty df
    df[model_name] = pred.prediction["mean"]  # Copy
    df[date_col] = pred.index                 # Copy
    df[id_col] = unique_id                    # Copy
    df["fcd"] = fcd                           # Copy
    df = df.assign(**{quantile_cols})         # Copy entire df
    dfs.append(df)
pd.concat(dfs)  # Concat 391+ small dfs
```

**Problem:** 4-5 DataFrame copies per response, multiplied by 391 batches = ~2000 copies

### Optimized Approach

```python
# Collect all data into lists first
all_model_values = []
all_dates = []
all_ids = []
all_fcds = []
all_quantiles = {key: [] for key in quantile_keys}

for response in response_list:
    for serie in response.series:
        for fcd, pred in zip(fcds, serie):
            all_model_values.extend(pred.prediction["mean"])
            all_dates.extend(pred.index)
            all_ids.extend([response.unique_id] * len(pred.index))
            all_fcds.extend([fcd] * len(pred.index))
            for key in quantile_keys:
                all_quantiles[key].extend(pred.prediction.get(key, []))

# Single DataFrame creation at the end
result = pd.DataFrame({
    model_name: all_model_values,
    date_col: pd.to_datetime(all_dates),
    id_col: all_ids,
    "fcd": pd.to_datetime(all_fcds),
    **{f"{model_name}_q{k}": v for k, v in all_quantiles.items()}
})
```

**Expected savings:** 70-80s (from 97s to ~15-25s)

---

## Part 3: Optimize `_build_input_serie`

**File:** `src/theforecastingcompany/utils.py` (lines 682-744)

### Current Problem

```python
# Line 702 - formats ALL timestamps
index = ts_df[date_col].dt.strftime("%Y-%m-%d %H:%M:%S").to_list()

# Line 711 - formats SAME timestamps AGAIN if future_vars exist
future_variables_index = ts_df[date_col].dt.strftime("%Y-%m-%d %H:%M:%S").to_list()
```

**Problem:** Duplicate datetime formatting (9s total, could be 4.5s)

### Optimized Approach

```python
# Format once, reuse
formatted_index = ts_df[date_col].dt.strftime("%Y-%m-%d %H:%M:%S").to_list()
index = formatted_index

# Reuse for future variables
future_variables_index = formatted_index if future_vars else []
```

**Expected savings:** 4-5s

---

## Part 4: Optimize `_get_ts_df` (Lower Priority)

**File:** `src/theforecastingcompany/utils.py` (lines 655-679)

### What this function does

`_get_ts_df` extracts a single time series from a larger DataFrame. The training DataFrame is indexed by `unique_id`, so `train_df.loc[unique_id]` fetches all rows for that series.

**The edge case:** When a unique_id has only **one row**, pandas returns a `Series` instead of a `DataFrame`. The function handles this by converting the Series back to a DataFrame.

### Current Code (lines 666-679)

```python
ts_df = train_df.loc[unique_id]  # Get rows for this unique_id

if isinstance(ts_df, pd.Series):
    # Single row case: Series → DataFrame conversion
    ts_df = (
        ts_df.to_frame()      # Series → single-column DataFrame
        .T                     # Transpose: columns become row values
        .reset_index()         # Move index to column
        .rename(columns={"index": id_col})  # Rename the index column
        .assign(**{date_col: lambda df: pd.to_datetime(df[date_col])})  # Parse date
        .astype({target_col: float})  # Ensure target is float
    )
else:
    # Multi-row case: just reset index
    ts_df = ts_df.reset_index()
```

### Why it's slow (17.5s total)

This is called **100,000 times** (once per unique_id). Each call:
1. `.loc[unique_id]` - Index lookup
2. `isinstance()` check
3. For multi-row: `.reset_index()` - Creates new DataFrame with index as column
4. For single-row: 6 chained operations, each creating intermediate DataFrames

The overhead is cumulative: 100k × 0.175ms = 17.5s

### Optimized Approach

For single-row case, construct DataFrame directly instead of chaining:

```python
if isinstance(ts_df, pd.Series):
    # Direct construction - one DataFrame creation instead of 6
    ts_df = pd.DataFrame({
        id_col: [ts_df.name],  # ts_df.name is the unique_id (from index)
        date_col: [pd.to_datetime(ts_df[date_col])],
        target_col: [float(ts_df[target_col])],
        # Include any other columns from the original Series
    })
```

This avoids: `to_frame()` → `T` → `reset_index()` → `rename()` → `assign()` → `astype()` chain.

**Expected savings:** 5-10s (depends on how many single-row series exist)

---

## Implementation Order (with testing after each part)

1. **Part 1: Create test file** (`test_extract_forecast_df.py`)
   - Run tests to verify current behavior
   - Establish baseline
   - **Test:** `pytest src/tests/test_extract_forecast_df.py -v`

2. **Part 2: Optimize `extract_forecast_df_from_model_idresponse`**
   - Largest impact (97s → ~20s)
   - **Test:** Run unit tests + scalability benchmark to measure improvement

3. **Part 3: Optimize `_build_input_serie`**
   - Easy fix (remove duplicate strftime)
   - **Test:** Run scalability benchmark to measure improvement

4. **Part 4: Optimize `_get_ts_df`**
   - **Test:** Run scalability benchmark to measure improvement

---

## Verification Plan

1. **Unit tests pass** - `pytest src/tests/test_extract_forecast_df.py`

2. **Integration test** - Run existing tests:
   ```bash
   pytest src/tests/test_client.py
   pytest src/tests/test_integration.py -k "not slow"
   ```

3. **Performance benchmark** - Re-run the scalability test:
   ```bash
   TFC_API_KEY="..." uv run --with pyinstrument python -m pyinstrument \
     src/tests/test_scalability.py --num_series 100_000 --model chronos-2 --batch_size 256
   ```

4. **Expected results:**
   - Total time: ~180s → ~90-100s
   - Throughput: ~600 series/sec → ~1000-1100 series/sec
   - `extract_forecast_df_from_model_idresponse`: 97s → 15-25s

---

## Files to Modify

| File | Action |
|------|--------|
| `src/tests/test_extract_forecast_df.py` | Create new test file |
| `src/theforecastingcompany/utils.py` | Optimize 3 functions |

## Files to Read (for reference during implementation)

- `src/theforecastingcompany/api.py` - `OutputSerie`, `ForecastResponse` definitions
- `src/theforecastingcompany/utils.py` - Current implementations
