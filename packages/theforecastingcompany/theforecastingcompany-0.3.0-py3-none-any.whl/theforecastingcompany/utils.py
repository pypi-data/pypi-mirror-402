import asyncio
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Generator, Iterable, List, Literal

import httpx
import nest_asyncio
import numpy as np
import pandas as pd
from pydantic import BaseModel
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio

from .api import (
    Chronos2ModelConfig,
    ForecastRequest,
    ForecastResponse,
    InputSerie,
    OutputSerie,
)
from .api import ModelConfig as APIModelConfig
from .errors import _handle_response

logger = logging.getLogger(__name__)


# Types definiton
ModelAlias = str


class ForecastJobSubmitResponse(BaseModel):
    """Response from POST /forecast-jobs containing the job ID."""

    call_id: str


class IDForecastResponse(ForecastResponse):
    model: ModelAlias
    unique_id: str

    def __post_init__(self):
        # Only one series at a time, which can be easily transformed to df
        assert self.series is None or len(self.series) == 1, "IDForecastResponse should have exactly one series"

    def to_df(self) -> pd.DataFrame:
        raise NotImplementedError("IDForecastResponse.to_df is not implemented yet")


class IDForecastRequest(ForecastRequest):
    model: ModelAlias
    unique_ids: list[str] | None = None
    series: List[InputSerie] | None = None

    def add_serie(self, serie: InputSerie, unique_id: str) -> "IDForecastRequest":
        """This modifies the forecast request in place, adding a new series to it."""
        if self.series is None:
            self.series = []
        if self.unique_ids is None:
            self.unique_ids = []
        self.series.append(serie)
        self.unique_ids.append(unique_id)
        return self

    def replace_serie(self, serie: InputSerie, unique_id: str) -> "IDForecastRequest":
        """Creates a NEW forecast request with the given series and unique_id."""
        new_req = self.model_copy(deep=True)
        new_req.series = [serie]
        new_req.unique_ids = [unique_id]
        return new_req

    @property
    def ids_to_forecast(self) -> list[str]:
        if self.series is None or self.unique_ids is None:
            raise ValueError("Empty IDForecastRequest: series or unique_ids is None")
        return [idx for idx, serie in zip(self.unique_ids, self.series, strict=False) if not serie.only_as_context]

    @property
    def forecast_request(self) -> ForecastRequest:
        return ForecastRequest(**{k: v for k, v in self.model_dump(by_alias=True).items() if k != "unique_ids"})

    @property
    def payload(self) -> dict[str, dict | list]:
        # Validate everything by creating a ForecastRequets and then create the Dump
        return self.forecast_request.model_dump(by_alias=True, exclude_none=True)


class TFCModels(StrEnum):
    """Utils Enum that defines the models available in TFC.
    For each model, it defines the type of covariates it can handle and whether it's a global model or not.
    """

    TimesFM_2 = "timesfm-2"
    TabPFN_TS = "tabpfn-ts"
    TFCGlobal = "tfc-global"
    ChronosBolt = "chronos-bolt"
    Moirai = "moirai"
    MoiraiMoe = "moirai-moe"
    Moirai2 = "moirai-2"
    Chronos_2 = "chronos-2"
    Chronos_2_multivariate = "chronos-2-mv"

    @property
    def accept_future_variables(self) -> bool:
        return self.value in [
            TFCModels.TabPFN_TS,
            TFCModels.TFCGlobal,
            TFCModels.Moirai,
            TFCModels.MoiraiMoe,
            TFCModels.Moirai2,
            TFCModels.Chronos_2,
            TFCModels.Chronos_2_multivariate,
        ]

    @property
    def accept_historical_variables(self) -> bool:
        return self.value in [
            TFCModels.TabPFN_TS,
            TFCModels.TFCGlobal,
            TFCModels.Moirai,
            TFCModels.MoiraiMoe,
            TFCModels.Moirai2,
            TFCModels.Chronos_2,
            TFCModels.Chronos_2_multivariate,
        ]

    @property
    def accept_static_variables(self) -> bool:
        return self.value in [
            TFCModels.TabPFN_TS,
            TFCModels.TFCGlobal,
            TFCModels.Moirai,
            TFCModels.MoiraiMoe,
            TFCModels.Moirai2,
            TFCModels.Chronos_2,
            TFCModels.Chronos_2_multivariate,
        ]

    @property
    def is_global(self) -> bool:
        return self.value in [TFCModels.TFCGlobal, TFCModels.Chronos_2_multivariate]

    @property
    def supports_batching(self) -> bool:
        """Whether this model supports batching multiple series into one request.

        Note: Effective batch size handled by model is `nb_series * nb_fcds` since
        each FCD is treated as a separate series by the model.
        """
        return self.value in [TFCModels.Chronos_2, TFCModels.Moirai2]

    @property
    def config(self) -> APIModelConfig | None:
        if self.value != TFCModels.Chronos_2_multivariate:
            return None
        return Chronos2ModelConfig(
            **{
                "model": "chronos-2",
                "config": {
                    "is_global": True,
                },
            }
        )


