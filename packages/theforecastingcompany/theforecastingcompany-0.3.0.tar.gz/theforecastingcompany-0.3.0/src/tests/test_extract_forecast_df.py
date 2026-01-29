"""Tests for extract_forecast_df_from_model_idresponse function.

This test file ensures the function's contract is maintained before and after refactoring.
"""

import pandas as pd
import pytest

from theforecastingcompany.api import OutputSerie
from theforecastingcompany.utils import IDForecastResponse, extract_forecast_df_from_model_idresponse


def create_mock_response(
    model: str,
    unique_id: str,
    predictions: dict,
    index: list,
) -> IDForecastResponse:
    """Create a mock IDForecastResponse for testing.

    Args:
        model: Model alias (e.g., "chronos-2")
        unique_id: Time series identifier
        predictions: Dict with "mean" and optional quantile keys (e.g., {"mean": [1,2,3], "0.1": [0.5,1,1.5]})
        index: List of date strings (e.g., ["2024-01-01", "2024-01-02"])

    Returns:
        IDForecastResponse with a single OutputSerie
    """
    output_serie = OutputSerie(prediction=predictions, index=index)
    return IDForecastResponse(
        model=model,
        unique_id=unique_id,
        series=[[output_serie]],
        status="completed",
    )


def create_mock_response_multi_fcd(
    model: str,
    unique_id: str,
    predictions_list: list[dict],
    index_list: list[list],
) -> IDForecastResponse:
    """Create a mock IDForecastResponse with multiple FCDs (multiple OutputSeries).

    Args:
        model: Model alias
        unique_id: Time series identifier
        predictions_list: List of prediction dicts, one per FCD
        index_list: List of index lists, one per FCD

    Returns:
        IDForecastResponse with multiple OutputSeries
    """
    output_series = [
        OutputSerie(prediction=pred, index=idx) for pred, idx in zip(predictions_list, index_list, strict=True)
    ]
    return IDForecastResponse(
        model=model,
        unique_id=unique_id,
        series=[output_series],
        status="completed",
    )


