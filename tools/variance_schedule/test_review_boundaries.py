import os
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import pytest

from test_generate import write_prices
from test_parquet_boundaries import continuous_prices
from test_parquet_schedule import run_generator


ROOT = Path(__file__).parent
UTC = timezone.utc


def test_ambiguous_local_midnight_requires_explicit_offset(tmp_path):
    prices, output = tmp_path / "prices.parquet", tmp_path / "schedule.parquet"
    continuous_prices(prices, 3)
    result = run_generator(
        prices, output, "--timezone", "America/Havana", "--calendar", "always",
        "--start", "2000-10-29", "--end", "2000-10-30",
    )
    assert result.returncode != 0
    assert "ambiguous" in result.stderr.lower()
    assert "offset" in result.stderr.lower()
    assert not output.exists()

    result = run_generator(
        prices, output, "--timezone", "America/Havana", "--calendar", "always",
        "--start", "2000-10-29T00:00:00-04:00", "--end", "2000-10-29T00:00:00-05:00",
    )
    assert result.returncode == 0, result.stderr
    assert pl.read_parquet(output).height == 12


def test_repeated_dst_hour_has_distinct_fold_values(tmp_path):
    prices, output = tmp_path / "prices.parquet", tmp_path / "schedule.parquet"
    continuous_prices(prices, 3)
    result = run_generator(
        prices, output, "--timezone", "America/New_York", "--calendar", "always",
        "--start", "2024-11-03T01:00:00-04:00", "--end", "2024-11-03T02:00:00-05:00",
    )
    assert result.returncode == 0, result.stderr
    rows = pl.read_parquet(output).to_dicts()
    assert len(rows) == 24
    assert [row["minute_of_day"] for row in rows] == list(range(60, 120, 5)) * 2
    assert [row["fold"] for row in rows] == [0] * 12 + [1] * 12
    assert rows[0]["start_utc"] == datetime(2024, 11, 3, 5, tzinfo=UTC)
    assert rows[-1]["end_utc"] == datetime(2024, 11, 3, 7, tzinfo=UTC)


@pytest.mark.skipif(os.name == "nt", reason="POSIX umask and file modes")
@pytest.mark.parametrize("kind", ["daily", "intraday"])
def test_schedule_writer_respects_umask(tmp_path, kind):
    output = tmp_path / ("schedule.json" if kind == "daily" else "schedule.parquet")
    output.write_bytes(b"old schedule")
    output.chmod(0o600)
    if kind == "daily":
        prices = tmp_path / "prices.csv"
        write_prices(prices)
        command = [sys.executable, str(ROOT / "generate.py"), "--prices", str(prices),
                   "--start", "2024-03-09", "--end", "2024-03-12", "--output", str(output)]
    else:
        prices = tmp_path / "prices.parquet"
        continuous_prices(prices, 3)
        command = [sys.executable, str(ROOT / "generate_intraday.py"), "--prices", str(prices),
                   "--timestamp-column", "observed_at", "--price-column", "mid_price",
                   "--timezone", "UTC", "--calendar", "always", "--min-samples", "2",
                   "--start", "2024-01-04T00:00:00Z", "--end", "2024-01-04T00:10:00Z",
                   "--output", str(output)]
    result = subprocess.run(command, capture_output=True, text=True,
                            preexec_fn=lambda: os.umask(0o027))
    assert result.returncode == 0, result.stderr
    assert stat.S_IMODE(output.stat().st_mode) == 0o640


@pytest.mark.parametrize("boundary", ["20240105", "2024-W01-5"])
def test_daily_rejects_noncanonical_date_only_boundary(tmp_path, boundary):
    prices = tmp_path / "prices.csv"
    output = tmp_path / "schedule.json"
    write_prices(prices)
    result = subprocess.run(
        [sys.executable, str(ROOT / "generate.py"), "--prices", str(prices),
         "--start", boundary, "--end", "2024-03-12", "--output", str(output)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert not output.exists()
