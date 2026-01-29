"""
Scalability test for TFCClient.

Usage:
    uv run python src/tests/test_scalability.py [--num_series 1000] [--model chronos-2] [--seed 42] [--batch_size 256] [--series_length 110]

Requires TFC_API_KEY environment variable.
"""

import argparse
import logging
import time
from datetime import datetime, timedelta

import pandas as pd

from theforecastingcompany import TFCClient
from theforecastingcompany.utils import TFCModels

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def mulberry32(seed: int):
    """Seeded PRNG (mulberry32) for deterministic generation - matches k6 implementation."""

    def rand():
        nonlocal seed
        seed = (seed + 0x6D2B79F5) & 0xFFFFFFFF
        t = seed
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t = (t ^ (t + ((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return rand


def generate_dataset(num_series: int, seed: int, num_points: int = 110) -> pd.DataFrame:
    """Generate synthetic time series dataset."""
    start_date = datetime(2001, 1, 6)
    dates = [start_date + timedelta(days=i) for i in range(num_points)]

    rows = []
    for i in range(num_series):
        series_seed = seed + i
        rand = mulberry32(series_seed)

        base_value = 50 + rand() * 950  # 50-1000 range
        scale = 0.5 + rand() * 1.5  # variation factor

        value = base_value
        for date in dates:
            # Random walk with mean reversion (matches k6 logic)
            value += (rand() - 0.5) * 20 * scale
            value += (base_value - value) * 0.05  # mean reversion
            rows.append(
                {
                    "unique_id": f"seed_{series_seed}",
                    "ds": date,
                    "target": round(value),
                }
            )

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="TFCClient scalability test")
    parser.add_argument(
        "--num_series",
        type=int,
        default=1000,
        help="Number of time series to generate (default: 1000)",
    )
    parser.add_argument(
        "--model",
        default="chronos-2",
        help="Model to use (default: timesfm-2)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Starting seed for generation (default: 42)",
    )
    parser.add_argument(
        "--max_retries",
        type=int,
        default=3,
        help="Maximum number of retries (default: 3)",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=256,
        help="Number of series per batch for batching-enabled models (default: 256)",
    )
    parser.add_argument(
        "--series_length",
        type=int,
        default=110,
        help="Number of data points per time series (default: 110)",
    )
    args = parser.parse_args()

    gen_start = time.time()
    logger.info(
        f"Generating time series dataset: {args.num_series} series (seed={args.seed}..{args.seed + args.num_series - 1})"
    )
    df = generate_dataset(args.num_series, args.seed, args.series_length)
    gen_elapsed = time.time() - gen_start
    logger.info(f"Generated {df['unique_id'].nunique()} time series, {len(df)} rows in {gen_elapsed:.2f}s")

    client = TFCClient(max_tries=args.max_retries)
    model = TFCModels(args.model)

    start = time.time()
    forecast_df = client.forecast(
        train_df=df,
        model=model,
        horizon=12,
        freq="D",
        id_col="unique_id",
        date_col="ds",
        target_col="target",
        batch_size=args.batch_size,
    )
    elapsed = time.time() - start

    logger.info(f"Forecast completed in {elapsed:.2f}s")
    logger.info(f"Throughput: {args.num_series / elapsed:.2f} series/sec")
    logger.info(f"Forecast shape: {forecast_df.shape}")
    logger.debug(f"Forecast head:\n{forecast_df.head(10)}")


if __name__ == "__main__":
    main()
