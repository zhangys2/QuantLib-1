import math
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl
import pytest

from test_parquet_schedule import run_generator


UTC = timezone.utc
GENERATOR = Path(__file__).with_name("generate_intraday.py")


def write_bars(path, timestamps, prices):
    pl.DataFrame({"observed_at": timestamps, "mid_price": prices}).write_parquet(path)


def test_fully_observed_schedule_ignores_unidentifiable_historical_gap(tmp_path):
    start = datetime(2024, 1, 2, tzinfo=UTC)
    end = datetime(2024, 1, 5, 16, tzinfo=UTC)
    timestamps = []
    cursor = start
    while cursor <= end:
        timestamps.append(cursor)
        cursor += timedelta(minutes=5)
    prices = [100.0 * math.exp(0.01 * (i % 2)) for i in range(len(timestamps))]
    timestamps.append(datetime(2024, 1, 16, 14, 30, tzinfo=UTC))
    prices.append(prices[-1])
    input_path, output = tmp_path / "prices.parquet", tmp_path / "schedule.parquet"
    write_bars(input_path, timestamps, prices)

    result = run_generator(
        input_path, output, "--timezone", "UTC", "--calendar", "nyse",
        "--start", "2024-01-17T15:00:00Z", "--end", "2024-01-17T15:10:00Z",
    )
    assert result.returncode == 0, result.stderr
    rows = pl.read_parquet(output).to_dicts()
    assert len(rows) == 2
    assert all(row["calibration_method"] == "observed" for row in rows)


def test_requested_pool_ignores_unrelated_unidentifiable_gap(tmp_path):
    start = datetime(2024, 1, 8, tzinfo=UTC)
    end = datetime(2024, 1, 13, tzinfo=UTC)
    timestamps, prices = [], []
    cursor, i = start, 0
    while cursor <= end:
        if not (cursor.hour == 15 and cursor.minute == 5):
            timestamps.append(cursor)
            prices.append(100.0 * math.exp(0.02 * math.sin(i * 0.618)))
        cursor += timedelta(minutes=5)
        i += 1
    timestamps.append(datetime(2024, 1, 16, tzinfo=UTC))
    prices.append(prices[-1])
    input_path, output = tmp_path / "prices.parquet", tmp_path / "schedule.parquet"
    write_bars(input_path, timestamps, prices)

    result = run_generator(
        input_path, output, "--timezone", "UTC", "--calendar", "nyse",
        "--start", "2024-01-17T15:00:00Z", "--end", "2024-01-17T15:10:00Z",
    )
    assert result.returncode == 0, result.stderr
    rows = pl.read_parquet(output).to_dicts()
    assert len(rows) == 2
    assert all(row["calibration_method"] == "gap_pool" for row in rows)
    assert all(row["weight"] > 0 for row in rows)


def noisy_prices(path):
    t = lambda day, minute: datetime(2024, 1, day, 0, minute, tzinfo=UTC)
    write_bars(path, [t(1, 0), t(1, 5), t(2, 0), t(2, 5), t(3, 5)],
               [100.0, 100.0 * math.exp(0.05), 100.0 * math.exp(0.05), 100.0, 100.0])


def run_noisy(prices, output, extra=()):
    return subprocess.run(
        [sys.executable, str(GENERATOR), "--prices", str(prices),
         "--timestamp-column", "observed_at", "--price-column", "mid_price",
         "--output", str(output), "--timezone", "UTC", "--calendar", "always",
         "--start", "2024-01-04T00:00:00Z", "--end", "2024-01-04T00:10:00Z", *extra],
        capture_output=True, text=True,
    )


def test_default_does_not_treat_two_samples_as_a_known_profile(tmp_path):
    prices, output = tmp_path / "prices.parquet", tmp_path / "schedule.parquet"
    noisy_prices(prices)
    result = run_noisy(prices, output)
    assert result.returncode == 0, result.stderr
    rows = pl.read_parquet(output).to_dicts()
    assert rows[0]["sample_count"] == 2
    assert rows[0]["calibration_method"] == "gap_pool"


def test_zero_pooled_rate_is_reported(tmp_path):
    prices, output = tmp_path / "prices.parquet", tmp_path / "schedule.parquet"
    noisy_prices(prices)
    result = run_noisy(prices, output, ("--min-samples", "2"))
    assert result.returncode == 0, result.stderr
    rows = pl.read_parquet(output).to_dicts()
    assert rows[0]["calibration_method"] == "observed"
    assert rows[1]["calibration_method"] == "gap_pool"
    assert rows[1]["weight"] == pytest.approx(0.0, abs=1e-14)
    assert "warning" in result.stderr.lower()
    assert "weekday" in result.stderr.lower()
    assert "zero" in result.stderr.lower()