@dataclass
class ModelConfig:
    """
    Represents the configuration of a model for which forecasts are requested.

    Attributes:
        model (TFCModels): string identifier of the model.
        model_alias (str): alias of the model. This will be the name of the column in the result df containing the forecasts.
        future_variables (list[str]): list of future variables to be used by the model.
        with_holidays (bool): whether to include TFC-holidays in the forecast.
        with_events (bool): whether to include TFC-events in the forecast.
        country_isocode (str): ISO code of the country for which the forecast is requested. This is used for fetching the right
        holidays and events.
        historical_variables (list[str]): list of historical variables to be used by the model.
        static_variables (list[str]): list of static variables to be used by the model.
    """

    model: TFCModels
    model_alias: ModelAlias | None = None
    historical_variables: list[str] | None = None
    static_variables: list[str] | None = None
    future_variables: list[str] | None = None
    add_holidays: bool = False
    add_events: bool = False
    country_isocode: str | None = None
    batch_size: int = 256  # Only used for models with supports_batching=True

    def __post_init__(self) -> None:
        # Validate and possibly convert str to TFCModels
        self.model = TFCModels(self.model)
        if self.future_variables and not self.model.accept_future_variables:
            raise ValueError(f"Model {self.model} does not accept future variables")
        if any([self.add_holidays, self.add_events, self.country_isocode]) and not self.model.accept_future_variables:
            raise ValueError(f"Model {self.model} does not accept holidays or events")
        if self.historical_variables and not self.model.accept_historical_variables:
            raise ValueError(f"Model {self.model} does not accept historical variables")
        if self.static_variables and not self.model.accept_static_variables:
            raise ValueError(f"Model {self.model} does not accept static variables")
        if self.model_alias is None:
            self.model_alias = self.model.value

    def get_covariates(self):
        if not (self.add_holidays or self.add_events):
            return None
        if self.country_isocode is None:
            raise ValueError("holidays and events need a countryisocode or `Global` for global events.")

        cov = []
        if self.add_holidays:
            cov += [{"type": "holidays", "config": {"country": self.country_isocode}}]
        if self.add_events:
            # Add by default also Global events.
            cov += [{"type": "events", "config": {"country": self.country_isocode}}]
            cov += [{"type": "events", "config": {"country": "Global"}}]
        return cov


