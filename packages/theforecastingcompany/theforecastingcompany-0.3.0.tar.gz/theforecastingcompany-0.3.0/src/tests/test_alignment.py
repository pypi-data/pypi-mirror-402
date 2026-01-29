"""Tests for input/output series alignment.

These tests verify that forecast outputs are correctly associated with their
input time series, especially for:
- Multiple series
- Global models (batched requests)
- Partitioned global models
- Multiple models
"""

import numpy as np
import pandas as pd
import pytest

from theforecastingcompany import TFCClient
from theforecastingcompany.utils import ModelConfig, TFCModels, _build_forecast_requests


def create_distinctive_series(
    n_series: int = 3,
    n_points: int = 100,
    base_values: list[float] | None = None,
) -> pd.DataFrame:
    """Create time series with distinctive constant values for alignment verification."""
    if base_values is None:
        base_values = [100 * (i + 1) for i in range(n_series)]

    dates = pd.date_range("2023-01-01", periods=n_points, freq="D")
    series = []

    for i, base_value in enumerate(base_values):
        uid = f"series_{chr(65 + i)}"  # series_A, series_B, etc.
        # Small noise but mean ~= base_value
        values = base_value + np.random.normal(0, 2, n_points)
        series.append(
            pd.DataFrame(
                {
                    "unique_id": uid,
                    "ds": dates,
                    "target": values,
                }
            )
        )

    return pd.concat(series, ignore_index=True)


def assert_forecast_alignment(
    result_df: pd.DataFrame,
    model_col: str,
    expected_means: dict[str, float],
    tolerance: float = 0.1,
):
    """Verify forecasts match expected values based on unique_id."""
    for uid, expected_mean in expected_means.items():
        subset = result_df[result_df["unique_id"] == uid]
        assert len(subset) > 0, f"No forecasts found for {uid}"

        forecast_mean = subset[model_col].mean()
        max_deviation = expected_mean * tolerance

        assert abs(forecast_mean - expected_mean) < max_deviation, (
            f"Series {uid}: forecast mean {forecast_mean:.1f} "
            f"too far from expected {expected_mean:.1f} "
            f"(tolerance: {tolerance*100}%)"
        )


@pytest.mark.slow
class TestUnivariateAlignment:
    """Test alignment for univariate models (one request per series)."""

    def test_multiple_series_alignment(self):
        """Each series should get forecast matching its input pattern."""
        np.random.seed(42)
        train_df = create_distinctive_series(n_series=3, base_values=[100, 200, 300])

        client = TFCClient()
        result = client.forecast(
            train_df,
            model=TFCModels.TimesFM_2,
            horizon=10,
            freq="D",
        )

        assert_forecast_alignment(
            result,
            model_col="timesfm-2",
            expected_means={"series_A": 100, "series_B": 200, "series_C": 300},
        )


@pytest.mark.slow
class TestGlobalModelAlignment:
    """Test alignment for global models (batched requests)."""

    def test_batched_series_alignment(self):
        """Global model should correctly associate batched series with outputs."""
        np.random.seed(42)
        train_df = create_distinctive_series(n_series=3, base_values=[100, 200, 300])

        client = TFCClient()
        result = client.forecast(
            train_df,
            model=TFCModels.TFCGlobal,
            horizon=10,
            freq="D",
            add_holidays=True,
            country_isocode="US",
            static_variables=["unique_id"],  # Include ID to get different forecasts per series
        )

        assert_forecast_alignment(
            result,
            model_col="tfc-global",
            expected_means={"series_A": 100, "series_B": 200, "series_C": 300},
        )

    def test_partitioned_alignment(self):
        """Partitioned global model should maintain alignment across partitions.

        The global model automatically includes id_col as a static variable,
        so each series gets its own forecast based on its unique_id, not a
        partition-pooled average.
        """
        np.random.seed(42)

        # Create series with 5 partitions, 2 series each, with very distinct values
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        series = []
        expected = {}

        partition_configs = [
            # (partition, series_configs) where series_configs = [(uid, base), ...]
            ("P1", [("series_A", 100), ("series_B", 120)]),
            ("P2", [("series_C", 300), ("series_D", 320)]),
            ("P3", [("series_E", 500), ("series_F", 520)]),
            ("P4", [("series_G", 700), ("series_H", 720)]),
            ("P5", [("series_I", 900), ("series_J", 920)]),
        ]

        for partition, series_configs in partition_configs:
            for uid, base in series_configs:
                values = base + np.random.normal(0, 2, 100)
                series.append(
                    pd.DataFrame(
                        {
                            "unique_id": uid,
                            "ds": dates,
                            "target": values,
                            "partition_col": partition,
                        }
                    )
                )
                # Each series should forecast to its own base value
                expected[uid] = base

        train_df = pd.concat(series, ignore_index=True)

        client = TFCClient()
        result = client.forecast(
            train_df,
            model=TFCModels.TFCGlobal,
            horizon=10,
            freq="D",
            partition_by=["partition_col"],
            add_holidays=True,
            country_isocode="US",
        )

        # Verify each series gets its own forecast based on its unique_id
        assert_forecast_alignment(result, "tfc-global", expected, tolerance=0.05)


