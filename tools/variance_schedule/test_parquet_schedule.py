import json
import math
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl
import pytest


GENERATOR = Path(__file__).with_name("generate_intraday.py")
UTC = timezone.utc
ET = ZoneInfo("America/New_York")


def run_generator(prices, output, *arguments):
    return subprocess.run(
        [sys.executable, str(GENERATOR), "--prices", str(prices),
         "--timestamp-column", "observed_at", "--price-column", "mid_price",
         "--output", str(output), "--min-samples", "2", *arguments],
        capture_output=True, text=True,
    )


def test_parquet_intraday_pattern_and_partial_intervals(tmp_path):
    timestamp = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps, prices = [timestamp], [100.0]
    for i in range(3 * 288):
        minute = timestamp.hour * 60 + timestamp.minute
        variance = 0.0004 if minute in (600, 605) else 0.0001
        price = prices[-1] * math.exp((1 if i % 2 == 0 else -1) * math.sqrt(variance))
        timestamp += timedelta(minutes=5)
        timestamps.append(timestamp)
        prices.append(price)
    input_path, output = tmp_path / "prices.parquet", tmp_path / "schedule.parquet"
    pl.DataFrame({"observed_at": timestamps, "mid_price": prices}).write_parquet(input_path)

    result = run_generator(
        input_path, output, "--timezone", "UTC", "--calendar", "always",
        "--start", "2024-01-02T09:57:30Z", "--end", "2024-01-02T10:12:30Z",
    )
    assert result.returncode == 0, result.stderr
    schedule = pl.read_parquet(output)
    assert schedule.height == 4
    rows = schedule.to_dicts()
    assert rows[0]["start_utc"] == datetime(2024, 1, 2, 9, 57, 30, tzinfo=UTC)
    assert rows[-1]["end_utc"] == datetime(2024, 1, 2, 10, 12, 30, tzinfo=UTC)
    assert all(row["category"] == "weekday" for row in rows)
    assert all(row["calibration_method"] == "observed" for row in rows)
    assert all(row["sample_count"] == 3 for row in rows)
    assert rows[1]["weight"] / rows[0]["weight"] == pytest.approx(4.0, rel=1e-9)
    assert rows[2]["weight"] / rows[3]["weight"] == pytest.approx(4.0, rel=1e-9)
    total = math.fsum(row["weighted_days"] for row in rows)
    assert rows[0]["remaining_fraction"] == pytest.approx(1.0)
    for i, row in enumerate(rows):
        expected = math.fsum(item["weighted_days"] for item in rows[i:])
        assert row["remaining_weighted_days"] == pytest.approx(expected)
        assert row["remaining_fraction"] == pytest.approx(expected / total)
    metadata = json.loads(pl.read_parquet_metadata(output)["variance_schedule"])
    assert metadata["timezone"] == "UTC"
    assert metadata["calendar"] == "always"


def test_unobserved_closed_hours_are_fitted_from_price_gaps(tmp_path):
    holidays = {date(2024, 1, 15), date(2024, 2, 19)}
    d = date(2024, 1, 2)
    previous = None
    price = 100.0
    counts = defaultdict(int)
    timestamps, prices = [], []
    session = 0
    while d <= date(2024, 2, 27):
        if d.weekday() < 5 and d not in holidays:
            if previous is not None:
                gap = (d - previous).days
                variance = (287 * 0.000025
                            + (576 * 0.00001 if gap >= 3 else 0.0)
                            + (288 * 0.000015 if gap == 4 else 0.0))
                sign = 1 if counts[gap] % 2 == 0 else -1
                price *= math.exp(sign * math.sqrt(variance))
                counts[gap] += 1
            timestamps.append(datetime.combine(d, time(9, 30), ET))
            prices.append(price)
            if d != date(2024, 2, 27):
                price *= math.exp((1 if session % 2 == 0 else -1) * 0.01)
            timestamps.append(datetime.combine(d, time(9, 35), ET))
            prices.append(price)
            session += 1
            previous = d
        d += timedelta(days=1)
    input_path, output = tmp_path / "prices.parquet", tmp_path / "schedule.parquet"
    pl.DataFrame({"observed_at": timestamps, "mid_price": prices}).write_parquet(input_path)

    result = run_generator(
        input_path, output, "--timezone", "America/New_York", "--calendar", "nyse",
        "--start", "2024-01-05T08:00:00-05:00", "--end", "2024-01-16T09:35:00-05:00",
    )
    assert result.returncode == 0, result.stderr
    rows = pl.read_parquet(output).to_dicts()
    by_slot = {(row["local_date"], row["minute_of_day"]): row for row in rows}
    observed = by_slot[(date(2024, 1, 5), 570)]
    overnight = by_slot[(date(2024, 1, 5), 480)]
    weekend = by_slot[(date(2024, 1, 6), 720)]
    holiday = by_slot[(date(2024, 1, 15), 720)]
    assert observed["calibration_method"] == "observed"
    assert overnight["calibration_method"] == "gap_pool"
    assert weekend["category"] == "weekend"
    assert holiday["category"] == "holiday"
    assert observed["weight"] / overnight["weight"] == pytest.approx(4 * 38 / 39, rel=1e-8)
    assert weekend["weight"] / overnight["weight"] == pytest.approx(0.4, rel=1e-8)
    assert holiday["weight"] / overnight["weight"] == pytest.approx(0.6, rel=1e-8)