def extract_forecast_df_from_model_idresponse(
    responses: list[IDForecastResponse],
    fcds: list[pd.Timestamp] | dict[str, list[pd.Timestamp]],
    id_col: str = "unique_id",
    date_col: str = "ds",
) -> pd.DataFrame:
    """Build a DataFrame with the Forecasts from each TFCModel.

    responses: For each ModelAlias, a list of IDForecastResponse, one per time series (unique_id) to be forecasted.
    fcds: the forecast creation date
    id_col: the column name for the time series id
    date_col: the column name for the forecast date
    """
    models = set(response.model for response in responses)
    grouped_responses = {model: [response for response in responses if response.model == model] for model in models}
    model_dfs = []

    for model_name, response_list in grouped_responses.items():
        # Collect all data into lists first (avoid repeated DataFrame operations)
        all_mean_values: list = []
        all_dates: list = []
        all_ids: list = []
        all_fcds: list = []
        all_quantiles: dict[str, list] = {}

        for response in response_list:
            unique_id = response.unique_id
            if response.series is None:
                raise ValueError(
                    f"Response series is None: this means the model failed to generate a forecast for serie:{unique_id}"
                )
            series: list[list[OutputSerie]] = response.series
            for serie in series:
                if isinstance(fcds, list):
                    unique_id_fcds = fcds
                elif isinstance(fcds, dict):
                    unique_id_fcds = fcds.get(unique_id, [])
                    if not isinstance(unique_id_fcds, list):
                        unique_id_fcds = [unique_id_fcds]
                else:
                    raise ValueError("fcds must be a list[pd.Timestamp] or a dict[str, list[pd.Timestamp]]")
                assert len(serie) == len(unique_id_fcds) or (len(serie) == 1 and len(unique_id_fcds) == 0), (
                    "Wrong number of fcds. Expected %d, got %d" % (len(serie), len(unique_id_fcds))
                )
                if len(serie) == 1 and len(unique_id_fcds) == 0:
                    # get the fcd from the serie index
                    unique_id_fcds = [pd.Timestamp(serie[0].index[0])]

                for fcd, pred in zip(unique_id_fcds, serie, strict=False):
                    n_points = len(pred.prediction["mean"])
                    all_mean_values.extend(pred.prediction["mean"])
                    all_dates.extend(pred.index)
                    all_ids.extend([unique_id] * n_points)
                    all_fcds.extend([fcd] * n_points)

                    # Collect quantile predictions
                    for key in pred.prediction.keys():
                        if key != "mean":
                            quantile_col = f"{model_name}_q{key}"
                            if quantile_col not in all_quantiles:
                                all_quantiles[quantile_col] = []
                            all_quantiles[quantile_col].extend(pred.prediction[key])

        # Build single DataFrame at the end (much faster than repeated assign/setitem)
        model_df = pd.DataFrame(
            {
                model_name: all_mean_values,
                date_col: pd.to_datetime(all_dates),
                id_col: [str(x) for x in all_ids],
                "fcd": pd.to_datetime(all_fcds),
                **all_quantiles,
            }
        )
        model_df = model_df.sort_values([id_col, "fcd", date_col])
        model_dfs.append(model_df)

    if not all(len(df) == len(model_dfs[0]) for df in model_dfs):
        raise ValueError("All model dfs must have the same number of rows")

    res = pd.concat(model_dfs, axis=1)
    if len(res) != len(model_dfs[0]):
        raise ValueError(
            "Concatenation of model forecasts resulted in more rows than expected. Indexes unique_id, ds, fcd must be the same for all models."
        )

    return res


async def send_request_with_retries(
    forecast_request: IDForecastRequest,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    api_key: str,
    url: str,
    max_retries: int = 3,
    retry_delay: int = 2,  # nb seconds before retrying.
) -> List[IDForecastResponse] | None:
    """
    Send a request to the Retrocast API for a single time series. Return one separate ForecastResponse per OutputSerie
    """
    if max_retries < 1:
        raise ValueError("max retries should be >= 1")
    if forecast_request.unique_ids is None:
        raise ValueError("Empty ForecastRequest: unique_ids is None")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def _extract_response(
        response: ForecastResponse, unique_ids: list[str], model: ModelAlias
    ) -> list[IDForecastResponse]:
        """
        Separate all series in a forecast response and associate each to the corresponding
        model and unique_id.

        CRITICAL ASSUMPTION: The API returns series in the same order as they were sent.
        The unique_ids list is aligned with response.series by position.
        """
        assert response.series is None or len(unique_ids) == len(
            response.series
        ), "nb of forecasted unique ids and nb of series in the response do not match."
        if response.series is None:
            return [
                IDForecastResponse(model=model, unique_id=unique_id, status=response.status) for unique_id in unique_ids
            ]

        return [
            IDForecastResponse(
                model=model,
                unique_id=unique_id,
                status=response.status,
                series=[serie],
            )
            for unique_id, serie in zip(unique_ids, response.series, strict=False)
        ]

    response = None
    for _ in range(max_retries):
        async with semaphore:
            response = await client.post(url, json=forecast_request.payload, headers=headers)
        if response.status_code == 200:
            return _extract_response(
                ForecastResponse(**response.json()), forecast_request.ids_to_forecast, forecast_request.model
            )
        await asyncio.sleep(retry_delay)  # Wait before retrying

    _handle_response(response)