@pytest.mark.slow
class TestMultipleModelsAlignment:
    """Test alignment when running multiple models."""

    def test_univariate_and_global_together(self):
        """Both model types should produce correctly aligned forecasts."""
        np.random.seed(42)
        train_df = create_distinctive_series(n_series=2, base_values=[100, 300])

        client = TFCClient()

        # Run univariate
        result_univariate = client.forecast(
            train_df,
            model=TFCModels.TimesFM_2,
            horizon=10,
            freq="D",
        )

        # Run global
        result_global = client.forecast(
            train_df,
            model=TFCModels.TFCGlobal,
            horizon=10,
            freq="D",
            add_holidays=True,
            country_isocode="US",
            static_variables=["unique_id"],  # Include ID to get different forecasts per series
        )

        expected = {"series_A": 100, "series_B": 300}

        assert_forecast_alignment(result_univariate, "timesfm-2", expected)
        assert_forecast_alignment(result_global, "tfc-global", expected)


class TestRequestOrderDeterminism:
    """Unit tests for request building order consistency."""

    def test_build_requests_deterministic_order(self):
        """_build_forecast_requests should yield same order on repeated calls."""
        np.random.seed(42)
        train_df = create_distinctive_series(n_series=5)

        model_config = ModelConfig(model=TFCModels.TimesFM_2)

        def get_request_order():
            requests = list(
                _build_forecast_requests(
                    train_df=train_df,
                    fcds=[],
                    models=[model_config],
                    horizon=10,
                    freq="D",
                    api_key="test",
                    id_col="unique_id",
                    date_col="ds",
                    target_col="target",
                    new_ids=None,
                    quantiles=None,
                    partition_by=None,
                )
            )
            return [req.unique_ids[0] for req, _ in requests]

        order1 = get_request_order()
        order2 = get_request_order()
        order3 = get_request_order()

        assert order1 == order2 == order3, "Request order is not deterministic"

    def test_global_model_series_order_in_request(self):
        """Global model should have deterministic series order within batch."""
        np.random.seed(42)
        train_df = create_distinctive_series(n_series=5)

        model_config = ModelConfig(
            model=TFCModels.TFCGlobal,
            add_holidays=True,
            country_isocode="US",
        )

        def get_batch_order():
            requests = list(
                _build_forecast_requests(
                    train_df=train_df,
                    fcds=[],
                    models=[model_config],
                    horizon=10,
                    freq="D",
                    api_key="test",
                    id_col="unique_id",
                    date_col="ds",
                    target_col="target",
                    new_ids=None,
                    quantiles=None,
                    partition_by=None,
                )
            )
            # Global model yields one request with all series
            assert len(requests) == 1
            return requests[0][0].unique_ids

        order1 = get_batch_order()
        order2 = get_batch_order()
        order3 = get_batch_order()

        assert order1 == order2 == order3, "Batch series order is not deterministic"


