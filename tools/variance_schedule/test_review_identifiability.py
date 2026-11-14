import math
from datetime import datetime, timedelta, timezone

import polars as pl

from test_parquet_schedule import run_generator
from test_review_model import write_bars


UTC = timezone.utc


def test_identifiable_requested_rate_survives_confounded_nuisance_rates(tmp_path):
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
    # This gap couples an otherwise identified weekday rate to weekend and
    # holiday rates, which are observed only in a fixed proportion.
    timestamps.append(datetime(2024, 1, 16, 15, 5, tzinfo=UTC))
    prices.append(prices[-1] * math.exp(0.30))
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