async def submit_forecast_job(
    forecast_request: IDForecastRequest,
    client: httpx.AsyncClient,
    api_key: str,
    url: str,
) -> str:
    """Submit a forecast job to POST /forecast-jobs endpoint.

    Args:
        forecast_request: The forecast request to submit
        client: The httpx async client
        api_key: API key for authentication
        url: The forecast-jobs endpoint URL

    Returns:
        The job ID (call_id) for polling
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = await client.post(url, json=forecast_request.payload, headers=headers)
    _handle_response(response)
    # The API returns the call_id directly as a string in the response body
    return response.json()


async def poll_job_result(
    job_id: str,
    client: httpx.AsyncClient,
    api_key: str,
    base_url: str,
) -> ForecastResponse | None:
    """Poll GET /forecast-jobs/{job_id} for result.

    Args:
        job_id: The job ID to poll
        client: The httpx async client
        api_key: API key for authentication
        base_url: Base URL for the API (e.g., https://api.retrocast.com)

    Returns:
        ForecastResponse if job is complete, None if still in_progress
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{base_url}/forecast-jobs/{job_id}"
    response = await client.get(url, headers=headers)
    _handle_response(response)
    result = ForecastResponse(**response.json())
    if result.status == "completed":
        return result
    return None


def _extract_job_response(
    response: ForecastResponse, unique_ids: list[str], model: ModelAlias
) -> list[IDForecastResponse]:
    """Extract IDForecastResponse objects from a ForecastResponse.

    This is the same logic as in send_request_with_retries but extracted for reuse.

    CRITICAL ASSUMPTION: The API returns series in the same order as they were sent.
    The unique_ids list is aligned with response.series by position.
    """
    assert response.series is None or len(unique_ids) == len(
        response.series
    ), "nb of forecasted unique ids and nb of series in the response do not match."
    if response.series is None:
        return [
            IDForecastResponse(model=model, unique_id=unique_id, status=response.status) for unique_id in unique_ids
        ]

    return [
        IDForecastResponse(
            model=model,
            unique_id=unique_id,
            status=response.status,
            series=[serie],
        )
        for unique_id, serie in zip(unique_ids, response.series, strict=False)
    ]


def _build_forecast_requests(
    train_df: pd.DataFrame,
    fcds: list[pd.Timestamp] | dict[str, pd.Timestamp | list[pd.Timestamp]],
    models: list["ModelConfig"],
    horizon: int,
    freq: str,
    api_key: str | None,
    id_col: str,
    date_col: str,
    target_col: str,
    new_ids: Iterable[str] | None,
    quantiles: list[float] | None,
    partition_by: list[str] | None,
) -> Generator[tuple[IDForecastRequest, "ModelConfig"], None, None]:
    """Build and yield forecast requests for all models and unique_ids.

    Yields (IDForecastRequest, ModelConfig) tuples ready for dispatch.

    Request batching strategy:
    - Global models (is_global=True): One request with ALL series per partition
    - Batching models (supports_batching=True): One request per batch_size series
    - Other non-global models: One request per unique_id

    Note for batching models: The effective batch size handled by the model is
    `nb_series * nb_fcds` since each FCD is treated as a separate forecasting task.

    The train_df is sorted by [id_col, date_col] internally to ensure consistent
    series ordering.
    """
    # Validation
    if api_key is None:
        raise ValueError("api_key must be provided")

    if new_ids is None:
        new_ids = set()

    if quantiles and 0.5 not in quantiles:
        quantiles = quantiles + [0.5]

    # Partition handling
    if partition_by is not None:
        if not all(model.model.is_global for model in models):
            raise ValueError("Only global models support partitioned context.")
        if not all(col in train_df.columns for col in partition_by):
            raise ValueError(
                f"All columns in partition_by must be present in train_df. "
                f"Missing columns: {set(partition_by) - set(train_df.columns)}"
            )
        if any(col == id_col for col in partition_by):
            raise ValueError(
                f"ID Column {id_col} cannot be in partition_by, as it is used to identify time series. "
                "Use a local model rather than tfc-global."
            )
        # Use sorted(set(...)) to ensure deterministic iteration order.
        # Row order in the request affects tfc-global predictions due to TabPFN's position-dependent features.
        unique_ids_to_iter = (
            train_df[partition_by + [id_col]].groupby(partition_by)[id_col].agg(lambda x: sorted(set(x))).to_dict()
        )
    else:
        unique_ids_to_iter = {"all": train_df[id_col].unique()}

    # CRITICAL: Sort and index for consistent series ordering
    train_df = train_df.sort_values(by=[id_col, date_col]).set_index(id_col)

    # Validate date_col is datetime and convert to string format once (much faster than per-series strftime)
    if not pd.api.types.is_datetime64_any_dtype(train_df[date_col]):
        raise ValueError(
            f"Column '{date_col}' must be datetime type, got {train_df[date_col].dtype}. "
            f"Convert using: df['{date_col}'] = pd.to_datetime(df['{date_col}'])"
        )
    train_df[date_col] = train_df[date_col].dt.strftime("%Y-%m-%d %H:%M:%S")

    def _make_fresh_request(mc: "ModelConfig") -> IDForecastRequest:
        """Create a fresh IDForecastRequest for the given model config."""
        return IDForecastRequest(
            model=mc.model_alias,
            horizon=horizon,
            freq=freq,
            context=None,
            covariates=mc.get_covariates(),
            quantiles=quantiles if quantiles else ForecastRequest.model_fields["quantiles"].default,
            model_config=mc.model.config,
        )

    # Build requests
    for model_config in models:
        for partition in unique_ids_to_iter.values():
            forecast_request = _make_fresh_request(model_config)
            batch_count = 0

            for unique_id in partition:
                ts_df = _get_ts_df(train_df, unique_id, target_col)
                is_new = unique_id in new_ids
                input_serie = _build_input_serie(
                    ts_df, unique_id, is_new, fcds, model_config, id_col, date_col, target_col
                )

                if model_config.model.is_global:
                    # Global: accumulate ALL series in one request
                    forecast_request.add_serie(input_serie, unique_id)

                elif model_config.model.supports_batching:
                    # Batching: accumulate up to batch_size series
                    forecast_request.add_serie(input_serie, unique_id)
                    batch_count += 1

                    if batch_count >= model_config.batch_size:
                        # Batch is full, yield it
                        yield (forecast_request, model_config)
                        # Start new batch
                        forecast_request = _make_fresh_request(model_config)
                        batch_count = 0
                else:
                    # Non-global, non-batching: yield one request per unique_id
                    yield (forecast_request.replace_serie(input_serie, unique_id), model_config)

            # Yield remaining series for global or batching models
            if model_config.model.is_global:
                yield (forecast_request, model_config)
            elif model_config.model.supports_batching and batch_count > 0:
                # Yield partial batch
                yield (forecast_request, model_config)


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
    """Submit forecast jobs and poll for completion with tqdm progress.

    This is an alternative to send_async_requests_multiple_models that uses the
    /forecast-jobs endpoint instead of /forecast. Each request is submitted as a
    separate job, and we poll all jobs concurrently, updating tqdm as each completes.

    Args:
        Same as send_async_requests_multiple_models, plus:
        poll_interval: Seconds between polling attempts (default 2.0)

    Returns:
        List of IDForecastResponse objects
    """
    base_url = "https://api.retrocast.com"
    semaphore = asyncio.Semaphore(max_concurrent)

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=120, read=600, pool=600, write=120), follow_redirects=True
    ) as client:

        async def submit_with_semaphore(request: IDForecastRequest, model_url: str) -> tuple[str, IDForecastRequest]:
            async with semaphore:
                job_id = await submit_forecast_job(request, client, api_key, model_url)
            return (job_id, request)

        # Phase 1: Build all submission tasks
        submit_tasks = []

        for request, model_config in _build_forecast_requests(
            train_df,
            fcds,
            models,
            horizon,
            freq,
            api_key,
            id_col,
            date_col,
            target_col,
            new_ids,
            quantiles,
            partition_by,
        ):
            # Build URL for this model
            model_api = (
                model_config.model if model_config.model != TFCModels.Chronos_2_multivariate else TFCModels.Chronos_2
            )
            model_url = url if url else f"{base_url}/forecast-jobs?model={model_api.value}"
            if cloud:
                model_url = f"{model_url}&cloud={cloud}"

            submit_tasks.append(submit_with_semaphore(request, model_url))

        # Submit all jobs in parallel with progress bar
        job_submissions: list[tuple[str, IDForecastRequest]] = await tqdm_asyncio.gather(
            *submit_tasks, desc=f"Submitting {len(submit_tasks)} jobs"
        )

        # Phase 2: Poll until all jobs complete
        pending: dict[str, IDForecastRequest] = {job_id: req for job_id, req in job_submissions}
        results: list[IDForecastResponse] = []

        with tqdm(total=len(pending), desc=f"Processing {len(pending)} forecast jobs") as pbar:
            while pending:
                completed_jobs = []
                for job_id, req in pending.items():
                    async with semaphore:
                        result = await poll_job_result(job_id, client, api_key, base_url)
                    if result is not None:
                        # Job completed - extract responses
                        responses = _extract_job_response(result, req.ids_to_forecast, req.model)
                        results.extend(responses)
                        completed_jobs.append(job_id)
                        pbar.update(1)

                # Remove completed jobs from pending
                for job_id in completed_jobs:
                    del pending[job_id]

                if pending:
                    await asyncio.sleep(poll_interval)

        return results