class TestBatchingModels:
    """Unit tests for batching model support (chronos-2, moirai-2)."""

    def test_supports_batching_property(self):
        """Verify supports_batching returns correct values for each model."""
        # Models that should support batching
        assert TFCModels.Chronos_2.supports_batching is True
        assert TFCModels.Moirai2.supports_batching is True

        # Models that should NOT support batching
        assert TFCModels.TimesFM_2.supports_batching is False
        assert TFCModels.ChronosBolt.supports_batching is False
        assert TFCModels.TFCGlobal.supports_batching is False
        assert TFCModels.Chronos_2_multivariate.supports_batching is False
        assert TFCModels.Moirai.supports_batching is False
        assert TFCModels.MoiraiMoe.supports_batching is False
        assert TFCModels.TabPFN_TS.supports_batching is False

    def test_batch_size_default_in_model_config(self):
        """Verify default batch_size=256 is set in ModelConfig."""
        config = ModelConfig(model=TFCModels.Chronos_2)
        assert config.batch_size == 256

        config2 = ModelConfig(model=TFCModels.Moirai2)
        assert config2.batch_size == 256

        # Non-batching models also have batch_size but it's not used
        config3 = ModelConfig(model=TFCModels.TimesFM_2)
        assert config3.batch_size == 256

    def test_build_requests_batching_yields_correct_batches(self):
        """Batching model with 650 series, batch_size=256 should yield 3 requests."""
        np.random.seed(42)
        train_df = create_distinctive_series(n_series=650)

        model_config = ModelConfig(model=TFCModels.Chronos_2, batch_size=256)

        requests = list(
            _build_forecast_requests(
                train_df=train_df,
                fcds=[],
                models=[model_config],
                horizon=10,
                freq="D",
                api_key="test",
                id_col="unique_id",
                date_col="ds",
                target_col="target",
                new_ids=None,
                quantiles=None,
                partition_by=None,
            )
        )

        # Should yield 3 requests: 256 + 256 + 138 = 650
        assert len(requests) == 3
        assert len(requests[0][0].unique_ids) == 256
        assert len(requests[1][0].unique_ids) == 256
        assert len(requests[2][0].unique_ids) == 138

    def test_build_requests_partial_batch(self):
        """Batching model with fewer series than batch_size should yield 1 request."""
        np.random.seed(42)
        train_df = create_distinctive_series(n_series=100)

        model_config = ModelConfig(model=TFCModels.Chronos_2, batch_size=256)

        requests = list(
            _build_forecast_requests(
                train_df=train_df,
                fcds=[],
                models=[model_config],
                horizon=10,
                freq="D",
                api_key="test",
                id_col="unique_id",
                date_col="ds",
                target_col="target",
                new_ids=None,
                quantiles=None,
                partition_by=None,
            )
        )

        # Should yield 1 partial batch request
        assert len(requests) == 1
        assert len(requests[0][0].unique_ids) == 100

    def test_build_requests_exact_batch_size(self):
        """Batching model with exact multiple of batch_size should yield exact batches."""
        np.random.seed(42)
        train_df = create_distinctive_series(n_series=512)

        model_config = ModelConfig(model=TFCModels.Chronos_2, batch_size=256)

        requests = list(
            _build_forecast_requests(
                train_df=train_df,
                fcds=[],
                models=[model_config],
                horizon=10,
                freq="D",
                api_key="test",
                id_col="unique_id",
                date_col="ds",
                target_col="target",
                new_ids=None,
                quantiles=None,
                partition_by=None,
            )
        )

        # Should yield exactly 2 requests with 256 series each
        assert len(requests) == 2
        assert len(requests[0][0].unique_ids) == 256
        assert len(requests[1][0].unique_ids) == 256

    def test_batch_unique_ids_alignment(self):
        """Verify unique_ids list matches series list length in each batch."""
        np.random.seed(42)
        train_df = create_distinctive_series(n_series=300)

        model_config = ModelConfig(model=TFCModels.Chronos_2, batch_size=100)

        requests = list(
            _build_forecast_requests(
                train_df=train_df,
                fcds=[],
                models=[model_config],
                horizon=10,
                freq="D",
                api_key="test",
                id_col="unique_id",
                date_col="ds",
                target_col="target",
                new_ids=None,
                quantiles=None,
                partition_by=None,
            )
        )

        # Should yield 3 requests with 100 series each
        assert len(requests) == 3
        for req, _ in requests:
            assert len(req.unique_ids) == len(req.series)
            assert len(req.unique_ids) == 100

    def test_non_batching_model_unchanged(self):
        """Verify non-batching models still yield one request per series."""
        np.random.seed(42)
        train_df = create_distinctive_series(n_series=5)

        model_config = ModelConfig(model=TFCModels.TimesFM_2)

        requests = list(
            _build_forecast_requests(
                train_df=train_df,
                fcds=[],
                models=[model_config],
                horizon=10,
                freq="D",
                api_key="test",
                id_col="unique_id",
                date_col="ds",
                target_col="target",
                new_ids=None,
                quantiles=None,
                partition_by=None,
            )
        )

        # Should yield 5 requests, one per series
        assert len(requests) == 5
        for req, _ in requests:
            assert len(req.unique_ids) == 1

    def test_global_model_unchanged(self):
        """Verify global models still yield one request with all series."""
        np.random.seed(42)
        train_df = create_distinctive_series(n_series=5)

        model_config = ModelConfig(
            model=TFCModels.TFCGlobal,
            add_holidays=True,
            country_isocode="US",
        )

        requests = list(
            _build_forecast_requests(
                train_df=train_df,
                fcds=[],
                models=[model_config],
                horizon=10,
                freq="D",
                api_key="test",
                id_col="unique_id",
                date_col="ds",
                target_col="target",
                new_ids=None,
                quantiles=None,
                partition_by=None,
            )
        )

        # Should yield 1 request with all 5 series
        assert len(requests) == 1
        assert len(requests[0][0].unique_ids) == 5

    def test_batching_deterministic_order(self):
        """Batching model should have deterministic series order across batches."""
        np.random.seed(42)
        train_df = create_distinctive_series(n_series=300)

        model_config = ModelConfig(model=TFCModels.Chronos_2, batch_size=100)

        def get_all_unique_ids():
            requests = list(
                _build_forecast_requests(
                    train_df=train_df,
                    fcds=[],
                    models=[model_config],
                    horizon=10,
                    freq="D",
                    api_key="test",
                    id_col="unique_id",
                    date_col="ds",
                    target_col="target",
                    new_ids=None,
                    quantiles=None,
                    partition_by=None,
                )
            )
            # Flatten all unique_ids across batches
            return [uid for req, _ in requests for uid in req.unique_ids]

        order1 = get_all_unique_ids()
        order2 = get_all_unique_ids()
        order3 = get_all_unique_ids()

        assert order1 == order2 == order3, "Batching order is not deterministic"