class TestExtractForecastDfSingleModel:
    """Tests with a single model."""

    def test_single_series_single_fcd(self):
        """Basic test: single model, single series, single FCD."""
        response = create_mock_response(
            model="chronos-2",
            unique_id="series_1",
            predictions={"mean": [10.0, 20.0, 30.0], "0.1": [8.0, 16.0, 24.0], "0.9": [12.0, 24.0, 36.0]},
            index=["2024-01-01", "2024-01-02", "2024-01-03"],
        )
        fcds = [pd.Timestamp("2023-12-31")]

        result = extract_forecast_df_from_model_idresponse([response], fcds)

        # Check shape
        assert len(result) == 3, f"Expected 3 rows, got {len(result)}"

        # Check columns exist
        expected_cols = {"chronos-2", "chronos-2_q0.1", "chronos-2_q0.9", "unique_id", "ds", "fcd"}
        assert expected_cols.issubset(set(result.columns)), f"Missing columns: {expected_cols - set(result.columns)}"

        # Check values
        assert list(result["chronos-2"]) == [10.0, 20.0, 30.0]
        assert list(result["chronos-2_q0.1"]) == [8.0, 16.0, 24.0]
        assert list(result["chronos-2_q0.9"]) == [12.0, 24.0, 36.0]
        assert list(result["unique_id"]) == ["series_1"] * 3

        # Check types
        assert pd.api.types.is_datetime64_any_dtype(result["ds"])
        assert pd.api.types.is_datetime64_any_dtype(result["fcd"])
        assert result["unique_id"].dtype == object  # string type

    def test_multiple_series(self):
        """Test with multiple time series (unique_ids)."""
        response1 = create_mock_response(
            model="chronos-2",
            unique_id="series_1",
            predictions={"mean": [10.0, 20.0]},
            index=["2024-01-01", "2024-01-02"],
        )
        response2 = create_mock_response(
            model="chronos-2",
            unique_id="series_2",
            predictions={"mean": [100.0, 200.0]},
            index=["2024-01-01", "2024-01-02"],
        )
        fcds = [pd.Timestamp("2023-12-31")]

        result = extract_forecast_df_from_model_idresponse([response1, response2], fcds)

        # Check shape: 2 series × 2 forecast points = 4 rows
        assert len(result) == 4

        # Check both series are present
        assert set(result["unique_id"].unique()) == {"series_1", "series_2"}

        # Check values are correct for each series (sorted by unique_id, fcd, ds)
        series_1_data = result[result["unique_id"] == "series_1"]["chronos-2"].tolist()
        series_2_data = result[result["unique_id"] == "series_2"]["chronos-2"].tolist()
        assert series_1_data == [10.0, 20.0]
        assert series_2_data == [100.0, 200.0]

    def test_multiple_fcds_with_list(self):
        """Test with multiple FCDs provided as a list (same for all series)."""
        response = create_mock_response_multi_fcd(
            model="chronos-2",
            unique_id="series_1",
            predictions_list=[
                {"mean": [10.0, 20.0]},  # FCD 1
                {"mean": [15.0, 25.0]},  # FCD 2
            ],
            index_list=[
                ["2024-01-01", "2024-01-02"],
                ["2024-01-02", "2024-01-03"],
            ],
        )
        fcds = [pd.Timestamp("2023-12-30"), pd.Timestamp("2023-12-31")]

        result = extract_forecast_df_from_model_idresponse([response], fcds)

        # Check shape: 2 FCDs × 2 forecast points = 4 rows
        assert len(result) == 4

        # Check both FCDs are present
        assert len(result["fcd"].unique()) == 2

    def test_multiple_fcds_with_dict(self):
        """Test with FCDs provided as a dict (per-series FCDs)."""
        response = create_mock_response_multi_fcd(
            model="chronos-2",
            unique_id="series_1",
            predictions_list=[
                {"mean": [10.0, 20.0]},
                {"mean": [15.0, 25.0]},
            ],
            index_list=[
                ["2024-01-01", "2024-01-02"],
                ["2024-01-02", "2024-01-03"],
            ],
        )
        fcds = {"series_1": [pd.Timestamp("2023-12-30"), pd.Timestamp("2023-12-31")]}

        result = extract_forecast_df_from_model_idresponse([response], fcds)

        assert len(result) == 4
        assert len(result["fcd"].unique()) == 2

    def test_single_point_forecast(self):
        """Test edge case: single point forecast."""
        response = create_mock_response(
            model="chronos-2",
            unique_id="series_1",
            predictions={"mean": [42.0]},
            index=["2024-01-01"],
        )
        fcds = [pd.Timestamp("2023-12-31")]

        result = extract_forecast_df_from_model_idresponse([response], fcds)

        assert len(result) == 1
        assert result["chronos-2"].iloc[0] == 42.0

    def test_fcd_inferred_from_index(self):
        """Test that FCD is inferred from index when fcds is empty list."""
        response = create_mock_response(
            model="chronos-2",
            unique_id="series_1",
            predictions={"mean": [10.0, 20.0]},
            index=["2024-01-01", "2024-01-02"],
        )
        fcds: list[pd.Timestamp] = []

        result = extract_forecast_df_from_model_idresponse([response], fcds)

        assert len(result) == 2
        # FCD should be inferred from the first index value
        assert result["fcd"].iloc[0] == pd.Timestamp("2024-01-01")

    def test_many_quantiles(self):
        """Test with many quantile levels."""
        quantiles = {
            "mean": [10.0],
            "0.05": [5.0],
            "0.1": [6.0],
            "0.25": [7.5],
            "0.5": [10.0],
            "0.75": [12.5],
            "0.9": [14.0],
            "0.95": [15.0],
        }
        response = create_mock_response(
            model="chronos-2",
            unique_id="series_1",
            predictions=quantiles,
            index=["2024-01-01"],
        )
        fcds = [pd.Timestamp("2023-12-31")]

        result = extract_forecast_df_from_model_idresponse([response], fcds)

        # Check all quantile columns are present
        for q in ["0.05", "0.1", "0.25", "0.5", "0.75", "0.9", "0.95"]:
            col_name = f"chronos-2_q{q}"
            assert col_name in result.columns, f"Missing column {col_name}"


class TestExtractForecastDfMultipleModels:
    """Tests with multiple models."""

    def test_two_models_same_series(self):
        """Test horizontal concat of two models for the same series."""
        response1 = create_mock_response(
            model="chronos-2",
            unique_id="series_1",
            predictions={"mean": [10.0, 20.0]},
            index=["2024-01-01", "2024-01-02"],
        )
        response2 = create_mock_response(
            model="moirai-2",
            unique_id="series_1",
            predictions={"mean": [11.0, 21.0]},
            index=["2024-01-01", "2024-01-02"],
        )
        fcds = [pd.Timestamp("2023-12-31")]

        result = extract_forecast_df_from_model_idresponse([response1, response2], fcds)

        # Check shape: same rows, but columns for both models
        assert len(result) == 2
        assert "chronos-2" in result.columns
        assert "moirai-2" in result.columns

        # Check values
        assert list(result["chronos-2"]) == [10.0, 20.0]
        assert list(result["moirai-2"]) == [11.0, 21.0]

    def test_two_models_multiple_series(self):
        """Test two models with multiple series."""
        responses = [
            create_mock_response("chronos-2", "series_1", {"mean": [10.0]}, ["2024-01-01"]),
            create_mock_response("chronos-2", "series_2", {"mean": [20.0]}, ["2024-01-01"]),
            create_mock_response("moirai-2", "series_1", {"mean": [11.0]}, ["2024-01-01"]),
            create_mock_response("moirai-2", "series_2", {"mean": [21.0]}, ["2024-01-01"]),
        ]
        fcds = [pd.Timestamp("2023-12-31")]

        result = extract_forecast_df_from_model_idresponse(responses, fcds)

        # Check shape: 2 series × 1 forecast point = 2 rows
        assert len(result) == 2
        assert "chronos-2" in result.columns
        assert "moirai-2" in result.columns