def _get_ts_df(train_df: pd.DataFrame, unique_id: str, target_col: str):
    """Extract the time series dataframe, handling edge cases were the time series has only one observation.

    Args:
        train_df: The training dataframe (must be indexed by id_col)
        unique_id: The unique id of the time series
        target_col: The column name for the target

    Returns:
        DataFrame with columns for the time series data. Note: Does NOT include id_col as a column
        (it's the index). The unique_id is passed separately to _build_input_serie.
    """
    ts_df = train_df.loc[unique_id]
    if isinstance(ts_df, pd.Series):
        # When unique_id has only one row in train_df, train_df.loc[unique_id] returns a Series
        # and not a dataframe. Convert to single-row DataFrame directly.
        ts_df = pd.DataFrame(
            {col: [ts_df[col]] for col in ts_df.index},
            index=[0],
        )
        # Ensure target is float (date_col is already string from _build_forecast_requests)
        ts_df[target_col] = ts_df[target_col].astype(float)
    # Note: We no longer call reset_index() - the unique_id is passed separately
    return ts_df


def _build_input_serie(
    ts_df: pd.DataFrame,
    unique_id: str,
    is_new: bool,
    fcds: list[pd.Timestamp] | dict[str, pd.Timestamp | list[pd.Timestamp]],
    model_config: ModelConfig,
    id_col: str,
    date_col: str,
    target_col: str,
) -> InputSerie:
    """Build the input series for the API request.

    Args:
        ts_df: The time series dataframe (id_col is the index, not a column)
        unique_id: The unique id of this time series
        is_new: Whether the time series is new, ie, it's only in the test set but not in the train set.
        model_config: The model configuration
        id_col: The column name for the unique id (used if id_col is in static_variables)
        date_col: The column name for the date
        target_col: The column name for the target
    """
    # date_col is already converted to string format in _build_forecast_requests
    index = ts_df[date_col].to_list()
    target = ts_df[target_col].to_list()

    # TODO: Treat future_vars and static_vars separately in the future.
    future_vars = model_config.future_variables[:] if model_config.future_variables else []
    if model_config.static_variables:
        future_vars += model_config.static_variables
    if future_vars:
        # Reuse already formatted index (avoid duplicate strftime call)
        future_variables_index = index
        # Handle id_col specially: it's the index, not a column, so use unique_id parameter
        future_dict = {col: [unique_id] * len(index) if col == id_col else ts_df[col].to_list() for col in future_vars}
    else:
        future_variables_index = []
        future_dict = {}
    if model_config.historical_variables:
        hist_variables_dict = {col: ts_df[col].to_list() for col in model_config.historical_variables}
    else:
        hist_variables_dict = {}

    if (
        # Only global model supports only_as_context=True
        not model_config.model.is_global
        # If fcds is a list, all time series will be predicte with same FCDs
        or isinstance(fcds, list)
        # If fcds is a dict, it contains the FCDs for the time that needs to be forecasted
        or unique_id in fcds
    ):
        only_as_context = False
    else:
        only_as_context = True

    return InputSerie(
        **{
            "future_variables": future_dict,
            "future_variables_index": future_variables_index,
            "hist_variables": hist_variables_dict,
            "index": index,
            "static_variables": {},
            "target": target,
            "fcds": _compute_fcds_idx(unique_id, is_new, fcds, index),
            "only_as_context": only_as_context,
        }
    )


