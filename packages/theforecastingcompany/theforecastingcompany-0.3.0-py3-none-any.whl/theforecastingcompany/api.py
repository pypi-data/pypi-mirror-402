"""
API definitions. CI picks this up and creates a PR in public-api.
"""

from datetime import date, datetime
from typing import Annotated, Dict, List, Literal, Optional, TypeAlias, Union

from pydantic import BaseModel, ValidationInfo
from pydantic.fields import Field
from pydantic.functional_validators import field_validator

Numeric: TypeAlias = Union[float, int]
Array: TypeAlias = List[Numeric | str]
Index: TypeAlias = Union[List[str], List[date], List[datetime]]
FrequencyType: TypeAlias = Literal["5min", "15min", "30min", "H", "D", "W", "M", "Q", "Y"]
ModelSlug: TypeAlias = Literal["aarima", "aets"]


class BaseModelConfig(BaseModel):
    model_config = {"extra": "forbid"}


class AarimaConfig(BaseModelConfig):
    season_length: Optional[int] = Field(
        default=None,
        ge=1,
        description="Override automatic seasonal period detection.",
    )


class AarimaModelConfig(BaseModel):
    model: Literal["aarima"]
    config: AarimaConfig


class AetsConfig(BaseModelConfig):
    season_length: Optional[int] = Field(
        default=None,
        ge=1,
        description="Override automatic seasonal period detection.",
    )


class AetsModelConfig(BaseModel):
    model: Literal["aets"]
    config: AetsConfig


class Chronos2Config(BaseModelConfig):
    is_global: bool = Field(
        default=False,
        description="Enable influence across the time-series - useful if all passed in time-series are related (e.g. same product, different stores).",
    )


class Chronos2ModelConfig(BaseModel):
    model: Literal["chronos-2"]
    config: Chronos2Config


ModelConfig = Annotated[Union[AarimaModelConfig, AetsModelConfig, Chronos2ModelConfig], Field(discriminator="model")]


# TODO: create a wrapper to do this once
def get_aarima_config(model_config: ModelConfig | None) -> AarimaConfig | None:
    """Get auto-ARIMA config parameters."""
    if model_config is None:
        return None
    if isinstance(model_config, AarimaModelConfig):
        return model_config.config
    raise ValueError("Received model_config for a different model; expected 'aarima'.")


def get_aets_config(model_config: ModelConfig | None) -> AetsConfig | None:
    """Get auto-ETS config parameters."""
    if model_config is None:
        return None
    if isinstance(model_config, AetsModelConfig):
        return model_config.config
    raise ValueError("Received model_config for a different model; expected 'aets'.")


def get_chronos_2_config(model_config: ModelConfig | None) -> Chronos2Config:
    """Get Chronos-2 config parameters."""
    if model_config is None:
        return Chronos2Config()
    if isinstance(model_config, Chronos2ModelConfig):
        return model_config.config
    raise ValueError("Received model_config for a different model; expected 'chronos-2'.")


class HolidayConfig(BaseModel):
    country: str = Field(
        ...,
        description="ISO country code for holidays",
        examples=["US", "GB", "FR", "DE"],
        min_length=2,
        max_length=2,
    )
    smoothing_method: Optional[Literal["none", "gaussian", "exponential", "ramp", "flat"]] = Field(
        default="none",
        description="Method to smooth holiday indicators (none=binary 0/1)",
    )
    window_size: Optional[int] = Field(
        default=15,
        description="Size of the smoothing window, should be odd",
        ge=1,
        le=15,
    )
    sigma: Optional[float] = Field(
        default=7.0,
        description="Standard deviation for Gaussian kernel",
        gt=0,
    )
    ramp_days: Optional[int] = Field(
        default=14,
        description="Number of days before/after for ramp up/down",
        ge=1,
        le=35,
    )


