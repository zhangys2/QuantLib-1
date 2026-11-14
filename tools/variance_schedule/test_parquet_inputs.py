import polars as pl
import pytest

from test_parquet_boundaries import continuous_prices
from test_parquet_schedule import run_generator


@pytest.mark.parametrize("fault", ["naive", "duplicate", "submicrosecond"])
def test_invalid_price_timestamps_do_not_replace_schedule(tmp_path, fault):
    prices = tmp_path / "prices.parquet"
    output = tmp_path / "schedule.parquet"
    continuous_prices(prices, 3)
    bars = pl.read_parquet(prices)
    if fault == "naive":
        bars = bars.with_columns(pl.col("observed_at").dt.replace_time_zone(None))
    elif fault == "duplicate":
        bars = pl.concat([bars, bars.head(1)])
    else:
        bars = bars.with_columns(
            (pl.col("observed_at").dt.epoch("ns") + 1)
            .cast(pl.Datetime("ns", "UTC"))
            .alias("observed_at")
        )
    bars.write_parquet(prices)
    output.write_bytes(b"existing schedule")
    result = run_generator(
        prices, output, "--timezone", "UTC", "--calendar", "always",
        "--start", "2024-01-04T00:00:00Z", "--end", "2024-01-04T01:00:00Z",
    )
    assert result.returncode != 0
    assert output.read_bytes() == b"existing schedule"