def _compute_fcds_idx(
    unique_id: str,
    is_new: bool,
    fcds: list[pd.Timestamp] | dict[str, pd.Timestamp | list[pd.Timestamp]],
    index: list[str],
) -> list[int] | None:
    """Compute the index of the forecast creation dates in the index list.

    Args:
        unique_id: The unique id of the time series
        is_new: Whether the time series is new, ie, it's only in the test set but not in the train set.
        fcds: List of forecast creation dates or dictionary of forecast creation dates per unique_id.
            If fcds is a list, the same FCD is used for all time series.
            If fcds is a dict, a different FCD is used for each time series.
            If fcds is an empty list, the forecast is created from the period following the last observation.
        index: List of dates in the time series

    Returns:
        List of indices of the forecast creation dates in the index list
    """
    if is_new:
        # Support only single forecast for a new series. If several FCD needs to be tried, at the moment these need to be separate calls
        return [0]

    unique_id_fcds = fcds if isinstance(fcds, list) else fcds.get(unique_id, [])
    if not isinstance(unique_id_fcds, list):
        unique_id_fcds = [unique_id_fcds]
    if unique_id_fcds and not isinstance(unique_id_fcds[0], str):
        unique_id_fcds = [c.strftime("%Y-%m-%d %H:%M:%S") for c in unique_id_fcds]

    idxs = np.nonzero(np.isin(np.array(index), unique_id_fcds))[0].tolist()
    # TODO: test this function and that ir raises errors when expected.
    # Test forecast: FCD > max(index) --> fcds = [] passed to the API
    # Backtest forecast: FCD <= max(index) --> fcds = [] will be passed to the API but this is wrong, cause
    # FCD > max(index) will be used in this case.
    if len(idxs) != len(unique_id_fcds) and max(unique_id_fcds) < max(index):
        # TODO: I should check for each fcd to be more precise, cause I can have some fcd that re smaller
        # and some fcds that are bigger than max(index)
        raise ValueError(f"Not all fcds found in among given dates for id={unique_id}")

    return idxs if idxs else None  # TimesFM and Chronos do not handle correctly fcds=[]