class TestExtractForecastDfSortOrder:
    """Tests for correct sort order."""

    def test_sort_order_by_unique_id_fcd_ds(self):
        """Verify results are sorted by (unique_id, fcd, ds)."""
        # Create responses in non-sorted order
        responses = [
            create_mock_response("chronos-2", "series_2", {"mean": [200.0]}, ["2024-01-02"]),
            create_mock_response("chronos-2", "series_1", {"mean": [100.0]}, ["2024-01-01"]),
        ]
        fcds = [pd.Timestamp("2023-12-31")]

        result = extract_forecast_df_from_model_idresponse(responses, fcds)

        # series_1 should come before series_2
        assert result["unique_id"].iloc[0] == "series_1"
        assert result["unique_id"].iloc[1] == "series_2"


class TestExtractForecastDfErrors:
    """Tests for error conditions."""

    def test_none_series_raises_error(self):
        """Test that None series raises ValueError."""
        response = IDForecastResponse(
            model="chronos-2",
            unique_id="series_1",
            series=None,
            status="completed",
        )
        fcds = [pd.Timestamp("2023-12-31")]

        with pytest.raises(ValueError, match="Response series is None"):
            extract_forecast_df_from_model_idresponse([response], fcds)

    def test_mismatched_fcd_count_raises_error(self):
        """Test that mismatched FCD count raises AssertionError."""
        response = create_mock_response_multi_fcd(
            model="chronos-2",
            unique_id="series_1",
            predictions_list=[{"mean": [10.0]}, {"mean": [20.0]}],  # 2 series
            index_list=[["2024-01-01"], ["2024-01-02"]],
        )
        fcds = [pd.Timestamp("2023-12-31")]  # Only 1 FCD but 2 series

        with pytest.raises(AssertionError, match="Wrong number of fcds"):
            extract_forecast_df_from_model_idresponse([response], fcds)

    def test_invalid_fcds_type_raises_error(self):
        """Test that invalid fcds type raises ValueError."""
        response = create_mock_response(
            model="chronos-2",
            unique_id="series_1",
            predictions={"mean": [10.0]},
            index=["2024-01-01"],
        )

        with pytest.raises(ValueError, match="fcds must be a list"):
            extract_forecast_df_from_model_idresponse([response], "invalid")  # type: ignore

    def test_models_with_different_row_counts_raises_error(self):
        """Test that models with different row counts raises ValueError."""
        response1 = create_mock_response(
            model="chronos-2",
            unique_id="series_1",
            predictions={"mean": [10.0, 20.0]},  # 2 rows
            index=["2024-01-01", "2024-01-02"],
        )
        response2 = create_mock_response(
            model="moirai-2",
            unique_id="series_1",
            predictions={"mean": [11.0]},  # 1 row - different!
            index=["2024-01-01"],
        )
        fcds = [pd.Timestamp("2023-12-31")]

        with pytest.raises(ValueError, match="All model dfs must have the same number of rows"):
            extract_forecast_df_from_model_idresponse([response1, response2], fcds)


class TestExtractForecastDfCustomColumns:
    """Tests for custom column names."""

    def test_custom_id_col(self):
        """Test with custom id column name."""
        response = create_mock_response(
            model="chronos-2",
            unique_id="series_1",
            predictions={"mean": [10.0]},
            index=["2024-01-01"],
        )
        fcds = [pd.Timestamp("2023-12-31")]

        result = extract_forecast_df_from_model_idresponse([response], fcds, id_col="my_id")

        assert "my_id" in result.columns
        assert "unique_id" not in result.columns
        assert result["my_id"].iloc[0] == "series_1"

    def test_custom_date_col(self):
        """Test with custom date column name."""
        response = create_mock_response(
            model="chronos-2",
            unique_id="series_1",
            predictions={"mean": [10.0]},
            index=["2024-01-01"],
        )
        fcds = [pd.Timestamp("2023-12-31")]

        result = extract_forecast_df_from_model_idresponse([response], fcds, date_col="timestamp")

        assert "timestamp" in result.columns
        assert "ds" not in result.columns
        assert pd.api.types.is_datetime64_any_dtype(result["timestamp"])