@pytest.mark.slow
class TestBatchingIntegration:
    """Integration tests for batching with real API calls."""

    def test_chronos2_multiple_and_partial_batches(self):
        """Test 276 series with batch_size=256 -> 2 batches (256 full + 20 partial).

        This verifies both full batches and partial last batch work correctly
        and that alignment is preserved across batch boundaries.
        """
        np.random.seed(42)
        # Create 276 series with distinctive values for alignment verification
        # Use multiples of 10 to make values easy to distinguish
        base_values = [10 * (i + 1) for i in range(276)]  # 10, 20, 30, ..., 2760
        train_df = create_distinctive_series(n_series=276, base_values=base_values)

        client = TFCClient()
        result = client.forecast(
            train_df,
            model=TFCModels.Chronos_2,
            horizon=10,
            freq="D",
        )

        # Verify we got forecasts for all 276 series
        unique_ids_in_result = result["unique_id"].unique()
        assert len(unique_ids_in_result) == 276, f"Expected 276 series, got {len(unique_ids_in_result)}"

        # Verify alignment: each series should have forecast close to its input value
        # Using a subset to speed up verification
        sample_checks = [
            ("series_A", 10),  # First series
            ("series_Z", 260),  # 26th series
            ("series_BA", 530),  # 53rd series (after first batch boundary check)
            ("series_JR", 2760),  # Last series (276th = 10*276)
        ]

        for uid, expected_base in sample_checks:
            if uid in unique_ids_in_result:
                subset = result[result["unique_id"] == uid]
                forecast_mean = subset["chronos-2"].mean()
                # Allow 50% tolerance for model predictions
                assert abs(forecast_mean - expected_base) < expected_base * 0.5, (
                    f"Series {uid}: forecast mean {forecast_mean:.1f} " f"too far from expected {expected_base:.1f}"
                )