async def send_async_requests_multiple_models(
    train_df: pd.DataFrame,
    fcds: list[pd.Timestamp] | dict[str, pd.Timestamp | list[pd.Timestamp]],
    models: list[ModelConfig],
    horizon: int = 13,
    freq: str = "W",
    max_retries: int = 5,
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
) -> list[IDForecastResponse]:
    """Sends request for each unique_id (timeseries) asynchronously to the Retrocast API.
    Returns a list of responses.

    Args:
        train_df: DataFrame with columns [id_col, date_col, target_col]
        fcds: List of forecast creation dates or dictionary of forecast creation dates per unique_id
        models: List of ModelConfig objects
        horizon: Forecast horizon
        freq: Frequency of the time series
        max_retries: Maximum number of retries
        max_concurrent: Maximum number of concurrent requests
        api_key: API key for authentication
        url: URL for the API
        id_col: Column name for unique_id
        date_col: Column name for date
        target_col: Column name for target
        new_ids: List of new unique_ids to be predicted
        partition_by: List of columns to partition by. Only global models support partitioned context.
    """
    base_url = "https://api.retrocast.com"
    semaphore = asyncio.Semaphore(max_concurrent)

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=120, read=600, pool=600, write=120), follow_redirects=True
    ) as client:
        tasks = []

        for request, model_config in _build_forecast_requests(
            train_df,
            fcds,
            models,
            horizon,
            freq,
            api_key,
            id_col,
            date_col,
            target_col,
            new_ids,
            quantiles,
            partition_by,
        ):
            # Build URL for this model
            model_api = (
                model_config.model if model_config.model != TFCModels.Chronos_2_multivariate else TFCModels.Chronos_2
            )
            model_url = url if url else f"{base_url}/forecast?model={model_api.value}"
            if cloud:
                model_url = f"{model_url}&cloud={cloud}"

            # URL validation (keep existing check)
            if model_api not in model_url:
                raise ValueError(f"Wrong url provided: {model_api} not found in url {model_url}")

            tasks.append(
                asyncio.create_task(
                    send_request_with_retries(
                        request,
                        client=client,
                        semaphore=semaphore,
                        api_key=api_key,
                        url=model_url,
                        max_retries=max_retries,
                    )
                )
            )

        # Check if any model uses batching for the progress bar description
        uses_batching = any(m.model.supports_batching for m in models)
        desc = f"Sending {len(tasks)} {'batched ' if uses_batching else ''}requests"
        responses: list[list[IDForecastResponse]] = await tqdm_asyncio.gather(*tasks, desc=desc)

        # Chain the responses from different models/batches into one single list
        return [item for sublist in responses for item in sublist]