# TODO: Add events_type and superclass Holidays and SportsEvents etc
class EventConfig(BaseModel):
    country: str = Field(
        ...,
        description="ISO country code for events (2-char code or 'Global')",
        examples=["US", "GB", "FR", "DE", "Global"],
    )

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:  # noqa
        if v == "Global":
            return v
        if isinstance(v, str) and len(v) == 2:
            return v
        raise ValueError("country must be a 2-character string or the literal 'Global'")


class FloatConfig(BaseModel):
    data_source: str
    column: str = Field(..., description="Column for the data source", min_length=1, max_length=100)


class TemporalFeaturesConfig(BaseModel):
    pass


class HolidaysCovariate(BaseModel):
    type: Literal["holidays"] = Field(..., examples=["holidays"])
    config: HolidayConfig = Field(..., examples=[{"country": "US"}])


class EventsCovariate(BaseModel):
    type: Literal["events"] = Field(..., examples=["events"])
    config: EventConfig = Field(..., examples=[{"country": "US"}])


class FloatDataSourceCovariate(BaseModel):
    type: Literal["float"] = Field(..., examples=["float"])
    config: FloatConfig = Field(..., examples=[{"column": "SomeColumn"}])


class TemporalFeaturesCovariate(BaseModel):
    type: Literal["temporal_features"] = Field(..., examples=["temporal_features"])
    config: TemporalFeaturesConfig = Field(..., examples=[{}])


Covariate = Union[
    HolidaysCovariate,
    FloatDataSourceCovariate,
    EventsCovariate,
    TemporalFeaturesCovariate,
]


class InputSerie(BaseModel):
    target: Array = Field(..., description="A list of numeric target values.")
    index: Index = Field(..., description="A list of dates, datetimes, times, or integers.")
    hist_variables: Dict[str, Array] = Field(
        default={},
        description="A dictionary mapping string keys to lists of historical numeric values, e.g. recorded temperatures.",
    )
    future_variables_index: Index = Field(default=[], description="A list of dates, datetimes, times, or integers.")
    future_variables: Dict[str, Array] = Field(
        default={},
        description="A dictionary mapping string keys to lists of numeric values that have the length of the target plus the horizon, e.g. forecasted temperatures.",
    )
    static_variables: Dict[str, Numeric] = Field(
        default={},
        description="A dictionary mapping string keys to static numeric values, e.g. a SKU.",
    )
    fcds: List[int] | None = Field(
        default=None,
        description="A list of indexes representing the forecast creation dates, indexing the target. If not provided the forecast creation date is the latest possible date. This can be used to get multiple forecasts from the same series at once (e.g. for backtesting).",
    )

    only_as_context: bool = Field(
        default=False,
        description="If True, the series will be used only as context (ie, not forecasted). This should always be False unless a global model is used.",
    )

    @field_validator("fcds")
    @classmethod
    def validate_fcds(cls, v: List[int] | None) -> List[int] | None:
        """
        Require all FCDs to be non-negative.

        Note: fcd=0 is valid when predicting new products with TFCGlobal (no historical data).
        """
        if v is None:
            return v

        for i in v:
            if i < 0:
                raise ValueError(f"FCDs must be non-negative integers. Found invalid value: {i}.")

        return v

    @field_validator("future_variables")
    @classmethod
    def validate_future_variables_length(cls, v: Dict[str, Array], info: ValidationInfo) -> Dict[str, Array]:  # noqa
        future_variables_index = info.data.get("future_variables_index")
        if future_variables_index is None:
            raise ValueError("future_variables_index must be set if including future_variables")

        expected_length = len(future_variables_index)
        for var_name, array in v.items():
            if len(array) != expected_length:
                raise ValueError(
                    f"Array '{var_name}' in future_variables has length {len(array)}, "
                    f"but should have length {expected_length} to match future_variables_index"
                )
        return v


# Custom type for quantile levels as strings
def validate_quantile_level(v: str) -> str:  # noqa
    try:
        float_val = float(v)
        if 0 < float_val < 1:
            return v
    except ValueError:
        pass
    raise ValueError("QuantileLevelStr must be a string representing a float between 0 and 1.")


QuantileLevel = Annotated[str, field_validator("QuantileLevelStr", mode="before")(validate_quantile_level)]


class Metrics(BaseModel):
    mae: float | None = Field(default=None, ge=0)
    mape: float | None = Field(default=None, ge=0)
    crps: float | None = Field(default=None, ge=0)
    wape: float | None = Field(default=None, ge=0)
    scaled_bias: float | None = Field(default=None)


class OutputSerie(BaseModel):
    prediction: Dict[str, Array] = Field(
        ...,
        examples=[
            {
                "mean": [1, 2, 3],
                "0.1": [1, 2, 3],
                "0.9": [1, 2, 3],
            }
        ],
    )
    index: Index = Field(..., examples=[])
    metrics: Optional[Metrics] = None

    @field_validator("prediction")
    def validate_prediction_keys(cls, v):  # noqa
        for key in v.keys():
            if key not in ["mean", "samples"]:
                validate_quantile_level(key)
        return v


class ForecastResponse(BaseModel):
    series: Optional[List[List[OutputSerie]]] = None  # if job is processing
    status: Literal["completed"] | Literal["in_progress"] = "completed"


class ForecastRequest(BaseModel):
    """
    API request model for the model inference endpoint.
    """

    series: List[InputSerie] = Field(
        examples=[
            [
                {
                    "target": [
                        125,
                        120,
                        140,
                        135,
                        133,
                    ],
                    "index": [
                        "2001-01-06",
                        "2001-01-07",
                        "2001-01-08",
                        "2001-01-09",
                        "2001-01-10",
                    ],
                    "hist_variables": {
                        "temperature": [74, 72, 79, 77, 75],
                    },
                    "future_variables_index": [
                        "2001-01-06",
                        "2001-01-07",
                        "2001-01-08",
                        "2001-01-09",
                        "2001-01-10",
                        "2001-01-11",
                        "2001-01-12",
                        "2001-01-13",
                        "2001-01-14",
                        "2001-01-15",
                    ],
                    "future_variables": {
                        "local_attendance_forecast": [
                            125,
                            75,
                            200,
                            122,
                            123,
                            150,
                            100,
                            120,
                            121,
                            119,
                        ],
                    },
                    "static_variables": {"Population": 100000},
                },
            ]
        ]
    )

    horizon: int = Field(
        ...,
        ge=1,
        le=10_000,
        examples=[5],
        description="Number of steps to forecast given the frequency.",
    )
    freq: FrequencyType = Field(..., examples=["D"], description="Frequency of the time series.")
    context: int | None = Field(
        default=None,
        ge=1,
        examples=[20],
        description="The amount of history to use when forecasting. This is the number of steps to look back in the target series. More history can improve the forecast accuracy, but can also increase the computation time. By default this is set to the max of model capability or the length of the provided target series, whichever is shorter.",
    )
    quantiles: List[float] | None = Field(default=[0.1, 0.9, 0.4, 0.5])
    covariates: List[Covariate] | None = Field(
        default=None,
        description="Apply additional co-variates provided by TFC. Only supported by the following models: Navi, Moirai, Moriai-MoE and TabPFN-TS.",
        examples=[[{"type": "holidays", "config": {"country": "US"}}]],
    )
    model_cfg: ModelConfig | None = Field(
        alias="model_config",
        default=None,
        description="Optional model-specific configuration overrides.",
        examples=[
            {
                "model": "aarima",
                "config": {
                    "season_length": 7,
                },
            }
        ],
    )


if __name__ == "__main__":
    # NOTE: can copy these to the gateway schemas
    # Ideally we'd have it automated with github actions eventually
    import json

    with open("ForecastRequest.json", "w") as f:
        json.dump(ForecastRequest.model_json_schema(), f, indent=2)

    with open("ForecastResponse.json", "w") as f:
        json.dump(ForecastResponse.model_json_schema(), f, indent=2)