def cross_validate_models(
    train_df: pd.DataFrame,
    fcds: list[pd.Timestamp] | dict[str, pd.Timestamp],
    models: list[ModelConfig],
    horizon: int,
    freq: str,
    max_retries: int = 5,
    max_concurrent: int = 100,
    api_key: str | None = None,
    url: str | None = None,
    id_col: str = "unique_id",
    date_col: str = "ds",
    target_col: str = "target",
    new_ids: Iterable[str] | None = None,
    cloud: Literal["aws", "gcp", "oci"] | None = None,
    quantiles: list[float] | None = None,
    partition_by: list[str] | None = None,
    async_threshold: int | None = None,
) -> pd.DataFrame:
    # Calculate the number of requests that will be made
    num_unique_ids = train_df[id_col].nunique()
    # For non-global models, each unique_id becomes a separate request
    # For global models, all unique_ids are batched into one request per partition
    num_requests = sum(1 if model.model.is_global else num_unique_ids for model in models)

    # TODO: Improve polling for async jobs before enabling by default
    use_jobs_endpoint = async_threshold is not None and num_requests > async_threshold

    async def _run():
        if use_jobs_endpoint:
            return await send_async_requests_via_jobs(
                train_df,
                fcds,
                models,
                horizon,
                freq,
                max_concurrent,
                api_key,
                url,
                id_col,
                date_col,
                target_col,
                new_ids,
                cloud,
                quantiles,
                partition_by,
            )
        else:
            return await send_async_requests_multiple_models(
                train_df,
                fcds,
                models,
                horizon,
                freq,
                max_retries,
                max_concurrent,
                api_key,
                url,
                id_col,
                date_col,
                target_col,
                new_ids,
                cloud,
                quantiles,
                partition_by,
            )

    try:
        return extract_forecast_df_from_model_idresponse(asyncio.run(_run()), fcds, id_col, date_col)
    except RuntimeError as e:
        if "asyncio.run() cannot be called" in str(e) or "This event loop is already running" in str(e):
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            return extract_forecast_df_from_model_idresponse(loop.run_until_complete(_run()), fcds, id_col, date_col)
        else:
            raise
